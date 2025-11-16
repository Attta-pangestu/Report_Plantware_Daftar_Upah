from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from app.models.user import User
from app.services.payroll_service import PayrollService
from app.services.gang_service import GangService
from app.services.header_service import HeaderService
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.employee_repository_db import EmployeeRepositoryDB
from app.repositories.gang_repository_db import GangRepositoryDB
from app.models.payroll import PayrollRow

# Temporary auth bypass for testing
def get_current_user_temp():
    now = datetime.now()
    return User(
        id=1,
        username="admin",
        email="admin@test.com",
        full_name="Test Admin",
        role="admin",
        divisions=["PG1A", "PG1B", "PG2A", "PG2B", "DME", "ARA", "ARB1", "ARB2", "INFRA", "AREC", "IJL", "STF-OFFICE", "SECURITY"],
        is_active=True,
        password_hash="dummy_hash",
        created_at=now,
        updated_at=now
    )

router = APIRouter()

class PayrollRequest(BaseModel):
    upah_dasar: float
    hk_count: int
    allowances: Dict[str, float] = {}
    deductions: Dict[str, float] = {}

@router.post("/calculate")
async def calculate_payroll(req: PayrollRequest, user=Depends(get_current_user_temp)):
    svc = PayrollService()
    return await svc.calculate(req.upah_dasar, req.hk_count, req.allowances, req.deductions)

@router.get("/report", response_model=List[PayrollRow])
async def report_grid(gang_code: Optional[str] = Query(None), month: Optional[int] = Query(None), year: Optional[int] = Query(None), user=Depends(get_current_user_temp)):
    svc = PayrollService()
    try:
        # Always try to use real database first
        repo = EmployeeRepositoryDB()
        rows = await svc.generate_rows(repo, gang_code=gang_code, month=month, year=year)
        return rows
    except Exception as e:
        # Log the error but still try to return data if possible
        print(f"Database error: {e}")
        # Return empty result instead of fallback to mock data
        return []

# Initialize services
gang_service = GangService()
header_service = HeaderService()

@router.get("/divisions", response_model=List[str])
async def get_divisions(user=Depends(get_current_user_temp)):
    """Get all available divisions"""
    return gang_service.get_all_divisions()

@router.get("/gangs", response_model=List[str])
async def get_gangs(
    division: Optional[str] = Query(None, description="Filter gangs by division"),
    search: Optional[str] = Query(None, description="Search gangs with LIKE operator"),
    force: Optional[bool] = Query(False, description="Force refresh from database"),
    user=Depends(get_current_user_temp)
):
    """Get gang codes with optional division filtering and LIKE search"""
    try:
        if not division:
            accessible = gang_service.get_all_divisions() if user.role == 'admin' else user.divisions
            division = accessible[0] if accessible else None
        else:
            if user.role != 'admin' and division not in (user.divisions or []):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Division not accessible")

        # Use new gang service with division and search support
        gangs = await gang_service.fetch_gangs_from_database(division=division, search=search, force=bool(force))

        if division and not gangs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No gangs found for division {division}. Available divisions: {gang_service.get_all_divisions()}"
            )

        return gangs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch gangs: {str(e)}"
        )

@router.get("/gang/{gang_code}/info", response_model=dict)
async def get_gang_info(gang_code: str, user=Depends(get_current_user_temp)):
    """Get detailed information about a specific gang"""
    try:
        info = gang_service.get_gang_info(gang_code)
        if not info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gang {gang_code} not found"
            )
        return info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gang info: {str(e)}"
        )

@router.get("/headers", response_model=dict)
async def get_dynamic_headers(
    month: Optional[int] = Query(None, description="Month for report (1-12)"),
    year: Optional[int] = Query(None, description="Year for report"),
    gang_code: Optional[str] = Query(None, description="Gang code filter"),
    user=Depends(get_current_user_temp)
):
    """Generate dynamic headers based on real data"""
    try:
        headers = header_service.generate_dynamic_headers(
            month=month,
            year=year,
            gang_code=gang_code
        )
        return headers
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate headers: {str(e)}"
        )

@router.get("/columns", response_model=List[dict])
async def get_column_definitions(user=Depends(get_current_user_temp)):
    """Get AG Grid column definitions based on header structure"""
    try:
        column_defs = header_service.get_column_definitions()
        return column_defs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate column definitions: {str(e)}"
        )
