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
        resp = client.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=body.voice or "alloy",
            input=body.text,
        )

        audio_bytes = resp.read()

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
        )

    except Exception as e:
        raise HTTPException(500, str(e))
