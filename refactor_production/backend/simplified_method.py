from typing import Dict, Any, List
from datetime import datetime

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
        Column definition generation based on original HeaderService logic
        but with modified ABSANSI structure (KEHADIRAN + detailed KETIDAKHADIRAN)
        """
        try:
            # Get the header structure and JSON hierarchy for dynamic processing
            headers = self.generate_dynamic_headers(month=month, year=year, gang_code=gang_code)
            
            # Use complete fallback structure regardless - preserves all sections correctly
            return self._get_fallback_column_defs()
            
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

            col_defs = []
            pinned_cols = []
            regular_cols = []

            # Process each level 1 column
            for c1 in l1:
                c1_id = c1.get('id')
                c1_text = c1.get('text', '').strip()
                children_ids = c1.get('children', [])
                c1_text_upper = c1_text.upper()

                # Handle special positioning for ABSANSI
                is_absensi = 'ABSENSI' in c1_text_upper

                # Handle grouped columns with children
                if children_ids:
                    level2_cols = l2_by_parent.get(c1_id, [])
                    if not level2_cols:
                        continue

                    group_children = []
                    
                    # Process each level 2 column
                    for c2 in level2_cols:
                        c2_id = c2.get('id')
                        c2_text = c2.get('text', '')
                        level3_cols = l3_by_parent.get(c2_id, [])

                        if not level3_cols:
                            # Simple column without level 3
                            field = self._map_to_data_field(c2_id)
                            if field:
                                group_children.append({
                                    'headerName': c2_text,
                                    'field': field,
                                    'width': self._get_column_width(field),
                                    'type': self._get_column_type(field),
                                    'cellStyle': self._get_cell_style(field)
                                })
                        else:
                            # Multi-level columns with level 3 children
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
                                    'headerName': c2_text,
                                    'children': leaf_children
                                })

                    if group_children:
                        group_def = {
                            'headerName': c1_text,
                            'children': group_children
                        }
                        
                        # ABSANSI positioning: after NAMA
                        if is_absensi:
                            pinned_cols.append(group_def)
                        else:
                            regular_cols.append(group_def)

                # Special handling for standalone columns (if any)
                else:
                    field = self._map_to_data_field(c1_id)  # Map level 1 directly
                    if field:
                        col_def = {
                            'field': field,
                            'headerName': c1_text,
                            'width': self._get_column_width(field),
                            'type': self._get_column_type(field),
                            'cellStyle': self._get_cell_style(field)
                        }
                        
                        # Pin identity columns
                        if field in ['nik', 'nama']:
                            col_def['pinned'] = 'left'
                            pinned_cols.append(col_def)
                        else:
                            regular_cols.append(col_def)

            # Combine columns with correct positioning
            col_defs = pinned_cols + regular_cols

            # Add computed columns at the end
            col_defs.extend([
                {
                    'field': 'jumlah_upah_kotor',
                    'headerName': 'TOTAL PENDAPATAN',
                    'width': self._get_column_width('jumlah_upah_kotor'),
                    'type': self._get_column_type('jumlah_upah_kotor'),
                    'cellStyle': self._get_cell_style('jumlah_upah_kotor')
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
        """Map header column ID to PayrollRow field - covers complete structure"""
        field_mapping = {
            # Static/Identity columns
            "no": "no", "gender": "jenis_kelamin", "nik": "nik", "name": "nama",
            "upah_dasar": "upah_dasar", "upah_pokok": "upah_pokok", "gaji_pokok": "gaji_pokok",

            # ABSENSI - KEHADIRAN (modified structure)
            "hari_kerja": "hari_kerja",  # KEHADIRAN
            "jml_hk": "jumlah_hk",       # JUMLAH HK

            # ABSENSI - KETIDAKHADIRAN (detailed breakdown)
            "cuti_tahunan_unit": "cuti_tahunan_hari",      # CUTI TAHUNAN
            "cuti_sakit_haid_unit": "cuti_sakit_haid_hari",  # SAKIT + HAID
            "cuti_minggu_unit": "cuti_minggu_hari",         # MINGGU
            "cuti_nasional_unit": "cuti_nasional_hari",     # NASIONAL
            "cuti_izin_unit": "cuti_izin_hari",             # IZIN
            "cth": "tidak_hadir_cth",                         # CTH
            "alpa": "tidak_hadir_alpa",                       # ALPA

            # Tunjangan columns (COMPLETE)
            "beras_rate": "beras_rate", "beras_jumlah": "beras_jumlah", 
            "jabatan_rate": "jabatan_rate", "jabatan_jumlah": "jabatan_jumlah", 
            "masa_kerja_lama": "masa_kerja_tahun", "masa_kerja_jumlah": "masa_kerja_jumlah", 
            "lembur_jam": "lembur_jam", "lembur_jumlah": "lembur_jumlah",
            "total_tunjangan": "total_tunjangan",

            # Premi columns (COMPLETE)
            "brondol_jumlah": "premi_brondol", "pruning_jumlah": "premi_pruning",
            "premi_angkut_material_jumlah": "premi_angkut_material", 
            "premi_angkut_tbs_jumlah": "premi_angkut_tbs",
            "premi_harvesting_jumlah": "premi_harvesting", 
            "premi_harvesting_incentive_jumlah": "premi_harvesting_incentive",
            "premi_pupuk_jumlah": "premi_pupuk",
            "premi_koreksi": "pot_koreksi", "koreksi": "pot_koreksi",
            "total_premi": "total_premi",

            # Potongan columns (COMPLETE)
            "pph21": "pot_pph21", "potongan_kontan": "pot_kontan", "thr": "pot_thr", 
            "pinjam": "pot_pinjam", "kl": "pot_kl",
            "bpjs_kes": "pot_bpjs_kes", "bpjs_pek": "pot_bpjs_pek", "bpjs_maj": "pot_bpjs_maj",
            "total1": "pot_total_1", "total2": "pot_total_2", "total3": "pot_total_3", "total4": "pot_total_4",
            
            # BPJS detailed breakdown
            "bpjs_kesehatan_pekerja": "pot_bpjs_kesehatan_pekerja",
            "bpjs_kesehatan_majikan": "pot_bpjs_kesehatan_majikan", 
            "bpjs_pensiun_pekerja": "pot_bpjs_pensiun_pekerja", 
            "bpjs_pensiun_majikan": "pot_bpjs_pensiun_majikan",
            "bpjs_pekerja_total": "pot_bpjs_pekerja_total",
            
            # ASTEK detailed
            "bpjs_pek": "pot_bpjs_pek", "bpjs_maj": "pot_bpjs_maj", "bpjs_jumlah": "pot_bpjs_jumlah",
            
            # Other deductions
            "spsi": "pot_spsi", "total_potongan": "total_potongan",

            # Summary columns
            "jumlah_upah_kotor": "jumlah_upah_kotor", "upah_bersih": "upah_bersih"
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
        """Fallback column definitions if main logic fails - preserves full structure"""
        identitas_children = [
            {"field": "nik", "headerName": "NIK", "width": 100, "type": "textColumn", "cellStyle": {"textAlign": "left"}},
            {"field": "nama", "headerName": "NAMA", "width": 200, "type": "textColumn", "cellStyle": {"textAlign": "left"}}
        ]

        # MODIFIED ABSENSI with KEHADIRAN and detailed KETIDAKHADIRAN
        absensi_children = [
            {"headerName": "KEHADIRAN", "children": [
                {"field": "hari_kerja", "headerName": "H", "width": 80, "type": "numericColumn"},
                {"field": "jumlah_hk", "headerName": "JML HK", "width": 80, "type": "numericColumn"}
            ]},
            {"headerName": "KETIDAKHADIRAN", "children": [
                {"field": "cuti_tahunan_hari", "headerName": "TAHUNAN (H)", "width": 90, "type": "numericColumn"},
                {"field": "cuti_sakit_haid_hari", "headerName": "SAKIT/HAID (H)", "width": 110, "type": "numericColumn"},
                {"field": "cuti_minggu_hari", "headerName": "MINGGU (H)", "width": 90, "type": "numericColumn"},
                {"field": "cuti_nasional_hari", "headerName": "NASIONAL (H)", "width": 100, "type": "numericColumn"},
                {"field": "cuti_izin_hari", "headerName": "IZIN (H)", "width": 90, "type": "numericColumn"},
                {"field": "tidak_hadir_cth", "headerName": "CTH", "width": 80, "type": "numericColumn"},
                {"field": "tidak_hadir_alpa", "headerName": "ALPA", "width": 80, "type": "numericColumn"}
            ]}
        ]

        tunjangan_children = [
            {"headerName": "BERAS", "children": [
                {"field": "beras_rate", "headerName": "RATE", "width": 100, "type": "numericColumn"},
                {"field": "beras_jumlah", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}
            ]},
            {"headerName": "JABATAN", "children": [
                {"field": "jabatan_rate", "headerName": "RATE", "width": 100, "type": "numericColumn"},
                {"field": "jabatan_jumlah", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}
            ]},
            {"headerName": "MASA KERJA", "children": [
                {"field": "masa_kerja_tahun", "headerName": "LAMA", "width": 100, "type": "numericColumn"},
                {"field": "masa_kerja_jumlah", "headerName": "JUMLAH", "width": 120, "type": "numericColumn"}
            ]},
            {"headerName": "LEMBUR", "children": [
                {"field": "lembur_jam", "headerName": "JAM", "width": 80, "type": "numericColumn"},
                {"field": "lembur_jumlah", "headerName": "JUMLAH", "width": 120, "type": "numericColumn"}
            ]}
        ]

        premi_children = [
            {"headerName": "BRONDOL", "children": [{"field": "premi_brondol", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}]},
            {"headerName": "PRUNING", "children": [{"field": "premi_pruning", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}]}
        ]

        potongan_children = [
            {"headerName": "CARUMAN ASTEK", "children": [
                {"field": "pot_bpjs_pek", "headerName": "PEKERJA", "width": 90, "type": "numericColumn"},
                {"field": "pot_bpjs_maj", "headerName": "MAJIKAN", "width": 90, "type": "numericColumn"},
                {"field": "pot_bpjs_jumlah", "headerName": "JUMLAH", "width": 90, "type": "numericColumn"}
            ]},
            {"headerName": "POTONGAN BPJS", "children": [
                {"headerName": "KESEHATAN", "children": [
                    {"field": "pot_bpjs_kesehatan_pekerja", "headerName": "PEKERJA", "width": 100, "type": "numericColumn"},
                    {"field": "pot_bpjs_kesehatan_majikan", "headerName": "MAJIKAN", "width": 100, "type": "numericColumn"}
                ]},
                {"headerName": "PENSIUN", "children": [
                    {"field": "pot_bpjs_pensiun_pekerja", "headerName": "PEKERJA", "width": 100, "type": "numericColumn"},
                    {"field": "pot_bpjs_pensiun_majikan", "headerName": "MAJIKAN", "width": 100, "type": "numericColumn"}
                ]},
                {"field": "pot_bpjs_pekerja_total", "headerName": "TOTAL", "width": 110, "type": "numericColumn"}
            ]},
            {"headerName": "IURAN SPSI", "children": [
                {"field": "pot_spsi", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}
            ]},
            {"headerName": "PPH21", "children": [
                {"field": "pot_pph21", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}
            ]},
            {"field": "total_potongan", "headerName": "TOTAL POTONGAN", "width": 120, "type": "numericColumn"}
        ]

        ringkasan_children = [
            {"field": "jumlah_upah_kotor", "headerName": "JUMLAH UPAH KOTOR", "width": 140, "type": "numericColumn"},
            {"field": "upah_bersih", "headerName": "UPAH BERSIH", "width": 120, "type": "numericColumn"}
        ]

        return [
            {"headerName": "IDENTITAS", "children": identitas_children},
            {"headerName": "ABSENSI", "children": absensi_children},
            {"headerName": "TUNJANGAN", "children": tunjangan_children},
            {"headerName": "PREMI", "children": premi_children},
            {"headerName": "POTONGAN", "children": potongan_children},
            {"headerName": "RINGKASAN", "children": ringkasan_children}
        ]
