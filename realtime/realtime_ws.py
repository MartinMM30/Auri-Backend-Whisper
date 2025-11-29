import asyncio
import json
from io import BytesIO

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
from openai import AsyncOpenAI

router = APIRouter()
client = AsyncOpenAI()

# -----------------------
# CONFIG
# -----------------------
STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "aurivoice"
SAMPLE_RATE = 16000


# -----------------------
# SESSION (PCM Buffer)
# -----------------------
class RealtimeSession:
    def __init__(self):
        self.buffer = bytearray()

    def append(self, b: bytes):
        self.buffer.extend(b)

    def clear(self):
        self.buffer = bytearray()


# -----------------------
# WEBSOCKET ROUTE
# -----------------------
@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    print("🔌 Cliente conectado")

    session = RealtimeSession()

    try:
        while True:
            msg = await ws.receive()

            # -----------------------
            # BYTES (AUDIO DE FLUTTER)
            # -----------------------
            if msg["type"] == "websocket.receive" and msg.get("bytes") is not None:
                session.append(msg["bytes"])
                continue

            # -----------------------
            # TEXTO JSON
            # -----------------------
            if msg.get("text") is not None:
                data = json.loads(msg["text"])
                await handle_json(ws, session, data)

    except WebSocketDisconnect:
        print("❌ Cliente desconectado")

    except Exception as e:
        print("🔥 ERROR severo:", e)


# -----------------------
# HANDLE JSON EVENTS
# -----------------------
async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):
    t = msg.get("type")

    if t == "client_hello":
        print("🙋 HELLO:", msg)

    elif t == "start_session":
        print("🎤 Iniciando sesión de voz")
        session.clear()
        await ws.send_json({"type": "thinking", "state": True})

    elif t == "audio_end":
        print("🛑 Audio terminado → procesando STT/TTS")
        await process_stt_tts(ws, session)

    elif t == "stop_session":
        print("🔻 stop_session")
        await ws.send_json({"type": "thinking", "state": False})

    elif t == "text_command":
        text = msg.get("text", "")
        await send_tts_reply(ws, text)

    elif t == "ping":
        # Mantener vivo el WebSocket
        pass


# -----------------------
# PROCESS STT + TTS
# -----------------------
async def process_stt_tts(ws: WebSocket, session: RealtimeSession):

    if len(session.buffer) == 0:
        print("⚠ No audio enviado")
        await ws.send_json({"type": "thinking", "state": False})
        return

    # -----------------------
    # STT WHISPER
    # -----------------------
    print("🎙 Whisper STT…")

    wav = BytesIO(session.buffer)
    wav.name = "audio.wav"

    stt = await client.audio.transcriptions.create(
        model=STT_MODEL,
        file=wav,
    )

    text = stt.text.strip()
    print("📝 STT:", text)

    await ws.send_json({"type": "stt_final", "text": text})

    # -----------------------
    # TTS (RESPUESTA DE AURI)
    # -----------------------
    await send_tts_reply(ws, f"Entendido Martín, dijiste: {text}")


# -----------------------
# TTS STREAMING
# -----------------------
async def send_tts_reply(ws: WebSocket, text: str):
    print("🔊 Generando TTS:", text)

    # Pre-respuestas tipo Siri/Alexa
    await ws.send_json({"type": "reply_partial", "text": text[:15]})
    await ws.send_json({"type": "reply_partial", "text": text[:30]})
    await ws.send_json({"type": "reply_final",   "text": text})

    # Streaming de audio → Flutter
    try:
        stream = await client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=VOICE_ID,
            input=text,
        )

        async for chunk in stream.iter_bytes():
            # Envía audio PCM directo a Flutter
            await ws.send_bytes(chunk)

    except Exception as e:
        print("🔥 Error en TTS STREAM:", e)

    # Terminar estado pensando
    await ws.send_json({"type": "thinking", "state": False})
