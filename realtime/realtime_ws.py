# realtime/realtime_ws.py

import io
import json
import logging
import wave

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from auribrain.auri_singleton import auri
from realtime.realtime_broadcast import realtime_broadcast

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


def pcm16_to_wav(pcm_bytes: bytes, sample_rate: int):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)
    buffer.seek(0)
    return buffer


# ============================================================
# SESSION
# ============================================================

class RealtimeSession:
    def __init__(self):
        self.pcm_buffer = bytearray()
        self.firebase_uid = None  # usuario real de la sesión

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

                # 🚀 NUEVO — sincronizar plan desde Firebase
                try:
                    auri.context.sync_plan_from_firebase()
                    auri.context.mark_ready()
                    logger.info(f"✅ Contexto sincronizado para UID={uid}")
                except Exception as e:
                    logger.error(f"⚠ Error sincronizando plan desde Firebase: {e}")

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
            # 🚀 NUEVO: re-sincronizar plan desde Firebase
            try:
                auri.context.sync_plan_from_firebase()
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
                # 🚀 NUEVO: re-sincronizar plan desde Firebase
            try:
                auri.context.sync_plan_from_firebase()
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
# TTS STREAMING
# ============================================================

async def send_tts(ws: WebSocket, text: str, voice_id: str = "alloy"):
    await ws.send_json({"type": "reply_partial", "text": text[:60]})
    await ws.send_json({"type": "reply_final", "text": text})

    try:
        async with client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=voice_id,
            input=text,
            response_format="mp3",
        ) as resp:
            async for chunk in resp.iter_bytes():
                await ws.send_bytes(chunk)

        await ws.send_json({"type": "tts_end"})

    except Exception as e:
        logger.exception("🔥 TTS error: %s", e)
        await ws.send_json({"type": "tts_error", "error": str(e)})
        await ws.send_json({"type": "tts_end"})
