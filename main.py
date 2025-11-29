import os
import uvicorn
from server import app  # usa tu FastAPI real con los routers ya incluidos

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=False,
        workers=1
    )
