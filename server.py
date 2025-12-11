# server.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_router import router as api_router
from realtime.realtime_ws import router as realtime_router
from dotenv import load_dotenv
from api.memory_router import router as memory_router
from routes import admin_tools





load_dotenv()


app = FastAPI(title="Auri Backend", version="3.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    allow_methods=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(realtime_router)
app.include_router(api_router, prefix="/api")
app.include_router(memory_router, prefix="/api")   # ← NUEVO
app.include_router(realtime_router)
app.include_router(admin_tools.router, prefix="/admin", tags=["admin"])


@app.get("/")
def home():
    return {"status": "Auri Backend OK", "version": "3.8"}
