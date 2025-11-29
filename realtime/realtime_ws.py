import json
import io
import wave
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import OpenAI

from core.emotional_engine import EmotionalEngine
from core.jarvis_brain import JarvisBrain

client = OpenAI()

router = APIRouter()

# ------------------------------------------------------------
# PCM → WAV
# ------------------------------------------------------------
def pcm_to_wav(pcm_bytes: bytes, sample_rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    buf.seek(0)
    return buf

# ------------------------------------------------------------
# REALTIME ENDPOINT
# ------------------------------------------------------------
@router.websocket("/realtime")
async def realtime_endpoint(ws: WebSocket):
    await ws.accept()
    print("🔌 Cliente conectado")

    brain = JarvisBrain()
    audio_buffer = bytearray()
    session_active = False

    try:
        while True:
            message = await ws.receive()

            # ---------------- PCM BINARIO ----------------
            if "bytes" in message and message["bytes"] is not None:
                if not session_active:
                    continue

                chunk = message["bytes"]
                audio_buffer.extend(chunk)

                energy = min(1.0, max(0.05, len(chunk) / 4000.0))
                await ws.send_json({"type": "lip_sync", "energy": energy})
                continue

            # ---------------- JSON ----------------
            if "text" in message:
                try:
                    data = json.loads(message["text"])
                except Exception:
                    continue

                t = data.get("type")

                # ✔ Session Start
                if t == "start_session":
                    session_active = True
                    audio_buffer.clear()
                    await ws.send_json(EmotionalEngine.thinking(False))
                    continue

                # ✔ Session Stop
                if t == "stop_session":
                    session_active = False
                    audio_buffer.clear()
                    await ws.send_json(EmotionalEngine.thinking(False))
                    continue

                # ✔ Audio End → Whisper + GPT + TTS
                if t == "audio_end":
                    print("🎤 Procesando STT…")

                    if not audio_buffer:
                        await ws.send_json({"type": "stt_final", "text": ""})
                        continue

                    await ws.send_json(EmotionalEngine.thinking(True))

                    try:
                        wav = pcm_to_wav(bytes(audio_buffer))

                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=("audio.wav", wav, "audio/wav"),
                        )
                        text = transcript.text.strip()

                        await ws.send_json({"type": "stt_final", "text": text})
                        await ws.send_json(
                            EmotionalEngine.lip_sync_from_text(text)
                        )

                        # GPT → evento final
                        event = await brain.process_text(text)
                        final_text = event.get("text", "")

                        await ws.send_json({"type": "reply_final", "text": final_text})

                        # ---------------- TTS STREAM ----------------
                        print("🎧 Generando TTS…")

                        with client.audio.speech.with_streaming_response.create(
                            model="gpt-4o-mini-tts",
                            voice="aurivoice",
                            format="pcm16",
                            input=final_text,
                        ) as stream:
                            for chunk in stream.iter_bytes():
                                await ws.send_bytes(chunk)

                                # Lipsync basado en amplitud aproximada
                                amp = min(1.0, max(0.1, len(chunk) / 1800.0))
                                await ws.send_json({
                                    "type": "lip_sync",
                                    "energy": amp,
                                })

                    except Exception as e:
                        print("❌ Error:", e)
                        await ws.send_json({
                            "type": "reply_final",
                            "text": "Hubo un problema al procesar tu voz.",
                        })

                    finally:
                        audio_buffer.clear()
                        await ws.send_json(EmotionalEngine.thinking(False))

                    continue

                # ✔ Texto directo
                if t == "text_command":
                    txt = data.get("text", "")
                    await ws.send_json(EmotionalEngine.thinking(True))

                    event = await brain.process_text(txt)
                    final_text = event.get("text", "")

                    await ws.send_json({"type": "reply_final", "text": final_text})

                    # TTS direct
                    with client.audio.speech.with_streaming_response.create(
                        model="gpt-4o-mini-tts",
                        voice="aurivoice",
                        format="pcm16",
                        input=final_text,
                    ) as stream:
                        for chunk in stream.iter_bytes():
                            await ws.send_bytes(chunk)

                            amp = min(1.0, max(0.1, len(chunk) / 1600.0))
                            await ws.send_json({
                                "type": "lip_sync",
                                "energy": amp,
                            })

                    await ws.send_json(EmotionalEngine.thinking(False))
                    continue

                # Debug / Heartbeat
                if t == "ping":
                    await ws.send_json({"type": "pong"})
                    continue

    except WebSocketDisconnect:
        print("🔌 Cliente desconectado")
