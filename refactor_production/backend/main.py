import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router

# Check if running in development mode
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Add development mode info
@app.get("/dev-mode")
async def get_dev_mode():
    return {"dev_mode": DEV_MODE}

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
