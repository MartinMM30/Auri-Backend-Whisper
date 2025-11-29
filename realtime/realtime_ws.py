# realtime/realtime_ws.py

import asyncio
import json
import wave
import io
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

router = APIRouter()
client = AsyncOpenAI()

STT_MODEL = "whisper-1"
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "aurivoice"
SAMPLE_RATE = 16000


# -------------------------------------------------------
# PCM → WAV (PROFESSIONAL IMPLEMENTATION)
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
    print("🔌 Cliente conectado")

    session = RealtimeSession()

    try:
        while True:
            msg = await ws.receive()

            # Bytes = audio PCM
            if msg.get("bytes") is not None:
                session.append_pcm(msg["bytes"])
                continue

            # Texto JSON
            if msg.get("text") is not None:
                data = json.loads(msg["text"])
                await handle_json(ws, session, data)

    except WebSocketDisconnect:
        print("❌ Cliente desconectado")
    except Exception as e:
        print("🔥 ERROR en WS:", e)


# -------------------------------------------------------
async def handle_json(ws: WebSocket, session: RealtimeSession, msg: dict):

    t = msg.get("type")

    # Handshake
    if t == "client_hello":
        await ws.send_json({"type": "hello_ok"})
        print("🙋 HELLO:", msg)

    # Inicio de sesión de voz
    elif t == "start_session":
        print("🎤 Inicio sesión")
        session.clear()
        await ws.send_json({"type": "thinking", "state": True})

    # Fin de audio
    elif t == "audio_end":
        await process_stt_tts(ws, session)

    # Comando por texto (teclado)
    elif t == "text_command":
        txt = msg.get("text", "")
        await send_tts_reply(ws, txt)


# -------------------------------------------------------
async def process_stt_tts(ws: WebSocket, session: RealtimeSession):

    if len(session.pcm_buffer) == 0:
        await ws.send_json({"type": "thinking", "state": False})
        return

    print(f"🎙 Recibidos {len(session.pcm_buffer)} bytes PCM")

    # ------- CONVERT PCM → WAV SAFE ----------
    wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
    wav.name = "audio.wav"

    # --------------- STT ---------------------
    print("🧠 Whisper STT…")
    stt = await client.audio.transcriptions.create(
        model=STT_MODEL,
        file=wav,
    )

    text = stt.text.strip()
    print("📝 Texto:", text)

    await ws.send_json({"type": "stt_final", "text": text})

    # --------------- TTS ---------------------
    await send_tts_reply(ws, f"Dijiste: {text}")


# -------------------------------------------------------
async def send_tts_reply(ws: WebSocket, text: str):
    print("🔊 TTS:", text)

    await ws.send_json({"type": "reply_partial", "text": text[:30]})
    await ws.send_json({"type": "reply_final", "text": text})

    # NEW: Responses API streaming PCM16
    stream = client.responses.stream(
        model=TTS_MODEL,
        input=[{
            "role": "assistant",
            "content": [
                {"type": "input_text", "text": text}
            ]
        }],
        audio={
            "voice": VOICE_ID,
            "format": "pcm16",
        }
    )

    async with stream as s:
        async for event in s:
            if event.type == "response.output_audio.delta":
                await ws.send_bytes(event.delta)

    await ws.send_json({"type": "thinking", "state": False})
    print("✅ Respuesta TTS enviada")
