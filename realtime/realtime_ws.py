# realtime/realtime_ws.py

import asyncio
import json
import wave
import io
import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import AsyncOpenAI

# IMPORTAMOS EL MISMO AuriMind QUE USA /think
from router import auri as auri_mind  # <- usa la instancia global de router.py

router = APIRouter()

# Usa la misma API KEY del entorno
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

STT_MODEL = "whisper-1"          # puedes cambiar a gpt-4o-mini-transcribe si quieres
TTS_MODEL = "gpt-4o-mini-tts"
VOICE_ID = "aurivoice"           # tu voz custom en OpenAI
SAMPLE_RATE = 16000


# -------------------------------------------------------
# PCM → WAV
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

            # Audio crudo PCM16 desde Flutter
            if msg.get("bytes") is not None:
                session.append_pcm(msg["bytes"])
                continue

            # Mensajes texto JSON
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

    # Handshake inicial
    if t == "client_hello":
        await ws.send_json({"type": "hello_ok"})
        print("🙋 HELLO:", msg)

    # Inicio de sesión de voz
    elif t == "start_session":
        print("🎤 Inicio sesión de voz")
        session.clear()
        # Auri está pensando / preparando todo
        await ws.send_json({"type": "thinking", "state": True})

    # Cliente indica que ya terminó de mandar audio
    elif t == "audio_end":
        await process_stt_and_auri(ws, session)

    # Comando directo por texto (teclado / debug)
    elif t == "text_command":
        txt = msg.get("text", "").strip()
        if not txt:
            return
        await run_auri_and_tts(ws, user_text=txt)


# -------------------------------------------------------
async def process_stt_and_auri(ws: WebSocket, session: RealtimeSession):
    """
    1) Convierte el PCM acumulado en WAV
    2) Lo manda a Whisper
    3) Con el texto llama a AuriMind
    4) Streamea TTS de la respuesta
    """
    if len(session.pcm_buffer) == 0:
        print("⚠ audio_end pero buffer vacío")
        await ws.send_json({"type": "thinking", "state": False})
        return

    print(f"🎙 Recibidos {len(session.pcm_buffer)} bytes PCM")

    # PCM → WAV
    wav = pcm16_to_wav(session.pcm_buffer, SAMPLE_RATE)
    wav.name = "audio.wav"

    # ---------- STT ----------
    print("🧠 Whisper STT…")
    stt = await client.audio.transcriptions.create(
        model=STT_MODEL,
        file=wav,
    )

    user_text = (stt.text or "").strip()
    print("📝 Texto usuario:", user_text)

    # Notificamos al cliente el texto final reconocido
    await ws.send_json({"type": "stt_final", "text": user_text})

    if not user_text:
        # Nada que pensar / responder
        await ws.send_json({"type": "thinking", "state": False})
        return

    # ---------- AuriMind + TTS ----------
    await run_auri_and_tts(ws, user_text=user_text)


# -------------------------------------------------------
async def run_auri_and_tts(ws: WebSocket, user_text: str):
    """
    Llama a AuriMind.think() en un hilo de fondo y
    luego streamea la respuesta por texto + audio.
    """
    print("🧠 AuriMind.think()…")

    loop = asyncio.get_running_loop()

    # AuriMind.think es síncrono → lo mandamos a thread pool
    def _think_sync():
        return auri_mind.think(user_text)

    try:
        result = await loop.run_in_executor(None, _think_sync)
    except Exception as e:
        print("🔥 Error en AuriMind:", e)
        await ws.send_json({
            "type": "reply_final",
            "text": "Lo siento, tuve un problema interno al pensar tu respuesta."
        })
        await ws.send_json({"type": "thinking", "state": False})
        return

    intent = result.get("intent", "unknown")
    raw = result.get("raw", "")
    final = result.get("final", "").strip()

    if not final:
        final = raw or user_text  # fallback muy defensivo

    print(f"🎯 Intent: {intent}")
    print(f"💭 Raw: {raw}")
    print(f"💬 Final: {final}")

    # Eventos extra para debug / UI avanzada
    await ws.send_json({"type": "auri_intent", "intent": intent})
    await ws.send_json({"type": "auri_raw", "raw": raw})

    # Texto para UI (burbujas / etc.)
    await ws.send_json({"type": "reply_partial", "text": final[:80]})
    await ws.send_json({"type": "reply_final", "text": final})

    # Ahora streameamos el audio TTS
    await stream_tts_audio(ws, final)


# -------------------------------------------------------
async def stream_tts_audio(ws: WebSocket, text: str):
    """
    Streamea audio PCM16 por el WebSocket. El cliente Flutter
    lo reproduce con TtsPlayerPCM.
    """
    print("🔊 TTS streaming…")

    try:
        response = await client.audio.speech.with_streaming_response.create(
            model=TTS_MODEL,
            voice=VOICE_ID,
            input=text,
            format="pcm16",
            sample_rate=SAMPLE_RATE,
        )

        async with response:
            async for chunk in response.iter_bytes():
                # Cada chunk es bytes PCM16 mono 16k
                await ws.send_bytes(chunk)

        print("✅ TTS completado")

    except Exception as e:
        print("🔥 Error TTS:", e)
    finally:
        # Señal al cliente: terminó la respuesta
        await ws.send_json({"type": "thinking", "state": False})
