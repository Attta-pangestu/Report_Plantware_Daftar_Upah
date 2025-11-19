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

# Configure CORS with explicit allowed origins to avoid browser cancellations
def _allowed_origins():
    env_origins = os.getenv("CORS_ALLOW_ORIGINS")
    if env_origins:
        try:
            items = [o.strip() for o in env_origins.split(",") if o.strip()]
            if items:
                return items
        except Exception:
            pass
    return [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)

# Add development mode info
@app.get("/dev-mode")
async def get_dev_mode():
    from app.core.config import TEST_MODE, DEFAULT_GANG, DEFAULT_MONTH, DEFAULT_YEAR, get_testing_token, is_test_mode
    return {
        "dev_mode": is_test_mode(),
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
    # Ensure Referrer-Policy is set to avoid noisy browser warnings; does not affect auth
    try:
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    except Exception:
        pass
    return response

if __name__ == "__main__":
    workers = 1
    try:
        workers = int(os.getenv("UVICORN_WORKERS", "1"))
    except Exception:
        workers = 1
    uvicorn.run("main:app", host="0.0.0.0", port=8002, workers=workers)
