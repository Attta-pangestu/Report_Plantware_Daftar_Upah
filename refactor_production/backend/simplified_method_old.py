  from typing import Dict, Any, List

class SimplifiedHeaderService:
    """
    Optimized header service with clean structure and minimal redundancy.
    
    NEW ABSENSI STRUCTURE:
    ┌─────────────────────────────────────────────────────────┐
    │ ABSENSI (colspan: 9)                                    │
    ├──────────┬─────────┬──────────────┬───────────┬───────┤
    │ KEHADIRAN│ JUMLAH HK│ CUTI TAHUNAN │ SAKIT+HAID│ ...  │
    │ (Hari)   │ (Jumlah) │   (H)       │   (H)     │       │
    └──────────┴─────────┴──────────────┴───────────┴───────┘
    
    KEHADIRAN = hari_kerja (moved inside absensi)
    KETIDAKHADIRAN diperinci: TAHUNAN + IZIN, SAKIT + HAID, MINGGU, NASIONAL
    """
    
    def __init__(self):
        # Import needed modules
        import os
        import json
        from datetime import datetime
        
        # Load header structure from JSON file
        current_dir = os.path.dirname(__file__)
        header_file = os.path.join(current_dir, 'struktur', 'struktur_header_report.json')
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                self.header_structure = json.load(f)
        except Exception as e:
            print(f"ERROR: Failed to load header structure: {e}")
            self.header_structure = self._get_fallback_structure()

    def generate_dynamic_headers(self, month: int = None, year: int = None, gang_code: str = None) -> Dict[str, Any]:
        """Generate dynamic headers based on real data"""
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
                "database": "ARC",
                "description": "Laporan daftar upah dengan header dinamis berdasarkan data real"
            }

            table_structure = self.header_structure.get('table_structure', {})
            hierarchy = table_structure.get('hierarchy', {})

            return {
                "report_info": report_info,
                "table_structure": {
                    **table_structure,
                    "hierarchy": hierarchy,
                    "total_columns": len(hierarchy.get('level_3', {}).get('columns', [])),
                    "data_source": "real_database"
                }
            }

        except Exception as e:
            print(f"Error generating dynamic headers: {e}")
            return self._get_error_response(str(e))

    def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Standard error response for header generation"""
        return {
            "report_info": {"title": "ERROR", "description": error_msg},
            "table_structure": {
                "header_rows": 3,
                "total_columns": 0,
                "hierarchy": {
                    "level_1": {"columns": []},
                    "level_2": {"columns": []},
                    "level_3": {"columns": []}
                },
                "error": error_msg
            }
        }

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

    def get_column_definitions(self, month: int = None, year: int = None, gang_code: str = None) -> List[Dict[str, Any]]:
        """
        Simplified and optimized column definition generation.
        Places ABSENSI immediately after NAMA column for better UX.
        """
        try:
            # Get the header structure
            headers = self.generate_dynamic_headers(month=month, year=year, gang_code=gang_code)
            hierarchy = headers.get('table_structure', {}).get('hierarchy', {})
            l1 = hierarchy.get('level_1', {}).get('columns', [])
            l2 = hierarchy.get('level_2', {}).get('columns', [])
            l3 = hierarchy.get('level_3', {}).get('columns', [])

            # Build parent-child mappings
            l2_by_parent = {}
            for c in l2:
                parent = c.get('parent')
                if parent:
                    l2_by_parent.setdefault(parent, []).append(c)

            l3_by_parent = {}
            for c in l3:
                parent = c.get('parent')
                if parent:
                    l3_by_parent.setdefault(parent, []).append(c)

            # Static field mappings for simple columns
            static_map = {
                'no': 'no',
                'gender': 'jenis_kelamin',
                'nik': 'nik',
                'name': 'nama',
                'upah_dasar': 'upah_dasar',
                'upah_pokok': 'upah_pokok',
                'gaji_pokok': 'gaji_pokok',
                'total_tunjangan': 'total_tunjangan'
            }

            col_defs = []
            pinned_cols = []
            regular_cols = []

            # Process each level 1 column and categorize
            for c1 in l1:
                c1_id = c1.get('id')
                c1_text = c1.get('text', '').strip()
                children_ids = c1.get('children', [])

                # Simple columns without children (NO, NIK, NAMA, etc.)
                if not children_ids:
                    field = static_map.get(c1_id)
                    if field:
                        col_def = {
                            'field': field,
                            'headerName': c1_text,
                            'width': self._get_column_width(field),
                            'type': self._get_column_type(field),
                            'cellStyle': self._get_cell_style(field)
                        }
                        
                        # Pin NIK and NAMA to left
                        if field in ['nik', 'nama']:
                            col_def['pinned'] = 'left'
                            pinned_cols.append(col_def)
                        else:
                            regular_cols.append(col_def)
                    continue

                # Process grouped columns
                level2_cols = l2_by_parent.get(c1_id, [])
                if not level2_cols:
                    continue

                c1_text_upper = c1_text.upper()
                group_children = []

                # Handle each level 2 column
                for c2 in level2_cols:
                    c2_id = c2.get('id')
                    level3_cols = l3_by_parent.get(c2_id, [])

                    if not level3_cols:
                        # If no level 3 columns, create a simple column
                        field = self._map_to_data_field(c2_id)
                        if field:
                            group_children.append({
                                'headerName': c2.get('text'),
                                'field': field,
                                'width': self._get_column_width(field),
                                'type': self._get_column_type(field),
                                'cellStyle': self._get_cell_style(field)
                            })
                    else:
                        # Process level 3 columns
                        leaf_children = []
                        for c3 in level3_cols:
                            field = self._map_to_data_field(c3.get('id'))
                            if field:
                                leaf_children.append({
                                    'headerName': c3.get('text'),
                                    'field': field,
                                    'width': self._get_column_width(field),
                                    'type': self._get_column_type(field),
                                    'cellStyle': self._get_cell_style(field)
                                })

                        if leaf_children:
                            group_children.append({
                                'headerName': c2.get('text'),
                                'children': leaf_children
                            })

                if group_children:
                    group_def = {
                        'headerName': c1_text,
                        'children': group_children
                    }
                    
                    # Place ABSENSI right after NAMA
                    if 'ABSENSI' in c1_text_upper:
                        pinned_cols.append(group_def)
                    else:
                        regular_cols.append(group_def)

            # Combine pinned columns first, then regular columns
            col_defs = pinned_cols + regular_cols

            # Add computed columns at the end
            col_defs.extend([
                {
                    'field': 'jumlah_upah_kotor',
                    'headerName': 'TOTAL PENDAPATAN',
                    'width': self._get_column_width('jumlah_upah_kotor'),
                    'type': self._get_column_type('jumlah_upah_kotor'),
                    'cellStyle': self._get_cell_style('jumlah_upah_kotor'),
                    'compute': {'type': 'sum', 'fields': ['gaji_pokok', 'total_tunjangan', 'total_premi']}
                },
                {
                    'field': 'upah_bersih',
                    'headerName': 'UPAH BERSIH',
                    'width': self._get_column_width('upah_bersih'),
                    'type': self._get_column_type('upah_bersih'),
                    'cellStyle': self._get_cell_style('upah_bersih')
                }
            ])

            return col_defs

        except Exception as e:
            print(f"Error in get_column_definitions: {e}")
            return self._get_fallback_column_defs()

    def _map_to_data_field(self, column_id: str) -> str:
        """Map header column ID to PayrollRow field with updated ABSANSI structure"""
        field_mapping = {
            # Static columns
            "no": "no", "gender": "jenis_kelamin", "nik": "nik", "name": "nama",
            "upah_dasar": "upah_dasar", "upah_pokok": "upah_pokok", "gaji_pokok": "gaji_pokok",

            # ABSENSI - KEHADIRAN (moved inside absensi)
            "hari_kerja": "hari_kerja",  # KEHADIRAN -> hari_kerja
            "jml_hk": "jumlah_hk",       # JUMLAH HK

            # ABSENSI - KETIDAKHADIRAN (detailed breakdown)
            "cuti_tahunan_unit": "cuti_tahunan_hari",      # CUTI TAHUNAN
            "cuti_sakit_haid_unit": "cuti_sakit_haid_hari",  # SAKIT + HAID
            "cuti_minggu_unit": "cuti_minggu_hari",         # MINGGU
            "cuti_nasional_unit": "cuti_nasional_hari",     # NASIONAL
            "cuti_izin_unit": "cuti_izin_hari",             # IZIN
            "cth": "tidak_hadir_cth",                         # CTH
            "alpa": "tidak_hadir_alpa",                       # ALPA

            # Tunjangan columns
            "beras_rate": "beras_rate", "beras_jumlah": "beras_jumlah", "jabatan_rate": "jabatan_rate",
            "jabatan_jumlah": "jabatan_jumlah", "masa_kerja_lama": "masa_kerja_tahun",
            "masa_kerja_jumlah": "masa_kerja_jumlah", "lembur_jam": "lembur_jam", "lembur_jumlah": "lembur_jumlah",

            # Premi columns
            "brondol_jumlah": "premi_brondol", "pruning_jumlah": "premi_pruning",
            "premi_angkut_material_jumlah": "premi_angkut_material", "premi_angkut_tbs_jumlah": "premi_angkut_tbs",
            "premi_harvesting_jumlah": "premi_harvesting", "premi_harvesting_incentive_jumlah": "premi_harvesting_incentive",
            "premi_pupuk_jumlah": "premi_pupuk",
            "premi_koreksi": "pot_koreksi", "koreksi": "pot_koreksi",

            # Potongan columns
            "pph21": "pot_pph21", "potongan_kontan": "pot_kontan", "thr": "pot_thr", "pinjam": "pot_pinjam",
            "kl": "pot_kl", "bpjs_kes": "pot_bpjs_kes", "bpjs_pek": "pot_bpjs_pek", "bpjs_maj": "pot_bpjs_maj",
            "total1": "pot_total_1", "total2": "pot_total_2", "total3": "pot_total_3", "total4": "pot_total_4",

            # Summary columns
            "total_tunjangan": "total_tunjangan", "upah_bersih": "upah_bersih"
        }

        return field_mapping.get(column_id, column_id)

    def _get_column_width(self, field: str) -> int:
        """Get default width for columns based on field type with ABSANSI optimization"""
        width_map = {
            # Static columns
            'no': 60, 'gender': 50, 'nik': 100, 'nama': 200,
            
            # ABSENSI - KEHADIRAN
            'hari_kerja': 80,           # KEHADIRAN
            'jumlah_hk': 80,            # JUMLAH HK
            
            # ABSENSI - KETIDAKHADIRAN 
            'cuti_tahunan_hari': 90,    # CUTI TAHUNAN (H)
            'cuti_sakit_haid_hari': 110, # SAKIT + HAID (H)
            'cuti_minggu_hari': 90,     # MINGGU (H)
            'cuti_nasional_hari': 100,  # NASIONAL (H)
            'cuti_izin_hari': 90,       # IZIN (H)
            'tidak_hadir_cth': 80,      # CTH
            'tidak_hadir_alpa': 80,     # ALPA
            
            # Tunjangan columns
            'beras_rate': 100, 'beras_jumlah': 100, 'jabatan_rate': 100, 'jabatan_jumlah': 100,
            'masa_kerja_tahun': 100, 'masa_kerja_jumlah': 120, 'lembur_jam': 80, 'lembur_jumlah': 120,
            
            # Upah columns
            'upah_dasar': 120, 'upah_pokok': 120, 'gaji_pokok': 120,
            'total_tunjangan': 120, 'jumlah_upah_kotor': 140, 'upah_bersih': 120
        }
        return width_map.get(field, 100)

    def _get_column_type(self, field: str) -> str:
        """Get column type based on field"""
        text_fields = ['no', 'gender', 'nik', 'nama']
        return 'textColumn' if field in text_fields else 'numericColumn'

    def _get_cell_style(self, field: str) -> Dict[str, Any]:
        """Get cell style based on field"""
        text_fields = ['no', 'gender', 'nik', 'nama']
        if field in text_fields:
            return {'textAlign': 'left'}
        return {'textAlign': 'right'}

    def _get_fallback_column_defs(self) -> List[Dict[str, Any]]:
        """Fallback column definitions if main logic fails"""
        return [
            {'field': 'nik', 'headerName': 'NIK', 'width': 100, 'pinned': 'left'},
            {'field': 'nama', 'headerName': 'NAMA', 'width': 200, 'pinned': 'left'},
            {'field': 'hari_kerja', 'headerName': 'HARI KERJA', 'width': 80},
            {'field': 'jumlah_hk', 'headerName': 'JML HK', 'width': 80},
            {'field': 'gaji_pokok', 'headerName': 'GAJI POKOK', 'width': 120},
            {'field': 'total_tunjangan', 'headerName': 'TOTAL TUNJANGAN', 'width': 120},
            {'field': 'upah_bersih', 'headerName': 'UPAH BERSIH', 'width': 120}
        ]