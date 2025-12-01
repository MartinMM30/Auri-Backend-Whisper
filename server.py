from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api_router import router as api_router

app = FastAPI(title="Auri Backend", version="3.0")

# CORS (para Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(api_router, prefix="/api")


@app.get("/")
def home():
    return {"status": "Auri Backend OK", "version": "3.0"}
