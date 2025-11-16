from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel
from typing import Dict, List, Optional
from app.api.auth import get_current_user_from_token
from app.services.payroll_service import PayrollService
from app.services.gang_service import GangService
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.employee_repository_db import EmployeeRepositoryDB
from app.repositories.gang_repository_db import GangRepositoryDB
from app.models.payroll import PayrollRow

router = APIRouter()

class PayrollRequest(BaseModel):
    upah_dasar: float
    hk_count: int
    allowances: Dict[str, float] = {}
    deductions: Dict[str, float] = {}

@router.post("/calculate")
async def calculate_payroll(req: PayrollRequest, user=Depends(get_current_user_from_token)):
    svc = PayrollService()
    return await svc.calculate(req.upah_dasar, req.hk_count, req.allowances, req.deductions)

@router.get("/report", response_model=List[PayrollRow])
async def report_grid(gang_code: Optional[str] = Query(None), month: Optional[int] = Query(None), year: Optional[int] = Query(None), user=Depends(get_current_user_from_token)):
    svc = PayrollService()
    try:
        repo = EmployeeRepositoryDB()
        rows = await svc.generate_rows(repo, gang_code=gang_code, month=month, year=year)
        if rows:
            return rows
    except Exception:
        pass
    repo = EmployeeRepository()
    return await svc.generate_rows(repo, gang_code=gang_code, month=month, year=year)

# Initialize gang service
gang_service = GangService()

@router.get("/divisions", response_model=List[str])
async def get_divisions(user=Depends(get_current_user_from_token)):
    """Get all available divisions"""
    return gang_service.get_all_divisions()

@router.get("/gangs", response_model=List[str])
async def get_gangs(
    division: Optional[str] = Query(None, description="Filter gangs by division"),
    search: Optional[str] = Query(None, description="Search gangs with LIKE operator"),
    force: Optional[bool] = Query(False, description="Force refresh from database"),
    user=Depends(get_current_user_from_token)
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
async def get_gang_info(gang_code: str, user=Depends(get_current_user_from_token)):
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
