from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .employees import router as employees_router
from .payroll import router as payroll_router
from .reports import router as reports_router
from .config import router as config_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, tags=["users"])
router.include_router(employees_router, prefix="/employees", tags=["employees"])
router.include_router(payroll_router, prefix="/payroll", tags=["payroll"])
router.include_router(reports_router, prefix="/reports", tags=["reports"])
router.include_router(config_router, prefix="/config", tags=["config"])
