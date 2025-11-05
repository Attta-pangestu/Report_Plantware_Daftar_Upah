#!/usr/bin/env python3
"""
Database Integration Module for Daftar Upah Template
Handles employee data extraction from SQL Server database
"""

import json
import pyodbc
from pathlib import Path
from typing import List, Dict, Any, Optional

class DatabaseIntegration:
    """
    Database integration class for fetching employee data
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize database connection

        Args:
            config_path: Path to database configuration file
        """
        if config_path is None:
            # Default to project config file
            config_path = Path(r"D:\Gawean Rebinmas\Monitoring Database\Plantware_Auto_Report\Daftar_Upah_Reporting\Explore_database\config.json")

        self.config_path = Path(config_path)
        self.connection = None
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration from JSON file"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config['database']
        except Exception as e:
            raise Exception(f"Failed to load database config: {e}")

    def connect(self) -> bool:
        """
        Establish database connection

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Build connection string
            conn_str = (
                f"DRIVER={{{self.config['driver']}}};"
                f"SERVER={self.config['server']},{self.config['port']};"
                f"DATABASE={self.config['database_name']};"
                f"UID={self.config['username']};"
                f"PWD={self.config['password']};"
                f"TrustConnection={'yes' if self.config.get('trusted_connection', False) else 'no'};"
                f"Encrypt={'yes' if self.config.get('encrypt', False) else 'no'}"
            )

            self.connection = pyodbc.connect(conn_str)
            print(f"✓ Connected to database: {self.config['database_name']}")
            return True

        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("✓ Database connection closed")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results as list of dictionaries

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            List of dictionaries representing rows
        """
        if not self.connection:
            raise Exception("Database connection not established")

        try:
            cursor = self.connection.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names
            columns = [column[0] for column in cursor.description]

            # Fetch all rows and convert to dictionaries
            rows = []
            for row in cursor.fetchall():
                row_dict = dict(zip(columns, row))
                rows.append(row_dict)

            print(f"✓ Query executed successfully: {len(rows)} rows returned")
            return rows

        except Exception as e:
            print(f"✗ Query execution failed: {e}")
            raise

    def get_employee_data_by_gang(self, gang_code: str = 'H1H', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get employee data for specific gang

        Args:
            gang_code: Gang code filter (default: 'H1H')
            limit: Maximum number of records to fetch

        Returns:
            List of employee dictionaries with mapped fields
        """
        query = f"""
        SELECT TOP {limit}
            "HR_EMPLOYEE"."EmpCode",
            "HR_EMPLOYEE"."EmpName",
            "HR_EMPLOYEE"."Gender",
            "HR_EMPLOYEE"."LocCode"
        FROM "HR_EMPLOYEE"
        JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
        WHERE "HR_GANGLN"."GangCode" = ?
        ORDER BY "HR_EMPLOYEE"."EmpName"
        """

        try:
            rows = self.execute_query(query, (gang_code,))

            # Map fields to template format
            mapped_employees = []
            for row in rows:
                employee = {
                    'nik': row['EmpCode'],
                    'nama': row['EmpName'],
                    'jenis_kelamin': self._map_gender(row['Gender']),
                    'loc_code': row['LocCode']
                }
                mapped_employees.append(employee)

            print(f"✓ Retrieved {len(mapped_employees)} employees for gang {gang_code}")
            return mapped_employees

        except Exception as e:
            print(f"✗ Failed to get employee data: {e}")
            return []

    def _map_gender(self, gender_value) -> str:
        """
        Map database gender value to template format

        Args:
            gender_value: Gender value from database (1 or 0)

        Returns:
            str: 'L' for male (1), 'P' for female (0)
        """
        try:
            if gender_value == 1 or str(gender_value).upper() == 'L' or str(gender_value).upper() == 'M':
                return 'L'
            elif gender_value == 0 or str(gender_value).upper() == 'P' or str(gender_value).upper() == 'F':
                return 'P'
            else:
                print(f"⚠ Unknown gender value: {gender_value}, defaulting to 'L'")
                return 'L'
        except:
            return 'L'

    def get_all_gangs(self) -> List[str]:
        """
        Get list of all available gang codes

        Returns:
            List of gang codes
        """
        query = """
        SELECT DISTINCT "GangCode"
        FROM "HR_GANGLN"
        ORDER BY "GangCode"
        """

        try:
            rows = self.execute_query(query)
            gang_codes = [row['GangCode'] for row in rows]
            print(f"✓ Found {len(gang_codes)} gangs: {', '.join(gang_codes)}")
            return gang_codes
        except Exception as e:
            print(f"✗ Failed to get gang list: {e}")
            return []

    def test_connection(self) -> bool:
        """
        Test database connection with simple query

        Returns:
            bool: True if test successful
        """
        try:
            query = "SELECT 1 as test, @@VERSION as version"
            rows = self.execute_query(query)
            if rows:
                print(f"✓ Database test successful")
                print(f"  Server version: {rows[0]['version'][:50]}...")
                return True
            return False
        except Exception as e:
            print(f"✗ Database test failed: {e}")
            return False

def main():
    """Test database integration"""
    print("=" * 60)
    print("DATABASE INTEGRATION TEST")
    print("=" * 60)

    db = DatabaseIntegration()

    # Test connection
    if not db.connect():
        print("❌ Cannot proceed without database connection")
        return

    # Test basic query
    if not db.test_connection():
        print("❌ Database test failed")
        db.disconnect()
        return

    # Get available gangs
    gangs = db.get_all_gangs()
    if not gangs:
        print("❌ No gangs found")
        db.disconnect()
        return

    # Get employee data for first gang
    test_gang = gangs[0]
    print(f"\n📋 Getting employee data for gang: {test_gang}")
    employees = db.get_employee_data_by_gang(test_gang, limit=5)

    if employees:
        print(f"\n📄 Sample employee data:")
        for i, emp in enumerate(employees[:3], 1):
            print(f"  {i}. {emp['nik']} - {emp['nama']} ({emp['jenis_kelamin']})")

    db.disconnect()
    print("\n✅ Database integration test completed")

if __name__ == "__main__":
    main()