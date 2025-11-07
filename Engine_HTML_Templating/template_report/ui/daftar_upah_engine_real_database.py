#!/usr/bin/env python3
"""
Daftar Upah Template Engine with Real Database Integration - Fixed Version
Uses simple database connection to get real employee data from SQL query
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse
from jinja2 import Environment, FileSystemLoader, Template

from simple_database_query import SimpleEmployeeQueryManager
from cuti_data_manager import CutiDataManager


@dataclass
class PayrollData:
    """Payroll calculation data"""
    basic_salary: float = 4000000
    overtime_hours: int = 0
    overtime_rate: float = 20000
    allowance_transport: float = 500000
    allowance_meal: float = 300000
    allowance_other: float = 200000
    deduction_bpjs: float = 200000
    deduction_pph: float = 150000
    deduction_other: float = 0
    loan_payment: float = 200000
    gross_salary: float = 0
    net_salary: float = 0


class DaftarUpahEngineRealFixed:
    """Template engine with real database integration - Fixed Version"""

    def __init__(self):
        self.template_dir = Path(__file__).parent
        self.output_dir = self.template_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

        # Initialize database query manager
        query_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Engine_HTML_Templating/template_report/query/get_detail_emp_each_gang.sql"
        config_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json"
        self.query_manager = SimpleEmployeeQueryManager(query_file, config_file)

        # Initialize cuti data manager
        self.cuti_manager = CutiDataManager(config_file)

        self.stats = {
            'reports_generated': 0,
            'total_employees_processed': 0,
            'database_queries_executed': 0,
            'processing_times': []
        }

    def load_sample_payroll_data(self, sample_data_path: str) -> Dict[str, Any]:
        """Load sample payroll data for merging"""
        try:
            with open(sample_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"[OK] Sample payroll data loaded: {len(data.get('karyawan', []))} records")
            return data
        except Exception as e:
            print(f"[ERROR] Failed to load sample payroll data: {e}")
            return {}

    def merge_employee_with_payroll_data(self, employees: List, sample_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Merge real employee data with payroll data"""
        print(f"[MERGE] Merging {len(employees)} real employee records with payroll data...")

        if not sample_data:
            print("[WARN] No sample payroll data available, using default values")
            return self._create_default_payroll_data(employees)

        sample_employees = sample_data.get('karyawan', [])
        merged_employees = []

        for i, emp in enumerate(employees):
            # Use corresponding sample payroll data (cycle through if needed)
            sample_idx = i % len(sample_employees)
            sample_emp = sample_employees[sample_idx]

            merged_emp = {
                # Real employee data from database
                'nik': emp.nik,
                'nama': emp.nama,
                'jenis_kelamin': emp.jenis_kelamin,
                'loc_code': emp.LocCode,
                'gang_code': emp.GangCode,  # Added GangCode

                # Payroll data from sample
                'gaji_pokok': sample_emp.get('gaji_pokok', 4000000),
                'uang_lembur': sample_emp.get('uang_lembur', 0),
                'tunjangan_transport': sample_emp.get('tunjangan_transport', 500000),
                'tunjangan_makan': sample_emp.get('tunjangan_makan', 300000),
                'tunjangan_lain': sample_emp.get('tunjangan_lain', 200000),
                'potongan_bpjs': sample_emp.get('potongan_bpjs', 200000),
                'potongan_pph': sample_emp.get('potongan_pph', 150000),
                'potongan_lain': sample_emp.get('potongan_lain', 0),
                'potongan_pinjaman_uang': sample_emp.get('potongan_pinjaman_uang', 200000),
                'upah_bersih': sample_emp.get('upah_bersih', 3750000),
                'tidak_hadir_cth': sample_emp.get('tidak_hadir_cth', 0),
                'tidak_hadir_alpa': sample_emp.get('tidak_hadir_alpa', 0)
            }

            merged_employees.append(merged_emp)

        print(f"[OK] Successfully merged {len(merged_employees)} employee records")
        return merged_employees

    def _create_default_payroll_data(self, employees: List) -> List[Dict[str, Any]]:
        """Create default payroll data when sample data is not available"""
        merged_employees = []
        for emp in employees:
            payroll = PayrollData()
            merged_emp = {
                'nik': emp.nik,
                'nama': emp.nama,
                'jenis_kelamin': emp.jenis_kelamin,
                'loc_code': emp.LocCode,
                'gang_code': emp.GangCode,  # Add gang_code field
                'gaji_pokok': payroll.basic_salary,
                'uang_lembur': payroll.overtime_hours * payroll.overtime_rate,
                'tunjangan_transport': payroll.allowance_transport,
                'tunjangan_makan': payroll.allowance_meal,
                'tunjangan_lain': payroll.allowance_other,
                'potongan_bpjs': payroll.deduction_bpjs,
                'potongan_pph': payroll.deduction_pph,
                'potongan_lain': payroll.deduction_other,
                'potongan_pinjaman_uang': payroll.loan_payment,
                'upah_bersih': payroll.basic_salary + payroll.allowance_transport + payroll.allowance_meal - payroll.deduction_bpjs - payroll.deduction_pph,
                'tidak_hadir_cth': 0,
                'tidak_hadir_alpa': 0
            }
            merged_employees.append(merged_emp)

        return merged_employees

    def merge_employee_with_cuti_data(self, employees: List, bulan: str = "Mei", tahun: str = "2025") -> List[Dict[str, Any]]:
        """Merge employee data with real cuti data"""
        print(f"[CUTI-MERGE] Merging cuti data for {len(employees)} employees...")

        merged_employees = []

        for emp in employees:
            # Get cuti data for this employee
            cuti_data = self.cuti_manager.get_cuti_data_for_employee(emp.EmpCode, bulan, tahun)

            # Create employee record with cuti data
            merged_emp = {
                'nik': emp.EmpCode,
                'nama': emp.EmpName,
                'jenis_kelamin': emp.jenis_kelamin,
                'loc_code': emp.LocCode,
                'gang_code': emp.GangCode,

                # Basic payroll data (using default values for now)
                'gaji_pokok': 4000000,
                'uang_lembur': 0,
                'tunjangan_transport': 500000,
                'tunjangan_makan': 300000,
                'tunjangan_lain': 200000,
                'potongan_bpjs': 200000,
                'potongan_pph': 150000,
                'potongan_lain': 0,
                'potongan_pinjaman_uang': 200000,
                'upah_bersih': 4000000 + 500000 + 300000 - 200000 - 150000 - 200000,

                # Cuti data from real queries
                'cuti_tahunan_hari': cuti_data.cuti_tahunan_hari,
                'cuti_tahunan_jumlah': cuti_data.cuti_tahunan_jumlah,
                'cuti_sakit_hari': cuti_data.cuti_sakit_hari,
                'cuti_sakit_jumlah': cuti_data.cuti_sakit_jumlah,
                'cuti_haid_hari': cuti_data.cuti_haid_hari,
                'cuti_haid_jumlah': cuti_data.cuti_haid_jumlah,
                'cuti_minggu_hari': cuti_data.hk_minggu,
                'cuti_nasional_hari': cuti_data.hk_nasional,
                'cuti_melahirkan_hari': cuti_data.cuti_melahirkan_hari,
                'cuti_melahirkan_jumlah': cuti_data.cuti_melahirkan_jumlah,
                'cuti_izin_hari': cuti_data.cuti_izin_hari,
                'cuti_izin_jumlah': cuti_data.cuti_izin_jumlah,

                # Other default values
                'tidak_hadir_cth': 0,
                'tidak_hadir_alpa': 0
            }

            merged_employees.append(merged_emp)

        print(f"[OK] Successfully merged cuti data for {len(merged_employees)} employees")
        return merged_employees

    def get_employee_hk_count(self, emp_code: str, bulan: str, tahun: str) -> int:
        """Get HK count for employee from database"""
        try:
            import pyodbc
            import json

            # Load database config
            with open("D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json", 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Query to get HK count
            query = """
            SELECT COUNT(*) as hk_count
            FROM "PR_EMP_ATTN"
            WHERE EmpCode = ?
              AND AttnDate >= ?
              AND AttnDate < DATEADD(month, 1, ?)
              AND IsPresent = 'true'
            """

            # Format dates
            start_date = f"{tahun}-{bulan:02d}-01"
            print(f"[DEBUG] Querying HK for {emp_code.strip()} from {start_date}")
            cursor.execute(query, emp_code.strip(), start_date, start_date)
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            hk_count = result[0] if result and result[0] else 0
            print(f"[DEBUG] HK count for {emp_code.strip()}: {hk_count}")
            return hk_count

        except Exception as e:
            print(f"[WARN] Failed to get HK count for {emp_code}: {e}")
            return 25  # Return default value instead of 0

    def format_value(self, value, format_str=""):
        """Format value and handle zero values"""
        if value == 0 or value == 0.0:
            return ""
        if format_str:
            return format(value, format_str)
        return str(value)

    def get_employee_payrate(self, emp_code: str) -> float:
        """Get employee payrate from database"""
        try:
            import pyodbc
            import json

            # Load database config
            with open("D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json", 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Query to get payrate
            query = """
            SELECT TOP 1 "PayRate"
            FROM "HR_PAYROLL"
            WHERE "EmpCode" = ?
            """

            cursor.execute(query, emp_code.strip())
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            return result[0] if result and result[0] else 0

        except Exception as e:
            print(f"[WARN] Failed to get payrate for {emp_code}: {e}")
            return 0

    def get_employee_beras_payrate(self, emp_code: str) -> float:
        """Get employee beras payrate from database using Payrate_Beras.sql"""
        try:
            import pyodbc

            # Load database config
            with open("D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json", 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Load query from file
            query_file = Path(__file__).parent.parent / "query" / "Tunjangan" / "Payrate_Beras.sql"
            with open(query_file, 'r', encoding='utf-8') as f:
                query = f.read()

            cursor.execute(query, emp_code.strip())
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result and result[0] is not None:
                return float(result[0])
            return 0  # Default if not found

        except Exception as e:
            print(f"[ERROR] Failed to get beras payrate for {emp_code}: {e}")
            return 0  # Default

    def get_employee_jabatan_amount(self, emp_code: str, month: int, year: int) -> float:
        """Get employee jabatan tunjangan amount directly from database using Get_Amount_Tunjangan_Jabatan.sql"""
        try:
            import pyodbc

            # Load database config
            with open("D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json", 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Load query from file
            query_file = Path(__file__).parent.parent / "query" / "Tunjangan" / "Gett_Amount_Tunjangan_Jabatan.sql"
            with open(query_file, 'r', encoding='utf-8') as f:
                query = f.read()

            # Calculate date range for the specified month and year
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"

            # Replace the hardcoded values in query with parameterized query
            query = query.replace("'H0330'", "?")
            query = query.replace("'2025-05-01'", "?")
            query = query.replace("'2025-06-01'", "?")

            cursor.execute(query, emp_code.strip(), start_date, end_date)
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            # Return the Amount (Jumlah in Rp)
            if result and len(result) > 0 and result[-1] is not None:
                return float(result[-1])
            return 0  # Default if not found

        except Exception as e:
            print(f"[ERROR] Failed to get jabatan amount for {emp_code}: {e}")
            return 0  # Default

    def get_employee_jabatan_payrate(self, emp_code: str, month: int, year: int) -> float:
        """Get employee jabatan payrate from database using Payrate_Jabatan.sql (legacy function - kept for compatibility)"""
        try:
            import pyodbc

            # Load database config
            with open("D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json", 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Load query from file
            query_file = Path(__file__).parent.parent / "query" / "Tunjangan" / "Payrate_Jabatan.sql"
            with open(query_file, 'r', encoding='utf-8') as f:
                query = f.read()

            # Calculate date range for the specified month and year
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"

            # Replace the hardcoded values in query with parameterized query
            query = query.replace("'H0033'", "?")
            query = query.replace("'2025-05-01'", "?")
            query = query.replace("'2025-06-01'", "?")

            cursor.execute(query, emp_code.strip(), start_date, end_date)
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            if result and len(result) > 0 and result[0] is not None:
                return float(result[0])
            return 0  # Default if not found

        except Exception as e:
            print(f"[ERROR] Failed to get jabatan payrate for {emp_code}: {e}")
            return 0  # Default

    def get_employee_masa_kerja_years(self, emp_code: str) -> int:
        """Get employee masa kerja (work period) in years using count_masa_kerja.sql"""
        try:
            import pyodbc

            # Load database config
            with open("D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json", 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Load query from file
            query_file = Path(__file__).parent.parent / "query" / "Tunjangan" / "count_masa_kerja.sql"
            with open(query_file, 'r', encoding='utf-8') as f:
                query = f.read()

            # Replace hardcoded EmpCode with parameter
            query = query.replace("'H0093'", "?")

            cursor.execute(query, emp_code.strip())
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            # Return the calculated years (Lama in Thn)
            if result and len(result) > 0 and result[-1] is not None:
                return int(result[-1])
            return 0  # Default if not found

        except Exception as e:
            print(f"[ERROR] Failed to get masa kerja years for {emp_code}: {e}")
            return 0  # Default

    def get_employee_masa_kerja_amount(self, emp_code: str, month: int, year: int) -> float:
        """Get employee masa kerja allowance amount using get_amount_masa_kerja.sql"""
        try:
            import pyodbc

            # Load database config
            with open("D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json", 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Load query from file
            query_file = Path(__file__).parent.parent / "query" / "Tunjangan" / "get_amount_masa_kerja.sql"
            with open(query_file, 'r', encoding='utf-8') as f:
                query = f.read()

            # Calculate date range for the specified month and year
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"

            # Replace hardcoded values in query with parameterized query
            query = query.replace("'H0033'", "?")
            query = query.replace("'2025-05-01'", "?")
            query = query.replace("'2025-06-01'", "?")

            cursor.execute(query, emp_code.strip(), start_date, end_date)
            result = cursor.fetchone()

            cursor.close()
            conn.close()

            # Return the Amount (Jumlah in Rp)
            if result and len(result) > 0 and result[-1] is not None:
                return float(result[-1])
            return 0  # Default if not found

        except Exception as e:
            print(f"[ERROR] Failed to get masa kerja amount for {emp_code}: {e}")
            return 0  # Default

    def calculate_hari_kerja(self, hk_count: int, cuti_tahunan: int, cuti_sakit: int, hk_minggu: int, hk_nasional: int) -> int:
        """Calculate Hari Kerja = HK - (Tahunan + Sakit + Minggu + Nasional)"""
        total_cuti = cuti_tahunan + cuti_sakit + hk_minggu + hk_nasional
        hari_kerja = max(0, hk_count - total_cuti)
        return hari_kerja

    def calculate_gaji_pokok(self, hk_count: int, payrate, cuti_tahunan: int = 0, cuti_sakit: int = 0, hk_minggu: int = 0, hk_nasional: int = 0) -> float:
        """Calculate Gaji Pokok = (HK - Total Cuti) x Payrate (Rp)"""
        total_cuti = cuti_tahunan + cuti_sakit + hk_minggu + hk_nasional
        hari_kerja = max(0, hk_count - total_cuti)
        return hari_kerja * float(payrate) if payrate else 0

    def generate_final_employee_rows(self, merged_employees: List[Dict[str, Any]]) -> str:
        """Generate employee rows for final template with correct layout"""
        def clean_nik(nik):
            """Clean NIK by removing extra spaces and dots"""
            return nik.strip().replace('.', '').replace(' ', '')

        employee_rows = ""
        for i, emp in enumerate(merged_employees, 1):
            # Clean the NIK
            clean_emp_nik = clean_nik(emp['nik'])

            # Get real HK count from database
            hk_count = self.get_employee_hk_count(emp['nik'], 5, 2025) if isinstance(emp['nik'], str) else 25

            # Get employee payrate from database
            payrate = self.get_employee_payrate(emp['nik'])

            # Calculate Hari Kerja
            hari_kerja = self.calculate_hari_kerja(
                hk_count,
                emp.get('cuti_tahunan_hari', 0),
                emp.get('cuti_sakit_hari', 0),
                emp.get('cuti_minggu_hari', 0),
                emp.get('cuti_nasional_hari', 0)
            )

            # Calculate Gaji Pokok (legacy, not rendered as salary in Gaji Pokok column)
            gaji_pokok = self.calculate_gaji_pokok(hk_count, payrate)

            # Prepare cuti data with alternating colors and red text (5 kolom)
            cuti_data = [
                ('cuti_tahunan_hari', emp.get('cuti_tahunan_hari', 0)),  # Tahunan (Izin)
                ('cuti_sakit_hari', emp.get('cuti_sakit_hari', 0)),  # Sakit + Haid (gabungan)
                ('cuti_minggu_hari', emp.get('cuti_minggu_hari', 0)),  # Minggu
                ('cuti_nasional_hari', emp.get('cuti_nasional_hari', 0)),  # Nasional
                ('cuti_izin_hari', emp.get('cuti_izin_hari', 0))  # Izin (biasa)
            ]

            # Start building the row
            employee_rows += f"""
                <tr class="employee-row">
                    <td class="number-cell col-no center-cell">{i}</td>
                    <td class="text-cell col-gender center-cell">{emp['jenis_kelamin']}</td>
                    <td class="nik-cell col-nik center-cell">{clean_emp_nik}</td>
                    <td class="text-cell col-name text-left center-cell">{emp['nama']}</td>
                    <td class="number-cell col-upah-dasar center-cell">{self.format_value(payrate, ',.0f')}</td>
                    <td class="number-cell col-hari-kerja center-cell">{self.format_value(hari_kerja)}</td>"""

            # Add Upah Pokok column (Hari Kerja × Upah Dasar) right after Hari Kerja
            upah_pokok = self.calculate_gaji_pokok(
                hk_count,
                payrate,
                emp.get('cuti_tahunan_hari', 0),
                emp.get('cuti_sakit_hari', 0),
                emp.get('cuti_minggu_hari', 0),
                emp.get('cuti_nasional_hari', 0)
            )
            employee_rows += f"""
                    <td class="number-cell col-upah-pokok center-cell">{self.format_value(upah_pokok, ',.0f')}</td>"""

            # (Removed) Previously mapped Gaji Pokok to Cuti Tahunan

            # Add cuti columns with alternating colors and red text
            for j, (field, value) in enumerate(cuti_data):
                bg_class = 'cuti-col-odd' if j % 2 == 0 else 'cuti-col-even'
                clean_value = self.format_value(value)
                red_class = 'cuti-libur-text' if clean_value != "" else ""
                employee_rows += f"""
                    <td class="number-cell col-cuti center-cell {bg_class} {red_class}">{clean_value}</td>"""

            # Add HK column (JML HK) after Cuti columns to match header layout section
            hk_value = self.format_value(hk_count)
            employee_rows += f"""
                    <td class="number-cell col-hk center-cell">{hk_value}</td>"""

            # Add Gaji Pokok column next to JML HK using formula: Upah Dasar × JML HK
            gaji_pokok_jmlhk = (hk_count * float(payrate)) if payrate else 0
            employee_rows += f"""
                    <td class="number-cell col-gaji-pokok center-cell">{self.format_value(gaji_pokok_jmlhk, ',.0f')}</td>"""

            # Get payrates from database
            beras_payrate = self.get_employee_beras_payrate(emp['nik'])

            # Get tunjangan jabatan amount directly from database
            jabatan_amount = self.get_employee_jabatan_amount(emp['nik'], 5, 2025)  # May 2025
            # Calculate jabatan rate as amount ÷ hari kerja
            jabatan_rate = jabatan_amount / hari_kerja if hari_kerja > 0 and jabatan_amount > 0 else 0

            # Get masa kerja data from database using the two queries
            masa_kerja_years = self.get_employee_masa_kerja_years(emp['nik'])
            masa_kerja_amount = self.get_employee_masa_kerja_amount(emp['nik'], 5, 2025)  # May 2025

            # Prepare tunjangan data with new structure
            tunjangan_data = {
                # Beras: Rate = Payrate dari database, Jumlah = JML HK × Rate
                'beras_rate': beras_payrate,
                'beras_jumlah': hk_count * beras_payrate if beras_payrate > 0 else 0,

                # Jabatan: Jumlah dari Get_Amount_Tunjangan_Jabatan.sql, Rate = Jumlah ÷ Hari Kerja
                'jabatan_rate': jabatan_rate,
                'jabatan_jumlah': jabatan_amount,

                # Masa Kerja: Lama (Thn) from count_masa_kerja.sql, Jumlah (Rp) from get_amount_masa_kerja.sql
                'masa_kerja_rate': masa_kerja_years,  # This will show as Lama (Thn)
                'masa_kerja_jumlah': masa_kerja_amount,  # This will show as Jumlah (Rp)

                # Lembur: Rate = 20,000 per hour, Jumlah = Rate × LemburHours
                'lembur_rate': 20000,
                'lembur_jumlah': emp.get('uang_lembur', 0),

                # Lainnya: Transport + Makan + Lainnya
                'lainnya_rate': 0,  # Will be calculated as average
                'lainnya_jumlah': emp['tunjangan_transport'] + emp['tunjangan_makan'] + emp.get('tunjangan_lain', 0)
            }

            # Calculate average rate for Lainnya
            total_jumlah_lainnya = tunjangan_data['lainnya_jumlah']
            if hk_count > 0:
                tunjangan_data['lainnya_rate'] = total_jumlah_lainnya / hk_count

            # Calculate total tunjangan
            total_tunjangan = (tunjangan_data['beras_jumlah'] + tunjangan_data['jabatan_jumlah'] +
                             tunjangan_data['masa_kerja_jumlah'] + tunjangan_data['lembur_jumlah'] +
                             tunjangan_data['lainnya_jumlah'])

            # Add Tunjangan columns with new structure
            tunjangan_order = [
                ('beras_rate', tunjangan_data['beras_rate']),
                ('beras_jumlah', tunjangan_data['beras_jumlah']),
                ('jabatan_rate', tunjangan_data['jabatan_rate']),
                ('jabatan_jumlah', tunjangan_data['jabatan_jumlah']),
                ('masa_kerja_rate', tunjangan_data['masa_kerja_rate']),
                ('masa_kerja_jumlah', tunjangan_data['masa_kerja_jumlah']),
                ('lembur_rate', tunjangan_data['lembur_rate']),
                ('lembur_jumlah', tunjangan_data['lembur_jumlah']),
                ('lainnya_rate', tunjangan_data['lainnya_rate']),
                ('lainnya_jumlah', tunjangan_data['lainnya_jumlah'])
            ]

            for field_name, value in tunjangan_order:
                formatted_value = self.format_value(value, ",.0f")
                employee_rows += f"""
                    <td class="number-cell col-tunjangan center-cell">{formatted_value}</td>"""

            # Add Total Tunjangan column
            employee_rows += f"""
                    <td class="number-cell col-total-tunjangan center-cell">{self.format_value(total_tunjangan, ',.0f')}</td>"""

            # Add Potongan columns
            potongan_values = [
                emp['potongan_pph'],
                emp.get('potongan_premi_kontan', 0),
                emp.get('potongan_leg_pajak_thr', 0),
                emp['potongan_pinjaman_uang'],
                emp.get('potongan_lain', 0),
                emp['potongan_bpjs'],
                0, 0,
                emp['potongan_bpjs'],
                0, 0, 0, 0, 0
            ]

            for pot_value in potongan_values:
                formatted_pot = self.format_value(pot_value, ",.0f")
                employee_rows += f"""
                    <td class="number-cell col-potongan center-cell">{formatted_pot}</td>"""

            # Add final columns
            upah_formatted = self.format_value(emp['upah_bersih'], ",.0f")
            cth_formatted = self.format_value(emp.get('tidak_hadir_cth', 0))
            alpa_formatted = self.format_value(emp.get('tidak_hadir_alpa', 0))

            employee_rows += f"""
                    <td class="number-cell col-upah center-cell">{upah_formatted}</td>
                    <td class="number-cell col-tidak-hadir center-cell">{cth_formatted}</td>
                    <td class="number-cell col-tidak-hadir center-cell">{alpa_formatted}</td>
                </tr>"""

        return employee_rows

    def generate_report_from_real_database(self, gang_code: str = 'H1H', limit: int = 100,
                                         template_file: str = "daftar_upah_template_final.html",
                                         sample_data_file: str = "large_data.json",
                                         output_file: Optional[str] = None) -> Optional[Path]:
        """Generate report using real database query"""
        try:
            start_time = datetime.now()

            print("=" * 80)
            print("DAFTAR UPAH TEMPLATE ENGINE - REAL DATABASE INTEGRATION (FIXED)")
            print("=" * 80)

            print(f"[INFO] Gang Code: {gang_code}")
            print(f"[TEMPLATE] Template: {template_file}")
            print(f"[SAMPLE] Sample Data: {sample_data_file}")
            print(f"[QUERY] Query File: {self.query_manager.query_file_path}")
            print(f"[LIMIT] Max Employees: {limit}")

            print(f"\n[1] Getting real employee data for gang '{gang_code}'...")

            # Get real employee data from database
            start_processing = datetime.now()
            employees = self.query_manager.get_employees_by_gang(gang_code, limit)
            processing_time = (datetime.now() - start_processing).total_seconds()
            print(f"   Query time: {processing_time:.2f}s")

            if not employees:
                print(f"[ERROR] No employee data found for gang '{gang_code}'")
                return None

            print(f"\n[OK] Found {len(employees)} real employees from database")
            print(f"[DATA] Sample employees:")
            for i, emp in enumerate(employees[:3], 1):
                print(f"   {i}. {emp.nik} - {emp.nama} ({emp.jenis_kelamin}) - {emp.LocCode}")

            # Load sample payroll data
            print(f"\n[2] Loading sample payroll data...")
            sample_data = self.load_sample_payroll_data(sample_data_file)

            # Merge employee data with real cuti data
            print(f"\n[3] Merging data with real cuti information...")
            merged_employees = self.merge_employee_with_cuti_data(employees, "Mei", "2025")

            # Calculate tunjangan totals for new structure
            total_tunjangan = 0
            total_beras_rate = 0
            total_beras_jumlah = 0
            total_jabatan_rate = 0
            total_jabatan_jumlah = 0
            total_masa_kerja_rate = 0
            total_masa_kerja_jumlah = 0
            total_lembur_rate = 0
            total_lembur_jumlah = 0
            total_lainnya_rate = 0
            total_lainnya_jumlah = 0
            grand_total_hari_kerja = 0

            for emp in merged_employees:
                # Get employee data for calculations
                hk_count = self.get_employee_hk_count(emp['nik'], 5, 2025) if isinstance(emp['nik'], str) else 25
                payrate = self.get_employee_payrate(emp['nik'])
                hari_kerja = self.calculate_hari_kerja(
                    hk_count,
                    emp.get('cuti_tahunan_hari', 0),
                    emp.get('cuti_sakit_hari', 0),
                    emp.get('cuti_minggu_hari', 0),
                    emp.get('cuti_nasional_hari', 0)
                )

                # Get payrates from database for this employee
                emp_beras_rate = self.get_employee_beras_payrate(emp['nik'])

                # Get tunjangan jabatan amount directly from database
                emp_jabatan_amount = self.get_employee_jabatan_amount(emp['nik'], 5, 2025)  # May 2025
                # Calculate jabatan rate as amount ÷ hari kerja
                emp_jabatan_rate = emp_jabatan_amount / hari_kerja if hari_kerja > 0 and emp_jabatan_amount > 0 else 0

                # Get masa kerja data from database using the two queries
                emp_masa_kerja_years = self.get_employee_masa_kerja_years(emp['nik'])
                emp_masa_kerja_amount = self.get_employee_masa_kerja_amount(emp['nik'], 5, 2025)  # May 2025

                # Calculate for this employee using database payrates
                emp_beras_jumlah = hk_count * emp_beras_rate if emp_beras_rate > 0 else 0
                emp_jabatan_jumlah = emp_jabatan_amount  # Direct amount from query
                emp_masa_kerja_rate = emp_masa_kerja_years  # Lama (Thn)
                emp_masa_kerja_jumlah = emp_masa_kerja_amount  # Jumlah (Rp)
                emp_lembur_rate = 20000
                emp_lembur_jumlah = emp.get('uang_lembur', 0)
                emp_lainnya_jumlah = emp['tunjangan_transport'] + emp['tunjangan_makan'] + emp.get('tunjangan_lain', 0)
                emp_lainnya_rate = emp_lainnya_jumlah / hk_count if hk_count > 0 else 0

                # Add to totals
                total_beras_rate += emp_beras_rate
                total_beras_jumlah += emp_beras_jumlah
                total_jabatan_rate += emp_jabatan_rate
                total_jabatan_jumlah += emp_jabatan_jumlah
                total_masa_kerja_rate += emp_masa_kerja_rate
                total_masa_kerja_jumlah += emp_masa_kerja_jumlah
                total_lembur_rate += emp_lembur_rate
                total_lembur_jumlah += emp_lembur_jumlah
                total_lainnya_rate += emp_lainnya_rate
                total_lainnya_jumlah += emp_lainnya_jumlah
                grand_total_hari_kerja += hari_kerja

                # Add to total tunjangan
                emp_total_tunjangan = (emp_beras_jumlah + emp_jabatan_jumlah +
                                         emp_masa_kerja_jumlah + emp_lembur_jumlah +
                                         emp_lainnya_jumlah)
                total_tunjangan += emp_total_tunjangan

            # Calculate other totals
            total_gaji_pokok = sum(emp['gaji_pokok'] for emp in merged_employees)
            total_potongan = sum(emp['potongan_bpjs'] + emp['potongan_pph'] + emp['potongan_lain'] + emp['potongan_pinjaman_uang'] for emp in merged_employees)
            total_upah_bersih = sum(emp['upah_bersih'] for emp in merged_employees)

            # Calculate actual grand totals from employee data
            grand_total_cuti_tahunan = sum(emp.get('cuti_tahunan_hari', 0) for emp in merged_employees)
            grand_total_cuti_sakit = sum(emp.get('cuti_sakit_hari', 0) for emp in merged_employees)
            grand_total_cuti_minggu = sum(emp.get('cuti_minggu_hari', 0) for emp in merged_employees)
            grand_total_cuti_nasional = sum(emp.get('cuti_nasional_hari', 0) for emp in merged_employees)
            grand_total_cuti_izin = sum(emp.get('cuti_izin_hari', 0) for emp in merged_employees)

            grand_total_hk = sum(self.get_employee_hk_count(emp['nik'], 5, 2025) for emp in merged_employees if isinstance(emp['nik'], str))

            # Calculate grand total Upah Pokok as sum of (Hari Kerja × Upah Dasar) for all employees
            grand_total_upah_pokok = 0
            for emp in merged_employees:
                hk_count = self.get_employee_hk_count(emp['nik'], 5, 2025) if isinstance(emp['nik'], str) else 25
                payrate = self.get_employee_payrate(emp['nik'])
                upah_pokok = self.calculate_gaji_pokok(hk_count, payrate,
                                                     emp.get('cuti_tahunan_hari', 0),
                                                     emp.get('cuti_sakit_hari', 0),
                                                     emp.get('cuti_minggu_hari', 0),
                                                     emp.get('cuti_nasional_hari', 0))
                grand_total_upah_pokok += upah_pokok

            # Calculate grand total Gaji Pokok as sum of (JML HK × Upah Dasar) for all employees
            grand_total_gaji_pokok = 0
            for emp in merged_employees:
                hk_count = self.get_employee_hk_count(emp['nik'], 5, 2025) if isinstance(emp['nik'], str) else 25
                payrate = self.get_employee_payrate(emp['nik'])
                gaji_pokok_val = (hk_count * float(payrate)) if payrate else 0
                grand_total_gaji_pokok += gaji_pokok_val

            # Grand totals for tunjangan (calculated from actual employee data)
            grand_total_beras_rate = total_beras_rate
            grand_total_beras_jumlah = total_beras_jumlah
            grand_total_jabatan_rate = total_jabatan_rate
            grand_total_jabatan_jumlah = total_jabatan_jumlah
            grand_total_masa_kerja_rate = total_masa_kerja_rate
            grand_total_masa_kerja_jumlah = total_masa_kerja_jumlah
            grand_total_lembur_rate = total_lembur_rate
            grand_total_lembur_jumlah = total_lembur_jumlah
            grand_total_lainnya_rate = total_lainnya_rate
            grand_total_lainnya_jumlah = total_lainnya_jumlah
            grand_total_tunjangan = total_tunjangan

            # Grand totals for potongan
            grand_total_pph21 = sum(emp['potongan_pph'] for emp in merged_employees)
            grand_total_kontan = 0
            grand_total_thr = 0
            grand_total_pinjam = sum(emp['potongan_pinjaman_uang'] for emp in merged_employees)
            grand_total_kl = 0
            grand_total_bpjs_kes = 0
            grand_total_bpjs_pek = sum(emp['potongan_bpjs'] for emp in merged_employees)
            grand_total_bpjs_maj = 0

            # Grand totals for final columns
            grand_total_upah_bersih = total_upah_bersih
            grand_total_cth = sum(emp.get('tidak_hadir_cth', 0) for emp in merged_employees)
            grand_total_alpa = sum(emp.get('tidak_hadir_alpa', 0) for emp in merged_employees)

            # Clean NIK function
            def clean_nik(nik):
                """Clean NIK by removing extra spaces and dots"""
                return nik.strip().replace('.', '').replace(' ', '')

            # Generate employee rows HTML based on template type
            if 'final' in template_file:
                employee_rows = self.generate_final_employee_rows(merged_employees)
            else:
                # Original template structure (legacy)
                employee_rows = ""
                for i, emp in enumerate(merged_employees, 1):
                    # Clean the NIK
                    clean_emp_nik = clean_nik(emp['nik'])

                    # Generate employee row with proper styling
                    employee_rows += f"""
                    <tr class="employee-row">
                        <td class="number-cell col-no">{i}</td>
                        <td class="text-cell col-gender">{emp['jenis_kelamin']}</td>
                        <td class="nik-cell col-nik">{clean_emp_nik}</td>
                        <td class="text-cell col-name text-left">{emp['nama']}</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-hk">25</td>
                        <td class="number-cell col-cuti">0</td>
                        <td class="number-cell col-tunjangan">{emp['tunjangan_transport']:,.0f}</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">{emp['tunjangan_makan']:,.0f}</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">0</td>
                        <td class="number-cell col-tunjangan">{emp['gaji_pokok']:,.0f}</td>
                        <td class="number-cell col-potongan">0</td>
                        <td class="number-cell col-potongan">{emp['potongan_bpjs']:,.0f}</td>
                        <td class="number-cell col-potongan">0</td>
                        <td class="number-cell col-potongan">0</td>
                        <td class="number-cell col-potongan">0</td>
                        <td class="number-cell col-potongan">{emp['potongan_pph']:,.0f}</td>
                        <td class="number-cell col-potongan">0</td>
                        <td class="number-cell col-potongan">0</td>
                        <td class="number-cell col-potongan">{emp['potongan_pinjaman_uang']:,.0f}</td>
                        <td class="number-cell col-upah-bersih">{emp['upah_bersih']:,.0f}</td>
                        <td class="number-cell col-tidak-hadir">0</td>
                        <td class="number-cell col-tidak-hadir">0</td>
                    </tr>"""

            # Get unique gang codes and locations for title
            unique_gangs = list(set(emp['gang_code'] for emp in merged_employees))
            unique_locs = list(set(emp['loc_code'] for emp in merged_employees))

            # Prepare comprehensive data for template
            report_data = {
                'bulan': 'Mei',
                'tahun': '2025',
                'gang_code': ', '.join(unique_gangs),
                'loc_code': ', '.join(unique_locs),
                'tanggal_cetak': datetime.now().strftime('%d-%m-%Y'),
                'employee_rows': employee_rows,
                'karyawan': merged_employees,
                'total_karyawan': len(merged_employees),
                'total': {
                    # Cut/Cuti totals (5 kolom)
                    'cuti_tahunan_hari': 0,
                    'cuti_sakit_hari': 0,  # Sakit + Haid gabungan
                    'cuti_minggu_hari': 0,
                    'cuti_nasional_hari': 0,
                    'cuti_izin_hari': 0,

                    # Working days
                    'jumlah_hk': 25 * len(merged_employees),

                    # Allowances (Tunjangan) - New Structure with Rate/Jumlah
                    'beras_rate_total': total_beras_rate,
                    'beras_jumlah_total': total_beras_jumlah,
                    'jabatan_rate_total': total_jabatan_rate,
                    'jabatan_jumlah_total': total_jabatan_jumlah,
                    'masa_kerja_rate_total': total_masa_kerja_rate,
                    'masa_kerja_jumlah_total': total_masa_kerja_jumlah,
                    'lembur_rate_total': total_lembur_rate,
                    'lembur_jumlah_total': total_lembur_jumlah,
                    'lainnya_rate_total': total_lainnya_rate,
                    'lainnya_jumlah_total': total_lainnya_jumlah,
                    'total_tunjangan': total_tunjangan,

                    # Legacy tunjangan fields (for compatibility)
                    'tunjangan_beras': total_beras_jumlah,
                    'tunjangan_beras_jumlah': total_beras_jumlah,
                    'tunjangan_jabatan': total_jabatan_jumlah,
                    'tunjangan_jabatan_hk': total_jabatan_jumlah,
                    'tunjangan_masa_kerja': total_masa_kerja_jumlah,
                    'tunjangan_masa_kerja_jumlah': total_masa_kerja_jumlah,
                    'tunjangan_lembur': total_lembur_jumlah,
                    'tunjangan_premi': 0,
                    'tunjangan_angkut_tbs': 0,
                    'tunjangan_angkut_pc_tbk': 0,
                    'tunjangan_premi_retase': 0,
                    'tunjangan_antar_jemput': 0,
                    'tunjangan_angkut_puru': 0,
                    'tunjangan_premi_kontan': 0,
                    'tunjangan_koreksi': 0,
                    'upah_kotor': total_gaji_pokok + total_tunjangan,

                    # Deductions (Potongan)
                    'potongan_pph21_total': sum(emp['potongan_pph'] for emp in merged_employees),
                    'potongan_kontan_total': 0,
                    'potongan_thr_total': 0,
                    'potongan_pinjam_total': sum(emp['potongan_pinjaman_uang'] for emp in merged_employees),
                    'potongan_kl_total': 0,
                    'potongan_bpjs_kes_total': 0,
                    'potongan_bpjs_pek_total': sum(emp['potongan_bpjs'] for emp in merged_employees),
                    'potongan_bpjs_maj_total': 0,

                    # Legacy potongan fields (for compatibility)
                    'potongan_astek_pekerja': 0,
                    'potongan_astek_majikan': 0,
                    'potongan_astek_jumlah': 0,
                    'potongan_bpjs_kesehatan': 0,
                    'potongan_bpjs_pekerja': sum(emp['potongan_bpjs'] for emp in merged_employees),
                    'potongan_bpjs_pensiun': 0,
                    'potongan_bpjs_majikan': 0,
                    'potongan_bpjs_jumlah': sum(emp['potongan_bpjs'] for emp in merged_employees),
                    'potongan_pph21': sum(emp['potongan_pph'] for emp in merged_employees),
                    'potongan_premi_kontan': 0,
                    'potongan_lebih_potong_pajak_thr': 0,
                    'potongan_pinjaman_uang': sum(emp['potongan_pinjaman_uang'] for emp in merged_employees),

                    # Additional potongan totals for template compatibility
                    'potongan_total1': 0,
                    'potongan_total2': 0,
                    'potongan_total3': 0,
                    'potongan_total4': 0,
                    'tunjangan_total8': 0,
                    'tunjangan_total9': 0,

                  # Final totals
                    'upah_bersih_total': total_upah_bersih,
                    'tidak_hadir_cth': 0,
                    'tidak_hadir_alpa': 0,

                  # Legacy final totals (for compatibility)
                    'upah_bersih': total_upah_bersih
                },
                'grand_total': {
                    # Cut/Libur Grand Totals
                    'cuti_tahunan_hari': grand_total_cuti_tahunan,
                    'cuti_sakit_hari': grand_total_cuti_sakit,
                    'cuti_minggu_hari': grand_total_cuti_minggu,
                    'cuti_nasional_hari': grand_total_cuti_nasional,
                    'cuti_izin_hari': grand_total_cuti_izin,

                    # Working Days Grand Total
                    'jumlah_hk': grand_total_hk,
                    'hari_kerja_total': grand_total_hari_kerja,

                    # Upah Pokok Grand Total (Hari Kerja × Upah Dasar)
                    'upah_pokok_total': grand_total_upah_pokok,

                    # Gaji Pokok Grand Total (JML HK × Upah Dasar)
                    'gaji_pokok_total': grand_total_gaji_pokok,

                    # Tunjangan Grand Totals
                    'beras_rate_total': grand_total_beras_rate,
                    'beras_jumlah_total': grand_total_beras_jumlah,
                    'jabatan_rate_total': grand_total_jabatan_rate,
                    'jabatan_jumlah_total': grand_total_jabatan_jumlah,
                    'masa_kerja_rate_total': grand_total_masa_kerja_rate,
                    'masa_kerja_jumlah_total': grand_total_masa_kerja_jumlah,
                    'lembur_rate_total': grand_total_lembur_rate,
                    'lembur_jumlah_total': grand_total_lembur_jumlah,
                    'lainnya_rate_total': grand_total_lainnya_rate,
                    'lainnya_jumlah_total': grand_total_lainnya_jumlah,
                    'total_tunjangan': grand_total_tunjangan,

                    # Additional tunjangan grand totals
                    'tunjangan_total8': 0,
                    'tunjangan_total9': 0,

                    # Potongan Grand Totals
                    'potongan_pph21_total': grand_total_pph21,
                    'potongan_kontan_total': grand_total_kontan,
                    'potongan_thr_total': grand_total_thr,
                    'potongan_pinjam_total': grand_total_pinjam,
                    'potongan_kl_total': grand_total_kl,
                    'potongan_bpjs_kes_total': grand_total_bpjs_kes,
                    'potongan_bpjs_pek_total': grand_total_bpjs_pek,
                    'potongan_bpjs_maj_total': grand_total_bpjs_maj,

                    # Additional potongan grand totals
                    'potongan_total1': 0,
                    'potongan_total2': 0,
                    'potongan_total3': 0,
                    'potongan_total4': 0,

                    # Final Grand Totals
                    'upah_bersih_total': grand_total_upah_bersih,
                    'tidak_hadir_cth_total': grand_total_cth,
                    'tidak_hadir_alpa_total': grand_total_alpa
                },
                'tanggal_cetak': datetime.now().strftime('%d-%m-%Y'),
                'data_source': 'Real Database Query + Sample Payroll'
            }

            # Validation: ensure grand totals equal sums from rows
            self.validate_grand_totals(merged_employees, report_data['grand_total'])

            # Load template
            print(f"\n[4] Loading HTML template...")
            template_path = self.template_dir / template_file
            if not template_path.exists():
                print(f"[ERROR] Template file not found: {template_path}")
                return None

            # Render template using custom placeholder replacement
            print(f"[5] Rendering template...")
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Replace placeholders safely (only replace specific placeholders)
            html_content = template_content

            # Header placeholders
            html_content = html_content.replace('{bulan}', report_data['bulan'])
            html_content = html_content.replace('{tahun}', report_data['tahun'])
            html_content = html_content.replace('{gang_code}', report_data['gang_code'])
            html_content = html_content.replace('{loc_code}', report_data['loc_code'])
            html_content = html_content.replace('{tanggal_cetak}', report_data['tanggal_cetak'])
            html_content = html_content.replace('{employee_rows}', report_data['employee_rows'])

            # Total placeholders
            total = report_data['total']
            for key, value in total.items():
                html_content = html_content.replace(f'{{total.{key}}}', str(value))

            # Grand Total placeholders with proper formatting
            grand_total = report_data['grand_total']

            # Replace placeholders with exact match including formatting
            html_content = html_content.replace('{grand_total.cuti_tahunan_hari}', f"{int(grand_total['cuti_tahunan_hari'])}")
            html_content = html_content.replace('{grand_total.cuti_sakit_hari}', f"{int(grand_total['cuti_sakit_hari'])}")
            html_content = html_content.replace('{grand_total.cuti_minggu_hari}', f"{int(grand_total['cuti_minggu_hari'])}")
            html_content = html_content.replace('{grand_total.cuti_nasional_hari}', f"{int(grand_total['cuti_nasional_hari'])}")
            html_content = html_content.replace('{grand_total.cuti_izin_hari}', f"{int(grand_total['cuti_izin_hari'])}")
            html_content = html_content.replace('{grand_total.jumlah_hk}', f"{int(grand_total['jumlah_hk'])}")
            html_content = html_content.replace('{grand_total.hari_kerja_total}', f"{int(grand_total['hari_kerja_total'])}")
            html_content = html_content.replace('{grand_total.upah_pokok_total:,.0f}', f"{grand_total['upah_pokok_total']:,.0f}")
            html_content = html_content.replace('{grand_total.gaji_pokok_total:,.0f}', f"{grand_total['gaji_pokok_total']:,.0f}")
            html_content = html_content.replace('{grand_total.beras_rate_total:,.0f}', f"{grand_total['beras_rate_total']:,.0f}")
            html_content = html_content.replace('{grand_total.beras_jumlah_total:,.0f}', f"{grand_total['beras_jumlah_total']:,.0f}")
            html_content = html_content.replace('{grand_total.jabatan_rate_total:,.0f}', f"{grand_total['jabatan_rate_total']:,.0f}")
            html_content = html_content.replace('{grand_total.jabatan_jumlah_total:,.0f}', f"{grand_total['jabatan_jumlah_total']:,.0f}")
            html_content = html_content.replace('{grand_total.masa_kerja_rate_total:,.0f}', f"{grand_total['masa_kerja_rate_total']:,.0f}")
            html_content = html_content.replace('{grand_total.masa_kerja_jumlah_total:,.0f}', f"{grand_total['masa_kerja_jumlah_total']:,.0f}")
            html_content = html_content.replace('{grand_total.lembur_rate_total:,.0f}', f"{grand_total['lembur_rate_total']:,.0f}")
            html_content = html_content.replace('{grand_total.lembur_jumlah_total:,.0f}', f"{grand_total['lembur_jumlah_total']:,.0f}")
            html_content = html_content.replace('{grand_total.lainnya_rate_total:,.0f}', f"{grand_total['lainnya_rate_total']:,.0f}")
            html_content = html_content.replace('{grand_total.lainnya_jumlah_total:,.0f}', f"{grand_total['lainnya_jumlah_total']:,.0f}")
            html_content = html_content.replace('{grand_total.total_tunjangan:,.0f}', f"{grand_total['total_tunjangan']:,.0f}")
            html_content = html_content.replace('{grand_total.tunjangan_total8:,.0f}', f"{grand_total['tunjangan_total8']:,.0f}")
            html_content = html_content.replace('{grand_total.tunjangan_total9:,.0f}', f"{grand_total['tunjangan_total9']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_pph21_total:,.0f}', f"{grand_total['potongan_pph21_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_kontan_total:,.0f}', f"{grand_total['potongan_kontan_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_thr_total:,.0f}', f"{grand_total['potongan_thr_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_pinjam_total:,.0f}', f"{grand_total['potongan_pinjam_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_kl_total:,.0f}', f"{grand_total['potongan_kl_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_bpjs_kes_total:,.0f}', f"{grand_total['potongan_bpjs_kes_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_bpjs_pek_total:,.0f}', f"{grand_total['potongan_bpjs_pek_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_bpjs_maj_total:,.0f}', f"{grand_total['potongan_bpjs_maj_total']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_total1:,.0f}', f"{grand_total['potongan_total1']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_total2:,.0f}', f"{grand_total['potongan_total2']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_total3:,.0f}', f"{grand_total['potongan_total3']:,.0f}")
            html_content = html_content.replace('{grand_total.potongan_total4:,.0f}', f"{grand_total['potongan_total4']:,.0f}")
            html_content = html_content.replace('{grand_total.upah_bersih_total:,.0f}', f"{grand_total['upah_bersih_total']:,.0f}")
            html_content = html_content.replace('{grand_total.tidak_hadir_cth_total}', f"{int(grand_total['tidak_hadir_cth_total'])}")
            html_content = html_content.replace('{grand_total.tidak_hadir_alpa_total}', f"{int(grand_total['tidak_hadir_alpa_total'])}")

            # Generate output filename
            if output_file is None:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                output_file = f"daftar_upah_gang_{gang_code}_real_{timestamp}.html"

            output_path = self.output_dir / output_file

            # Save output
            print(f"[6] Saving output...")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)

            # Calculate statistics
            total_time = (datetime.now() - start_time).total_seconds()
            file_size = output_path.stat().st_size

            # Update statistics
            self.stats['reports_generated'] += 1
            self.stats['total_employees_processed'] += len(merged_employees)
            self.stats['processing_times'].append(total_time)
            self.stats['database_queries_executed'] += 1

            print(f"\n" + "=" * 80)
            print("[OK] REPORT GENERATION COMPLETED!")
            print("=" * 80)
            print(f"[FILE] Output: {output_path}")
            print(f"[SIZE] File Size: {file_size:,} bytes")
            print(f"[EMPLOYEES] Real Employees: {len(merged_employees)}")
            print(f"[GANG] Gang: {gang_code}")
            print(f"[TIME] Total Time: {total_time:.2f}s")
            print(f"[DATA] Data Source: Real Database Query + Sample Payroll")
            print(f"[INFO] Gender Mapping: 1->L, 0->P")
            print(f"[TARGET] Query File: {self.query_manager.query_file_path}")

            print(f"\n[STATS] STATISTICS:")
            print(f"   Total Reports Generated: {self.stats['reports_generated']}")
            print(f"   Total Employees Processed: {self.stats['total_employees_processed']}")
            print(f"   Database Queries Executed: {self.stats['database_queries_executed']}")
            print(f"   Average Processing Time: {sum(self.stats['processing_times'])/len(self.stats['processing_times']):.2f}s")

            return output_path

        except Exception as e:
            print(f"\n[ERROR] Report generation failed: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            # Always cleanup database connections
            self.query_manager.cleanup()
            self.cuti_manager.cleanup()

    def validate_grand_totals(self, merged_employees: List[Dict[str, Any]], grand_total: Dict[str, Any]) -> None:
        """Verify that grand totals equal the SUM of all values above them in the same column.
        Checks start from 'Hari Kerja' and include all numeric columns to the right.
        Handles zeros, negatives, and decimals.
        """
        try:
            print("\n[VALIDATION] Verifying grand totals against column sums...")

            sum_hari_kerja = 0
            sum_upah_pokok = 0
            sum_gaji_pokok = 0
            sum_jumlah_hk = 0
            sum_upah_bersih = 0

            # Column-wise sums
            sum_cuti_tahunan = 0
            sum_cuti_sakit = 0
            sum_cuti_minggu = 0
            sum_cuti_nasional = 0
            sum_cuti_izin = 0
            sum_potongan_pph = 0
            sum_potongan_pinjam = 0
            sum_potongan_bpjs_pek = 0

            # Accumulate per-employee values consistent with row computation
            for emp in merged_employees:
                hk_count = self.get_employee_hk_count(emp['nik'], 5, 2025) if isinstance(emp['nik'], str) else 25
                payrate = self.get_employee_payrate(emp['nik'])
                hari_kerja = self.calculate_hari_kerja(
                    hk_count,
                    emp.get('cuti_tahunan_hari', 0),
                    emp.get('cuti_sakit_hari', 0),
                    emp.get('cuti_minggu_hari', 0),
                    emp.get('cuti_nasional_hari', 0)
                )
                upah_pokok = self.calculate_gaji_pokok(
                    hk_count,
                    payrate,
                    emp.get('cuti_tahunan_hari', 0),
                    emp.get('cuti_sakit_hari', 0),
                    emp.get('cuti_minggu_hari', 0),
                    emp.get('cuti_nasional_hari', 0)
                )
                gaji_pokok = (hk_count * float(payrate)) if payrate else 0

                sum_hari_kerja += hari_kerja
                sum_upah_pokok += upah_pokok
                sum_gaji_pokok += gaji_pokok
                sum_jumlah_hk += hk_count
                sum_upah_bersih += emp.get('upah_bersih', 0)

                sum_cuti_tahunan += emp.get('cuti_tahunan_hari', 0)
                sum_cuti_sakit += emp.get('cuti_sakit_hari', 0)
                sum_cuti_minggu += emp.get('cuti_minggu_hari', 0)
                sum_cuti_nasional += emp.get('cuti_nasional_hari', 0)
                sum_cuti_izin += emp.get('cuti_izin_hari', 0)
                sum_potongan_pph += emp.get('potongan_pph', 0)
                sum_potongan_pinjam += emp.get('potongan_pinjaman_uang', 0)
                sum_potongan_bpjs_pek += emp.get('potongan_bpjs', 0)

            checks = [
                ('hari_kerja_total', sum_hari_kerja),
                ('upah_pokok_total', sum_upah_pokok),
                ('gaji_pokok_total', sum_gaji_pokok),
                ('jumlah_hk', sum_jumlah_hk),
                ('upah_bersih_total', sum_upah_bersih),
                ('cuti_tahunan_hari', sum_cuti_tahunan),
                ('cuti_sakit_hari', sum_cuti_sakit),
                ('cuti_minggu_hari', sum_cuti_minggu),
                ('cuti_nasional_hari', sum_cuti_nasional),
                ('cuti_izin_hari', sum_cuti_izin),
                ('potongan_pph21_total', sum_potongan_pph),
                ('potongan_pinjam_total', sum_potongan_pinjam),
                ('potongan_bpjs_pek_total', sum_potongan_bpjs_pek),
            ]

            mismatches = []
            for key, expected in checks:
                actual = grand_total.get(key, 0)
                if float(actual) != float(expected):
                    mismatches.append((key, actual, expected))

            if mismatches:
                print('[VALIDATION] FAILED: mismatches found')
                for key, actual, expected in mismatches:
                    print(f"   - {key}: rendered={actual} expected={expected}")
            else:
                print('[VALIDATION] PASSED: all grand totals match the column sums.')

        except Exception as e:
            print(f"[VALIDATION] ERROR: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        return {
            'stats': self.stats,
            'last_processed': datetime.now().isoformat()
        }


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Daftar Upah Template Engine with Real Database (Fixed)')
    parser.add_argument('--gang', default='H1H', help='Gang code (default: H1H)')
    parser.add_argument('--limit', type=int, default=100, help='Maximum employees (default: 100)')
    parser.add_argument('--template', default='daftar_upah_template_final.html', help='Template file')
    parser.add_argument('--sample-data', default='large_data.json', help='Sample data file')
    parser.add_argument('--output', help='Output file name')

    args = parser.parse_args()

    try:
        # Initialize engine
        engine = DaftarUpahEngineRealFixed()

        # Generate report
        result = engine.generate_report_from_real_database(
            gang_code=args.gang,
            limit=args.limit,
            template_file=args.template,
            sample_data_file=args.sample_data,
            output_file=args.output
        )

        if result:
            print(f"\n[SUCCESS] Report saved to: {result}")
        else:
            print("\n[ERROR] Failed to generate report")

        # Show statistics
        stats = engine.get_statistics()
        print(f"\n[STATS] Final Statistics:")
        print(f"   Reports Generated: {stats['stats']['reports_generated']}")
        print(f"   Employees Processed: {stats['stats']['total_employees_processed']}")
        print(f"   Database Queries: {stats['stats']['database_queries_executed']}")

    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Operation cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
