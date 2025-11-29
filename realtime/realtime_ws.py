# realtime/realtime_ws.py

import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

router = APIRouter()
client = AsyncOpenAI()

# -----------------------------------------
# CONFIG
# -----------------------------------------
TTS_MODEL = "gpt-4o-mini-tts"     # modelo rápido
VOICE_ID = "aurivoice"            # lo puedes cambiar
SAMPLE_RATE = 16000               # Flutter envía/recibe esto

# -----------------------------------------
# SESSION STATE (por conexión)
# -----------------------------------------
class RealtimeSession:
    def __init__(self):
        self.buffer = bytearray()
        self.audio_chunks = []

    def append_audio(self, data: bytes):
        self.buffer.extend(data)

    def clear(self):
        self.buffer = bytearray()
        self.audio_chunks = []


# -----------------------------------------
# ROUTER WS
# -----------------------------------------
@router.websocket("/realtime")
async def realtime_socket(ws: WebSocket):
    await ws.accept()
    print("🔌 Cliente conectado")

    session = RealtimeSession()

    try:
        while True:
            data = await ws.receive()

            # AUDIO (bytes)
            if isinstance(data, dict) and "bytes" in data:
                session.append_audio(data["bytes"])
                continue

            # MENSAJE JSON
            if "text" in data:
                msg = json.loads(data["text"])
                t = msg.get("type")

                if t == "client_hello":
                    print("🙋 HELLO:", msg)

                elif t == "start_session":
                    print("🎤 Start session")
                    session.clear()

                elif t == "audio_end":
                    print("🛑 Audio end, procesando…")
                    await process_stt_tts(ws, session)

                elif t == "ping":
                    pass  # heartbeat

    except WebSocketDisconnect:
        print("❌ Cliente desconectado")
    except Exception as e:
        print("🔥 ERROR:", e)


# -----------------------------------------
# PROCESS: STT + TTS
# -----------------------------------------
async def process_stt_tts(ws: WebSocket, session: RealtimeSession):

    if len(session.buffer) == 0:
        print("⚠ No audio en buffer")
        return

    # ------------------------------------
    # 1. STT → transcribir el audio
    # ------------------------------------
    print("🎙 Enviando a Whisper… (STT)")
    stt = await client.audio.transcriptions.create(
        model="gpt-4o-mini-tts",
        file=("audio.wav", session.buffer, "audio/wav")
    )

    text = stt.text.strip()
    print("📝 Texto reconocido:", text)

    # enviar texto parcial/final
    await ws.send_json({
        "type": "stt_final",
        "text": text
    })

    # ------------------------------------
    # 2. TTS → generar audio de respuesta
    # ------------------------------------
    print("🔊 Enviando a TTS…")
    tts = await client.audio.speech.with_streaming_response.create(
        model=TTS_MODEL,
        voice=VOICE_ID,
        input=f"Entendido. Dijiste: {text}"
    )

    async for chunk in tts.iter_bytes():
        await ws.send_bytes(chunk)

    await ws.send_json({"type": "reply_final", "text": f"Entendido: {text}"})
    print("🎉 TTS enviado en vivo")
