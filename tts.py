import os
import io
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class TTSRequest(BaseModel):
    text: str
    voice: str | None = "alloy"

@router.post("/tts")
async def tts_endpoint(body: TTSRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="text is required")

    try:
        # ❗FORMA CORRECTA para obtener bytes
        result = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=body.voice or "alloy",
            input=body.text,
            format="mp3",                 # <-- IMPORTANTE
            output="bytes"                # <-- NECESARIO para obtener audio completo
        )

        # result es directamente bytes
        audio_bytes = result

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=tts.mp3"
            }
        )

    except Exception as e:
        raise HTTPException(500, f"TTS Error: {str(e)}")
