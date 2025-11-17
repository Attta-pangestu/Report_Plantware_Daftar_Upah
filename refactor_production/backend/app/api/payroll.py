from fastapi import APIRouter, Depends, Query, HTTPException, status, Response
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
from app.models.user import User
from app.services.payroll_service import PayrollService
from app.services.gang_service import GangService
from app.services.header_service import HeaderService
from app.services.threaded_header_service import ThreadedHeaderService
from app.services.threaded_data_extractor import ThreadedDataExtractor
from app.repositories.employee_repository import EmployeeRepository
from app.repositories.employee_repository_db import EmployeeRepositoryDB
from app.repositories.gang_repository_db import GangRepositoryDB
from app.models.payroll import PayrollRow
import logging
from app.api.auth import get_current_user_from_token
from app.core.config import is_test_mode, DEFAULT_GANG, DEFAULT_MONTH, DEFAULT_YEAR
import time
import tracemalloc

logger = logging.getLogger(__name__)

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
async def report_grid(
    gang_code: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    skip: Optional[int] = Query(0, ge=0),
    limit: Optional[int] = Query(500, ge=1, le=2000),
    fields: Optional[str] = Query(None),
    benchmark: Optional[bool] = Query(False),
    monitor: Optional[bool] = Query(False),
    use_threading: Optional[bool] = Query(False, description="Use threaded data extraction for better performance"),
    response: Response = None,
    user=Depends(get_current_user_from_token)
):
    try:
        if is_test_mode():
            gang_code = gang_code or DEFAULT_GANG
            month = month or DEFAULT_MONTH
            year = year or DEFAULT_YEAR
            if response is not None:
                response.headers["X-Test-Mode"] = "true"

        start_time = time.perf_counter()

        if use_threading:
            # Use threaded data extraction
            extracted_data = threaded_data_extractor.extract_all_payroll_data_parallel(
                month=month or datetime.now().month,
                year=year or datetime.now().year,
                gang_code=gang_code or "ALL"
            )

            rows = extracted_data.get('data_rows', [])
            processing_type = "threaded"

            # Apply pagination if needed
            if skip or limit:
                rows = rows[skip:skip + limit]

            # Filter fields if specified
            if fields:
                f_list = [x.strip() for x in fields.split(',') if x.strip()]
                filtered_rows = []
                for row in rows:
                    filtered_row = {}
                    for field in f_list:
                        if hasattr(row, field):
                            filtered_row[field] = getattr(row, field)
                        elif field in row:
                            filtered_row[field] = row[field]
                    if filtered_row:
                        filtered_rows.append(filtered_row)
                rows = filtered_rows

        else:
            # Use original service
            svc = PayrollService()
            repo = EmployeeRepositoryDB()
            f_list = None
            if fields:
                f_list = [x.strip() for x in fields.split(',') if x.strip()]

            if monitor:
                tracemalloc.start()

            rows = await svc.generate_rows(repo, gang_code=gang_code, month=month, year=year, skip=skip, limit=limit, fields=f_list)
            processing_type = "sequential"

            if monitor:
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                if response is not None:
                    response.headers["X-Memory-Current-KB"] = str(int(current/1024))
                    response.headers["X-Memory-Peak-KB"] = str(int(peak/1024))

        execution_time = time.perf_counter() - start_time

        # Add performance headers
        if benchmark and response is not None:
            response.headers["X-TotalMs"] = str(int(execution_time * 1000))
            response.headers["X-Rows"] = str(len(rows))
            response.headers["X-Processing-Type"] = processing_type
            response.headers["X-Threading-Enabled"] = str(use_threading)

        return rows
    except Exception as e:
        logger.error(f"Database error: {e}")
        return []

# Initialize services
gang_service = GangService()
header_service = HeaderService()
threaded_header_service = ThreadedHeaderService.get_instance()
threaded_data_extractor = ThreadedDataExtractor.get_instance()

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

@router.get("/headers", response_model=dict)
async def get_dynamic_headers(
    month: Optional[int] = Query(None, description="Month for report (1-12)"),
    year: Optional[int] = Query(None, description="Year for report"),
    gang_code: Optional[str] = Query(None, description="Gang code filter"),
    use_threading: Optional[bool] = Query(True, description="Use threaded processing for better performance"),
    response: Response = None,
    user=Depends(get_current_user_from_token)
):
    """Generate dynamic headers based on real data with optional threading optimization"""
    try:
        if is_test_mode():
            month = month or DEFAULT_MONTH
            year = year or DEFAULT_YEAR
            gang_code = gang_code or DEFAULT_GANG
            if response is not None:
                response.headers["X-Test-Mode"] = "true"

        start_time = time.perf_counter()

        if use_threading:
            # Use optimized threaded service
            headers = threaded_header_service.generate_optimized_headers_parallel(
                month=month,
                year=year,
                gang_code=gang_code
            )
            processing_type = "threaded"
        else:
            # Use original service
            headers = header_service.generate_dynamic_headers(
                month=month,
                year=year,
                gang_code=gang_code
            )
            processing_type = "sequential"

        execution_time = time.perf_counter() - start_time

        # Add performance metrics to response
        if isinstance(headers, dict):
            headers['performance_info'] = {
                'processing_type': processing_type,
                'execution_time_ms': int(execution_time * 1000),
                'threading_enabled': use_threading
            }

        if response is not None:
            response.headers["X-Processing-Type"] = processing_type
            response.headers["X-Execution-Time-Ms"] = str(int(execution_time * 1000))
            response.headers["X-Threading-Enabled"] = str(use_threading)

        return headers
    except Exception as e:
        logger.error(f"Header generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate headers: {str(e)}"
        )

@router.get("/columns", response_model=List[dict])
async def get_column_definitions(
    month: Optional[int] = Query(None, description="Month for report (1-12)"),
    year: Optional[int] = Query(None, description="Year for report"),
    gang_code: Optional[str] = Query(None, description="Gang code filter"),
    response: Response = None,
    user=Depends(get_current_user_from_token)
):
    try:
        if is_test_mode():
            month = month or DEFAULT_MONTH
            year = year or DEFAULT_YEAR
            gang_code = gang_code or DEFAULT_GANG
            if response is not None:
                response.headers["X-Test-Mode"] = "true"
        column_defs = header_service.get_column_definitions(month=month, year=year, gang_code=gang_code)
        return column_defs
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate column definitions: {str(e)}"
        )

@router.get("/export_html")
async def export_html(
    gang_code: Optional[str] = Query(None, description="Gang code (e.g., H1H)"),
    month: Optional[int] = Query(None, description="Month for report (1-12)"),
    year: Optional[int] = Query(None, description="Year for report"),
    user=Depends(get_current_user_from_token)
):
    try:
        import sys
        from pathlib import Path
        engine_dir = Path(__file__).parent.parent.parent.parent.parent / "Engine_HTML_Templating" / "template_report" / "ui"
        sys.path.insert(0, str(engine_dir))
        from daftar_upah_engine_real_database import DaftarUpahEngineRealFixed

        if is_test_mode():
            m = str(DEFAULT_MONTH).zfill(2)
            y = str(DEFAULT_YEAR)
            gc = gang_code or DEFAULT_GANG
        else:
            m = str((month or datetime.now().month)).zfill(2)
            y = str(year or datetime.now().year)
            gc = gang_code or 'H1H'

        engine = DaftarUpahEngineRealFixed(month=m, year=y)
        out_path = engine.generate_report_from_real_database(
            gang_code=gc,
            limit=1000,
            template_file='daftar_upah_template_final.html',
            output_file=None
        )
        if not out_path:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate HTML report")
        with open(out_path, 'r', encoding='utf-8') as f:
            html = f.read()
        return Response(content=html, media_type='text/html')
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Export failed: {str(e)}")

@router.get("/reference_html")
async def reference_html(
    file_path: str = Query(..., description="Full path to reference HTML file"),
    user=Depends(get_current_user_from_token)
):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()
        return Response(content=html, media_type='text/html')
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Failed to read reference HTML: {str(e)}")

def _strip_html(s: str) -> str:
    import re
    return re.sub(r"<[^>]*>", "", s or "").strip()

def _num(s: str):
    try:
        import re
        cleaned = re.sub(r"[^0-9.-]", "", s or "")
        if cleaned == "":
            return None
        v = float(cleaned)
        return v
    except Exception:
        return None

@router.get("/validate_html")
async def validate_html(
    file_path: str = Query(..., description="Full path to reference HTML file"),
    gang_code: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    user=Depends(get_current_user_from_token)
):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html = f.read()

        import re
        thead_match = re.search(r"<thead[\s\S]*?<\/thead>", html, re.IGNORECASE)
        tbody_match = re.search(r"<tbody[\s\S]*?<\/tbody>", html, re.IGNORECASE)
        if not tbody_match:
            raise HTTPException(status_code=400, detail="No <tbody> found in reference HTML")
        tbody = tbody_match.group(0)

        # Extract rows
        tr_list = re.findall(r"<tr[\s\S]*?<\/tr>", tbody, re.IGNORECASE)
        rows_ref = []
        for tr in tr_list:
            tds = re.findall(r"<t[dh][^>]*>([\s\S]*?)<\/t[dh]>", tr, re.IGNORECASE)
            vals = [_strip_html(x) for x in tds]
            if len(vals) >= 5:
                rows_ref.append(vals)

        # Build a minimal header map by searching for known column names in the last header row
        header_leaf = []
        if thead_match:
            thead = thead_match.group(0)
            trs_h = re.findall(r"<tr[\s\S]*?<\/tr>", thead, re.IGNORECASE)
            if trs_h:
                last = trs_h[-1]
                header_leaf = [ _strip_html(m) for m in re.findall(r"<th[^>]*>([\s\S]*?)<\/th>", last, re.IGNORECASE) ]

        # Indices for key columns in reference
        def idx(name: str) -> int:
            try:
                return header_leaf.index(name)
            except Exception:
                return -1

        idx_map = {
            'nik': idx('NIK'),
            'nama': idx('NAMA'),
            'upah_dasar': idx('UPAH DASAR'),
            'hari_kerja': idx('HARI KERJA'),
            'upah_pokok': idx('UPAH POKOK')
        }

        # Build reference dict keyed by NIK
        ref_dict = {}
        for r in rows_ref:
            nidx = idx_map['nik']
            if nidx < 0 or nidx >= len(r):
                continue
            nik = r[nidx].strip()
            ref_item = {
                'nik': nik,
                'nama': r[idx_map['nama']] if idx_map['nama'] >= 0 else None,
                'upah_dasar': _num(r[idx_map['upah_dasar']]) if idx_map['upah_dasar'] >= 0 else None,
                'hari_kerja': int(_num(r[idx_map['hari_kerja']]) or 0) if idx_map['hari_kerja'] >= 0 else None,
                'upah_pokok': _num(r[idx_map['upah_pokok']]) if idx_map['upah_pokok'] >= 0 else None
            }
            ref_dict[nik] = ref_item

        # Get live rows from the system
        svc = PayrollService()
        repo = EmployeeRepositoryDB()
        if TEST_MODE:
            gang_code = gang_code or DEFAULT_GANG
            month = month or DEFAULT_MONTH
            year = year or DEFAULT_YEAR
        live_rows = await svc.generate_rows(repo, gang_code=gang_code, month=month, year=year)
        live_dict = { row.nik.strip(): row for row in live_rows }

        # Compare
        diffs = []
        all_keys = ['upah_dasar','hari_kerja','upah_pokok']
        for nik, ref in ref_dict.items():
            live = live_dict.get(nik)
            if not live:
                diffs.append({'nik': nik, 'status': 'missing_live_row'})
                continue
            mismatch = {}
            for k in all_keys:
                rv = ref.get(k)
                lv = getattr(live, k)
                if rv is None:
                    continue
                if float(lv or 0) != float(rv or 0):
                    mismatch[k] = {'reference': rv, 'live': lv}
            if mismatch:
                diffs.append({'nik': nik, 'nama': ref.get('nama'), 'mismatch': mismatch})

        # Heuristics for root cause
        same_upah_dasar = len({ r.upah_dasar for r in live_rows }) <= 1
        same_hari_kerja = len({ r.hari_kerja for r in live_rows }) <= 1
        same_upah_pokok = len({ r.upah_pokok for r in live_rows }) <= 1
        root = []
        if same_upah_dasar:
            root.append('Upah dasar constant across rows (likely fallback or single payrate).')
        if same_hari_kerja:
            root.append('Hari kerja constant across rows (HK count query or calendar misapplied).')
        if same_upah_pokok:
            root.append('Upah pokok constant because upah dasar and hari kerja are constant.')

        result = {
            'summary': {
                'total_reference_rows': len(ref_dict),
                'total_live_rows': len(live_rows),
                'differences_found': len(diffs),
                'root_cause_hints': root
            },
            'differences': diffs
        }
        logger.info(f"Validation summary: {result['summary']}")
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Validation failed: {str(e)}")
@router.get("/report/row/{nik}", response_model=PayrollRow)
async def report_single_row(
    nik: str,
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    fields: Optional[str] = Query(None),
    response: Response = None,
    user=Depends(get_current_user_from_token)
):
    try:
        if is_test_mode():
            month = month or DEFAULT_MONTH
            year = year or DEFAULT_YEAR
            if response is not None:
                response.headers["X-Test-Mode"] = "true"
        repo = EmployeeRepositoryDB()
        emp = repo.get_by_nik(nik)
        if not emp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        class SingleRepo:
            def list(self, skip, limit, gang_code=None, loc_code=None):
                return [emp]
        f_list = None
        if fields:
            f_list = [x.strip() for x in fields.split(',') if x.strip()]
        svc = PayrollService()
        out = await svc.generate_rows(SingleRepo(), gang_code=None, month=month, year=year, skip=0, limit=1, fields=f_list)
        return out[0]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/report/column/{field}", response_model=List[dict])
async def report_single_column(
    field: str,
    gang_code: Optional[str] = Query(None),
    month: Optional[int] = Query(None),
    year: Optional[int] = Query(None),
    skip: Optional[int] = Query(0, ge=0),
    limit: Optional[int] = Query(500, ge=1, le=2000),
    response: Response = None,
    user=Depends(get_current_user_from_token)
):
    try:
        if is_test_mode():
            gang_code = gang_code or DEFAULT_GANG
            month = month or DEFAULT_MONTH
            year = year or DEFAULT_YEAR
            if response is not None:
                response.headers["X-Test-Mode"] = "true"
        svc = PayrollService()
        repo = EmployeeRepositoryDB()
        rows = await svc.generate_rows(repo, gang_code=gang_code, month=month, year=year, skip=skip, limit=limit, fields=[field])
        out = []
        for r in rows:
            out.append({"nik": r.nik, field: getattr(r, field)})
        return out
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/performance/compare", response_model=dict)
async def compare_performance(
    gang_code: Optional[str] = Query(None, description="Gang code for testing"),
    month: Optional[int] = Query(None, description="Month for testing"),
    year: Optional[int] = Query(None, description="Year for testing"),
    response: Response = None,
    user=Depends(get_current_user_from_token)
):
    """
    Compare performance between sequential and threaded processing.
    This endpoint runs both methods and returns performance comparison.
    """
    try:
        if is_test_mode():
            gang_code = gang_code or DEFAULT_GANG
            month = month or DEFAULT_MONTH
            year = year or DEFAULT_YEAR
            if response is not None:
                response.headers["X-Test-Mode"] = "true"

        # Test 1: Sequential header generation
        seq_start = time.perf_counter()
        sequential_headers = header_service.generate_dynamic_headers(
            month=month,
            year=year,
            gang_code=gang_code
        )
        seq_time = time.perf_counter() - seq_start

        # Test 2: Threaded header generation
        thread_start = time.perf_counter()
        threaded_headers = threaded_header_service.generate_optimized_headers_parallel(
            month=month,
            year=year,
            gang_code=gang_code
        )
        thread_time = time.perf_counter() - thread_start

        # Test 3: Sequential data extraction (limited sample)
        seq_data_start = time.perf_counter()
        svc = PayrollService()
        repo = EmployeeRepositoryDB()
        sequential_data = await svc.generate_rows(repo, gang_code=gang_code, month=month, year=year, skip=0, limit=50)
        seq_data_time = time.perf_counter() - seq_data_start

        # Test 4: Threaded data extraction (limited sample)
        thread_data_start = time.perf_counter()
        threaded_extracted = threaded_data_extractor.extract_all_payroll_data_parallel(
            month=month,
            year=year,
            gang_code=gang_code
        )
        threaded_data = threaded_extracted.get('data_rows', [])[:50]  # Limit to 50 for fair comparison
        thread_data_time = time.perf_counter() - thread_data_start

        # Calculate performance improvements
        header_improvement = ((seq_time - thread_time) / seq_time * 100) if seq_time > 0 else 0
        data_improvement = ((seq_data_time - thread_data_time) / seq_data_time * 100) if seq_data_time > 0 else 0

        result = {
            "test_parameters": {
                "gang_code": gang_code,
                "month": month,
                "year": year,
                "sample_size": 50
            },
            "header_generation": {
                "sequential_time_ms": int(seq_time * 1000),
                "threaded_time_ms": int(thread_time * 1000),
                "improvement_percent": round(header_improvement, 2),
                "faster_by": round(seq_time / thread_time, 2) if thread_time > 0 else 0
            },
            "data_extraction": {
                "sequential_time_ms": int(seq_data_time * 1000),
                "threaded_time_ms": int(thread_data_time * 1000),
                "improvement_percent": round(data_improvement, 2),
                "faster_by": round(seq_data_time / thread_data_time, 2) if thread_data_time > 0 else 0
            },
            "overall": {
                "total_sequential_ms": int((seq_time + seq_data_time) * 1000),
                "total_threaded_ms": int((thread_time + thread_data_time) * 1000),
                "overall_improvement_percent": round(((seq_time + seq_data_time) - (thread_time + thread_data_time)) / (seq_time + seq_data_time) * 100, 2) if (seq_time + seq_data_time) > 0 else 0
            },
            "data_consistency": {
                "header_count_match": len(sequential_headers.get('table_structure', {}).get('generated_headers', {}).get('level_3', {}).get('columns', [])) == len(threaded_headers.get('table_structure', {}).get('generated_headers', {}).get('level_3', {}).get('columns', [])),
                "data_count_match": len(sequential_data) == len(threaded_data)
            }
        }

        if response is not None:
            response.headers["X-Header-Improvement"] = f"{round(header_improvement, 2)}%"
            response.headers["X-Data-Improvement"] = f"{round(data_improvement, 2)}%"
            response.headers["X-Overall-Improvement"] = f"{result['overall']['overall_improvement_percent']}%"

        logger.info(f"Performance comparison completed. Header improvement: {round(header_improvement, 2)}%, Data improvement: {round(data_improvement, 2)}%")

        return result
    except Exception as e:
        logger.error(f"Performance comparison failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Performance comparison failed: {str(e)}"
        )
