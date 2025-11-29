from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from realtime.realtime_ws import router as realtime_router
from router import router as api_router  # auri REST

app = FastAPI(title="Auri Backend v4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(realtime_router)
app.include_router(api_router)

@app.get("/")
async def root():
    return {"status": "ok", "service": "auri_realtime_v4"}
