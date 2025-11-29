import io
import json
import logging
import wave

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from auribrain.auri_mind import AuriMind

logger = logging.getLogger("uvicorn.error")

router = APIRouter()
client = AsyncOpenAI()                # Usa OPENAI_API_KEY automáticamente
auri = AuriMind()

STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "alloy"
SAMPLE_RATE = 16000


# -------------------------------------------------------
# PCM → WAV
# -------------------------------------------------------
def pcm16_to_wav(pcm_bytes: bytes, sample_rate: int):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)  # PCM16
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
        self.pcm_buffer.clear()


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

            # Recibimos audio PCM del micro
            if msg.get("bytes") is not None:
                session.append_pcm(msg["bytes"])
                continue

            # Recibimos JSON (texto)
            if msg.get("text") is not None:
                try:
                    data = json.loads(msg["text"])
                except Exception:
                    logger.warning("⚠ JSON inválido recibido")
                    continue

                await handle_json(ws, session, data)

    except WebSocketDisconnect:
        logger.info("❌ Cliente desconectado")
    except Exception as e:
        logger.exception("🔥 ERROR en WS principal: %s", e)


# -------------------------------------------------------
# HANDLER DE MENSAJES JSON
# -------------------------------------------------------
async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):
    t = msg.get("type")

    if t == "client_hello":
        await ws.send_json({"type": "hello_ok"})
        logger.info("🙋 HELLO: %s", msg)

    elif t == "start_session":
        logger.info("🎤 Inicio de sesión de voz")
        session.clear()

    elif t == "audio_end":
        await process_stt_tts(ws, session)

    elif t == "text_command":
        txt = (msg.get("text") or "").strip()
        if txt:
            await process_text_only(ws, txt)

    elif t == "ping":
        await ws.send_json({"type": "pong"})


# -------------------------------------------------------
# PIPELINE COMPLETO: PCM → STT → AuriMind → TTS
# -------------------------------------------------------
async def process_stt_tts(ws: WebSocket, session: RealtimeSession):
    if len(session.pcm_buffer) == 0:
        logger.info("🎙 No hay audio")
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})
        return

    logger.info("🎙 Recibidos %d bytes PCM", len(session.pcm_buffer))
    await ws.send_json({"type": "thinking", "state": True})

    try:
        # PCM → WAV
        wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
        wav.name = "audio.wav"

        # ---- STT ----
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

        # ---- THINK ----
        reply = await think_with_auri(text)

        # ---- TTS ----
        await send_tts_reply(ws, reply)

    except Exception as e:
        logger.exception("🔥 Error en pipeline: %s", e)
        await ws.send_json({
            "type": "reply_final",
            "text": "Lo siento, tuve un problema interno procesando tu voz."
        })

    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})
        session.clear()


# -------------------------------------------------------
# SOLO TEXTO (teclado)
# -------------------------------------------------------
async def process_text_only(ws: WebSocket, user_text: str):
    logger.info("✉ Texto directo: %s", user_text)
    await ws.send_json({"type": "thinking", "state": True})

    try:
        reply = await think_with_auri(user_text)
        await send_tts_reply(ws, reply)
    except Exception:
        logger.exception("🔥 Error en texto directo")
        await ws.send_json({
            "type": "reply_final",
            "text": "Lo siento, algo salió mal pensando tu respuesta."
        })

    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})


# -------------------------------------------------------
# AuriMind
# -------------------------------------------------------
async def think_with_auri(user_text: str) -> str:
    try:
        result = auri.think(user_text) or {}
        reply = (result.get("final") or result.get("raw") or "").strip()

        if not reply:
            reply = "Lo siento, no estoy seguro de cómo responder."

        logger.info("🧠 AuriMind reply: %s", reply)
        return reply

    except Exception as e:
        logger.exception("🔥 Error en AuriMind: %s", e)
        return "Lo siento, tuve un problema pensando tu respuesta."


# -------------------------------------------------------
# TTS STREAMING MP3 — CORREGIDO Y FUNCIONAL
# -------------------------------------------------------
async def send_tts_reply(ws: WebSocket, text: str):
    logger.info("🔊 TTS reply: %s", text)

    await ws.send_json({"type": "reply_partial", "text": text[:80]})
    await ws.send_json({"type": "reply_final", "text": text})

    try:
        # ❗ OJO: NO lleva await aquí.
        async with client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=VOICE_ID,
            input=text,
        ) as resp:

            async for chunk in resp.iter_bytes():
                await ws.send_bytes(chunk)

        logger.info("✅ TTS enviado correctamente")

    except Exception as e:
        logger.exception("🔥 Error generando TTS: %s", e)
        await ws.send_json({"type": "tts_error", "error": str(e)})

