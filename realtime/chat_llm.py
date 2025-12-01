from fastapi import APIRouter
from pydantic import BaseModel
from auribrain.auri_mind import AuriMind

router = APIRouter()
auri = AuriMind()

class ChatIn(BaseModel):
    text: str

@router.post("/")
async def chat(body: ChatIn):
    return auri.think(body.text)
