import json
import io
import wave
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from openai import OpenAI

from core.emotional_engine import Actions
from core.jarvis_brain import EmotionalEngine

client = OpenAI()

router = APIRouter()


# ------------------------------------------------------------
#  JARVIS BRAIN LITE
# ------------------------------------------------------------
class JarvisBrain:
    def __init__(self, user_profile=None):
        self.user_profile = user_profile or {}

    async def process_text(self, text: str):
        print("🧠 JarvisBrain: procesando:", text)

        low = text.lower()

        # Recordatorios
        if "recordatorio" in low or "recuérdame" in low:
            return Actions.create_reminder(text)

        # Conversación normal
        try:
            resp = client.responses.create(
                model="gpt-4o-mini",
                input=text,
            )
            final_text = resp.output_text
        except Exception as e:
            print("❌ Error en GPT:", e)
            final_text = "No pude generar una respuesta."

        return {
            "type": "reply_final",
            "text": final_text,
        }


# ------------------------------------------------------------
# CONVERSIÓN PCM → WAV (necesario para Whisper)
# ------------------------------------------------------------
def pcm_to_wav(pcm_bytes: bytes, sample_rate=16000):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    buf.seek(0)
    return buf


# ------------------------------------------------------------
#  ENDPOINT WEBSOCKET
# ------------------------------------------------------------
@router.websocket("/realtime")
async def realtime_endpoint(ws: WebSocket):
    await ws.accept()
    print("🔌 Cliente Realtime conectado")

    brain = JarvisBrain()
    audio_buffer = bytearray()
    session_active = False

    try:
        while True:
            message = await ws.receive()

            # ----------------------------------------------------
            #  AUDIO BINARIO (PCM16)
            # ----------------------------------------------------
            if "bytes" in message and message["bytes"] is not None:
                chunk: bytes = message["bytes"]
                print(f"🎧 chunk recibido: {len(chunk)} bytes, session_active={session_active}")
                if not session_active:
                    continue

                chunk = message["bytes"]
                audio_buffer.extend(chunk)

                # Lip-sync
                energy = min(1.0, max(0.05, len(chunk) / 4000.0))
                await ws.send_json({
                    "type": "lip_sync",
                    "energy": energy,
                })
                continue

            # ----------------------------------------------------
            #  MENSAJE JSON
            # ----------------------------------------------------
            if "text" in message and message["text"] is not None:
                try:
                    data = json.loads(message["text"])
                except Exception:
                    print("⚠ Mensaje no JSON:", message["text"])
                    continue

                m = data.get("type")

                # ---------------- START SESSION ----------------
                if m == "start_session":
                    print("🎙 start_session")
                    session_active = True
                    audio_buffer.clear()
                    await ws.send_json(EmotionalEngine.thinking(False))
                    continue

                # ---------------- AUDIO END ----------------
                if m == "audio_end":
                    print("🛑 audio_end recibido, procesando STT…")
                    print(f"📦 audio_buffer len = {len(audio_buffer)} bytes")
                    if not audio_buffer:
                        await ws.send_json({
                            "type": "stt_final",
                            "text": "",
                        })
                        continue

                    await ws.send_json(EmotionalEngine.thinking(True))

                    try:
                        # WAV requerido por Whisper
                        wav = pcm_to_wav(bytes(audio_buffer))

                        transcript = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=("audio.wav", wav, "audio/wav"),
                        )

                        text = transcript.text.strip()
                        print("📝 STT final:", text)

                        # Emitir stt_final
                        await ws.send_json({
                            "type": "stt_final",
                            "text": text,
                        })

                        # Lip-sync derivado del texto
                        await ws.send_json(
                            EmotionalEngine.lip_sync_from_text(text)
                        )

                        # Mente Jarvis
                        event = await brain.process_text(text)
                        await ws.send_json(event)

                    except Exception as e:
                        print("❌ Error en STT:", e)
                        await ws.send_json({
                            "type": "reply_final",
                            "text": "No pude escuchar bien, ¿podrías repetirlo?",
                        })

                    finally:
                        audio_buffer.clear()
                        await ws.send_json(EmotionalEngine.thinking(False))
                        

                    continue

                # ---------------- STOP SESSION ----------------
                if m == "stop_session":
                    print("🧵 stop_session")
                    session_active = False
                    audio_buffer.clear()
                    await ws.send_json(EmotionalEngine.thinking(False))
                    continue

                # ---------------- TEXTO DIRECTO ----------------
                if m == "text_command":
                    text = data.get("text", "").strip()
                    if not text:
                        continue

                    await ws.send_json(EmotionalEngine.thinking(True))

                    await ws.send_json(EmotionalEngine.lip_sync_from_text(text))

                    try:
                        event = await brain.process_text(text)
                        await ws.send_json(event)
                    finally:
                        await ws.send_json(EmotionalEngine.thinking(False))

                    continue

                # ---------------- OTROS ----------------
                if m == "client_hello":
                    print("🙋‍♂️ client_hello:", data)
                    await ws.send_json({"type": "hello_ack", "ok": True})
                    continue

                print("ℹ Mensaje desconocido:", data)

    except WebSocketDisconnect:
        print("🔌 Cliente Realtime desconectado")

    except Exception as e:
        print("❌ Error en WebSocket:", e)
        
        try:
            await ws.close()
        except:
            pass
