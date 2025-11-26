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

# Global variables for mode and IP
RUN_MODE = None  # "dev", "prod"
MODE_IP = None   # IP address based on mode

app = FastAPI()

# Configure CORS with explicit allowed origins based on mode
def _allowed_origins():
    global RUN_MODE, MODE_IP

    env_origins = os.getenv("CORS_ALLOW_ORIGINS")
    if env_origins:
        try:
            items = [o.strip() for o in env_origins.split(",") if o.strip()]
            if items:
                return items
        except Exception as e:
            logger.error(f"Failed to parse CORS_ALLOW_ORIGINS: {e}")

    # For multi-computer access, return specific origins in development mode or prod mode
    if DEV_MODE or RUN_MODE in ["dev", "prod"]:
        # Include localhost, 127.0.0.1, and common network ranges for development
        origins = [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://localhost:5175",
            "http://localhost:5176",
            "http://localhost:5177",
            "http://localhost:5178",
            "http://localhost:5182",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://127.0.0.1:5175",
            "http://127.0.0.1:5176",
            "http://127.0.0.1:5177",
            "http://127.0.0.1:5178",
            "http://127.0.0.1:5182",
            # Add 10.0.0.x range for your local network
            "http://10.0.0.128:5173",
            "http://10.0.0.128:5174",
            "http://10.0.0.128:5175",
            "http://10.0.0.128:5176",
            "http://10.0.0.128:5177",
            "http://10.0.0.128:5178",
            "http://10.0.0.128:5182",
            "http://10.0.0.128:5183",
            "http://10.0.0.128:5184"
        ]
        return origins

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

def get_mode_ip():
    """Get IP address based on the current mode"""
    global RUN_MODE, MODE_IP

    if MODE_IP:
        return MODE_IP

    # Try to get from global variables if already set
    try:
        if RUN_MODE == "prod":
            return "10.0.0.110"
        elif RUN_MODE == "dev":
            return ["localhost", "10.0.0.128"]  # Return list for dev mode
    except NameError:
        pass

    return "localhost"  # Default fallback

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
        "run_mode": RUN_MODE,
        "mode_ip": get_mode_ip(),
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
    parser = argparse.ArgumentParser(
        description="Payroll Backend Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Mode Examples:
  python main.py --mode dev     # Development mode (localhost + 10.0.0.128)
  python main.py --mode prod    # Production mode (10.0.0.110)
  python main.py --mode dev --custom-ip 192.168.1.100  # Custom IP for dev mode
        """
    )

    # Mode arguments
    parser.add_argument("--mode", choices=["dev", "prod"],
                       help="Run mode: dev=localhost+10.0.0.128, prod=10.0.0.110")
    parser.add_argument("--custom-ip",
                       help="Custom IP address to override mode-based IP")

    # Database arguments
    parser.add_argument("--db-driver")
    parser.add_argument("--db-server")
    parser.add_argument("--db-port", type=int)
    parser.add_argument("--db-name")
    parser.add_argument("--db-user")
    parser.add_argument("--db-pass")
    parser.add_argument("--db-profile")

    # Server arguments
    parser.add_argument("--uvicorn-workers", type=int)
    parser.add_argument("--port", type=int, help="Backend HTTP port")

    args = parser.parse_args()

    # Process mode and custom IP arguments
    if args.mode:
        RUN_MODE = args.mode
    else:
        RUN_MODE = None

    if args.custom_ip:
        MODE_IP = args.custom_ip
        logger.info(f"Using custom IP: {MODE_IP}")
    elif args.mode:
        if args.mode == "dev":
            MODE_IP = ["localhost", "10.0.0.128"]
            logger.info("Development mode: Using localhost + 10.0.0.128")
        elif args.mode == "prod":
            MODE_IP = "10.0.0.110"
            logger.info("Production mode: Using 10.0.0.110")

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

    # Log mode and IP information
    logger.info("="*60)
    logger.info("PAYROLL BACKEND SERVER CONFIGURATION")
    logger.info("="*60)
    logger.info(f"🚀 Run Mode: {RUN_MODE or 'default'}")
    logger.info(f"🌐 Mode IP: {get_mode_ip()}")
    logger.info(f"🔗 Host: 0.0.0.0")
    logger.info(f"📡 Port: {port}")
    logger.info(f"⚙️  Workers: {workers}")
    logger.info(f"🔧 Dev Mode: {DEV_MODE}")

    if RUN_MODE:
        logger.info(f"📋 Access URLs:")
        if RUN_MODE == "dev":
            if isinstance(MODE_IP, list):
                for ip in MODE_IP:
                    logger.info(f"   • http://{ip}:{port}")
            else:
                logger.info(f"   • http://{MODE_IP}:{port}")
        elif RUN_MODE == "prod":
            logger.info(f"   • http://{MODE_IP}:{port}")
    else:
        logger.info(f"📋 Access URL: http://localhost:{port}")

    logger.info("="*60)

    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=workers)