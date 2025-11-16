import uuid
import sys
import os
from typing import Dict
from pathlib import Path
from fastapi import BackgroundTasks

# Add path to original engine
engine_path = Path(__file__).parent.parent.parent.parent.parent / "Engine_HTML_Templating" / "template_report" / "ui"
sys.path.insert(0, str(engine_path))

jobs: Dict[str, Dict] = {}

def run_job(job_id: str, params: Dict):
    try:
        # Import original engine
        from daftar_upah_engine_real_database import DaftarUpahEngineRealFixed

        # Initialize engine with parameters
        engine = DaftarUpahEngineRealFixed(
            month=str(params.get('month', 5)).zfill(2),
            year=str(params.get('year', 2025))
        )

        # Generate report data
        jobs[job_id]["status"] = "processing"
        report_data = engine.generate_report_data()

        jobs[job_id] = {
            "status": "completed",
            "result": {
                "job_id": job_id,
                "params": params,
                "data": report_data
            }
        }
    except Exception as e:
        jobs[job_id] = {
            "status": "failed",
            "error": str(e)
        }

class ReportService:
    def start(self, params: Dict, tasks: BackgroundTasks):
        job_id = uuid.uuid4().hex
        jobs[job_id] = {"status": "pending"}
        tasks.add_task(run_job, job_id, params)
        return {"job_id": job_id}

    def get(self, job_id: str):
        data = jobs.get(job_id)
        if not data:
            return {"status": "not_found"}
        return data
