#!/usr/bin/env python3
"""
Simple Database Query Integration
Direct database connection using pyodbc without complex framework
"""

import json
import sys
import pyodbc
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class EmployeeInfo:
    """Employee information from database"""
    EmpCode: str
    EmpName: str
    Gender: int
    LocCode: str
    GangCode: str  # Added GangCode
    jenis_kelamin: str  # Mapped gender (L/P)
    nik: str  # EmpCode mapped to nik
    nama: str  # EmpName mapped to nama


class SimpleDatabaseQuery:
    """Simple database query executor"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.connection = None
        self.config = None

    def load_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            return self.config['database']
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            return {}

    def connect(self) -> bool:
        """Connect to database"""
        try:
            db_config = self.load_config()

            # Create connection string
            conn_str = (
                f'DRIVER={{{db_config["driver"]}}};'
                f'SERVER={db_config["server"]},{db_config["port"]};'
                f'DATABASE={db_config["database_name"]};'
                f'UID={db_config["username"]};'
                f'PWD={db_config["password"]};'
                f'TrustConnection=no;Encrypt=no'
            )

            print(f"[DATABASE] Connecting to {db_config['server']}:{db_config['port']}/{db_config['database_name']}...")

            self.connection = pyodbc.connect(conn_str, timeout=10)
            print("[OK] Database connection successful!")
            return True

        except Exception as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False

    def execute_query(self, query: str, params: List[str] = None) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        try:
            if not self.connection:
                if not self.connect():
                    return []

            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names
            columns = [column[0] for column in cursor.description]

            # Fetch all rows
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            results = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    row_dict[columns[i]] = value
                results.append(row_dict)

            return results

        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("[OK] Database connection closed")


class SimpleEmployeeQueryManager:
    """Simple employee query manager"""

    def __init__(self, query_file_path: str, config_path: str):
        self.query_file_path = Path(query_file_path)
        self.config_path = config_path
        self.db = SimpleDatabaseQuery(config_path)
        self.query_template = ""
        self._load_query_template()

    def _load_query_template(self) -> str:
        """Load SQL query from file"""
        try:
            with open(self.query_file_path, 'r', encoding='utf-8') as f:
                self.query_template = f.read().strip()
            print(f"[OK] Query template loaded from: {self.query_file_path}")
            return self.query_template
        except Exception as e:
            print(f"[ERROR] Failed to load query template: {e}")
            return ""

    def _map_gender(self, gender_value) -> str:
        """Map database gender value to template format"""
        # Convert to int to handle any type issues
        try:
            gender_int = int(gender_value)
            if gender_int == 1:
                return 'L'  # Laki-laki
            elif gender_int == 2:
                return 'P'  # Perempuan
            else:
                print(f"[WARN] Unknown gender value: {gender_value} (type: {type(gender_value)}), defaulting to 'L'")
                return 'L'  # Default
        except (ValueError, TypeError) as e:
            print(f"[WARN] Error converting gender value: {gender_value} ({type(gender_value)}): {e}, defaulting to 'L'")
            return 'L'  # Default

    def get_employees_by_gang(self, gang_code: str = "H1H", limit: int = 100) -> List[EmployeeInfo]:
        """Get employees by gang code using the SQL query"""
        print(f"[QUERY] Getting employees for gang '{gang_code}' (limit: {limit})")

        if not self.query_template:
            print("[ERROR] No query template available")
            return []

        try:
            # Modify query to use specified limit and gang code
            query = self.query_template.replace("TOP 100", f"TOP {limit}").replace("'H1H'", f"'{gang_code}'")

            # Add GangCode to SELECT if not already there
            if '"HR_GANGLN"."GangCode"' not in query:
                # Replace EmpName line to add GangCode
                query = query.replace(
                    '"HR_EMPLOYEE"."EmpName",',
                    '"HR_EMPLOYEE"."EmpName",\n    "HR_GANGLN"."GangCode",'
                )

            # Add ORDER BY if not present
            if "ORDER BY" not in query:
                query += f' ORDER BY "HR_EMPLOYEE"."EmpName"'

            print(f"[QUERY] Executing query: {query[:100]}...")

            # Execute query (no parameters needed, gang_code is already in query)
            results = self.db.execute_query(query)

            if results:
                employees = []
                for row in results:
                    employee = EmployeeInfo(
                        EmpCode=row['EmpCode'],
                        EmpName=row['EmpName'],
                        Gender=row['Gender'],
                        LocCode=row.get('LocCode', ''),
                        GangCode=row.get('GangCode', gang_code),  # Get GangCode from query
                        jenis_kelamin=self._map_gender(row['Gender']),
                        nik=row['EmpCode'],
                        nama=row['EmpName']
                    )
                    employees.append(employee)

                print(f"[OK] Retrieved {len(employees)} employees from database")
                return employees
            else:
                print("[ERROR] No results from query")
                return []

        except Exception as e:
            print(f"[ERROR] Database query failed: {e}")
            return []

    def cleanup(self):
        """Cleanup database connection"""
        self.db.close()


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Query employee data for specific gang')
    parser.add_argument('--gang', required=True, help='GangCode to query (e.g., H1H, H2A, etc.)')
    parser.add_argument('--limit', type=int, default=10, help='Number of employees to retrieve (default: 10)')
    parser.add_argument('--verbose', action='store_true', help='Show detailed output')

    args = parser.parse_args()

    print("=" * 60)
    print("SIMPLE DATABASE QUERY")
    print("=" * 60)

    # Paths
    query_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Engine_HTML_Templating/template_report/query/get_detail_emp_each_gang.sql"
    config_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json"

    # Create query manager
    query_manager = SimpleEmployeeQueryManager(query_file, config_file)

    # Query employees
    print(f"\n[QUERY] Querying employees for gang {args.gang} (limit: {args.limit})...")
    employees = query_manager.get_employees_by_gang(args.gang, args.limit)

    if employees:
        print(f"\n[SUCCESS] Found {len(employees)} employees:")
        for i, emp in enumerate(employees, 1):
            if args.verbose:
                print(f"  {i}. {emp.nik} - {emp.nama} ({emp.jenis_kelamin}) - {emp.LocCode} - Gang: {emp.GangCode}")
            else:
                print(f"  {i}. {emp.nik} - {emp.nama} ({emp.jenis_kelamin}) - {emp.LocCode}")

        # Summary statistics
        print(f"\n[SUMMARY] Gang: {args.gang}")
        print(f"         Total Employees: {len(employees)}")
        print(f"         Male (L): {sum(1 for e in employees if e.jenis_kelamin == 'L')}")
        print(f"         Female (P): {sum(1 for e in employees if e.jenis_kelamin == 'P')}")

        # Show unique LocCodes
        loc_codes = list(set(emp.LocCode for emp in employees if emp.LocCode))
        print(f"         LocCodes: {', '.join(sorted(loc_codes))}")

    else:
        print(f"\n[ERROR] No employees found for gang {args.gang}")

    # Cleanup
    query_manager.cleanup()
    print("\n[OK] Query completed")


def test_simple_query():
    """Test simple database query (legacy function)"""
    print("=" * 60)
    print("SIMPLE DATABASE QUERY TEST")
    print("=" * 60)

    # Paths
    query_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Engine_HTML_Templating/template_report/query/get_detail_emp_each_gang.sql"
    config_file = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json"

    # Create query manager
    query_manager = SimpleEmployeeQueryManager(query_file, config_file)

    # Test query
    print(f"\n[TEST] Querying employees for gang H1H...")
    employees = query_manager.get_employees_by_gang("H1H", 10)

    if employees:
        print(f"\n[SUCCESS] Found {len(employees)} employees:")
        for i, emp in enumerate(employees, 1):
            print(f"  {i}. {emp.nik} - {emp.nama} ({emp.jenis_kelamin}) - {emp.LocCode}")
    else:
        print("\n[ERROR] No employees found")

    # Cleanup
    query_manager.cleanup()
    print("\n[OK] Test completed")


if __name__ == "__main__":
    main()