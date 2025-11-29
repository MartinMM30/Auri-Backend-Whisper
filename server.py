# D:\proyectAuri\auri_backend_whisper\server.py

import os
import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

# ⬇ Ajustar si tu carpeta es diferente
from realtime.realtime_ws import router as realtime_router

# Logging global
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Auri Realtime Backend")

# ------------------------- CORS -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------- ROUTERS ----------------------
# WebSocket principal Auri
app.include_router(realtime_router)

# Healthcheck HTTP (Render will call this)
@app.get("/")
async def root():
    return {"status": "ok", "service": "auri_realtime"}

# Healthcheck WebSocket (optional but recommended)
@app.websocket("/ws-test")
async def ws_test(ws: WebSocket):
    await ws.accept()
    await ws.send_text("ok")
    await ws.close()

# ------------------------- LOCAL RUN ----------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
