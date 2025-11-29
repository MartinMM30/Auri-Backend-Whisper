# realtime/realtime_ws.py

import io
import json
import logging
import wave

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from auribrain.auri_mind import AuriMind

# -------------------------------------------------------
# LOGGING PROFESIONAL (se ve en logs de Railway)
# -------------------------------------------------------
logger = logging.getLogger("uvicorn.error")

router = APIRouter()
client = AsyncOpenAI()          # Usa OPENAI_API_KEY de las env vars
auri = AuriMind()               # Motor de pensamiento de Auri

STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "alloy"              # ⚠️ Voz válida por defecto
SAMPLE_RATE = 16000


# -------------------------------------------------------
# PCM → WAV
# -------------------------------------------------------
def pcm16_to_wav(pcm_bytes: bytes, sample_rate: int):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)          # 16-bit PCM
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)
    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# SESSION
# -------------------------------------------------------
class RealtimeSession:
    def __init__(self):
        self.pcm_buffer = bytearray()

    def append_pcm(self, data: bytes):
        self.pcm_buffer.extend(data)

    def clear(self):
        self.pcm_buffer = bytearray()


# -------------------------------------------------------
# WEBSOCKET
# -------------------------------------------------------
@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    logger.info("🔌 Cliente conectado al WS /realtime")

    session = RealtimeSession()

    try:
        while True:
            msg = await ws.receive()

            # Bytes = audio PCM del micro
            if msg.get("bytes") is not None:
                session.append_pcm(msg["bytes"])
                continue

            # Texto JSON
            if msg.get("text") is not None:
                try:
                    data = json.loads(msg["text"])
                except Exception:
                    logger.warning("⚠ JSON inválido recibido en WS")
                    continue

                await handle_json(ws, session, data)

    except WebSocketDisconnect:
        logger.info("❌ Cliente desconectado de /realtime")
    except Exception as e:
        logger.exception("🔥 ERROR en WS principal: %s", e)


# -------------------------------------------------------
# HANDLER DE MENSAJES JSON
# -------------------------------------------------------
async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):
    t = msg.get("type")

    # Handshake inicial
    if t == "client_hello":
        await ws.send_json({"type": "hello_ok"})
        logger.info("🙋 HELLO: %s", msg)

    # Inicio de sesión de voz
    elif t == "start_session":
        logger.info("🎤 Inicio de sesión de voz")
        session.clear()
        # El móvil ya pone el slime en 'listening'; aquí no marcamos thinking todavía.

    # Fin de audio: procesar STT + AuriMind + TTS
    elif t == "audio_end":
        await process_stt_tts(ws, session)

    # Comando por texto (teclado)
    elif t == "text_command":
        txt = (msg.get("text") or "").strip()
        if not txt:
            return
        await process_text_only(ws, txt)

    # Ping opcional
    elif t == "ping":
        await ws.send_json({"type": "pong"})


# -------------------------------------------------------
# PIPELINE COMPLETO: PCM -> STT -> AuriMind -> TTS
# -------------------------------------------------------
async def process_stt_tts(ws: WebSocket, session: RealtimeSession):
    if len(session.pcm_buffer) == 0:
        logger.info("🎙 Sesión sin audio, nada que transcribir")
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})
        return

    logger.info("🎙 Recibidos %d bytes PCM", len(session.pcm_buffer))
    await ws.send_json({"type": "thinking", "state": True})

    try:
        # ------- PCM → WAV ----------
        wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
        wav.name = "audio.wav"

        # --------------- STT ---------------------
        logger.info("🧠 Whisper STT…")
        stt = await client.audio.transcriptions.create(
            model=STT_MODEL,
            file=wav,
        )

        text = (getattr(stt, "text", "") or "").strip()
        logger.info("📝 Texto STT: %s", text)

        await ws.send_json({"type": "stt_final", "text": text})

        if not text:
            await ws.send_json({
                "type": "reply_final",
                "text": "No escuché nada claro, ¿puedes repetirlo?"
            })
            return

        # --------------- AuriMind (pensar respuesta) -----------
        reply = await think_with_auri(text)

        # --------------- TTS + envío ---------------------------
        await send_tts_reply(ws, reply)

    except Exception as e:
        logger.exception("🔥 Error en pipeline STT+LLM+TTS: %s", e)
        await ws.send_json({
            "type": "reply_final",
            "text": "Lo siento, tuve un problema interno al procesar tu voz."
        })
    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})
        session.clear()


# -------------------------------------------------------
# MODO SOLO TEXTO (sin audio de entrada)
# -------------------------------------------------------
async def process_text_only(ws: WebSocket, user_text: str):
    logger.info("✉ Texto directo recibido: %s", user_text)
    await ws.send_json({"type": "thinking", "state": True})

    try:
        reply = await think_with_auri(user_text)
        await send_tts_reply(ws, reply)
    except Exception:
        logger.exception("🔥 Error en pipeline solo texto")
        await ws.send_json({
            "type": "reply_final",
            "text": "Lo siento, tuve un problema interno al pensar tu respuesta."
        })
    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})


# -------------------------------------------------------
# AuriMind: pensar respuesta
# -------------------------------------------------------
async def think_with_auri(user_text: str) -> str:
    try:
        result = auri.think(user_text) or {}
        reply = (result.get("final") or result.get("raw") or "").strip()

        if not reply:
            reply = (
                "Lo siento, no supe qué responder exactamente, "
                "pero seguiré aprendiendo de ti."
            )

        logger.info("🧠 AuriMind reply: %s", reply)
        return reply

    except Exception as e:
        logger.exception("🔥 Error en AuriMind.think: %s", e)
        return "Lo siento, tuve un problema interno al pensar tu respuesta."


# -------------------------------------------------------
# TTS STREAMING (MP3 — compatible 100% con Railway)
# -------------------------------------------------------
async def send_tts_reply(ws: WebSocket, text: str):
    logger.info("🔊 TTS reply: %s", text)

    # Enviar texto al cliente (UI)
    await ws.send_json({"type": "reply_partial", "text": text[:80]})
    await ws.send_json({"type": "reply_final", "text": text})

    # === TTS MP3 (sin PCM16, sin sample rate, sin formato) ===
    try:
        # Stream MP3 desde la API moderna (sin format ni sample_rate)
        response = await client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,   # gpt-4o-mini-tts
            voice=VOICE_ID,    # alloy
            input=text         # texto a convertir
        )

        async with response:
            async for chunk in response.iter_bytes():
                # El chunk ya es MP3 raw
                await ws.send_bytes(chunk)

        logger.info("✅ Respuesta TTS (MP3) enviada por streaming")

    except Exception as e:
        logger.exception("🔥 Error generando TTS: %s", e)
        # Mostramos solo el texto final; audio no es obligatorio
        await ws.send_json({
            "type": "tts_error",
            "error": str(e)
        })

