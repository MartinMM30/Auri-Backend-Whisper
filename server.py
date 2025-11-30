# server.py — versión correcta para tu backend actual

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers reales
from api_router import router as api_router           # /api
from realtime.realtime_ws import router as ws_router  # /realtime

app = FastAPI(title="Auri Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix="/api")
app.include_router(ws_router)

@app.get("/")
def root():
    return {"status": "ok", "msg": "Auri backend running"}
