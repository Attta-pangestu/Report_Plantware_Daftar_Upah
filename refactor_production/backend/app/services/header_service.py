from typing import Dict, Any, List
from datetime import datetime
import json
import os

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
            print(f"Warning: Could not load header structure: {e}")
            self.header_structure = self._get_fallback_structure()

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

            try:
                import sys
                from pathlib import Path
                engine_dir = Path(__file__).parent.parent.parent.parent.parent / "Engine_HTML_Templating" / "template_report" / "ui"
                sys.path.insert(0, str(engine_dir))
                from daftar_upah_engine_real_database import DaftarUpahEngineRealFixed
                engine = DaftarUpahEngineRealFixed(month=str(month or datetime.now().month).zfill(2), year=str(year or datetime.now().year))
                employees = engine.query_manager.get_employees_by_gang(gang_code or 'H1H', 200)
                merged_emps = engine.merge_employee_with_cuti_data(employees, engine.month_name, str(engine.year))
                dyn = engine.get_dynamic_premi_headers(engine.month, engine.year)
                dyn = engine.filter_dynamic_headers_by_nonzero(dyn, merged_emps, engine.month, engine.year)
            except Exception:
                dyn = []

            hierarchy = table_structure.get('hierarchy', {})
            level2 = hierarchy.get('level_2', {}).get('columns', [])
            premi_children = [c for c in level2 if c.get('parent') == 'premi']
            fixed = []
            dynamic_slots = []
            for c in premi_children:
                t = (c.get('text') or '').upper()
                if 'BRONDOL' in t or 'PRUNING' in t:
                    fixed.append(c)
                else:
                    dynamic_slots.append(c)
            for i, c in enumerate(dynamic_slots):
                if i < len(dyn):
                    c['text'] = dyn[i]

            # Generate dynamic headers based on real data
            headers = self._build_header_hierarchy(table_structure)

            return {
                "report_info": report_info,
                "table_structure": {
                    **table_structure,
                    "generated_headers": headers,
                    "total_columns": len(headers.get('level_3', {}).get('columns', [])),
                    "data_source": "real_database"
                }
            }

        except Exception as e:
            print(f"Error generating dynamic headers: {e}")
            return self._get_error_response(str(e))

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
                'upah_bersih': 'upah_bersih'
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
                            'pinned': 'left' if field in ['jenis_kelamin','nik','nama'] else None
                        })
                    continue

                level2_cols = l2_by_parent.get(c1_id, [])
                group2_defs = []
                for c2 in level2_cols:
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

            return col_defs

        except Exception as e:
            print(f"Error generating nested column definitions: {e}")
            return self._get_fallback_column_defs()

    def _get_column_width(self, field: str) -> int:
        """Get appropriate width for column"""
        width_mapping = {
            "upah_dasar": 120, "hari_kerja": 100, "upah_pokok": 120, "jumlah_hk": 80,
            "gaji_pokok": 120, "total_tunjangan": 120, "upah_bersih": 120,
            "beras_rate": 100, "beras_jumlah": 100, "jabatan_rate": 100, "jabatan_jumlah": 100,
            "masa_kerja_tahun": 100, "masa_kerja_jumlah": 120, "lembur_jam": 80, "lembur_jumlah": 120
        }
        return width_mapping.get(field, 100)

    def _get_column_type(self, field: str) -> str:
        """Get column type for formatting"""
        if field in ['upah_dasar', 'upah_pokok', 'gaji_pokok', 'total_tunjangan', 'upah_bersih']:
            return 'numericColumn'
        elif any(x in field for x in ['rate', 'jumlah', 'pot_', 'premi_']):
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
