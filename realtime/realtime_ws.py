# realtime/realtime_ws.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

from auribrain.auri_mind import AuriMind

router = APIRouter()
auri = AuriMind()

logger = logging.getLogger("uvicorn.error")


@router.websocket("/realtime")
async def websocket_realtime(socket: WebSocket):
    await socket.accept()
    logger.info("🔌 Cliente conectado al WS /realtime")

    try:
        while True:
            pcm_bytes = await socket.receive_bytes()

            raw_text = auri.stt(pcm_bytes)
            user_msg = (raw_text or "").strip()

            mind = auri.think(user_msg)

            await socket.send_text(json.dumps(mind))

            tts_bytes = auri.tts(mind["final"])
            if tts_bytes:
                await socket.send_bytes(tts_bytes)

    except WebSocketDisconnect:
        logger.info("🔌 Cliente desconectado del WS")
