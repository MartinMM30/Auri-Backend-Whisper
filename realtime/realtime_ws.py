import asyncio
import json
from io import BytesIO
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

router = APIRouter()
client = AsyncOpenAI()

# -----------------------
# CONFIG
# -----------------------
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "aurivoice"
SAMPLE_RATE = 16000


# -----------------------
# SESSION CLASS
# -----------------------
class RealtimeSession:
    def __init__(self):
        self.buffer = bytearray()

    def append(self, b: bytes):
        self.buffer.extend(b)

    def clear(self):
        self.buffer = bytearray()


# -----------------------
# MAIN WS ROUTE
# -----------------------
@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    print("🔌 Cliente conectado")

    session = RealtimeSession()

    try:
        while True:
            data = await ws.receive()

            # 🔊 AUDIO FROM FLUTTER
            if isinstance(data, dict) and "bytes" in data:
                session.append(data["bytes"])
                continue

            # 📄 JSON FROM FLUTTER
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
                    text = msg.get("text", "")
                    await send_tts_reply(ws, text)

                elif t == "ping":
                    pass  # heartbeat for Flutter

    except WebSocketDisconnect:
        print("❌ Cliente desconectado")


# -----------------------
# PROCESS STT + TTS
# -----------------------
async def process_stt_tts(ws: WebSocket, session: RealtimeSession):

    if len(session.buffer) == 0:
        print("⚠ No audio")
        await ws.send_json({"type": "thinking", "state": False})
        return

    # -----------------------
    # STT (Whisper)
    # -----------------------
    print("🎙 Whisper STT…")

    audio_file = BytesIO(session.buffer)
    audio_file.name = "audio.wav"  # HTTPX lo requiere

    stt = await client.audio.transcriptions.create(
        model="gpt-4o-mini-tts",
        file=audio_file,
    )

    text = stt.text.strip()
    print("📝 STT:", text)

    await ws.send_json({"type": "stt_final", "text": text})

    # -----------------------
    # TTS (responder)
    # -----------------------
    await send_tts_reply(ws, f"Entendido. Dijiste: {text}")


# -----------------------
# TTS SENDER
# -----------------------
async def send_tts_reply(ws: WebSocket, text: str):
    print("🔊 TTS generando:", text)

    # Mensajes texto tipo Alexa/Siri
    await ws.send_json({"type": "reply_partial", "text": text[:15]})
    await ws.send_json({"type": "reply_partial", "text": text[:28]})
    await ws.send_json({"type": "reply_final", "text": text})

    # Audio por streaming
    tts_stream = await client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=VOICE_ID,
        input=text,
    )

    async for chunk in tts_stream.iter_bytes():
        await ws.send_bytes(chunk)

    await ws.send_json({"type": "thinking", "state": False})
