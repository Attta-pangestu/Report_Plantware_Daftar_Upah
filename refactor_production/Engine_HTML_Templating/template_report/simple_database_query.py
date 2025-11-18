#!/usr/bin/env python3
"""
Simple Database Query Manager for Employee Data
Based on the pattern used in daftar_upah_engine_real_database.py
"""

import json
import pyodbc
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class Employee:
    """Employee data structure"""
    nik: str
    nama: str
    jenis_kelamin: str
    LocCode: str
    gang_code: str


class SimpleEmployeeQueryManager:
    """Simple database query manager for employee data"""

    def __init__(self, query_file: str, config_file: str):
        self.query_file = Path(query_file)
        self.config_file = Path(config_file)
        self.query = self._load_query()
        self.db_config = self._load_config()

    def _load_query(self) -> str:
        """Load SQL query from file"""
        try:
            with open(self.query_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except Exception as e:
            print(f"[ERROR] Failed to load query from {self.query_file}: {e}")
            # Fallback query
            return '''
                SELECT
                    e."EmpCode" AS nik,
                    e."EmpName" AS nama,
                    CASE
                        WHEN e."Gender" = 1 THEN 'L'
                        WHEN e."Gender" = 2 THEN 'P'
                        ELSE 'L'
                    END AS jenis_kelamin,
                    e."LocCode" AS loc_code,
                    COALESCE(g."GangCode", e."LocCode") AS gang_code
                FROM "HR_EMPLOYEE" e
                LEFT JOIN "HR_GANGLN" g ON g."GangMember" = e."EmpCode"
                WHERE e."Status" = 'A'
                    AND (g."GangCode" = ? OR e."LocCode" = ? OR ? IS NULL)
                ORDER BY e."EmpName"
            '''

    def _load_config(self) -> Dict[str, Any]:
        """Load database configuration"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('database', {})
        except Exception as e:
            print(f"[ERROR] Failed to load config from {self.config_file}: {e}")
            # Fallback config
            return {
                "driver": "ODBC Driver 17 for SQL Server",
                "server": "localhost",
                "port": 1433,
                "username": "sa",
                "password": "windows0819",
                "database_name": "db_ptrj"
            }

    def _get_connection_string(self) -> str:
        """Build ODBC connection string"""
        cfg = self.db_config
        return f'DRIVER={{{cfg["driver"]}}};SERVER={cfg["server"]},{cfg["port"]};DATABASE={cfg["database_name"]};UID={cfg["username"]};PWD={cfg["password"]}'

    def get_employees_by_gang(self, gang_code: str = None, limit: int = 1000) -> List[Employee]:
        """Get employees by gang code with optional limit"""
        try:
            conn_str = self._get_connection_string()
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            print(f"[INFO] Querying employees for gang: {gang_code}")
            print(f"[INFO] Using query: {self.query[:100]}...")

            # Execute query with gang code parameter
            if gang_code:
                gang_code_upper = str(gang_code).strip().upper()
                cursor.execute(self.query, (gang_code_upper, gang_code_upper, gang_code_upper))
            else:
                # If no gang code specified, get all active employees
                all_query = '''
                    SELECT
                        e."EmpCode" AS nik,
                        e."EmpName" AS nama,
                        CASE
                            WHEN e."Gender" = 1 THEN 'L'
                            WHEN e."Gender" = 2 THEN 'P'
                            ELSE 'L'
                        END AS jenis_kelamin,
                        e."LocCode" AS loc_code,
                        e."LocCode" AS gang_code
                    FROM "HR_EMPLOYEE" e
                    WHERE e."Status" = 'A'
                    ORDER BY e."EmpName"
                '''
                cursor.execute(all_query)

            # Fetch results
            rows = cursor.fetchall()
            print(f"[INFO] Found {len(rows)} employee records")

            # Convert to Employee objects
            employees = []
            for row in rows:
                emp = Employee(
                    nik=str(row[0]).strip() if row[0] else '',
                    nama=str(row[1]).strip() if row[1] else '',
                    jenis_kelamin=str(row[2]).strip() if row[2] else 'L',
                    LocCode=str(row[3]).strip() if row[3] else '',
                    gang_code=str(row[4]).strip() if row[4] else ''
                )
                employees.append(emp)

            # Apply limit
            if limit and len(employees) > limit:
                employees = employees[:limit]
                print(f"[INFO] Limited to {limit} employees")

            cursor.close()
            conn.close()

            return employees

        except Exception as e:
            print(f"[ERROR] Failed to query employees: {e}")
            print(f"[ERROR] Connection string: {self._get_connection_string()}")
            return []

    def get_available_gangs(self) -> List[str]:
        """Get list of available gang codes"""
        try:
            conn_str = self._get_connection_string()
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            query = '''
                SELECT DISTINCT "GangCode" FROM "HR_GANGLN"
                WHERE "GangCode" IS NOT NULL AND "GangCode" != ''
                ORDER BY "GangCode"
            '''
            cursor.execute(query)
            rows = cursor.fetchall()

            gangs = [str(row[0]).strip() for row in rows if row[0]]
            cursor.close()
            conn.close()

            return gangs

        except Exception as e:
            print(f"[ERROR] Failed to get available gangs: {e}")
            return []

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn_str = self._get_connection_string()
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result and result[0] == 1
        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            return False