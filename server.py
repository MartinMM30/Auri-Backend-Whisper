# server.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from realtime.realtime_ws import router as realtime_router

app = FastAPI(title="Auri Realtime Backend")

# 🔓 CORS básico para que Flutter pueda hablarle desde cualquier lado
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # si quieres, luego restringes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔌 WebSocket /realtime
app.include_router(realtime_router)

# 🩺 Healthcheck para Render
@app.get("/")
async def root():
    return {"status": "ok", "service": "auri_realtime"}


# 🔥 Punto de entrada local (para pruebas en tu PC)
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
