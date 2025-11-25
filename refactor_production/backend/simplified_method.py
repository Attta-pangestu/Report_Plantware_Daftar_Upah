from typing import Dict, Any, List
from datetime import datetime
import time

# Force reload for absensi and koreksi fix - UPDATED 2025-11-25 - KORE FILTER ADDED

class SimplifiedHeaderService:
    """
    Optimized header service with clean structure and minimal redundancy.
    
    NEW ABSENSI STRUCTURE (3-LEVEL):
    ┌─────────────────────────────────────────────────────────┐
    │ ABSENSI (colspan: 6)                                    │
    ├──────────┬───────────────────────────────────┬─────────┤
    │KEHADIRAN│        KETIDAKHADIRAN             │JUMLAH HK│
    │(rowspan=2)├──────────┬─────────┬─────────┬───┤(rowspan=2)│
    │          │TAHUNAN  │SAKIT+HAID│MINGGU   │NAS│         │
    │          │(Hari)   │(Hari)   │(Hari)   │(H)│         │
    └──────────┴──────────┴─────────┴─────────┴───┴─────────┘

    KEHADIRAN = hari_kerja (Level 2 + Level 3)
    KETIDAKHADIRAN = parent untuk cuti details (Level 2 + Level 3)
    JUMLAH HK = jumlah_hk (Level 2 + Level 3)
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

    def _allowed_premi_keywords(self) -> set:
        try:
            table_structure = self.header_structure.get('table_structure', {})
            hierarchy = table_structure.get('hierarchy', {})
            level2 = hierarchy.get('level_2', {}).get('columns', [])
            tokens = set()
            for c in level2:
                if (c.get('parent') or '').strip().lower() == 'premi':
                    t = (c.get('text') or '').strip().upper()
                    t = t.replace('PREMI ', '')
                    for w in t.split():
                        if w and w not in {'PREMI'}:
                            tokens.add(w)
            base = {'PANEN','CUCI','UNIT','BLOWER','TABUR','KERANI','MANDOR','HARVEST'}
            return tokens | base
        except Exception:
            return {'PANEN','CUCI','UNIT','BLOWER','TABUR','ANGKUT','TBS','HARVEST','INCENTIVE','PUPUK','KERANI','MANDOR'}

    def generate_dynamic_headers(self, month: int = None, year: int = None, gang_code: str = None) -> Dict[str, Any]:
        """Generate dynamic headers based on real data with PREMI and POTONGAN dynamics"""
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
                "description": "Laporan daftar upah dengan header dinamis lengkap (PREMI + POTONGAN)"
            }

            table_structure = self.header_structure.get('table_structure', {})
            hierarchy = table_structure.get('hierarchy', {})

            # Generate dynamic headers for both PREMI and POTONGAN
            tq0 = time.perf_counter()
            dyn_premi = self._compute_dynamic_premi_headers_db(month or datetime.now().month, year or datetime.now().year, gang_code or 'H1H')
            dyn_potongan = self._compute_dynamic_potongan_headers_db(month or datetime.now().month, year or datetime.now().year, gang_code or 'H1H')
            dyn_potongan_pattern = self._compute_dynamic_potongan_pattern_headers_db(month or datetime.now().month, year or datetime.now().year, gang_code or 'H1H')
            tq1 = time.perf_counter()

            return {
                "report_info": {
                    **report_info,
                    "metrics": {
                        "query_premi_ms": int((tq1 - tq0) * 1000),
                        "query_potongan_ms": int((time.perf_counter() - tq1) * 1000),
                        "total_query_ms": int((time.perf_counter() - tq0) * 1000)
                    }
                },
                "table_structure": {
                    **table_structure,
                    "hierarchy": hierarchy,
                    "total_columns": len(hierarchy.get('level_3', {}).get('columns', [])),
                    "data_source": "real_database",
                    "dynamic_docdesc": {
                        "premi": dyn_premi,
                        "potongan": dyn_potongan,
                        "potongan_pattern": dyn_potongan_pattern
                    }
                }
            }

        except Exception as e:
            print(f"Error generating dynamic headers: {e}")
            return self._get_error_response(str(e))

    def _compute_dynamic_premi_headers_db(self, month: int, year: int, gang_code: str) -> List[str]:
        """Compute dynamic PREMI headers based on database transactions with optimized filtering"""
        try:
            from database.services.database import Database
            from database.services.queries import Queries

            # NO CACHE - Always query fresh data
            print(f"[CACHE DISABLED] Querying fresh PREMI data for {gang_code}, {month}/{year}")

            db = Database.instance()
            q = Queries()

            # Use new filtered query for PREMI (exclude POT%, PPH21, SPSI, BERAS, JABATAN, MASA)
            sql_entry = q.get('premi', 'dynamic_premi_headers_filtered')
            if sql_entry and 'sql' in sql_entry:
                start_date = f"{year}-{str(month).zfill(2)}-01"
                if month == 12:
                    end_date = f"{year+1}-01-01"
                else:
                    end_date = f"{year}-{str(month+1).zfill(2)}-01"

                rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])

                if rows is not None:
                    headers = []
                    for r in rows:
                        if not r or not r[0]:
                            continue
                        h = str(r[0]).strip()
                        if h:  # Only add non-empty headers
                            headers.append(h)

                    seen = set()
                    unique_headers = []
                    for h in headers:
                        if h not in seen:
                            unique_headers.append(h)
                            seen.add(h)
                    result = unique_headers[:7]  # Limit to first 7 items

                    print(f"PREMI: Found {len(unique_headers)} headers, returning {len(result)}")
                    return result

            # Fallback
            return []

        except Exception as e:
            print(f"Error computing PREMI headers: {e}")
            return []

    def _compute_dynamic_potongan_headers_db(self, month: int, year: int, gang_code: str) -> List[str]:
        """Compute dynamic POTONGAN headers based on database transactions (negative amounts)"""
        try:
            from database.services.database import Database
            from database.services.queries import Queries
            
            # NO CACHE - Always query fresh data
            print(f"[CACHE DISABLED] Querying fresh POTONGAN data for {gang_code}, {month}/{year}")

            db = Database.instance()
            q = Queries()
            
            # Use filtered potongan query (POT% only, exclude PPH21/koreksi/spsi)
            sql_entry = q.get('potongan', 'dynamic_potongan_headers_filtered')
            if sql_entry and 'sql' in sql_entry:
                start_date = f"{year}-{str(month).zfill(2)}-01"
                if month == 12:
                    end_date = f"{year+1}-01-01"
                else:
                    end_date = f"{year}-{str(month+1).zfill(2)}-01"

                rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])
                
                # Handle case where db.query_all returns None
                if rows is not None:
                    # Get all items from database
                    all_headers = [
                        str(r[0]).strip()
                        for r in rows
                        if r and r[0]
                    ]

                    # Apply exclude filtering for PREMI - exclude items already in TUNJANGAN section and basic deductions
                    excluded_keywords = ['BERAS', 'PPH', 'SPSI', 'TUNJANGAN JABATAN', 'TUNJANGAN MASA KERJA']
                    filtered_headers = []
                    
                    for header in all_headers:
                        header_upper = header.upper()
                        
                        # More precise exclude logic
                        should_exclude = False
                        
                        # Include items starting with 'POTONGAN' (we want these!)
                        if header_upper.startswith('POTONGAN'):
                            should_exclude = False  # Keep these items
                            print(f"    PRODUCTION FILTER: {header} -> INCLUDED (starts with POTONGAN)")
                        
                        # Exclude items containing specific keywords
                        for keyword in excluded_keywords:
                            if keyword in header_upper:
                                should_exclude = True
                                print(f"    PRODUCTION FILTER: {header} -> EXCLUDED (contains {keyword})")
                                break
                        
                        if not should_exclude:
                            filtered_headers.append(header)
                            print(f"    PRODUCTION FILTER: {header} -> INCLUDED")

                    # Remove duplicates and limit to 7 items (premium usually fewer)
                    seen = set()
                    unique_headers = []
                    for h in filtered_headers:
                        if h not in seen:
                            unique_headers.append(h)
                            seen.add(h)
                    result = unique_headers[:7]

                    return result

            # Fallback
            return []
            
        except Exception as e:
            print(f"Error computing POTONGAN headers: {e}")
            return []

    def _compute_dynamic_potongan_pattern_headers_db(self, month: int, year: int, gang_code: str) -> List[str]:
        """Compute dynamic POTONGAN headers based on 'Pot/potongan' pattern detection"""
        try:
            from database.services.database import Database
            from database.services.queries import Queries

            # NO CACHE - Always query fresh data
            print(f"[CACHE DISABLED] Querying fresh POTONGAN PATTERN data for {gang_code}, {month}/{year}")

            db = Database.instance()
            q = Queries()

            # Use potongan pattern query
            sql_entry = q.get('potongan', 'potongan_pattern_headers')
            if sql_entry and 'sql' in sql_entry:
                start_date = f"{year}-{str(month).zfill(2)}-01"
                if month == 12:
                    end_date = f"{year+1}-01-01"
                else:
                    end_date = f"{year}-{str(month+1).zfill(2)}-01"

                rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])

                # Handle case where db.query_all returns None
                if rows is not None:
                    # Get all potongan pattern items from database
                    pattern_headers = [
                        str(r[0]).strip()
                        for r in rows
                        if r and r[0]
                    ]

                    # Additional filtering to ensure quality
                    excluded_keywords = ['ASTEK', 'BPJS', 'PPH', 'SPSI']
                    filtered_headers = []

                    for header in pattern_headers:
                        header_upper = header.upper()

                        # Exclude items containing specific keywords
                        should_exclude = False
                        for keyword in excluded_keywords:
                            if keyword in header_upper:
                                should_exclude = True
                                print(f"    POTONGAN PATTERN FILTER: {header} -> EXCLUDED (contains {keyword})")
                                break

                        if not should_exclude:
                            filtered_headers.append(header)
                            print(f"    POTONGAN PATTERN FILTER: {header} -> INCLUDED")

                    # Remove duplicates and limit to reasonable number
                    seen = set()
                    unique_headers = []
                    for h in filtered_headers:
                        if h not in seen:
                            unique_headers.append(h)
                            seen.add(h)
                    result = unique_headers[:10]  # Allow more for potongan patterns

                    return result

            # Fallback
            return []

        except Exception as e:
            print(f"Error computing POTONGAN pattern headers: {e}")
            return []

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
        Column definition generation with dynamic PREMI and POTONGAN support
        """
        try:
            # Get the header structure and JSON hierarchy for dynamic processing
            headers = self.generate_dynamic_headers(month=month, year=year, gang_code=gang_code)

            # Get dynamic headers for PREMI and POTONGAN
            dynamic_docdesc = headers.get('table_structure', {}).get('dynamic_docdesc', {})
            dyn_premi = dynamic_docdesc.get('premi', [])
            dyn_potongan = dynamic_docdesc.get('potongan', [])
            dyn_potongan_pattern = dynamic_docdesc.get('potongan_pattern', [])

            # Generate fallback columns with dynamic PREMI and POTONGAN
            return self._get_dynamic_column_defs(dyn_premi, dyn_potongan, dyn_potongan_pattern)

        except Exception as e:
            print(f"Error in get_column_definitions: {e}")
            return self._get_fallback_column_defs()

    def _get_dynamic_column_defs(self, dyn_premi: List[str] = None, dyn_potongan: List[str] = None, dyn_potongan_pattern: List[str] = None) -> List[Dict[str, Any]]:
        """Generate column definitions with dynamic PREMI and POTONGAN"""
        dyn_premi = dyn_premi or []
        dyn_potongan = dyn_potongan or []
        dyn_potongan_pattern = dyn_potongan_pattern or []

        identitas_children = [
            {"field": "no", "headerName": "NO", "width": 60, "type": "numericColumn", "cellStyle": {"textAlign": "center"}},
            {"field": "jenis_kelamin", "headerName": "L/P", "width": 50, "type": "textColumn", "cellStyle": {"textAlign": "center"}},
            {"field": "nama", "headerName": "NAMA", "width": 200, "type": "textColumn", "cellStyle": {"textAlign": "left"}},
            {"field": "nik", "headerName": "NIK", "width": 100, "type": "textColumn", "cellStyle": {"textAlign": "left"}}
        ]

        # UPDATED ABSENSI with 3-level structure
        absensi_children = [
            {"headerName": "KEHADIRAN", "children": [
                {"field": "hari_kerja", "headerName": "Hari", "width": 80, "type": "numericColumn"}
            ]},
            {"headerName": "KETIDAKHADIRAN", "children": [
                {"field": "cuti_tahunan_hari", "headerName": "CUTI TAHUNAN", "width": 90, "type": "numericColumn"},
                {"field": "cuti_sakit_haid_hari", "headerName": "SAKIT + HAID", "width": 110, "type": "numericColumn"},
                {"field": "cuti_minggu_hari", "headerName": "MINGGU", "width": 90, "type": "numericColumn"},
                {"field": "cuti_nasional_hari", "headerName": "NASIONAL", "width": 100, "type": "numericColumn"}
            ]},
            {"headerName": "JUMLAH HK", "children": [
                {"field": "jumlah_hk", "headerName": "Jumlah", "width": 80, "type": "numericColumn"}
            ]}
        ]

        upah_dasar_children = [
            {"field": "upah_dasar", "headerName": "UPAH DASAR", "width": 120, "type": "numericColumn"},
            {"field": "upah_pokok", "headerName": "UPAH POKOK", "width": 120, "type": "numericColumn"},
            {"field": "gaji_pokok", "headerName": "GAJI POKOK", "width": 120, "type": "numericColumn"}
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
            ]},
            {"field": "total_tunjangan", "headerName": "TOTAL TUNJANGAN", "width": 120, "type": "numericColumn"}
        ]

        # Dynamic PREMI columns - ALWAYS include static BRONDOL first
        static_premi_columns = [
            {"headerName": "BRONDOL", "children": [{"field": "premi_brondol", "headerName": "JUMLAH", "width": 120, "type": "numericColumn"}]},
            {"headerName": "PRUNING", "children": [{"field": "premi_pruning", "headerName": "JUMLAH", "width": 120, "type": "numericColumn"}]}
        ]
        
        premi_children = static_premi_columns.copy()

        # Dynamic PREMI columns from database after filtering (exclude-only)
        # Use fields 'premi_1'..'premi_7' to match backend row model
        if dyn_premi:
            existing_headers = {col["headerName"].upper() for col in static_premi_columns}
            existing_fields = {col["children"][0]["field"] for col in static_premi_columns}
            dyn_index = 1
            for premi_name in dyn_premi:
                name_upper = (premi_name or "").strip().upper()
                if not name_upper:
                    continue
                if name_upper in existing_headers:
                    continue
                # Exclude KORE-related entries to avoid conflict with static KOREKSI column
                if 'KORE' in name_upper:
                    continue
                field_name = f"premi_{dyn_index}"
                dyn_index += 1
                original_field = field_name
                counter = 1
                while field_name in existing_fields:
                    field_name = f"{original_field}_{counter}"
                    counter += 1
                existing_fields.add(field_name)
                premi_children.append({
                    "headerName": name_upper,
                    "children": [
                        {"field": field_name, "headerName": "JUMLAH", "width": 120, "type": "numericColumn"}
                    ]
                })

        # Add TOTAL PREMI column if there are any premium columns
        if premi_children:
            premi_children.append({
                "headerName": "TOTAL PREMI",
                "children": [
                    {"field": "total_premi", "headerName": "JUMLAH", "width": 120, "type": "numericColumn", "cellStyle": {"backgroundColor": "#f0f8ff", "fontWeight": "bold"}}
                ]
            })

        # Dynamic POTONGAN columns - REMOVED to avoid duplication
        # Dynamic POTONGAN items are now only shown in POTONGAN LAINNYA section
        potongan_children = []

        # Add static potongan columns first
        potongan_children.extend([
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
            {"headerName": "KOREKSI", "children": [
                {"field": "pot_koreksi", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}
            ]}
        ])

        # Dynamic POTONGAN PATTERN columns (for "Pot/potongan" patterns)
        # These are items that start with "POTONGAN" but are not standard deductions
        # Use dyn_potongan instead of dyn_potongan_pattern to get all filtered items
        if dyn_potongan:
            potongan_lainnya_children = []
            for i, pot_name in enumerate(dyn_potongan):
                field_name = f"pot_dynamic_{i+1}"
                # Map known deduction names to existing fields
                mapped_field = self._map_potongan_field(pot_name)
                if mapped_field:
                    field_name = mapped_field

                potongan_lainnya_children.append({
                    "headerName": pot_name.upper(),
                    "children": [
                        {"field": field_name, "headerName": "JUMLAH", "width": 120, "type": "numericColumn"}
                    ]
                })

            # Add POTONGAN LAINNYA group if we have any potongan pattern items
            if potongan_lainnya_children:
                potongan_children.append({
                    "headerName": "POTONGAN LAINNYA",
                    "children": potongan_lainnya_children
                })

        # Add TOTAL POTONGAN at the end
        potongan_children.append({"field": "total_potongan", "headerName": "TOTAL POTONGAN", "width": 120, "type": "numericColumn"})

        ringkasan_children = [
            {"field": "jumlah_upah_kotor", "headerName": "JUMLAH UPAH KOTOR", "width": 140, "type": "numericColumn"},
            {"field": "upah_bersih", "headerName": "UPAH BERSIH", "width": 120, "type": "numericColumn"}
        ]

        result = [
            {"headerName": "IDENTITAS", "children": identitas_children},
            {"headerName": "ABSENSI", "children": absensi_children},
            {"headerName": "UPAH DASAR", "children": upah_dasar_children},
            {"headerName": "TUNJANGAN", "children": tunjangan_children}
        ]

        # Add PREMI section if any columns exist
        if premi_children:
            result.append({"headerName": "PREMI", "children": premi_children})

        # Add POTONGAN section if any columns exist
        if potongan_children:
            result.append({"headerName": "POTONGAN", "children": potongan_children})

        result.append({"headerName": "RINGKASAN", "children": ringkasan_children})

        return result

    def _map_premi_field(self, premi_name: str) -> str:
        """Map premium description to field name"""
        premi_lower = premi_name.lower()
        
        # Exclude keywords - should not be treated as premium
        if "potongan" in premi_lower:
            return None  # Explicitly exclude POTONGAN items
        
        # Known premium mappings
        if "brondol" in premi_lower:
            return "premi_brondol"
        elif "pruning" in premi_lower:
            return "premi_pruning"
        elif "angkut" in premi_lower and "material" in premi_lower:
            return "premi_angkut_material"
        elif "angkut" in premi_lower and "tbs" in premi_lower:
            return "premi_angkut_tbs"
        elif "harvesting" in premi_lower and "incentive" in premi_lower:
            return "premi_harvesting_incentive"
        elif "harvesting" in premi_lower and "tunjangan" in premi_lower:
            return None  # Use dynamic field - avoid duplicate with static harvesting
        elif "harvesting" in premi_lower:
            return "premi_harvesting"
        elif "pupuk" in premi_lower:
            return "premi_pupuk"
        elif "koreksi" in premi_lower:
            return "premi_koreksi"  # Keep as premium for now

        # Return None for unknown premiums - will use dynamic field name
        return None

    def _map_potongan_field(self, pot_name: str) -> str:
        """Map potongan description to field name"""
        pot_lower = pot_name.lower()

        # Known deduction mappings
        if "pph21" in pot_lower or "pph 21" in pot_lower:
            return "pot_pph21"
        elif "spsi" in pot_lower:
            return "pot_spsi"
        elif "bpjs" in pot_lower and "kes" in pot_lower:
            return "pot_bpjs_kesehatan_pekerja"
        elif "bpjs" in pot_lower and "pek" in pot_lower:
            return "pot_bpjs_pek"
        elif "bpjs" in pot_lower and "maj" in pot_lower:
            return "pot_bpjs_maj"
        elif "pinjam" in pot_lower:
            return "pot_pinjam"
        elif "kl" in pot_lower:
            return "pot_kl"
        elif "thr" in pot_lower:
            return "pot_thr"
        elif "kontan" in pot_lower:
            return "pot_kontan"

        # Return None for unknown deductions - will use dynamic field name
        return None

    def _has_loosefruit_data(self, month: int, year: int, gang_code: str) -> bool:
        """Check if there's any loosefruit data for given period and gang"""
        try:
            from database.services.database import Database
            
            db = Database.instance()
            
            # Query to check for any loosefruit data
            query = '''
            SELECT COUNT(*) as count
            FROM PR_LOOSEFRUIT_ARC LF
            JOIN PR_LOOSEFRUITLN_ARC LFLN ON LF.ID = LFLN.MasterID
            JOIN HR_GANGLN G ON G.GangMember = LFLN.EmpCode
            WHERE G.GangCode = ?
            AND LF.DocDate >= ?
            AND LF.DocDate < ?
            AND COALESCE(LFLN.Amount, 0) > 0
            '''
            
            start_date = f"{year}-{str(month).zfill(2)}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{str(month+1).zfill(2)}-01"
            
            result = db.query_one(query, [gang_code, start_date, end_date])
            
            # Return True if count > 0
            return result and result[0] > 0 if result else False
            
        except Exception as e:
            print(f"Error checking loosefruit data: {e}")
            # If error, assume there's data (better to show column)
            return True

    def _get_fallback_column_defs(self) -> List[Dict[str, Any]]:
        """Fallback column definitions if main logic fails - preserves full structure"""
        identitas_children = [
            {"field": "no", "headerName": "NO", "width": 60, "type": "numericColumn", "cellStyle": {"textAlign": "center"}},
            {"field": "jenis_kelamin", "headerName": "L/P", "width": 50, "type": "textColumn", "cellStyle": {"textAlign": "center"}},
            {"field": "nama", "headerName": "NAMA", "width": 200, "type": "textColumn", "cellStyle": {"textAlign": "left"}},
            {"field": "nik", "headerName": "NIK", "width": 100, "type": "textColumn", "cellStyle": {"textAlign": "left"}}
        ]

        # UPDATED ABSENSI with 3-level structure
        absensi_children = [
            {"headerName": "KEHADIRAN", "children": [
                {"field": "hari_kerja", "headerName": "Hari", "width": 80, "type": "numericColumn"}
            ]},
            {"headerName": "KETIDAKHADIRAN", "children": [
                {"field": "cuti_tahunan_hari", "headerName": "CUTI TAHUNAN", "width": 90, "type": "numericColumn"},
                {"field": "cuti_sakit_haid_hari", "headerName": "SAKIT + HAID", "width": 110, "type": "numericColumn"},
                {"field": "cuti_minggu_hari", "headerName": "MINGGU", "width": 90, "type": "numericColumn"},
                {"field": "cuti_nasional_hari", "headerName": "NASIONAL", "width": 100, "type": "numericColumn"}
            ]},
            {"headerName": "JUMLAH HK", "children": [
                {"field": "jumlah_hk", "headerName": "Jumlah", "width": 80, "type": "numericColumn"}
            ]}
        ]

        upah_dasar_children = [
            {"field": "upah_dasar", "headerName": "UPAH DASAR", "width": 120, "type": "numericColumn"},
            {"field": "upah_pokok", "headerName": "UPAH POKOK", "width": 120, "type": "numericColumn"},
            {"field": "gaji_pokok", "headerName": "GAJI POKOK", "width": 120, "type": "numericColumn"}
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
            ]},
            {"field": "total_tunjangan", "headerName": "TOTAL TUNJANGAN", "width": 120, "type": "numericColumn"}
        ]

        # Default PREMI columns for fallback
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
            {"headerName": "KOREKSI", "children": [
                {"field": "pot_koreksi", "headerName": "JUMLAH", "width": 100, "type": "numericColumn"}
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
            {"headerName": "UPAH DASAR", "children": upah_dasar_children},
            {"headerName": "TUNJANGAN", "children": tunjangan_children},
            {"headerName": "PREMI", "children": premi_children},
            {"headerName": "POTONGAN", "children": potongan_children},
            {"headerName": "RINGKASAN", "children": ringkasan_children}
        ]
