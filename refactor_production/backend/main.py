import uvicorn
import os
import logging
import argparse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import (
    is_test_mode,
    TEST_MODE,
    DEFAULT_GANG,
    DEFAULT_MONTH,
    DEFAULT_YEAR,
    get_testing_token,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if running in development mode
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

app = FastAPI()

# Configure CORS with explicit allowed origins
def _allowed_origins():
    env_origins = os.getenv("CORS_ALLOW_ORIGINS")
    if env_origins:
        try:
            items = [o.strip() for o in env_origins.split(",") if o.strip()]
            if items:
                return items
        except Exception as e:
            logger.error(f"Failed to parse CORS_ALLOW_ORIGINS: {e}")
    return [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Development mode info endpoint
@app.get("/dev-mode")
async def get_dev_mode():
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
            "VITE_DEV_MODE": os.getenv("VITE_DEV_MODE"),
        },
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
    
    # Sanitize query string to avoid logging sensitive data
    sanitized_query = str(request.url.query)
    sensitive_params = ["password", "token", "secret"]
    for param in sensitive_params:
        if param in sanitized_query:
            sanitized_query = sanitized_query.replace(
                f"{param}={request.query_params.get(param)}", 
                f"{param}=***"
            )
    
    request_logger.info(
        f"{request.method} {request.url.path}?{sanitized_query} "
        f"{response.status_code} {duration_ms}ms test_mode={is_test_mode()}"
    )
    
    # Set Referrer-Policy header safely
    if hasattr(response, "headers"):
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-driver")
    parser.add_argument("--db-server")
    parser.add_argument("--db-port", type=int)
    parser.add_argument("--db-name")
    parser.add_argument("--db-user")
    parser.add_argument("--db-pass")
    parser.add_argument("--db-profile")
    parser.add_argument("--uvicorn-workers", type=int)
    parser.add_argument("--port", type=int, help="Backend HTTP port")
    args = parser.parse_args()

    # Set environment variables from CLI args (CLI takes precedence)
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
    if args.db_profile:
        os.environ["DB_PROFILE"] = args.db_profile

    # Configure workers (CLI > env var > default)
    workers = 1
    if args.uvicorn_workers is not None:
        workers = args.uvicorn_workers
    else:
        try:
            env_workers = os.getenv("UVICORN_WORKERS")
            if env_workers:
                workers = int(env_workers)
        except ValueError:
            logger.warning("Invalid UVICORN_WORKERS value. Using default.")

    # Configure port (CLI > env var > default)
    port = 8002
    if args.port is not None:
        port = args.port
    else:
        try:
            env_port = os.getenv("BACKEND_PORT")
            if env_port:
                port = int(env_port)
        except ValueError:
            logger.warning("Invalid BACKEND_PORT value. Using default.")

    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=workers)