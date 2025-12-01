import io
import json
import logging
import wave

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from auribrain.auri_mind import AuriMind
from realtime.realtime_broadcast import realtime_broadcast


# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
logger = logging.getLogger("uvicorn.error")

router = APIRouter()
client = AsyncOpenAI()
auri = AuriMind()

STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
DEFAULT_VOICE = "alloy"
SAMPLE_RATE = 16000


# -------------------------------------------------------
# PCM → WAV
# -------------------------------------------------------
def pcm16_to_wav(pcm_bytes: bytes, sample_rate: int):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)

    buffer.seek(0)
    return buffer


# -------------------------------------------------------
# SESSION STATE
# -------------------------------------------------------
class RealtimeSession:
    def __init__(self):
        self.pcm_buffer = bytearray()

    def append_pcm(self, data: bytes):
        self.pcm_buffer.extend(data)

    def clear(self):
        self.pcm_buffer.clear()


# -------------------------------------------------------
# THINK PIPELINE WRAPPER
# -------------------------------------------------------
async def think_with_auri(text: str) -> dict:
    try:
        result = auri.think(text) or {}

        reply = (result.get("final") or result.get("raw") or "").strip()
        action = result.get("action")
        voice_id = result.get("voice_id", DEFAULT_VOICE)

        if not reply:
            reply = "Lo siento, no estoy seguro de cómo responder."

        logger.info("🧠 Auri reply: %s", reply)

        return {
            "text": reply,
            "action": action,
            "voice_id": voice_id,
        }

    except Exception as e:
        logger.exception("🔥 Error en AuriMind: %s", e)
        return {
            "text": "Lo siento, tuve un problema interno.",
            "action": None,
            "voice_id": DEFAULT_VOICE,
        }


# -------------------------------------------------------
# TTS STREAMING
# -------------------------------------------------------
async def send_tts(ws: WebSocket, text: str, voice_id: str):
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

    except Exception as e:
        logger.exception("🔥 TTS error: %s", e)
        await ws.send_json({"type": "tts_error", "error": str(e)})


# -------------------------------------------------------
# JSON HANDLER
# -------------------------------------------------------
async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):
    t = msg.get("type")

    if t == "client_hello":
        await ws.send_json({"type": "hello_ok"})
        logger.info("🙋 HELLO: %s", msg)

    elif t == "start_session":
        logger.info("🎤 Inicio sesión de voz")
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
# AUDIO PIPELINE STT → THINK → TTS
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
        wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
        wav.name = "audio.wav"

        stt = await client.audio.transcriptions.create(
            model=STT_MODEL,
            file=wav,
        )

        text = (getattr(stt, "text", "") or "").strip()
        logger.info("📝 Texto STT: %s", text)

        low = text.lower()
        if "auri" in low:
            text = low.split("auri", 1)[1].strip()

        await ws.send_json({"type": "stt_final", "text": text})

        if not text:
            await ws.send_json({
                "type": "reply_final",
                "text": "No escuché nada claro, ¿puedes repetirlo?"
            })
            return

        think_res = await think_with_auri(text)
        reply_text = think_res["text"]
        action = think_res["action"]
        voice_id = think_res["voice_id"]

        await send_tts(ws, reply_text, voice_id)

        if action:
            await ws.send_json({
                "type": "action",
                "action": action.get("type"),
                "payload": action.get("payload"),
            })

    except Exception as e:
        logger.exception("🔥 Error en pipeline: %s", e)
        await ws.send_json({
            "type": "reply_final",
            "text": "Hubo un problema procesando tu voz."
        })

    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})
        session.clear()


# -------------------------------------------------------
# TEXTO DIRECTO
# -------------------------------------------------------
async def process_text_only(ws: WebSocket, text: str):
    logger.info("✉ Texto: %s", text)
    await ws.send_json({"type": "thinking", "state": True})

    try:
        think_res = await think_with_auri(text)
        reply_text = think_res["text"]
        action = think_res["action"]
        voice_id = think_res["voice_id"]

        await send_tts(ws, reply_text, voice_id)

        if action:
            await ws.send_json({
                "type": "action",
                "action": action.get("type"),
                "payload": action.get("payload"),
            })

    except Exception:
        logger.exception("🔥 Error en texto directo")
        await ws.send_json({
            "type": "reply_final",
            "text": "Hubo un problema procesando tu mensaje."
        })

    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})


# -------------------------------------------------------
# WEBSOCKET ROUTE (ÚNICO Y CORRECTO)
# -------------------------------------------------------
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
                data = json.loads(msg["text"])
                await handle_json(ws, session, data)
                continue

    except WebSocketDisconnect:
        logger.info("❌ Cliente desconectado (exception)")

    finally:
        realtime_broadcast.unregister(ws)
        logger.info("🔌 WS cerrado")
