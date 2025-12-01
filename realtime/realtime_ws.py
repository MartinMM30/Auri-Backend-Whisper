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


# PCM → WAV
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


# JSON COMMAND HANDLER
async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):
    t = msg.get("type")

    if t == "client_hello":
        logger.info("🙋 HELLO: %s", msg)
        await ws.send_json({"type": "hello_ok"})

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


# PIPELINE
async def process_stt_tts(ws: WebSocket, session: RealtimeSession):
    if len(session.pcm_buffer) == 0:
        await ws.send_json({"type": "reply_final", "text": "No escuché nada."})
        return

    logger.info("🎙 Recibidos %d bytes PCM", len(session.pcm_buffer))

    wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
    wav.name = "audio.wav"

    try:
        stt = await client.audio.transcriptions.create(
            model=STT_MODEL,
            file=wav,
        )
        text = (getattr(stt, "text", "") or "").strip()
        logger.info("📝 Texto STT: %s", text)

        # THINK
        think_res = auri.think(text)
        reply_text = think_res["final"] or think_res["raw"]
        action = think_res["action"]

        logger.info("🧠 Auri reply: %s", reply_text)
        await send_tts(ws, reply_text)

        if action:
            await ws.send_json({
                "type": "action",
                "action": action.get("type"),
                "payload": action.get("payload")
            })

    except Exception as e:
        logger.exception("🔥 Error en pipeline STT→LLM→TTS: %s", e)
        await ws.send_json({"type": "reply_final", "text": "Hubo un problema procesando tu voz."})

    session.clear()


async def process_text_only(ws: WebSocket, text: str):
    think_res = auri.think(text)
    reply_text = think_res["final"] or think_res["raw"]
    action = think_res["action"]

    await send_tts(ws, reply_text)

    if action:
        await ws.send_json({
            "type": "action",
            "action": action.get("type"),
            "payload": action.get("payload")
        })


async def send_tts(ws: WebSocket, text: str, voice_id: str = "alloy"):
    # Texto para la UI
    await ws.send_json({"type": "reply_partial", "text": text[:60]})
    await ws.send_json({"type": "reply_final", "text": text})

    try:
        # IMPORTANTE: SIN sample_rate
        async with client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=voice_id,
            input=text,
            response_format="mp3",
        ) as resp:
            async for chunk in resp.iter_bytes():
                await ws.send_bytes(chunk)

        # Avisar al cliente que terminó el audio
        await ws.send_json({"type": "tts_end"})

    except Exception as e:
        logger.exception("🔥 TTS error: %s", e)
        await ws.send_json({"type": "tts_error", "error": str(e)})
        # Igual avisamos fin de TTS para que el cliente no se quede colgado
        await ws.send_json({"type": "tts_end"})

