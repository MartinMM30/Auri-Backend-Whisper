import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

router = APIRouter()
client = AsyncOpenAI()

TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "aurivoice"
SAMPLE_RATE = 16000


class RealtimeSession:
    def __init__(self):
        self.buffer = bytearray()

    def append(self, b: bytes):
        self.buffer.extend(b)

    def clear(self):
        self.buffer = bytearray()


@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    print("🔌 Cliente conectado")

    session = RealtimeSession()

    try:
        while True:
            data = await ws.receive()

            # 🔊 AUDIO ENTRANTE
            if isinstance(data, dict) and "bytes" in data:
                session.append(data["bytes"])
                continue

            # 📄 JSON ENTRANTE
            if "text" in data:
                msg = json.loads(data["text"])
                t = msg.get("type")

                if t == "client_hello":
                    print("🙋 HELLO", msg)

                elif t == "start_session":
                    print("🎤 start_session")
                    session.clear()
                    await ws.send_json({"type": "thinking", "state": True})

                elif t == "audio_end":
                    print("🛑 audio_end → procesando")
                    await process_stt_tts(ws, session)

                elif t == "stop_session":
                    print("🔻 stop_session")
                    await ws.send_json({"type": "thinking", "state": False})

                elif t == "text_command":
                    # Texto manual desde Flutter
                    text = msg.get("text", "")
                    await send_tts_reply(ws, text)

                elif t == "ping":
                    pass

    except WebSocketDisconnect:
        print("❌ Cliente desconectado")


async def process_stt_tts(ws: WebSocket, session: RealtimeSession):

    if len(session.buffer) == 0:
        print("⚠ No audio")
        await ws.send_json({"type": "thinking", "state": False})
        return

    # ---------------------
    # STT
    # ---------------------
    print("🎙 Whisper STT…")
    stt = await client.audio.transcriptions.create(
        model="gpt-4o-mini-tts",
        file=("audio.wav", session.buffer, "audio/wav")
    )

    text = stt.text.strip()
    print("📝 STT:", text)

    await ws.send_json({"type": "stt_final", "text": text})

    # ---------------------
    # TTS
    # ---------------------
    await send_tts_reply(ws, f"Entendido. Dijiste: {text}")


async def send_tts_reply(ws: WebSocket, text: str):
    print("🔊 TTS generando:", text)

    await ws.send_json({"type": "reply_partial", "text": text[:15]})
    await ws.send_json({"type": "reply_partial", "text": text[:28]})
    await ws.send_json({"type": "reply_final", "text": text})

    tts_stream = await client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=VOICE_ID,
        input=text,
    )

    async for chunk in tts_stream.iter_bytes():
        await ws.send_bytes(chunk)

    await ws.send_json({"type": "thinking", "state": False})
