from typing import Dict, Any, List
from datetime import datetime
import json
import os
import time
from database.services.database import Database
from database.services.queries import Queries
from database.services.cache import Cache

class HeaderService:
    def __init__(self):
        # Load header structure from JSON file
        # Get the project root (4 levels up from services directory)
        current_dir = os.path.dirname(__file__)
        app_dir = os.path.dirname(current_dir)  # Go up to app
        backend_dir = os.path.dirname(app_dir)  # Go up to backend
        refactor_dir = os.path.dirname(backend_dir)  # Go up to refactor_production
        project_root = os.path.dirname(refactor_dir)  # Go up to project root
        header_file = os.path.join(
            project_root,
            'Engine_HTML_Templating', 'template_report', 'struktur_header_report.json'
        )
        # print(f"Looking for header file at: {header_file}")  # Debug log
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                self.header_structure = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load header structure: {e}")
            raise Exception(f"Header structure file not found or invalid: {header_file}")

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

    def generate_dynamic_headers(self, month: int = None, year: int = None, gang_code: str = None) -> Dict[str, Any]:
        """
        Generate dynamic headers based on real data

        Args:
            month: Month for the report (1-12)
            year: Year for the report
            gang_code: Gang code filter

        Returns:
            Dictionary containing complete header structure with real data
        """
        try:
            # Get month name in Indonesian
            month_names = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
                          'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
            month_name = month_names[month] if month else "Unknown"

            # Update report info with real data
            report_info = {
                "title": f"DAFTAR UPAH - {month_name} {year or datetime.now().year}",
                "generated_date": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                "gang": gang_code or "All Gangs",
                "database": "ARC",  # Based on current database
                "description": "Laporan daftar upah dengan header dinamis berdasarkan data real"
            }

            table_structure = self.header_structure.get('table_structure', {})

            tq0 = time.perf_counter()
            dyn = self._compute_dynamic_premi_headers_db(month or datetime.now().month, year or datetime.now().year, gang_code or 'H1H')
            tq1 = time.perf_counter()

            hierarchy = table_structure.get('hierarchy', {})
            # Keep header texts from JSON; backend provides filtered dynamic_docdesc for reference only

            t0 = time.perf_counter()
            headers = self._build_header_hierarchy(table_structure)
            t1 = time.perf_counter()

            return {
                "report_info": {
                    **report_info,
                    "metrics": {
                        "build_ms": int((t1 - t0) * 1000),
                        "query_ms": int((tq1 - tq0) * 1000)
                    }
                },
                "table_structure": {
                    **table_structure,
                    "generated_headers": headers,
                    "total_columns": len(headers.get('level_3', {}).get('columns', [])),
                    "data_source": "real_database",
                    "dynamic_docdesc": dyn
                }
            }

        except Exception as e:
            print(f"Error generating dynamic headers: {e}")
            return self._get_error_response(str(e))

    def _compute_dynamic_premi_headers_db(self, month: int, year: int, gang_code: str) -> List[str]:
        """
        Optimized version with better caching and query performance.
        Uses faster query and improved caching strategy.
        """
        start = time.perf_counter()

        # Enhanced cache key with optimization strategy
        cache_key = f"dyn_hdr_opt:{gang_code}:{year}-{str(month).zfill(2)}"
        cached = Cache.instance().get(cache_key)
        if cached is not None:
            print(f"Cache hit for {cache_key}")
            return cached

        db = Database.instance()
        q = Queries()

        # Try optimized query first (without GROUP BY and SUM)
        sql_entry_opt = q.get('premi', 'dynamic_headers_by_gang_month_optimized')
        if sql_entry_opt and 'sql' in sql_entry_opt:
            start_date = f"{year}-{str(month).zfill(2)}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{str(month+1).zfill(2)}-01"

            # Execute optimized query
            rows = db.query_all(sql_entry_opt['sql'], [gang_code, start_date, end_date])
            mid = time.perf_counter()

            # Pre-defined excluded items for better performance
            # Note: Important deduction columns are NOW INCLUDED - not excluded
            excluded_lower = {
                # Remove these from exclusion as they should now be visible:
                # 'koreksi', 'potongan pph21', 'potongan spsi', 'pph21', 'spsi'
                'tunjangan jabatan',
                'tunjangan masa kerja', 'pruning', 'brondol', 'pph 21', # Keep 'pph 21' but not 'pph21'
                'koreksi panen', 'potongan koreksi', 'potongan koreksi panen',
                'tunjangan premi', 'tunjangan beras'
            }

            # Optimized filtering with list comprehension
            headers = [
                str(r[0]).strip()
                for r in rows
                if r and r[0] and str(r[0]).strip().lower() not in excluded_lower
            ]

            # Remove duplicates while preserving order
            seen = set()
            unique_headers = []
            for h in headers:
                if h not in seen:
                    seen.add(h)
                    unique_headers.append(h)

            # Limit to 7 items for consistency
            result = unique_headers[:7]

            # Extended cache TTL for better performance (1 hour)
            Cache.instance().set(cache_key, result, ttl=3600)

            query_time = (mid - start) * 1000
            total_time = (time.perf_counter() - start) * 1000
            print(f"Optimized query time: {query_time:.2f}ms, Total time: {total_time:.2f}ms")

            return result

        # Fallback to original query if optimized query not available
        return self._compute_dynamic_premi_headers_db_fallback(month, year, gang_code)

    def _compute_dynamic_premi_headers_db_fallback(self, month: int, year: int, gang_code: str) -> List[str]:
        """Fallback method using original query for compatibility"""
        start = time.perf_counter()
        cache_key = f"dyn_hdr_fallback:{gang_code}:{year}-{str(month).zfill(2)}"
        cached = Cache.instance().get(cache_key)
        if cached is not None:
            return cached

        db = Database.instance()
        q = Queries()
        sql_entry = q.get('premi', 'dynamic_headers_by_gang_month')
        if not sql_entry or 'sql' not in sql_entry:
            return []

        start_date = f"{year}-{str(month).zfill(2)}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{str(month+1).zfill(2)}-01"

        rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])
        mid = time.perf_counter()

        excluded = {
            # Remove important deduction columns from exclusion:
            # 'KOREKSI',
            # 'POTONGAN PPH21',
            # 'POTONGAN SPSI',
            # 'PPH21',
            # 'SPSI',
            'TUNJANGAN JABATAN',
            'TUNJANGAN MASA KERJA',
            'PRUNING',
            'BRONDOL',
            'PPH 21',  # Keep 'PPH 21' but not 'PPH21'
            'KOREKSI PANEN',
            'POTONGAN KOREKSI',
            'POTONGAN KOREKSI PANEN',
            'TUNJANGAN PREMI',
            'TUNJANGAN BERAS',
            'INCENTIVE PANEN',
            'INCENTIVE'
        }

        headers = []
        for r in rows:
            if not r:
                continue
            h = str(r[0]).strip()
            if h and h.upper() not in excluded:
                headers.append(h)

        seen = set()
        unique = []
        for h in headers:
            if h not in seen:
                seen.add(h)
                unique.append(h)

        Cache.instance().set(cache_key, unique[:7], ttl=1800)  # 30 minutes for fallback
        return unique[:7]

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
            "no": "no",
            "gender": "jenis_kelamin",
            "nik": "nik",
            "name": "nama",
            "upah_dasar": "upah_dasar",
            "hari_kerja": "hari_kerja",
            "upah_pokok": "upah_pokok",
            "jml_hk": "jumlah_hk",
            "gaji_pokok": "gaji_pokok",

            # Cuti columns
            "cuti_tahunan_unit": "cuti_tahunan_hari",
            "cuti_sakit_haid_unit": "cuti_sakit_haid_hari",
            "cuti_minggu_unit": "cuti_minggu_hari",
            "cuti_nasional_unit": "cuti_nasional_hari",
            "cuti_izin_unit": "cuti_izin_hari",

            # Tunjangan columns
            "beras_rate": "beras_rate",
            "beras_jumlah": "beras_jumlah",
            "jabatan_rate": "jabatan_rate",
            "jabatan_jumlah": "jabatan_jumlah",
            "masa_kerja_lama": "masa_kerja_tahun",
            "masa_kerja_jumlah": "masa_kerja_jumlah",
            "lembur_jam": "lembur_jam",
            "lembur_jumlah": "lembur_jumlah",

            # Premi columns
            "brondol_jumlah": "premi_brondol",
            "pruning_jumlah": "premi_pruning",
            "premi_angkut_material_jumlah": "premi_angkut_material",
            "premi_angkut_tbs_jumlah": "premi_angkut_tbs",
            "premi_harvesting_jumlah": "premi_harvesting",
            "premi_harvesting_incentive_jumlah": "premi_harvesting_incentive",
            "premi_pupuk_jumlah": "premi_pupuk",

            # Koreksi column (treated as Premi but actually deduction)
            "premi_koreksi": "premi_koreksi",
            "koreksi": "premi_koreksi",

            # Potongan columns
            "pph21": "pot_pph21",
            "potongan_kontan": "pot_kontan",
            "thr": "pot_thr",
            "pinjam": "pot_pinjam",
            "kl": "pot_kl",
            "bpjs_kes": "pot_bpjs_kes",
            "bpjs_pek": "pot_bpjs_pek",
            "bpjs_maj": "pot_bpjs_maj",
            "total1": "pot_total_1",
            "total2": "pot_total_2",
            "total3": "pot_total_3",
            "total4": "pot_total_4",

            # Additional potongan columns from reference code
            "pot_bpjs_kesehatan_pekerja": "pot_bpjs_kesehatan_pekerja",
            "pot_bpjs_kesehatan_majikan": "pot_bpjs_kesehatan_majikan",
            "pot_bpjs_pensiun_pekerja": "pot_bpjs_pensiun_pekerja",
            "pot_bpjs_pensiun_majikan": "pot_bpjs_pensiun_majikan",
            "pot_bpjs_jumlah": "pot_bpjs_jumlah",
            "pot_bpjs_pekerja_total": "pot_bpjs_pekerja_total",
            "pot_spsi": "pot_spsi",
            "spsi": "pot_spsi",  # Alternative mapping

            # Final columns
            "total_tunjangan": "total_tunjangan",
            "upah_bersih": "upah_bersih",
            "cth": "tidak_hadir_cth",
            "alpa": "tidak_hadir_alpa"
        }

        return field_mapping.get(column_id, column_id)

    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response structure"""
        return {
            "report_info": {
                "title": "ERROR - Header Generation Failed",
                "generated_date": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                "gang": "ERROR",
                "database": "ERROR",
                "description": f"Error: {error_message}"
            },
            "table_structure": {
                "total_columns": 0,
                "header_rows": 1,
                "data_rows": "error",
                "generated_headers": {
                    "level_1": {"row": 1, "columns": []},
                    "level_2": {"row": 2, "columns": []},
                    "level_3": {"row": 3, "columns": []}
                },
                "error": error_message,
                "data_source": "error"
            }
        }

    def get_column_definitions(self, month: int = None, year: int = None, gang_code: str = None) -> List[Dict[str, Any]]:
        try:
            headers = self.generate_dynamic_headers(month=month, year=year, gang_code=gang_code)
            hierarchy = headers.get('table_structure', {}).get('hierarchy', {})
            l1 = hierarchy.get('level_1', {}).get('columns', [])
            l2 = hierarchy.get('level_2', {}).get('columns', [])
            l3 = hierarchy.get('level_3', {}).get('columns', [])

            l2_by_parent = {}
            for c in l2:
                p = c.get('parent')
                l2_by_parent.setdefault(p, []).append(c)
            l3_by_parent = {}
            for c in l3:
                p = c.get('parent')
                l3_by_parent.setdefault(p, []).append(c)

            static_map = {
                'no': 'no',
                'gender': 'jenis_kelamin',
                'nik': 'nik',
                'name': 'nama',
                'upah_dasar': 'upah_dasar',
                'hari_kerja': 'hari_kerja',
                'upah_pokok': 'upah_pokok',
                'jml_hk': 'jumlah_hk',
                'gaji_pokok': 'gaji_pokok',
                'total_tunjangan': 'total_tunjangan',
                'upah_bersih': 'upah_bersih',
                # Added new fields to ensure they're recognized by the column definitions
                'premi_koreksi': 'premi_koreksi',
                'bpjs_pensiun_pekerja': 'pot_bpjs_pensiun_pekerja',
                'bpjs_pensiun_majikan': 'pot_bpjs_pensiun_majikan'
            }

            col_defs = []

            for c1 in l1:
                c1_id = c1.get('id')
                children_ids = c1.get('children', [])
                if not children_ids:
                    field = static_map.get(c1_id)
                    if field:
                        col_defs.append({
                            'field': field,
                            'headerName': c1.get('text'),
                            'width': self._get_column_width(field),
                            'type': self._get_column_type(field),
                            'cellStyle': self._get_cell_style(field),
                            'pinned': 'left' if field in ['no','nama'] else None
                        })
                    continue

                level2_cols = l2_by_parent.get(c1_id, [])
                group2_defs = []
                for c2 in level2_cols:
                    t2 = (c2.get('text') or '').strip().upper()
                    c1_text_upper = (c1.get('text') or '').strip().upper()
                    if 'PREMI' in c1_text_upper and t2 in {'TOTAL PREMI', 'UPAH KOTOR'}:
                        continue
                    c2_id = c2.get('id')
                    level3_cols = l3_by_parent.get(c2_id, [])
                    leaf_defs = []
                    for c3 in level3_cols:
                        field = self._map_to_data_field(c3.get('id'))
                        leaf_defs.append({
                            'field': field,
                            'headerName': c3.get('text'),
                            'width': self._get_column_width(field),
                            'type': self._get_column_type(field),
                            'cellStyle': self._get_cell_style(field)
                        })
                    group2_defs.append({ 'headerName': c2.get('text'), 'children': leaf_defs })
                col_defs.append({ 'headerName': c1.get('text'), 'children': group2_defs })

            # Insert summary columns after top-level 'PREMI' (only once)
            found_premi = False
            for idx, c in enumerate(col_defs):
                c_name = (c.get('headerName') or '').strip().upper()
                if c_name == 'PREMI' and not found_premi:
                    # Insert Total Premi and Upah Kotor as level 1 columns after PREMI
                    col_defs[idx+1:idx+1] = [
                        {
                            'field': 'total_premi',
                            'headerName': 'Total Premi',
                            'width': self._get_column_width('total_premi'),
                            'type': self._get_column_type('total_premi'),
                            'cellStyle': self._get_cell_style('total_premi')
                        },
                        {
                            'field': 'jumlah_upah_kotor',
                            'headerName': 'Upah Kotor',
                            'width': self._get_column_width('jumlah_upah_kotor'),
                            'type': self._get_column_type('jumlah_upah_kotor'),
                            'cellStyle': self._get_cell_style('jumlah_upah_kotor')
                        }
                    ]
                    found_premi = True
                    break

            # Insert structured deduction groups after 'Upah Kotor' column based on HTML template
            upah_kotor_idx = None
            for idx, c in enumerate(col_defs):
                if c.get('field') == 'jumlah_upah_kotor':
                    upah_kotor_idx = idx
                    break

            if upah_kotor_idx is not None:
                # Create structured deduction groups matching HTML template hierarchy
                deduction_groups = [
                    {
                        'headerName': 'CARUMAN ASTEK',
                        'children': [
                            {
                                'headerName': 'PEKERJA',
                                'field': 'pot_bpjs_pek',
                                'width': 80,
                                'type': 'numericColumn',
                                'cellStyle': {'textAlign': 'right', 'backgroundColor': '#e8f5e8', 'color': '#2e7d32'}
                            },
                            {
                                'headerName': 'MAJIKAN',
                                'field': 'pot_bpjs_maj',
                                'width': 80,
                                'type': 'numericColumn',
                                'cellStyle': {'textAlign': 'right', 'backgroundColor': '#e8f5e8', 'color': '#2e7d32'}
                            },
                            {
                                'headerName': 'JUMLAH',
                                'field': 'pot_bpjs_jumlah',
                                'width': 80,
                                'type': 'numericColumn',
                                'cellStyle': {'textAlign': 'right', 'backgroundColor': '#e8f5e8', 'color': '#2e7d32'}
                            }
                        ]
                    },
                    {
                        'headerName': 'POTONGAN BPJS',
                        'children': [
                            {
                                'headerName': 'KESEHATAN',
                                'children': [
                                    {
                                        'headerName': 'PEKERJA',
                                        'field': 'pot_bpjs_kesehatan_pekerja',
                                        'width': 90,
                                        'type': 'numericColumn',
                                        'cellStyle': {'textAlign': 'right', 'backgroundColor': '#fff3e0', 'color': '#e65100'}
                                    },
                                    {
                                        'headerName': 'MAJIKAN',
                                        'field': 'pot_bpjs_kesehatan_majikan',
                                        'width': 90,
                                        'type': 'numericColumn',
                                        'cellStyle': {'textAlign': 'right', 'backgroundColor': '#fff3e0', 'color': '#e65100'}
                                    }
                                ]
                            },
                            {
                                'headerName': 'PENSIUN',
                                'children': [
                                    {
                                        'headerName': 'PEKERJA',
                                        'field': 'pot_bpjs_pensiun_pekerja',
                                        'width': 90,
                                        'type': 'numericColumn',
                                        'cellStyle': {'textAlign': 'right', 'backgroundColor': '#fff3e0', 'color': '#e65100'}
                                    },
                                    {
                                        'headerName': 'MAJIKAN',
                                        'field': 'pot_bpjs_pensiun_majikan',
                                        'width': 90,
                                        'type': 'numericColumn',
                                        'cellStyle': {'textAlign': 'right', 'backgroundColor': '#fff3e0', 'color': '#e65100'}
                                    }
                                ]
                            },
                            {
                                'headerName': 'JUMLAH',
                                'field': 'pot_bpjs_pekerja_total',
                                'width': 100,
                                'type': 'numericColumn',
                                'cellStyle': {'textAlign': 'right', 'backgroundColor': '#fff3e0', 'color': '#e65100'}
                            }
                        ]
                    },
                    {
                        'headerName': 'IURAN SPSI',
                        'children': [
                            {
                                'headerName': 'JUMLAH',
                                'field': 'pot_spsi',
                                'width': 100,
                                'type': 'numericColumn',
                                'cellStyle': {'textAlign': 'right', 'backgroundColor': '#fff3e0', 'color': '#e65100'}
                            }
                        ]
                    },
                    {
                        'headerName': 'PPH21',
                        'children': [
                            {
                                'headerName': 'JUMLAH',
                                'field': 'pot_pph21',
                                'width': 100,
                                'type': 'numericColumn',
                                'cellStyle': {'textAlign': 'right', 'backgroundColor': '#fff3e0', 'color': '#e65100'}
                            }
                        ]
                    },
                    {
                        'field': 'total_potongan',
                        'headerName': 'TOTAL POTONGAN',
                        'width': 120,
                        'type': 'numericColumn',
                        'cellStyle': {'textAlign': 'right', 'backgroundColor': '#e1f5fe', 'color': '#0277bd', 'fontWeight': 'bold'}
                    },
                    {
                        'field': 'upah_bersih',
                        'headerName': 'UPAH BERSIH',
                        'width': 120,
                        'type': 'numericColumn',
                        'cellStyle': {'textAlign': 'right', 'backgroundColor': '#ffe082', 'color': '#bf360c', 'fontWeight': 'bold', 'fontSize': '14px'}
                    }
                ]
                col_defs[upah_kotor_idx + 1:upah_kotor_idx + 1] = deduction_groups

            # Reorder so 'no' and 'nama' are the first two columns
            lead = []
            rest = []
            for c in col_defs:
                f = c.get('field')
                if f in ['no', 'nama']:
                    lead.append(c)
                else:
                    rest.append(c)
            # Ensure order: no, then nama
            lead_sorted = []
            no_col = next((c for c in lead if c.get('field') == 'no'), None)
            nama_col = next((c for c in lead if c.get('field') == 'nama'), None)
            if no_col:
                lead_sorted.append(no_col)
            if nama_col:
                lead_sorted.append(nama_col)
            return lead_sorted + rest

        except Exception as e:
            print(f"ERROR: Failed to generate column definitions: {e}")
            raise Exception(f"Column definition generation failed: {e}")

    def _get_column_width(self, field: str) -> int:
        """Get appropriate width for column"""
        width_mapping = {
            "upah_dasar": 120, "hari_kerja": 100, "upah_pokok": 120, "jumlah_hk": 80,
            "gaji_pokok": 120, "total_tunjangan": 120, "upah_bersih": 120,
            "beras_rate": 100, "beras_jumlah": 100, "jabatan_rate": 100, "jabatan_jumlah": 100,
            "masa_kerja_tahun": 100, "masa_kerja_jumlah": 120, "lembur_jam": 80, "lembur_jumlah": 120,
            # New columns for deduction components
            "premi_koreksi": 120, "pot_bpjs_pensiun_pekerja": 150, "pot_bpjs_pensiun_majikan": 150,
            "pot_bpjs_kesehatan_pekerja": 150, "pot_bpjs_kesehatan_majikan": 150,
            "pot_bpjs_jumlah": 120, "pot_bpjs_pekerja_total": 140, "pot_spsi": 100
        }
        return width_mapping.get(field, 100)

    def _get_column_type(self, field: str) -> str:
        """Get column type for formatting"""
        if field in ['upah_dasar', 'upah_pokok', 'gaji_pokok', 'total_tunjangan', 'upah_bersih', 'total_premi', 'jumlah_upah_kotor']:
            return 'numericColumn'
        elif any(x in field for x in ['rate', 'jumlah', 'pot_', 'premi_', 'premi']):
            return 'numericColumn'
        else:
            return 'textColumn'

    def _get_cell_style(self, field: str) -> Dict[str, Any]:
        """Get cell style based on field type"""
        if self._get_column_type(field) == 'numericColumn':
            return {"textAlign": "right"}
        return {"textAlign": "left"}

    def _get_fallback_column_defs(self) -> List[Dict[str, Any]]:
        """Fallback column definitions if error occurs"""
        return [
            {"field": "no", "headerName": "NO", "width": 60},
            {"field": "nama", "headerName": "NAMA", "width": 200},
            {"field": "upah_bersih", "headerName": "UPAH BERSIH", "width": 120, "type": "numericColumn"}
        ]
