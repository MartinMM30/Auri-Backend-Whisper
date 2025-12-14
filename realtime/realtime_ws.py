# realtime/realtime_ws.py

import io
import json
import logging
import wave
import aiohttp
import asyncio
import time


from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from auribrain.auri_singleton import auri
from realtime.realtime_broadcast import realtime_broadcast
from auribrain.subscription.service import get_subscription
from typing import Optional



logger = logging.getLogger("uvicorn.error")

router = APIRouter()
client = AsyncOpenAI()

STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
SAMPLE_RATE = 16000

SAFE_ACTION_TYPES = {
    "create_reminder",
    "delete_reminder",
    "edit_reminder",
    "open_reminders_list",
}

# ============================================================
# RVC CONFIG
# ============================================================

RVC_URL = "http://127.0.0.1:8899/rvc"  # IP + puerto del servicio RVC

RVC_VOICES = {
    "auri_gf",
    "myGF_voice",  # alias legacy
}



def pcm16_to_wav(pcm_bytes: bytes, sample_rate: int):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)
    buffer.seek(0)
    return buffer

def is_rvc_voice(voice_id: str) -> bool:
    return voice_id in RVC_VOICES


# ============================================================
# SESSION
# ============================================================

class RealtimeSession:
    def __init__(self):
        self.pcm_buffer = bytearray()
        self.firebase_uid = None  # usuario real de la sesión
        self._last_plan_sync_ts = 0.0  # throttle
    def should_sync_plan(self, cooldown_sec: float = 30.0) -> bool:
        now = time.time()
        if now - self._last_plan_sync_ts >= cooldown_sec:
            self._last_plan_sync_ts = now
            return True
        return False

    def append_pcm(self, data: bytes):
        self.pcm_buffer.extend(data)

    def clear(self):
        self.pcm_buffer.clear()


# ============================================================
# MAIN WEBSOCKET HANDLER
# ============================================================

@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    realtime_broadcast.register(ws)
    logger.info("🔌 Cliente conectado al WS /realtime")

    session = RealtimeSession()

    try:
        while True:
            msg = await ws.receive()

            if msg["type"] == "websocket.disconnect":
                logger.info("❌ Cliente desconectado")
                break

            if msg.get("bytes") is not None:
                session.append_pcm(msg["bytes"])
                continue

            if msg.get("text") is not None:
                try:
                    data = json.loads(msg["text"])
                    await handle_json(ws, session, data)
                except Exception as e:
                    logger.warning(f"⚠ JSON inválido: {e}")
                continue

    except WebSocketDisconnect:
        logger.info("❌ Cliente desconectado (exception)")

    except Exception as e:
        logger.exception(f"🔥 ERROR en WS principal: {e}")

    finally:
        realtime_broadcast.unregister(ws)
        logger.info("🔌 WS cerrado")
        
# ============================================================
# PLAN SYNC (BACKEND SOURCE OF TRUTH)
# ============================================================

def _safe_plan_from_sub(sub: Optional[dict]) -> str:
    try:
        plan = (sub or {}).get("plan", "free")
        return (plan or "free").strip().lower()
    except Exception:
        return "free"

def _sync_plan_from_backend(uid: str) -> str:
    """
    Obtiene el plan desde el backend de suscripciones (get_subscription)
    y lo inyecta en ContextEngine.
    """
    try:
        sub = get_subscription(uid)  # puede ser in-memory o DB
        plan = _safe_plan_from_sub(sub)
        auri.context.set_user_plan(plan)
        return plan
    except Exception as e:
        logger.error(f"⚠ Error sync plan desde backend (UID={uid}): {e}")
        auri.context.set_user_plan("free")
        return "free"



# ============================================================
# JSON HANDLER
# ============================================================

async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):
    t = msg.get("type")

    # --------------------------
    # CLIENT HELLO
    # --------------------------
    if t == "client_hello":
        uid = msg.get("firebase_uid")
        session.firebase_uid = uid

        logger.info(f"🙋 HELLO recibido — UID: {uid}")

        if uid:
            try:
                auri.set_user_uid(uid)

                # ✅ Sync plan desde backend (source of truth)
                plan = _sync_plan_from_backend(uid)

                auri.context.mark_ready()
                logger.info(f"✅ Contexto listo — plan={plan} UID={uid}")
                logger.info(f"🔗 Auri asociado al usuario {uid}")

            except Exception as e:
                logger.error(f"⚠ Error asignando UID a AuriMind: {e}")

        await ws.send_json({"type": "hello_ok"})
        return



    # --------------------------
    # START SESSION
    # --------------------------
    elif t == "start_session":
        logger.info("🎤 Inicio sesión de voz")
        session.clear()
        return

    # --------------------------
    # AUDIO END
    # --------------------------
    elif t == "audio_end":
        await process_stt_tts(ws, session)
        return

    # --------------------------
    # TEXT ONLY MODE
    # --------------------------
    elif t == "text_command":
        txt = (msg.get("text") or "").strip()
        if txt:
            await process_text_only(ws, session, txt)
        return

    # --------------------------
    # PING
    # --------------------------
    elif t == "ping":
        await ws.send_json({"type": "pong"})
        return


# ============================================================
# SAFE ACTION SENDER
# ============================================================

async def _safe_send_action(ws: WebSocket, action: dict):
    if not isinstance(action, dict):
        logger.warning(f"⚠ Acción inválida (no dict): {action}")
        return

    a_type = action.get("type")
    if a_type not in SAFE_ACTION_TYPES:
        logger.warning(f"⚠ Acción ignorada (no segura): {action}")
        return

    payload = action.get("payload") or {}

    try:
        await ws.send_json({
            "type": "action",
            "action": a_type,
            "payload": payload,
        })
    except Exception as e:
        logger.exception(f"🔥 Error enviando acción por WS: {e}")


# ============================================================
# STT + LLM + TTS PIPELINE
# ============================================================

async def process_stt_tts(ws: WebSocket, session: RealtimeSession):
    if len(session.pcm_buffer) == 0:
        await ws.send_json({"type": "reply_final", "text": "No escuché nada."})
        return

    logger.info("🎙 Recibidos %d bytes PCM", len(session.pcm_buffer))

    wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
    wav.name = "audio.wav"

    try:
        # --------------------------
        # STT
        # --------------------------
        stt = await client.audio.transcriptions.create(
            model=STT_MODEL,
            file=wav,
        )
        text = (getattr(stt, "text", "") or "").strip()
        logger.info("📝 Texto STT: %s", text)

        # --------------------------
        # USER BINDING
        # --------------------------
        if session.firebase_uid:
            try:
                auri.set_user_uid(session.firebase_uid)
            except Exception as e:
                logger.error(f"⚠ No se pudo asignar UID en STT: {e}")

            # ✅ Re-sync plan solo ocasionalmente (evita overhead)
            try:
                if session.should_sync_plan(30.0):  # cada 30s
                    plan = _sync_plan_from_backend(session.firebase_uid)
                    logger.info(f"🔄 Plan re-sync (STT): {plan}")
            except Exception as e:
                logger.error(f"⚠ No se pudo sincronizar plan en STT: {e}")



        # --------------------------
        # THINK + ACTIONS
        # --------------------------
        think_res = auri.think(text)
        reply_text = think_res.get("final") or think_res.get("raw") or ""
        action = think_res.get("action")
        voice_id = think_res.get("voice_id") or "alloy"

        logger.info("🧠 Auri reply: %s", reply_text)

        # --------------------------
        # TTS
        # --------------------------
        await send_tts(ws, reply_text, voice_id=voice_id)

        # --------------------------
        # ACTION (SAFE)
        # --------------------------
        if action:
            await _safe_send_action(ws, action)

    except Exception as e:
        logger.exception("🔥 Error en pipeline STT→LLM→TTS: %s", e)
        await ws.send_json({
            "type": "reply_final",
            "text": "Hubo un problema procesando tu voz."
        })

    session.clear()


# ============================================================
# TEXT ONLY PIPELINE
# ============================================================

async def process_text_only(ws: WebSocket, session: RealtimeSession, text: str):
    try:
        if session.firebase_uid:
            try:
                auri.set_user_uid(session.firebase_uid)
            except Exception as e:
                logger.error(f"⚠ No se pudo asignar UID en TEXT: {e}")

            try:
                if session.should_sync_plan(30.0):
                    plan = _sync_plan_from_backend(session.firebase_uid)
                    logger.info(f"🔄 Plan re-sync (TEXT): {plan}")
            except Exception as e:
                logger.error(f"⚠ No se pudo sincronizar plan en TEXT: {e}")



        think_res = auri.think(text)
        reply_text = think_res.get("final") or think_res.get("raw") or ""
        action = think_res.get("action")
        voice_id = think_res.get("voice_id") or "alloy"

        await send_tts(ws, reply_text, voice_id=voice_id)

        if action:
            await _safe_send_action(ws, action)

    except Exception as e:
        logger.exception("🔥 Error en pipeline TEXT→LLM→TTS: %s", e)
        await ws.send_json({
            "type": "reply_final",
            "text": "Hubo un problema procesando tu mensaje."
        })


# ============================================================
# TTS + RVC PIPELINE FINAL
# ============================================================

async def send_tts(ws: WebSocket, text: str, voice_id: str = "alloy"):
    # Mensajes de texto (UI)
    await ws.send_json({"type": "reply_partial", "text": text[:60]})
    await ws.send_json({"type": "reply_final", "text": text})

    try:
        # --------------------------------------------------
        # 1️⃣ TTS BASE (siempre Alloy, WAV)
        # --------------------------------------------------
        audio_bytes = b""

        async with client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice="alloy",                 # SIEMPRE Alloy como base
            input=text,
            response_format="wav",         # RVC necesita WAV
        ) as resp:
            async for chunk in resp.iter_bytes():
                audio_bytes += chunk

        # --------------------------------------------------
        # 2️⃣ ¿PASA POR RVC?
        # --------------------------------------------------
        if is_rvc_voice(voice_id):
            logger.info("🎙 Aplicando RVC para voice_id=%s", voice_id)

            try:
                async with aiohttp.ClientSession() as session:
                    data = aiohttp.FormData()
                    data.add_field(
                        "file",
                        audio_bytes,
                        filename="input.wav",
                        content_type="audio/wav",
                    )

                    async with session.post(RVC_URL, data=data, timeout=60) as r:
                        if r.status == 200:
                            audio_bytes = await r.read()
                        else:
                            logger.error("⚠ RVC falló (status=%s), usando Alloy", r.status)

            except Exception as rvc_err:
                logger.error("⚠ Error RVC, fallback Alloy: %s", rvc_err)

        # --------------------------------------------------
        # 3️⃣ Enviar audio final a Flutter
        # --------------------------------------------------
        await ws.send_bytes(audio_bytes)
        await ws.send_json({"type": "tts_end"})

    except Exception as e:
        logger.exception("🔥 TTS/RVC error: %s", e)
        await ws.send_json({"type": "tts_error", "error": str(e)})
        await ws.send_json({"type": "tts_end"})

