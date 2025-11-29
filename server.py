# D:\proyectAuri\auri_backend_whisper\server.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# NUEVO WebSocket limpio
from realtime.realtime_ws import router as realtime_router

# Rutas REST de AuriMind
from router import router as rest_router

app = FastAPI(title="Auri Realtime Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket REAL (único)
app.include_router(realtime_router)

# Rutas REST
app.include_router(rest_router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "auri_realtime"}
