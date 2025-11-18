import threading
import concurrent.futures
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from database.services.database import Database
from database.services.queries import Queries
from database.services.cache import Cache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreadedHeaderService:
    """Optimized header service with threading and parallel processing"""

    def __init__(self, max_workers: int = 3):
        self.max_workers = max_workers
        self.db = Database.instance(pool_size=20)
        self.queries = Queries()

    def generate_optimized_headers_parallel(self, month: int, year: int, gang_code: str) -> Dict[str, Any]:
        """
        Generate headers using parallel processing for maximum performance.
        Separates static headers from dynamic processing for better concurrency.
        """
        start_time = time.perf_counter()

        # Prepare date parameters
        start_date = f"{year}-{str(month).zfill(2)}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{str(month+1).zfill(2)}-01"

        # Define parallel tasks
        tasks = {
            'static_structure': self._load_static_structure_task(),
            'dynamic_premi': self._get_dynamic_premi_task(gang_code, start_date, end_date),
            'employee_count': self._get_employee_count_task(gang_code),
            'report_metadata': self._get_report_metadata_task(month, year, gang_code)
        }

        results = {}
        execution_times = {}

        # Execute all tasks in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit tasks
            future_to_name = {
                executor.submit(self._execute_task, name, task_def): name
                for name, task_def in tasks.items()
            }

            # Collect results with timing
            for future in concurrent.futures.as_completed(future_to_name):
                task_name = future_to_name[future]
                task_start = time.perf_counter()
                try:
                    result = future.result(timeout=15)  # 15 second timeout
                    results[task_name] = result
                    execution_times[task_name] = (time.perf_counter() - task_start) * 1000
                    logger.info(f"Task {task_name} completed in {execution_times[task_name]:.2f}ms")
                except Exception as e:
                    logger.error(f"Task {task_name} failed: {e}")
                    results[task_name] = None

        # Process results and build final structure
        final_headers = self._build_final_headers(results, month, year, gang_code)

        total_time = time.perf_counter() - start_time
        logger.info(f"Parallel header generation completed in {total_time:.2f} seconds")

        return {
            **final_headers,
            'performance_metrics': {
                'total_execution_time_ms': total_time * 1000,
                'task_execution_times': execution_times,
                'parallel_workers_used': self.max_workers
            }
        }

    def _execute_task(self, task_name: str, task_def: Any):
        """Execute a single task based on its definition"""
        try:
            if callable(task_def):
                # Task is a function, call it directly
                return task_def()
            elif isinstance(task_def, dict) and 'sql' in task_def:
                # Task is a database query
                params = task_def.get('params', [])
                return self.db.query_all(task_def['sql'], params)
            elif isinstance(task_def, dict) and 'cache_key' in task_def:
                # Task involves caching
                return self._execute_cached_task(task_def)
            else:
                raise ValueError(f"Invalid task definition for {task_name}")
        except Exception as e:
            logger.error(f"Error executing task {task_name}: {e}")
            raise

    def _load_static_structure_task(self):
        """Load static header structure from JSON file"""
        def task():
            import json
            import os

            current_dir = os.path.dirname(__file__)
            app_dir = os.path.dirname(current_dir)
            backend_dir = os.path.dirname(app_dir)
            refactor_dir = os.path.dirname(backend_dir)
            project_root = os.path.dirname(refactor_dir)
            header_file = os.path.join(
                project_root,
                'Engine_HTML_Templating', 'template_report', 'struktur_header_report.json'
            )

            try:
                with open(header_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load header structure: {e}")
                raise Exception(f"Header structure file not found or invalid: {header_file}")

        return task

    def _get_dynamic_premi_task(self, gang_code: str, start_date: str, end_date: str):
        """Get dynamic premi headers with optimized query"""
        return {
            'cache_key': f"premi_headers:{gang_code}:{start_date}_{end_date}",
            'sql': """
                SELECT DISTINCT t.DocDesc
                FROM "PR_ADTRANS_ARC" AS t
                JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
                WHERE t.EmpCode IN (
                    SELECT "HR_EMPLOYEE"."EmpCode"
                    FROM "HR_EMPLOYEE"
                    JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
                    WHERE "HR_GANGLN"."GangCode" = ?
                )
                AND t.DocDate >= ?
                AND t.DocDate < ?
                ORDER BY t.DocDesc
            """,
            'params': [gang_code, start_date, end_date],
            'ttl': 1800  # 30 minutes cache
        }

    def _get_employee_count_task(self, gang_code: str):
        """Get employee count for the gang"""
        return {
            'cache_key': f"emp_count:{gang_code}",
            'sql': """
                SELECT COUNT(DISTINCT g.GangMember)
                FROM HR_GANGLN g
                WHERE g.GangCode = ? OR ? = 'ALL'
            """,
            'params': [gang_code, gang_code.upper()],
            'ttl': 3600  # 1 hour cache
        }

    def _get_report_metadata_task(self, month: int, year: int, gang_code: str):
        """Generate report metadata"""
        def task():
            month_names = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

            return {
                'title': f"DAFTAR UPAH - {month_names[month] if month else 'Unknown'} {year or datetime.now().year}",
                'generated_date': datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                'gang': gang_code or "All Gangs",
                'database': "ARC",
                'description': "Laporan daftar upah dengan header dinamis berdasarkan data real",
                'month': month,
                'year': year
            }

        return task

    def _execute_cached_task(self, task_def: Dict[str, Any]) -> Any:
        """Execute task with caching"""
        cache_key = task_def.get('cache_key')
        sql = task_def.get('sql')
        params = task_def.get('params', [])
        ttl = task_def.get('ttl', 900)  # Default 15 minutes

        # Try cache first
        cached = Cache.instance().get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for {cache_key}")
            return cached

        # Execute query
        result = self.db.query_all(sql, params)

        # Handle case where db.query_all returns None
        if result is None:
            result = []

        # Cache result
        Cache.instance().set(cache_key, result, ttl)
        logger.info(f"Cached result for {cache_key}")

        return result

    def _build_final_headers(self, results: Dict[str, Any], month: int, year: int, gang_code: str) -> Dict[str, Any]:
        """Build final header structure from parallel results"""

        # Get static structure - no fallback, must be present
        if 'static_structure' not in results or results['static_structure'] is None:
            raise Exception("Static structure is required but not available")
        header_structure = results['static_structure']
        table_structure = header_structure.get('table_structure', {})
        hierarchy = table_structure.get('hierarchy', {})

        # Get dynamic premium headers
        dynamic_premi_results = results.get('dynamic_premi', [])
        # Handle case where dynamic_premi_results is None
        if dynamic_premi_results is None:
            dynamic_premi_results = []
        dynamic_premi_headers = [str(row[0]).strip() for row in dynamic_premi_results if row and row[0]]
        excluded_lower = {
            'koreksi', 'potongan pph21', 'potongan spsi', 'tunjangan jabatan',
            'tunjangan masa kerja', 'pruning', 'brondol', 'pph 21', 'pph21',
            'spsi', 'koreksi panen', 'potongan koreksi', 'potongan koreksi panen',
            'tunjangan premi', 'tunjangan beras'
        }
        dynamic_premi_headers = [h for h in dynamic_premi_headers if h and h.strip().lower() not in excluded_lower]

        # Update premium headers in the structure
        level2 = hierarchy.get('level_2', {}).get('columns', [])
        premi_children = [c for c in level2 if c.get('parent') == 'premi']

        fixed_premi = []
        dynamic_slots = []
        for c in premi_children:
            t = (c.get('text') or '').upper()
            if 'BRONDOL' in t or 'PRUNING' in t:
                fixed_premi.append(c)
            else:
                dynamic_slots.append(c)

        # Keep static header texts; dynamic headers are exposed for reference only

        # Get report metadata
        report_metadata = results.get('report_metadata', {})
        employee_count_result = results.get('employee_count', [(0,)])
        # Handle case where employee_count_result is None
        if employee_count_result is None:
            employee_count_result = [(0,)]
        employee_count = employee_count_result[0][0] if employee_count_result else 0

        # Keep all original premi children; only adjust text for dynamic slot
        hierarchy.get('level_2', {})['columns'] = level2

        # Build complete header hierarchy
        headers = self._build_header_hierarchy(table_structure)

        return {
            "report_info": report_metadata,
            "table_structure": {
                **table_structure,
                "generated_headers": headers,
                "total_columns": len(headers.get('level_3', {}).get('columns', [])),
                "data_source": "real_database",
                "employee_count": employee_count,
                "dynamic_premi_count": len(dynamic_premi_headers),
                "dynamic_docdesc": dynamic_premi_headers
            }
        }

    def _build_header_hierarchy(self, table_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Build complete header hierarchy from structure"""
        hierarchy = table_structure.get('hierarchy', {})

        # Process each level
        level_1_columns = hierarchy.get('level_1', {}).get('columns', [])
        level_2_columns = hierarchy.get('level_2', {}).get('columns', [])
        level_3_columns = hierarchy.get('level_3', {}).get('columns', [])

        # Build column relationships
        column_map = self._build_column_mapping(level_1_columns, level_2_columns, level_3_columns)

        return {
            "level_1": {
                "row": 1,
                "columns": self._process_level_1_columns(level_1_columns, column_map)
            },
            "level_2": {
                "row": 2,
                "columns": self._process_level_2_columns(level_2_columns, column_map)
            },
            "level_3": {
                "row": 3,
                "columns": self._process_level_3_columns(level_3_columns, column_map)
            }
        }

    def _build_column_mapping(self, level_1: List[Dict], level_2: List[Dict], level_3: List[Dict]) -> Dict[str, Any]:
        """Build mapping between parent and child columns"""
        mapping = {
            'level_1_to_2': {},
            'level_2_to_3': {},
            'all_columns': {}
        }

        # Map level 1 to level 2
        for col in level_1:
            col_id = col.get('id')
            children = col.get('children', [])
            for child_id in children:
                mapping['level_1_to_2'][child_id] = col_id
                mapping['all_columns'][col_id] = col

        # Map level 2 to level 3
        for col in level_2:
            col_id = col.get('id')
            children = col.get('children', [])
            for child_id in children:
                mapping['level_2_to_3'][child_id] = col_id
                mapping['all_columns'][col_id] = col

        # Add level 3 columns
        for col in level_3:
            col_id = col.get('id')
            mapping['all_columns'][col_id] = col

        return mapping

    def _process_level_1_columns(self, columns: List[Dict], column_map: Dict[str, Any]) -> List[Dict]:
        """Process level 1 header columns"""
        processed = []
        for col in columns:
            processed_col = {
                "id": col.get('id'),
                "text": col.get('text'),
                "rowspan": col.get('rowspan', 1),
                "colspan": col.get('colspan', 1),
                "class": col.get('class', ''),
                "type": "main_header"
            }
            processed.append(processed_col)
        return processed

    def _process_level_2_columns(self, columns: List[Dict], column_map: Dict[str, Any]) -> List[Dict]:
        """Process level 2 header columns"""
        processed = []
        for col in columns:
            processed_col = {
                "id": col.get('id'),
                "text": col.get('text'),
                "parent": col.get('parent'),
                "colspan": col.get('colspan', 1),
                "class": col.get('class', ''),
                "type": "sub_header"
            }
            processed.append(processed_col)
        return processed

    def _process_level_3_columns(self, columns: List[Dict], column_map: Dict[str, Any]) -> List[Dict]:
        """Process level 3 header columns (actual data columns)"""
        processed = []
        for col in columns:
            processed_col = {
                "id": col.get('id'),
                "text": col.get('text'),
                "parent": col.get('parent'),
                "class": col.get('class', ''),
                "type": "data_column",
                "field": self._map_to_data_field(col.get('id'))
            }
            processed.append(processed_col)
        return processed

    def _map_to_data_field(self, column_id: str) -> str:
        """Map header column ID to PayrollRow field"""
        field_mapping = {
            # Static columns
            "no": "no", "gender": "jenis_kelamin", "nik": "nik", "name": "nama",
            "upah_dasar": "upah_dasar", "hari_kerja": "hari_kerja", "upah_pokok": "upah_pokok",
            "jml_hk": "jumlah_hk", "gaji_pokok": "gaji_pokok",

            # Cuti columns
            "cuti_tahunan_unit": "cuti_tahunan_hari", "cuti_sakit_haid_unit": "cuti_sakit_haid_hari",
            "cuti_minggu_unit": "cuti_minggu_hari", "cuti_nasional_unit": "cuti_nasional_hari",
            "cuti_izin_unit": "cuti_izin_hari",

            # Tunjangan columns
            "beras_rate": "beras_rate", "beras_jumlah": "beras_jumlah", "jabatan_rate": "jabatan_rate",
            "jabatan_jumlah": "jabatan_jumlah", "masa_kerja_lama": "masa_kerja_tahun",
            "masa_kerja_jumlah": "masa_kerja_jumlah", "lembur_jam": "lembur_jam", "lembur_jumlah": "lembur_jumlah",

            # Premi columns
            "brondol_jumlah": "premi_brondol", "pruning_jumlah": "premi_pruning",
            "premi_angkut_material_jumlah": "premi_angkut_material", "premi_angkut_tbs_jumlah": "premi_angkut_tbs",
            "premi_harvesting_jumlah": "premi_harvesting", "premi_harvesting_incentive_jumlah": "premi_harvesting_incentive",
            "premi_pupuk_jumlah": "premi_pupuk",

            # Potongan columns
            "pph21": "pot_pph21", "potongan_kontan": "pot_kontan", "thr": "pot_thr", "pinjam": "pot_pinjam",
            "kl": "pot_kl", "bpjs_kes": "pot_bpjs_kes", "bpjs_pek": "pot_bpjs_pek", "bpjs_maj": "pot_bpjs_maj",
            "total1": "pot_total_1", "total2": "pot_total_2", "total3": "pot_total_3", "total4": "pot_total_4",

            # Final columns
            "total_tunjangan": "total_tunjangan", "upah_bersih": "upah_bersih",
            "cth": "tidak_hadir_cth", "alpa": "tidak_hadir_alpa"
        }

        return field_mapping.get(column_id, column_id)

    def _get_fallback_structure(self) -> Dict[str, Any]:
        """Fallback structure if JSON file cannot be loaded"""
        return {
            "table_structure": {
                "header_rows": 3,
                "hierarchy": {
                    "level_1": {"columns": []},
                    "level_2": {"columns": []},
                    "level_3": {"columns": []}
                }
            }
        }

    @staticmethod
    def get_instance() -> 'ThreadedHeaderService':
        """Singleton pattern for ThreadedHeaderService"""
        if not hasattr(ThreadedHeaderService, '_instance'):
            ThreadedHeaderService._instance = ThreadedHeaderService()
        return ThreadedHeaderService._instance
