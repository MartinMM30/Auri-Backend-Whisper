from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_router import router as api_router
from realtime.realtime_ws import router as ws_router

app = FastAPI(title="Auri Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------
# RUTAS
# ----------------------
app.include_router(api_router, prefix="/api")     # REST
app.include_router(ws_router)                     # WS directo: /realtime

@app.get("/")
def root():
    return {"status": "ok", "msg": "Auri backend running"}
