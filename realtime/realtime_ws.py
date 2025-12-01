from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

from auribrain.auri_mind import AuriMind

router = APIRouter()
auri = AuriMind()

logger = logging.getLogger("uvicorn.error")

@router.websocket("/realtime")
async def websocket_realtime(ws: WebSocket):
    await ws.accept()
    logger.info("🔌 Cliente conectado al WS /realtime")

    session_active = False

    try:
        while True:

            msg = await ws.receive()

            # -----------------------------
            # 1) MENSAJE DE TEXTO (JSON)
            # -----------------------------
            if msg["type"] == "websocket.receive" and "text" in msg:
                raw = msg["text"]
                logger.info(f"🔤 Texto recibido: {raw}")

                try:
                    data = json.loads(raw)
                except:
                    continue

                # handshake
                if data.get("type") == "client_hello":
                    await ws.send_text(json.dumps({
                        "type": "hello_ok",
                        "server": "auri_backend_v3"
                    }))
                    continue

                # heartbeat
                if data.get("type") == "ping":
                    await ws.send_text(json.dumps({"type": "pong"}))
                    continue

                # start session
                if data.get("type") == "start_session":
                    session_active = True
                    continue

                # end recording
                if data.get("type") == "audio_end":
                    session_active = False
                    continue


            # -----------------------------
            # 2) AUDIO PCM (BYTES)
            # -----------------------------
            if msg["type"] == "websocket.receive" and "bytes" in msg:
                pcm_bytes = msg["bytes"]
                logger.info(f"🎙 Recibidos {len(pcm_bytes)} bytes PCM")

                if not session_active:
                    logger.info("⚠ Audio recibido fuera de sesión, ignorado.")
                    continue

                # ===== STT =====
                text = auri.stt(pcm_bytes)
                logger.info(f"📝 Texto STT (raw): {text}")

                if not text.strip():
                    continue

                # ===== THINK =====
                mind = auri.think(text.strip())

                # enviar JSON → Flutter
                await ws.send_text(json.dumps(mind))

                # ===== TTS =====
                audio_out = auri.tts(mind["final"])
                await ws.send_bytes(audio_out)

    except WebSocketDisconnect:
        logger.info("🔌 Cliente desconectado")
