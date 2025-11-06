#!/usr/bin/env python3
"""
Cuti/Libur Data Manager
Real data integration for cuti/libur information from database
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from simple_database_query import SimpleDatabaseQuery


@dataclass
class CutiData:
    """Cuti/Libur data for an employee"""
    emp_code: str
    cuti_tahunan_hari: int = 0
    cuti_tahunan_jumlah: float = 0
    cuti_sakit_hari: int = 0
    cuti_sakit_jumlah: float = 0
    cuti_haid_hari: int = 0
    cuti_haid_jumlah: float = 0
    hk_minggu: int = 0
    hk_nasional: int = 0
    cuti_melahirkan_hari: int = 0
    cuti_melahirkan_jumlah: float = 0
    cuti_izin_hari: int = 0
    cuti_izin_jumlah: float = 0


class CutiDataManager:
    """Manager for real cuti/libur data"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.db = SimpleDatabaseQuery(config_path)

        # Query file paths
        self.query_dir = Path(__file__).parent.parent / "query"
        self.cuti_tahunan_query = ""
        self.cuti_sakit_query = ""
        self.hk_minggu_query = ""
        self.hk_nasional_query = ""
        self.total_hk_query = ""

        self._load_query_templates()

    def _load_query_templates(self):
        """Load all cuti query templates"""
        try:
            # Load cuti tahunan query
            tahunan_file = self.query_dir / "get_cuti_tahunan.sql"
            if tahunan_file.exists():
                with open(tahunan_file, 'r', encoding='utf-8') as f:
                    self.cuti_tahunan_query = f.read().strip()

            # Load cuti sakit query
            sakit_file = self.query_dir / "get_cuti_sakit.sql"
            if sakit_file.exists():
                with open(sakit_file, 'r', encoding='utf-8') as f:
                    self.cuti_sakit_query = f.read().strip()

            # Load HK minggu query
            minggu_file = self.query_dir / "get_HK_minggu.sql"
            if minggu_file.exists():
                with open(minggu_file, 'r', encoding='utf-8') as f:
                    self.hk_minggu_query = f.read().strip()

            # Load HK nasional query
            nasional_file = self.query_dir / "get_HK_national_holiday.sql"
            if nasional_file.exists():
                with open(nasional_file, 'r', encoding='utf-8') as f:
                    self.hk_nasional_query = f.read().strip()

            # Load Total HK query
            total_hk_file = self.query_dir / "get_total_HK_each_Emp.sql"
            if total_hk_file.exists():
                with open(total_hk_file, 'r', encoding='utf-8') as f:
                    self.total_hk_query = f.read().strip()

            print("[OK] All cuti query templates loaded")

        except Exception as e:
            print(f"[ERROR] Failed to load cuti query templates: {e}")

    def get_cuti_data_for_employee(self, emp_code: str, bulan: str = "Mei", tahun: str = "2025") -> CutiData:
        """Get cuti data for a specific employee"""
        print(f"[CUTI] Getting cuti data for employee {emp_code}...")

        cuti_data = CutiData(emp_code=emp_code)

        try:
            # Get cuti tahunan
            cuti_tahunan = self._get_cuti_tahunan(emp_code, bulan, tahun)
            if cuti_tahunan:
                cuti_data.cuti_tahunan_hari = len(cuti_tahunan)
                # Calculate jumlah (amount) - this would need business logic
                cuti_data.cuti_tahunan_jumlah = cuti_data.cuti_tahunan_hari * 100000  # Example calculation

            # Get cuti sakit+haid (already combined from query)
            cuti_sakit_haid = self._get_cuti_sakit_haid(emp_code, bulan, tahun)
            if cuti_sakit_haid:
                # Query returns combined sakit + haid data
                # Use total as combined Personal Sick Leave
                total_hari = len(cuti_sakit_haid)
                cuti_data.cuti_sakit_hari = total_hari  # Combined sakit + haid
                cuti_data.cuti_haid_hari = 0  # No separate haid since it's combined

                # Only calculate for sakit (combined) since haid is 0
                cuti_data.cuti_sakit_jumlah = cuti_data.cuti_sakit_hari * 75000  # Example calculation
                cuti_data.cuti_haid_jumlah = 0  # No separate calculation since it's combined

            # Get HK minggu
            hk_minggu_data = self._get_hk_minggu(emp_code, bulan, tahun)
            if hk_minggu_data:
                cuti_data.hk_minggu = len(hk_minggu_data)

            # Get HK nasional
            hk_nasional_data = self._get_hk_nasional(emp_code, bulan, tahun)
            if hk_nasional_data:
                cuti_data.hk_nasional = len(hk_nasional_data)

            print(f"[OK] Cuti data retrieved for {emp_code}: "
                  f"Tahunan={cuti_data.cuti_tahunan_hari}, "
                  f"Sakit+haid={cuti_data.cuti_sakit_hari}, "
                  f"Haid={cuti_data.cuti_haid_hari}, "
                  f"Minggu={cuti_data.hk_minggu}, "
                  f"Nasional={cuti_data.hk_nasional}")

            # Debug detail for each query type
            if cuti_data.cuti_tahunan_hari > 0:
                print(f"[DEBUG] {emp_code} has cuti tahunan data")
            if cuti_data.cuti_sakit_hari > 0 or cuti_data.cuti_haid_hari > 0:
                print(f"[DEBUG] {emp_code} has cuti sakit/haid data")
            if cuti_data.hk_minggu > 0:
                print(f"[DEBUG] {emp_code} has HK minggu data")
            if cuti_data.hk_nasional > 0:
                print(f"[DEBUG] {emp_code} has HK nasional data")

        except Exception as e:
            print(f"[ERROR] Failed to get cuti data for {emp_code}: {e}")

        return cuti_data

    def _get_cuti_tahunan(self, emp_code: str, bulan: str, tahun: str) -> list:
        """Get cuti tahunan data"""
        if not self.cuti_tahunan_query:
            return []

        try:
            # Calculate date range based on bulan
            date_range = self._get_date_range(bulan, tahun)

            # Use query template and replace placeholders dynamically
            query = self.cuti_tahunan_query
            # Replace hardcoded EmpCode with current employee
            query = query.replace("WHERE tr.EmpCode = 'H0117'", f"WHERE tr.EmpCode = '{emp_code}'")
            # Replace hardcoded dates with dynamic date range
            query = query.replace("AND tr.CreatedDate >= '2025-05-01'", f"AND tr.CreatedDate >= '{date_range['start']}'")
            query = query.replace("AND tr.CreatedDate < '2025-06-01'", f"AND tr.CreatedDate < '{date_range['end']}'")

            result = self.db.execute_query(query, [])
            if result:
                print(f"[DEBUG] Found {len(result)} cuti tahunan records for {emp_code}")
            else:
                print(f"[DEBUG] No cuti tahunan records found for {emp_code}")
            return result if result else []

        except Exception as e:
            print(f"[ERROR] Failed to get cuti tahunan for {emp_code}: {e}")
            return []

    def _get_cuti_sakit_haid(self, emp_code: str, bulan: str, tahun: str) -> list:
        """Get cuti sakit+haid data (combined from query)"""
        if not self.cuti_sakit_query:
            return []

        try:
            # Calculate date range based on bulan
            date_range = self._get_date_range(bulan, tahun)

            # Use query template and replace placeholders dynamically
            query = self.cuti_sakit_query
            # Replace hardcoded EmpCode with current employee
            query = query.replace("WHERE tr.EmpCode = 'H0080'", f"WHERE tr.EmpCode = '{emp_code}'")
            # Replace hardcoded dates with dynamic date range
            query = query.replace("AND tr.CreatedDate >= '2025-05-01'", f"AND tr.CreatedDate >= '{date_range['start']}'")
            query = query.replace("AND tr.CreatedDate < '2025-06-01'", f"AND tr.CreatedDate < '{date_range['end']}'")

            result = self.db.execute_query(query, [])
            if result:
                print(f"[DEBUG] Found {len(result)} cuti sakit+haid records for {emp_code}")
            else:
                print(f"[DEBUG] No cuti sakit+haid records found for {emp_code}")
            return result if result else []

        except Exception as e:
            print(f"[ERROR] Failed to get cuti sakit+haid for {emp_code}: {e}")
            return []

    def _get_hk_minggu(self, emp_code: str, bulan: str, tahun: str) -> list:
        """Get HK minggu data"""
        if not self.hk_minggu_query:
            return []

        try:
            # Calculate date range based on bulan
            date_range = self._get_date_range(bulan, tahun)

            # Use query template and replace placeholders dynamically
            query = self.hk_minggu_query
            # Replace hardcoded EmpCode with current employee
            query = query.replace("WHERE EmpCode = 'H0517'", f"WHERE EmpCode = '{emp_code}'")
            # Replace hardcoded dates with dynamic date range
            query = query.replace("AND AttnDate >= '2025-05-01'", f"AND AttnDate >= '{date_range['start']}'")
            query = query.replace("AND AttnDate < '2025-06-01'", f"AND AttnDate < '{date_range['end']}'")

            result = self.db.execute_query(query, [])
            if result:
                print(f"[DEBUG] Found {len(result)} cuti tahunan records for {emp_code}")
            else:
                print(f"[DEBUG] No cuti tahunan records found for {emp_code}")
            return result if result else []

        except Exception as e:
            print(f"[ERROR] Failed to get HK minggu for {emp_code}: {e}")
            return []

    def _get_hk_nasional(self, emp_code: str, bulan: str, tahun: str) -> list:
        """Get HK nasional data"""
        if not self.hk_nasional_query:
            return []

        try:
            # Calculate date range based on bulan
            date_range = self._get_date_range(bulan, tahun)

            # Use query template and replace placeholders dynamically
            query = self.hk_nasional_query
            # Replace hardcoded EmpCode with current employee
            query = query.replace("WHERE EmpCode = 'H0511'", f"WHERE EmpCode = '{emp_code}'")
            # Replace hardcoded dates with dynamic date range
            query = query.replace("AND AttnDate >= '2025-05-01'", f"AND AttnDate >= '{date_range['start']}'")
            query = query.replace("AND AttnDate < '2025-06-01'", f"AND AttnDate < '{date_range['end']}'")

            result = self.db.execute_query(query, [])
            if result:
                print(f"[DEBUG] Found {len(result)} cuti tahunan records for {emp_code}")
            else:
                print(f"[DEBUG] No cuti tahunan records found for {emp_code}")
            return result if result else []

        except Exception as e:
            print(f"[ERROR] Failed to get HK nasional for {emp_code}: {e}")
            return []

    def _get_date_range(self, bulan: str, tahun: str) -> Dict[str, str]:
        """Get date range for a specific month and year"""
        month_map = {
            'Januari': '01', 'Februari': '02', 'Maret': '03', 'April': '04',
            'Mei': '05', 'Juni': '06', 'Juli': '07', 'Agustus': '08',
            'September': '09', 'Oktober': '10', 'November': '11', 'Desember': '12'
        }

        month_num = month_map.get(bulan, '05')
        start_date = f"{tahun}-{month_num}-01"

        # Calculate end date (first day of next month)
        if month_num == '12':
            end_date = f"{int(tahun) + 1}-01-01"
        else:
            next_month = f"{tahun}-{int(month_num) + 1:02d}-01"
            end_date = next_month

        return {
            'start': start_date,
            'end': end_date
        }

    def cleanup(self):
        """Cleanup database connection"""
        self.db.close()


def test_cuti_manager():
    """Test cuti data manager"""
    print("=" * 60)
    print("CUTI DATA MANAGER TEST")
    print("=" * 60)

    config_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json"

    # Create cuti manager
    cuti_manager = CutiDataManager(config_file)

    # Test getting cuti data for an employee
    print(f"\n[TEST] Getting cuti data for employee H0117...")
    cuti_data = cuti_manager.get_cuti_data_for_employee("H0117", "Mei", "2025")

    print(f"\n[RESULT] Cuti Data:")
    print(f"  Emp Code: {cuti_data.emp_code}")
    print(f"  Cuti Tahunan: {cuti_data.cuti_tahunan_hari} hari (Rp {cuti_data.cuti_tahunan_jumlah:,.0f})")
    print(f"  Cuti Sakit: {cuti_data.cuti_sakit_hari} hari (Rp {cuti_data.cuti_sakit_jumlah:,.0f})")
    print(f"  Cuti Haid: {cuti_data.cuti_haid_hari} hari (Rp {cuti_data.cuti_haid_jumlah:,.0f})")
    print(f"  HK Minggu: {cuti_data.hk_minggu} hari")
    print(f"  HK Nasional: {cuti_data.hk_nasional} hari")

    # Cleanup
    cuti_manager.cleanup()
    print("\n[OK] Test completed")


if __name__ == "__main__":
    test_cuti_manager()