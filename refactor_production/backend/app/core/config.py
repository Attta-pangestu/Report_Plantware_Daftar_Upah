import os
from datetime import timedelta, datetime

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
ACCESS_TOKEN_EXPIRE_DELTA = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
DEFAULT_GANG = os.getenv("DEFAULT_GANG", "H1H")
DEFAULT_MONTH = int(os.getenv("DEFAULT_MONTH", "5"))
DEFAULT_YEAR = int(os.getenv("DEFAULT_YEAR", str(datetime.now().year)))

def _is_true_env(name: str) -> bool:
    v = os.getenv(name, "false")
    return str(v).lower() == "true"

def is_test_mode() -> bool:
    if TEST_MODE:
        return True
    if _is_true_env("DEV_MODE"):
        return True
    if _is_true_env("VITE_DEV_MODE"):
        return True
    return False
