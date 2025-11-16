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

            # Get table structure from loaded JSON
            table_structure = self.header_structure.get('table_structure', {})

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
            "cuti_sakit_haid_unit": "cuti_sakit_haid_hai",
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

    def get_column_definitions(self) -> List[Dict[str, Any]]:
        """
        Get column definitions for AG Grid based on header structure
        """
        try:
            level_3_columns = self.header_structure.get('table_structure', {}).get('hierarchy', {}).get('level_3', {}).get('columns', [])

            column_defs = []

            # Add static columns first
            static_columns = [
                {"field": "no", "headerName": "NO", "width": 60, "pinned": "left"},
                {"field": "jenis_kelamin", "headerName": "L/P", "width": 50, "pinned": "left"},
                {"field": "nik", "headerName": "NIK", "width": 100, "pinned": "left"},
                {"field": "nama", "headerName": "NAMA", "width": 200, "pinned": "left"}
            ]

            column_defs.extend(static_columns)

            # Add dynamic columns based on header structure
            for col in level_3_columns:
                col_id = col.get('id')
                field = self._map_to_data_field(col_id)

                if field not in ['no', 'jenis_kelamin', 'nik', 'nama']:  # Skip already added
                    header_name = col.get('text', col_id.upper())

                    col_def = {
                        "field": field,
                        "headerName": header_name,
                        "width": self._get_column_width(field),
                        "type": self._get_column_type(field),
                        "cellStyle": self._get_cell_style(field)
                    }

                    column_defs.append(col_def)

            return column_defs

        except Exception as e:
            print(f"Error generating column definitions: {e}")
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