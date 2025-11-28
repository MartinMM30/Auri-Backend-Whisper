import io
import base64
from openai import OpenAI

client = OpenAI()

class WhisperStream:
    def __init__(self):
        pass

    async def transcribe_pcm(self, pcm_bytes: bytes):
        """
        Recibe PCM16 en bytes → lo pasa a Whisper Realtime → devuelve texto parcial/final.
        """
        try:
            audio_b64 = base64.b64encode(pcm_bytes).decode("utf-8")

            event = {
                "type": "input_audio_buffer.append",
                "audio": audio_b64,
            }
            return event

        except Exception as e:
            print("❌ Error procesando audio PCM:", e)
            return None

    def end_audio(self):
        return {"type": "input_audio_buffer.commit"}
