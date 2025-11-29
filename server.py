# D:\proyectAuri\auri_backend_whisper\server.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from realtime.realtime_ws import router as realtime_router

app = FastAPI(title="Auri Realtime Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 WebSocket de voz
app.include_router(realtime_router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "auri_realtime"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
