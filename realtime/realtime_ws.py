# routes/realtime_ws.py

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
            # RECIBIR BYTES PCM DEL CLIENTE
            pcm_bytes = await socket.receive_bytes()
            logger.info(f"🎙 Recibidos {len(pcm_bytes)} bytes PCM")

            # 1) STT (Whisper local/streaming)
            raw_text = auri.stt(pcm_bytes)
            logger.info(f"📝 Texto STT (raw): {raw_text}")

            user_text = raw_text.strip()

            # 2) PIENSA (intents + memoria + contexto + personalidad)
            mind_result = auri.think(user_text)

            final_text = mind_result["final"]

            # 3) ENVIAR RESULTADO DE TEXTO A FLUTTER
            await socket.send_text(json.dumps(mind_result))

            # 4) TTS
            tts_bytes = auri.tts(final_text)
            await socket.send_bytes(tts_bytes)

    except WebSocketDisconnect:
        logger.info("🔌 Cliente desconectado")
