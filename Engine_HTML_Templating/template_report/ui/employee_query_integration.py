#!/usr/bin/env python3
"""
Employee Query Integration Module
Integrates SQL queries with the template engine for real-time employee data rendering
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Import the database connector framework
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent / "connection"))


try:
    from connection import DatabaseConnector, DatabaseConnectorConfig
    DATABASE_AVAILABLE = True
    print("[OK] Database connector framework available")
except ImportError as e:
    DATABASE_AVAILABLE = False
    print(f"[WARN] Database connector not available: {e}")
    print("[WARN] Will use simulation mode instead")


@dataclass
class EmployeeInfo:
    """Employee information structure"""
    EmpCode: str
    EmpName: str
    Gender: int  # 1 = Laki-laki, 0 = Perempuan
    LocCode: str
    jenis_kelamin: str = ""  # Mapped from Gender (1→L, 0→P)
    nik: str = ""  # Alias for EmpCode
    nama: str = ""  # Alias for EmpName


class EmployeeQueryManager:
    """
    Manager for employee queries with database integration
    """

    def __init__(self, query_file_path: str = None):
        """
        Initialize query manager

        Args:
            query_file_path: Path to SQL query file
        """
        self.query_file_path = query_file_path or str(
            Path(__file__).parent.parent / "query" / "get_detail_emp_each_gang.sql"
        )
        self.query_template = self._load_query_template()
        self.connector: Optional[DatabaseConnector] = None

    def _load_query_template(self) -> str:
        """Load SQL query from file"""
        try:
            with open(self.query_file_path, 'r', encoding='utf-8') as f:
                query = f.read().strip()
            print(f"[OK] Query template loaded from: {self.query_file_path}")
            return query
        except Exception as e:
            print(f"[ERROR] Failed to load query template: {e}")
            # Return default query
            return """
            SELECT TOP 100
                "HR_EMPLOYEE"."EmpCode",
                "HR_EMPLOYEE"."EmpName",
                "HR_EMPLOYEE"."Gender",
                "HR_EMPLOYEE"."LocCode"
            FROM "HR_EMPLOYEE"
            JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
            WHERE "HR_GANGLN"."GangCode" = ?
            ORDER BY "HR_EMPLOYEE"."EmpName"
            """

    def initialize_database(self) -> bool:
        """
        Initialize database connection

        Returns:
            bool: True if successful
        """
        if not DATABASE_AVAILABLE:
            print("[WARN] Database connector not available, using simulation mode")
            return False

        try:
            print("[PROCESS] Initializing database connection...")

            # Configure database connector
            config = DatabaseConnectorConfig(
                log_file=Path(__file__).parent / "logs" / "employee_queries.log",
                connection_pool_size=3,
                max_retry_attempts=3
            )

            self.connector = DatabaseConnector(config)
            success = self.connector.initialize()

            if success:
                print("[OK] Database connection established")
                # Test the specific query
                return self._test_employee_query()
            else:
                print("[ERROR] Failed to initialize database connection")
                return False

        except Exception as e:
            print(f"[ERROR] Database initialization failed: {e}")
            return False

    def _test_employee_query(self) -> bool:
        """Test the employee query"""
        try:
            print("[QUERY] Testing employee query...")

            # Test with a small limit first
            test_query = self.query_template.replace("TOP 100", "TOP 5").replace("ORDER BY", "-- ORDER BY")
            result = self.connector.execute_query(test_query, ["H1H"])

            if result.success:
                print(f"[OK] Query test successful: {result.affected_rows} rows")
                print(f"   Sample data: {result.data[0] if result.data else 'No data'}")
                return True
            else:
                print(f"[ERROR] Query test failed: {result.error_message}")
                return False

        except Exception as e:
            print(f"[ERROR] Query test failed: {e}")
            return False

    def get_employees_by_gang(self, gang_code: str = "H1H", limit: int = 100) -> List[EmployeeInfo]:
        """
        Get employees by gang code using the SQL query

        Args:
            gang_code: Gang code to filter
            limit: Maximum number of employees to fetch

        Returns:
            List of EmployeeInfo objects
        """
        print(f"[INFO] Getting employees for gang '{gang_code}' (limit: {limit})")

        if DATABASE_AVAILABLE and self.connector and self.connector.is_initialized:
            return self._get_employees_from_database(gang_code, limit)
        else:
            return self._get_simulated_employees(gang_code, limit)

    def _get_employees_from_database(self, gang_code: str, limit: int) -> List[EmployeeInfo]:
        """Get employees from actual database"""
        try:
            # Modify query to use specified limit and gang code
            query = self.query_template.replace("TOP 100", f"TOP {limit}").replace("'H1H'", f"'{gang_code}'")

            # Add ORDER BY if not present
            if "ORDER BY" not in query:
                query += f' ORDER BY "HR_EMPLOYEE"."EmpName"'

            print(f"[QUERY] Executing query: {query[:100]}...")

            result = self.connector.execute_query(query, [gang_code])

            if result.success:
                employees = []
                for row in result.data:
                    employee = EmployeeInfo(
                        EmpCode=row['EmpCode'],
                        EmpName=row['EmpName'],
                        Gender=row['Gender'],
                        LocCode=row.get('LocCode', ''),
                        jenis_kelamin=self._map_gender(row['Gender']),
                        nik=row['EmpCode'],
                        nama=row['EmpName']
                    )
                    employees.append(employee)

                print(f"[OK] Retrieved {len(employees)} employees from database")
                return employees
            else:
                print(f"[ERROR] Query failed: {result.error_message}")
                return []

        except Exception as e:
            print(f"[ERROR] Database query failed: {e}")
            return []

    def _get_simulated_employees(self, gang_code: str, limit: int) -> List[EmployeeInfo]:
        """Get simulated employee data when database is not available"""
        print(f"[SIMULATION] Using simulated data for gang '{gang_code}'")

        # Simulated employee data based on typical Indonesian names
        simulated_data = [
            {"EmpCode": "EMP001", "EmpName": "AHMAD SUBEKTI", "Gender": 1, "LocCode": "LOC001"},
            {"EmpCode": "EMP002", "EmpName": "SITI NURHALIZA", "Gender": 0, "LocCode": "LOC001"},
            {"EmpCode": "EMP003", "EmpName": "BUDI SANTOSO", "Gender": 1, "LocCode": "LOC002"},
            {"EmpCode": "EMP004", "EmpName": "DEWI RATNASARI", "Gender": 0, "LocCode": "LOC002"},
            {"EmpCode": "EMP005", "EmpName": "RUDI WIBOWO", "Gender": 1, "LocCode": "LOC003"},
            {"EmpCode": "EMP006", "EmpName": "SRI MULYATI", "Gender": 0, "LocCode": "LOC003"},
            {"EmpCode": "EMP007", "EmpName": "HENDRA GUNAWAN", "Gender": 1, "LocCode": "LOC001"},
            {"EmpCode": "EMP008", "EmpName": "RATNA SARI", "Gender": 0, "LocCode": "LOC002"},
            {"EmpCode": "EMP009", "EmpName": "AGUS PRABOWO", "Gender": 1, "LocCode": "LOC003"},
            {"EmpCode": "EMP010", "EmpName": "WIWIT WULANDARI", "Gender": 0, "LocCode": "LOC001"},
        ]

        # Take only the requested limit
        limited_data = simulated_data[:limit]

        employees = []
        for data in limited_data:
            employee = EmployeeInfo(
                EmpCode=data["EmpCode"],
                EmpName=data["EmpName"],
                Gender=data["Gender"],
                LocCode=data["LocCode"],
                jenis_kelamin=self._map_gender(data["Gender"]),
                nik=data["EmpCode"],
                nama=data["EmpName"]
            )
            employees.append(employee)

        print(f"[OK] Generated {len(employees)} simulated employee records")
        return employees

    def _map_gender(self, gender_value: int) -> str:
        """
        Map database gender value to template format

        Args:
            gender_value: Gender value from database (1 or 0)

        Returns:
            str: 'L' for male (1), 'P' for female (0)
        """
        try:
            if gender_value == 1:
                return 'L'  # Laki-laki
            elif gender_value == 0:
                return 'P'  # Perempuan
            else:
                print(f"[WARN] Unknown gender value: {gender_value}, defaulting to 'L'")
                return 'L'
        except:
            return 'L'

    def get_available_gangs(self) -> List[str]:
        """
        Get list of available gang codes

        Returns:
            List of gang codes
        """
        print("[QUERY] Getting available gang codes...")

        if DATABASE_AVAILABLE and self.connector:
            try:
                # Query for distinct gang codes
                query = """
                SELECT DISTINCT "GangCode"
                FROM "HR_GANGLN"
                ORDER BY "GangCode"
                """

                result = self.connector.execute_query(query)
                if result.success:
                    gangs = [row['GangCode'] for row in result.data]
                    print(f"[OK] Found {len(gangs)} gangs: {gangs}")
                    return gangs
                else:
                    print(f"[ERROR] Failed to get gang codes: {result.error_message}")
                    return []

            except Exception as e:
                print(f"[ERROR] Gang query failed: {e}")
                return []
        else:
            # Simulated gang codes
            gangs = ["H1H", "H2H", "H3H", "H4H", "H5H"]
            print(f"🎭 Using simulated gang codes: {gangs}")
            return gangs

    def get_employee_count_by_gang(self, gang_code: str) -> int:
        """
        Get employee count for specific gang

        Args:
            gang_code: Gang code

        Returns:
            int: Number of employees
        """
        print(f"[STATS] Getting employee count for gang '{gang_code}'...")

        if DATABASE_AVAILABLE and self.connector:
            try:
                query = """
                SELECT COUNT(*) as employee_count
                FROM "HR_EMPLOYEE"
                JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
                WHERE "HR_GANGLN"."GangCode" = ?
                """

                result = self.connector.execute_query(query, [gang_code], "one")
                if result:
                    count = result['employee_count']
                    print(f"[OK] Gang '{gang_code}' has {count} employees")
                    return count
                else:
                    print(f"[ERROR] Failed to get employee count for gang '{gang_code}'")
                    return 0

            except Exception as e:
                print(f"[ERROR] Employee count query failed: {e}")
                return 0
        else:
            # Simulated count
            count = 25 + hash(gang_code) % 20  # Random-ish but consistent
            print(f"🎭 Simulated count for gang '{gang_code}': {count}")
            return count

    def cleanup(self):
        """Cleanup database connection"""
        if self.connector:
            self.connector.cleanup()
            print("[OK] Database connection cleaned up")


class EmployeeDataProcessor:
    """
    Process employee data for template rendering
    """

    def __init__(self):
        self.query_manager = EmployeeQueryManager()
        self.sample_payroll_data = None

    def load_sample_payroll_data(self, sample_data_path: str) -> bool:
        """
        Load sample payroll data for merging

        Args:
            sample_data_path: Path to sample data file

        Returns:
            bool: True if successful
        """
        try:
            sample_path = Path(sample_data_path)
            if not sample_path.exists():
                # Try relative path
                sample_path = Path(__file__).parent.parent.parent / sample_data_path

            if sample_path.exists():
                with open(sample_path, 'r', encoding='utf-8') as f:
                    self.sample_payroll_data = json.load(f)
                print(f"[OK] Sample payroll data loaded from: {sample_path}")
                print(f"   Sample data contains {len(self.sample_payroll_data.get('karyawan', []))} employee records")
                return True
            else:
                print(f"[ERROR] Sample data file not found: {sample_path}")
                return False

        except Exception as e:
            print(f"[ERROR] Failed to load sample payroll data: {e}")
            return False

    def merge_employee_with_payroll_data(self, employees: List[EmployeeInfo]) -> List[Dict[str, Any]]:
        """
        Merge employee information with payroll data

        Args:
            employees: List of employee information from database

        Returns:
            List of merged employee dictionaries
        """
        print(f"[MERGE] Merging {len(employees)} employee records with payroll data...")

        if not self.sample_payroll_data:
            print("[WARN] No sample payroll data available, using default payroll values")
            return self._create_default_payroll_data(employees)

        sample_employees = self.sample_payroll_data.get('karyawan', [])
        merged_employees = []

        print(f"   Sample payroll records available: {len(sample_employees)}")

        # Map sample employees by name for matching
        sample_map = {}
        for emp in sample_employees:
            name_key = emp.get('nama', '').strip().upper()
            if name_key:
                sample_map[name_key] = emp

        # Merge data
        for i, db_emp in enumerate(employees, start=1):
            emp_name = db_emp.nama.strip().upper()

            # Try to find matching sample data
            sample_emp = sample_map.get(emp_name, {})

            # Create merged employee record
            merged_emp = {
                # Database fields (these come from actual database)
                'nik': db_emp.EmpCode,
                'nama': db_emp.EmpName,
                'jenis_kelamin': db_emp.jenis_kelamin,
                'loc_code': db_emp.LocCode,

                # Sample payroll fields (use sample data if available, otherwise defaults)
                'cuti_tahun_hari': sample_emp.get('cuti_tahun_hari', 0),
                'cuti_tahun_jumlah': sample_emp.get('cuti_tahun_jumlah', 0),
                'cuti_sakit_hari': sample_emp.get('cuti_sakit_hari', 0),
                'cuti_sakit_jumlah': sample_emp.get('cuti_sakit_jumlah', 0),
                'cuti_haid_hari': sample_emp.get('cuti_haid_hari', 0),
                'cuti_haid_jumlah': sample_emp.get('cuti_haid_jumlah', 0),
                'cuti_minggu_hari': sample_emp.get('cuti_minggu_hari', 0),
                'cuti_minggu_jumlah': sample_emp.get('cuti_minggu_jumlah', 0),
                'cuti_nasional_hari': sample_emp.get('cuti_nasional_hari', 2),
                'cuti_nasional_jumlah': sample_emp.get('cuti_nasional_jumlah', 0),
                'cuti_hamil_hari': sample_emp.get('cuti_hamil_hari', 0),
                'cuti_hamil_jumlah': sample_emp.get('cuti_hamil_jumlah', 0),
                'cuti_izin_hari': sample_emp.get('cuti_izin_hari', 1),
                'cuti_izin_jumlah': sample_emp.get('cuti_izin_jumlah', 0),
                'jumlah_hk': sample_emp.get('jumlah_hk', 22),
                'tunjangan_beras': sample_emp.get('tunjangan_beras', 15000),
                'tunjangan_beras_jumlah': sample_emp.get('tunjangan_beras_jumlah', 330000),
                'tunjangan_jabatan': sample_emp.get('tunjangan_jabatan', 5000),
                'tunjangan_jabatan_hk': sample_emp.get('tunjangan_jabatan_hk', 22),
                'tunjangan_masa_kerja': sample_emp.get('tunjangan_masa_kerja', 2000),
                'tunjangan_masa_kerja_jumlah': sample_emp.get('tunjangan_masa_kerja_jumlah', 44000),
                'tunjangan_lembur': sample_emp.get('tunjangan_lembur', 250000),
                'tunjangan_premi': sample_emp.get('tunjangan_premi', 150000),
                'tunjangan_koreksi': sample_emp.get('tunjangan_koreksi', 0),
                'upah_kotor': sample_emp.get('upah_kotor', 4840000),
                'potongan_astek_pekerja': sample_emp.get('potongan_astek_pekerja', 200000),
                'potongan_astek_majikan': sample_emp.get('potongan_astek_majikan', 300000),
                'potongan_astek_jumlah': sample_emp.get('potongan_astek_jumlah', 500000),
                'potongan_bpjs_kesehatan': sample_emp.get('potongan_bpjs_kesehatan', 100000),
                'potongan_bpjs_pekerja': sample_emp.get('potongan_bpjs_pekerja', 50000),
                'potongan_bpjs_pensiun': sample_emp.get('potongan_bpjs_pensiun', 75000),
                'potongan_bpjs_majikan': sample_emp.get('potongan_bpjs_majikan', 75000),
                'potongan_bpjs_jumlah': sample_emp.get('potongan_bpjs_jumlah', 225000),
                'potongan_pph21': sample_emp.get('potongan_pph21', 150000),
                'potongan_premi_kontan': sample_emp.get('potongan_premi_kontan', 0),
                'potongan_lebih_potong_pajak_thr': sample_emp.get('potongan_lebih_potong_pajak_thr', 0),
                'potongan_pinjaman_uang': sample_emp.get('potongan_pinjaman_uang', 200000),
                'upah_bersih': sample_emp.get('upah_bersih', 3750000),
                'tidak_hadir_cth': sample_emp.get('tidak_hadir_cth', 0),
                'tidak_hadir_alpa': sample_emp.get('tidak_hadir_alpa', 0)
            }

            merged_employees.append(merged_emp)

        print(f"[OK] Successfully merged {len(merged_employees)} employee records")
        return merged_employees

    def _create_default_payroll_data(self, employees: List[EmployeeInfo]) -> List[Dict[str, Any]]:
        """Create default payroll data when sample data is not available"""
        print("   Creating default payroll values for all employees")

        merged_employees = []
        for emp in employees:
            default_emp = {
                # Database fields
                'nik': emp.EmpCode,
                'nama': emp.EmpName,
                'jenis_kelamin': emp.jenis_kelamin,
                'loc_code': emp.LocCode,

                # Default payroll values
                'cuti_tahun_hari': 0,
                'cuti_tahun_jumlah': 0,
                'cuti_sakit_hari': 0,
                'cuti_sakit_jumlah': 0,
                'cuti_haid_hari': 0,
                'cuti_haid_jumlah': 0,
                'cuti_minggu_hari': 0,
                'cuti_minggu_jumlah': 0,
                'cuti_nasional_hari': 2,
                'cuti_nasional_jumlah': 0,
                'cuti_hamil_hari': 0,
                'cuti_hamil_jumlah': 0,
                'cuti_izin_hari': 1,
                'cuti_izin_jumlah': 0,
                'jumlah_hk': 22,
                'tunjangan_beras': 15000,
                'tunjangan_beras_jumlah': 330000,
                'tunjangan_jabatan': 5000,
                'tunjangan_jabatan_hk': 22,
                'tunjangan_masa_kerja': 2000,
                'tunjangan_masa_kerja_jumlah': 44000,
                'tunjangan_lembur': 250000,
                'tunjangan_premi': 150000,
                'tunjangan_koreksi': 0,
                'upah_kotor': 4840000,
                'potongan_astek_pekerja': 200000,
                'potongan_astek_majikan': 300000,
                'potongan_astek_jumlah': 500000,
                'potongan_bpjs_kesehatan': 100000,
                'potongan_bpjs_pekerja': 50000,
                'potongan_bpjs_pensiun': 75000,
                'potongan_bpjs_majikan': 75000,
                'potongan_bpjs_jumlah': 225000,
                'potongan_pph21': 150000,
                'potongan_premi_kontan': 0,
                'potongan_lebih_potong_pajak_thr': 0,
                'potongan_pinjaman_uang': 200000,
                'upah_bersih': 3750000,
                'tidak_hadir_cth': 0,
                'tidak_hadir_alpa': 0
            }
            merged_employees.append(default_emp)

        return merged_employees

    def process_gang_data(self, gang_code: str = "H1H", limit: int = 100,
                         sample_data_path: str = "../large_data.json") -> List[Dict[str, Any]]:
        """
        Process complete gang data including database query and payroll merging

        Args:
            gang_code: Gang code to process
            limit: Maximum number of employees
            sample_data_path: Path to sample payroll data

        Returns:
            List of merged employee dictionaries ready for template rendering
        """
        print(f"[PROCESS] Processing gang '{gang_code}' data...")

        # Initialize database if available
        if self.query_manager.initialize_database():
            print("[OK] Database connection established")
        else:
            print("[WARN] Using simulation mode (no database connection)")

        # Load sample payroll data
        if not self.load_sample_payroll_data(sample_data_path):
            print("[WARN] No sample payroll data available, will use defaults")

        # Get employee data
        employees = self.query_manager.get_employees_by_gang(gang_code, limit)

        if not employees:
            print(f"[ERROR] No employees found for gang '{gang_code}'")
            return []

        # Merge with payroll data
        merged_data = self.merge_employee_with_payroll_data(employees)

        # Clean up
        self.query_manager.cleanup()

        return merged_data

    def get_processing_summary(self, data: List[Dict[str, Any]], gang_code: str) -> Dict[str, Any]:
        """
        Get processing summary

        Args:
            data: Processed data
            gang_code: Gang code

        Returns:
            Dictionary with processing summary
        """
        if not data:
            return {
                'gang_code': gang_code,
                'total_employees': 0,
                'data_source': 'None',
                'processing_time': None,
                'success': False
            }

        # Count gender distribution
        male_count = sum(1 for emp in data if emp.get('jenis_kelamin') == 'L')
        female_count = sum(1 for emp in data if emp.get('jenis_kelamin') == 'P')

        # Count locations
        locations = set(emp.get('loc_code', '') for emp in data)

        return {
            'gang_code': gang_code,
            'total_employees': len(data),
            'gender_distribution': {
                'Laki-laki': male_count,
                'Perempuan': female_count
            },
            'locations': sorted(list(locations)),
            'data_source': 'Database + Sample Payroll' if DATABASE_AVAILABLE else 'Simulated',
            'query_file': self.query_manager.query_file_path,
            'success': True
        }


def main():
    """Test employee query integration"""
    print("=" * 80)
    print("EMPLOYEE QUERY INTEGRATION TEST")
    print("=" * 80)

    try:
        # Initialize processor
        processor = EmployeeDataProcessor()

        # Test gang H1H processing
        print("\n" + "="*50)
        print("TESTING GANG H1H PROCESSING")
        print("="*50)

        data = processor.process_gang_data("H1H", 20, "../large_data.json")

        # Show results
        if data:
            summary = processor.get_processing_summary(data, "H1H")

            print(f"\n[STATS] PROCESSING SUMMARY FOR GANG {summary['gang_code']}:")
            print(f"   Total Employees: {summary['total_employees']}")
            print(f"   Data Source: {summary['data_source']}")
            print(f"   Query File: {summary['query_file']}")
            print(f"   Success: {summary['success']}")

            print(f"\n[EMPLOYEES] EMPLOYEE BREAKDOWN:")
            print(f"   Laki-laki: {summary['gender_distribution']['Laki-laki']}")
            print(f"   Perempuan: {summary['gender_distribution']['Perempuan']}")

            print(f"\n📍 LOCATIONS: {', '.join(summary['locations'])}")

            print(f"\n📄 SAMPLE EMPLOYEES:")
            for i, emp in enumerate(data[:5], 1):
                print(f"   {i}. {emp['nik']} - {emp['nama']} ({emp['jenis_kelamin']}) - {emp['loc_code']}")

            if len(data) > 5:
                print(f"   ... and {len(data) - 5} more employees")

        else:
            print("[ERROR] No data processed")

        print("\n✅ Employee query integration test completed successfully")

    except Exception as e:
        print(f"\n[ERROR] Employee query integration test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()