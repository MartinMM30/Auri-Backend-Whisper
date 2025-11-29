import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from openai import OpenAI

router = APIRouter()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("/stt")
async def stt(file: UploadFile = File(...)):
    try:
        audio = await file.read()

        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=("audio.wav", audio, "audio/wav")
        )

        return {"text": transcript.text.strip()}

    except Exception as e:
        raise HTTPException(500, str(e))
