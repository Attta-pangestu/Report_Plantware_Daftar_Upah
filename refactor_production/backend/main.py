import uvicorn
import os
import logging
import argparse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
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

from app.api import router as api_router
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-driver")
    parser.add_argument("--db-server")
    parser.add_argument("--db-port", type=int)
    parser.add_argument("--db-name")
    parser.add_argument("--db-user")
    parser.add_argument("--db-pass")
    parser.add_argument("--uvicorn-workers", type=int)
    parser.add_argument("--port", type=int, help="Backend HTTP port")
    args = parser.parse_args()

    if args.db_driver:
        os.environ["DB_DRIVER"] = args.db_driver
    if args.db_server:
        os.environ["DB_SERVER"] = args.db_server
    if args.db_port is not None:
        os.environ["DB_PORT"] = str(args.db_port)
    if args.db_name:
        os.environ["DB_NAME"] = args.db_name
    if args.db_user:
        os.environ["DB_USER"] = args.db_user
    if args.db_pass:
        os.environ["DB_PASS"] = args.db_pass

    workers = 1
    try:
        workers = int(os.getenv("UVICORN_WORKERS", "1"))
    except Exception:
        workers = 1
    if args.uvicorn_workers is not None:
        workers = args.uvicorn_workers
    port = 8002
    if args.port is not None:
        port = args.port
    try:
        env_port = int(os.getenv("BACKEND_PORT", str(port)))
        port = env_port
    except Exception:
        pass
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=workers)
