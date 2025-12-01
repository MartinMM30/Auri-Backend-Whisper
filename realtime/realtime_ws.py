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
            msg = await socket.receive()

            # ------------------------------------------------
            # 1) BYTES DE AUDIO PCM
            # ------------------------------------------------
            if msg["type"] == "websocket.receive" and "bytes" in msg:
                pcm_bytes = msg["bytes"]
                logger.info(f"🎙 Recibidos {len(pcm_bytes)} bytes PCM")

                # STT
                raw_text = auri.stt(pcm_bytes)
                logger.info(f"📝 Texto STT (raw): {raw_text}")

                user_text = raw_text.strip()

                # THINK
                mind_result = auri.think(user_text)

                final_text = mind_result["final"]

                # Enviar JSON con la respuesta
                await socket.send_text(json.dumps(mind_result))

                # TTS → bytes
                tts_bytes = auri.tts(final_text)

                await socket.send_bytes(tts_bytes)
                continue

            # ------------------------------------------------
            # 2) TEXTO (HELLO, PINGS, MENSAJES DE CONTROL)
            # ------------------------------------------------
            if msg["type"] == "websocket.receive" and "text" in msg:
                text = msg["text"]
                logger.info(f"🔤 Texto recibido en WS: {text}")
                # Opcional: responder algo o ignorarlo
                continue

            # ------------------------------------------------
            # 3) CIERRE DE SOCKET
            # ------------------------------------------------
            if msg["type"] == "websocket.disconnect":
                logger.info("🔌 Cliente desconectado")
                break

    except WebSocketDisconnect:
        logger.info("🔌 Cliente desconectado por excepción")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
