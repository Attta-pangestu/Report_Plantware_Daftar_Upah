import uvicorn
import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.core.config import is_test_mode

# Check if running in development mode
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

logging.basicConfig(level=logging.INFO)
app = FastAPI()
# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Add exposed headers to ensure all response headers are accessible
    expose_headers=["*"]
)

# Add development mode info
@app.get("/dev-mode")
async def get_dev_mode():
    from app.core.config import TEST_MODE, DEFAULT_GANG, DEFAULT_MONTH, DEFAULT_YEAR, get_testing_token
    return {
        "dev_mode": DEV_MODE,
        "test_mode": is_test_mode(),
        "test_mode_hardcoded": TEST_MODE,
        "default_gang": DEFAULT_GANG,
        "default_month": DEFAULT_MONTH,
        "default_year": DEFAULT_YEAR,
        "has_testing_token": bool(get_testing_token()),
        "environment_vars": {
            "TEST_MODE": os.getenv("TEST_MODE"),
            "DEV_MODE": os.getenv("DEV_MODE"),
            "VITE_DEV_MODE": os.getenv("VITE_DEV_MODE")
        }
    }

app.include_router(api_router)

request_logger = logging.getLogger("app.request")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import time
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = int((time.perf_counter() - start) * 1000)
    request_logger.info(f"{request.method} {request.url.path}?{request.url.query} {response.status_code} {duration_ms}ms test_mode={is_test_mode()}")
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8002)
