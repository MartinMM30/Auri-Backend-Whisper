import io
import json
import logging
import wave

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

from auribrain.auri_mind import AuriMind

logger = logging.getLogger("uvicorn.error")

router = APIRouter()
client = AsyncOpenAI()
auri = AuriMind()

STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "alloy"
SAMPLE_RATE = 16000


def pcm16_to_wav(pcm_bytes: bytes, sample_rate: int):
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm_bytes)
    buffer.seek(0)
    return buffer


class RealtimeSession:
    def __init__(self):
        self.pcm_buffer = bytearray()

    def append_pcm(self, data: bytes):
        self.pcm_buffer.extend(data)

    def clear(self):
        self.pcm_buffer.clear()


@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    logger.info("🔌 Cliente conectado al WS /realtime")

    session = RealtimeSession()

    try:
        while True:
            msg = await ws.receive()

            if msg.get("bytes") is not None:
                session.append_pcm(msg["bytes"])
                continue

            if msg.get("text") is not None:
                try:
                    data = json.loads(msg["text"])
                except Exception:
                    logger.warning("⚠ JSON inválido")
                    continue

                await handle_json(ws, session, data)

    except WebSocketDisconnect:
        logger.info("❌ Cliente desconectado")
        await ws.close()

    except Exception as e:
        logger.exception("🔥 ERROR WS: %s", e)
        await ws.close()


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
        text = (msg.get("text") or "").strip()
        if text:
            await process_text_only(ws, text)

    elif t == "ping":
        await ws.send_json({"type": "pong"})


async def process_stt_tts(ws: WebSocket, session: RealtimeSession):
    if len(session.pcm_buffer) == 0:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})
        return

    logger.info("🎙 Recibidos %d bytes PCM", len(session.pcm_buffer))
    await ws.send_json({"type": "thinking", "state": True})

    try:
        wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
        wav.name = "audio.wav"

        # ---------- STT ----------
        stt = await client.audio.transcriptions.create(
            model=STT_MODEL,
            file=wav,
        )

        text = (getattr(stt, "text", "") or "").strip()
        logger.info("📝 Texto STT (raw): %s", text)

        # ---------- ELIMINAR ECO (NUEVO) ----------
        # Si el STT parece incluir frases complejas previas → cortar última frase
        if "." in text and text.count(" ") > 8:
            parts = [p.strip() for p in text.split(".") if p.strip()]
            if parts:
                text = parts[-1]
                logger.info("✂️ STT limpio: %s", text)

        await ws.send_json({"type": "stt_final", "text": text})

        if not text:
            await ws.send_json({"type": "reply_final", "text": "No logré escucharte bien."})
            return

        # ---------- THINK ----------
        think_result = await think_with_auri(text)
        reply = think_result["text"]
        action = think_result["action"]

        # ---------- TTS ----------
        await send_tts_reply(ws, reply, action)

    except Exception as e:
        logger.exception("🔥 Error STT→TTS pipeline: %s", e)
        await ws.send_json({
            "type": "reply_final",
            "text": "Hubo un problema procesando tu voz."
        })

    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})
        session.clear()


async def process_text_only(ws: WebSocket, user_text: str):
    logger.info("✉ Texto directo: %s", user_text)
    await ws.send_json({"type": "thinking", "state": True})

    try:
        think_result = await think_with_auri(user_text)
        reply = think_result["text"]
        action = think_result["action"]

        await send_tts_reply(ws, reply, action)

    except Exception as e:
        logger.exception("🔥 Error texto directo")
        await ws.send_json({
            "type": "reply_final",
            "text": "Hubo un problema al pensar tu respuesta."
        })

    finally:
        await ws.send_json({"type": "thinking", "state": False})
        await ws.send_json({"type": "tts_end"})


async def think_with_auri(user_text: str) -> dict:
    try:
        result = auri.think(user_text)
        if not isinstance(result, dict):
            result = {}

        reply = (result.get("final") or result.get("raw") or "").strip()
        action = result.get("action")

        return {"text": reply, "action": action}

    except Exception as e:
        logger.exception("🔥 Error en AuriMind: %s", e)
        return {"text": "Tuve un problema interno.", "action": None}



async def send_tts_reply(ws: WebSocket, reply_text: str, action: dict | None):
    await ws.send_json({"type": "reply_partial", "text": reply_text[:80]})
    await ws.send_json({"type": "reply_final", "text": reply_text})

    if action:
        await ws.send_json({
            "type": "action",
            "action": action.get("type"),
            "payload": action.get("payload"),
        })

    try:
        async with client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=VOICE_ID,
            input=reply_text,
            response_format="mp3"
        ) as resp:

            async for chunk in resp.iter_bytes():
                await ws.send_bytes(chunk)

        logger.info("✅ TTS enviado correctamente")

    except Exception as e:
        logger.exception("🔥 Error generando TTS")
        await ws.send_json({"type": "tts_error", "error": str(e)})
