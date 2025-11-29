# D:\proyectAuri\auri_backend_whisper\server.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from realtime.realtime_ws import router as realtime_router
from router import router as rest_router  # AuriMind + TTS + STT REST

app = FastAPI(title="Auri Realtime Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔵 Ruta WebSocket REAL
app.include_router(realtime_router)

# 🔵 Rutas REST de AuriMind
app.include_router(rest_router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "auri_realtime"}

