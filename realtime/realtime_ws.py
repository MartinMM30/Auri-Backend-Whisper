# realtime/realtime_ws.py
import asyncio
import json
from io import BytesIO

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

router = APIRouter()
client = AsyncOpenAI()

STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "aurivoice"
SAMPLE_RATE = 16000

class RealtimeSession:
    def __init__(self):
        self.buffer = bytearray()

    def append(self, b: bytes):
        self.buffer.extend(b)

    def clear(self):
        self.buffer.clear()


@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    print("🔌 Cliente conectado")
    session = RealtimeSession()

    try:
        while True:
            msg = await ws.receive()

            if msg.get("bytes") is not None:
                session.append(msg["bytes"])
                continue

            if msg.get("text") is not None:
                data = json.loads(msg["text"])
                await handle_json(ws, session, data)

    except WebSocketDisconnect:
        print("❌ Cliente desconectado")

    except Exception as e:
        print("🔥 ERROR:", e)


async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):
    t = msg.get("type")

    if t == "client_hello":
        print("🙋 HELLO:", msg)

    elif t == "start_session":
        print("🎤 Inicio sesión de voz")
        session.clear()
        await ws.send_json({"type": "thinking", "state": True})

    elif t == "audio_end":
        await process_stt_tts(ws, session)

    elif t == "stop_session":
        await ws.send_json({"type": "thinking", "state": False})

    elif t == "text_command":
        txt = msg.get("text", "")
        await send_tts_reply(ws, txt)


async def process_stt_tts(ws: WebSocket, session: RealtimeSession):
    if len(session.buffer) == 0:
        await ws.send_json({"type": "thinking", "state": False})
        return

    wav = BytesIO(session.buffer)
    wav.name = "audio.wav"

    print("🎙 Whisper STT…")
    stt = await client.audio.transcriptions.create(
        model=STT_MODEL,
        file=wav,
    )

    text = stt.text.strip()
    await ws.send_json({"type": "stt_final", "text": text})

    await send_tts_reply(ws, f"Dijiste: {text}")


async def send_tts_reply(ws: WebSocket, text: str):
    print("🔊 TTS:", text)

    await ws.send_json({"type": "reply_partial", "text": text[:20]})
    await ws.send_json({"type": "reply_final", "text": text})

    stream = await client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=VOICE_ID,
        input=text,
    )

    async for chunk in stream.iter_bytes():
        await ws.send_bytes(chunk)

    await ws.send_json({"type": "thinking", "state": False})
