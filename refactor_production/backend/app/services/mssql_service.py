import pyodbc
from typing import List, Dict, Any, Optional
from pathlib import Path
from database.config.settings import get_db_config

class MSSQLService:
    def __init__(self, config_path: str = None):
        self.db_config = get_db_config()
        self._connection = None

    def get_connection_string(self) -> str:
        """Build ODBC connection string"""
        driver = self.db_config['driver']
        server = self.db_config['server']
        port = self.db_config['port']
        database = self.db_config['database_name']
        username = self.db_config['username']
        password = self.db_config['password']
        trusted_connection = self.db_config.get('trusted_connection', False)
        encrypt = self.db_config.get('encrypt', False)

        conn_str = f"DRIVER={{{driver}}};SERVER={server},{port};DATABASE={database};"

        if trusted_connection:
            conn_str += "Trusted_Connection=yes;"
        else:
            conn_str += f"UID={username};PWD={password};"

        if encrypt:
            conn_str += "Encrypt=yes;"
        else:
            conn_str += "Encrypt=no;"

        return conn_str

    def get_connection(self):
        """Get database connection"""
        if self._connection is None:
            try:
                self._connection = pyodbc.connect(self.get_connection_string())
                return self._connection
            except Exception as e:
                raise Exception(f"Failed to connect to database: {e}")
        return self._connection

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dictionaries"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Get column names
            columns = [column[0] for column in cursor.description]

            # Fetch all rows and convert to list of dictionaries
            results = []
            for row in cursor.fetchall():
                result_dict = {}
                for i, value in enumerate(row):
                    # Handle None values and convert to appropriate types
                    if value is None:
                        result_dict[columns[i]] = None
                    elif isinstance(value, str):
                        result_dict[columns[i]] = value.strip() if value.strip() else None
                    else:
                        result_dict[columns[i]] = value
                results.append(result_dict)

            return results

        except Exception as e:
            raise Exception(f"Failed to execute query: {e}")
        finally:
            if 'cursor' in locals():
                cursor.close()

    def get_employees_by_gang(self, gang_code: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get employees by gang code using the same query as the reference implementation"""
        query = '''
            SELECT TOP {limit}
                "HR_EMPLOYEE"."EmpCode",
                "HR_EMPLOYEE"."EmpName",
                "HR_EMPLOYEE"."Gender",
                "HR_EMPLOYEE"."LocCode"
            FROM "HR_EMPLOYEE"
            JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
            WHERE "HR_GANGLN"."GangCode" = ?
            ORDER BY "HR_EMPLOYEE"."EmpName"
        '''.format(limit=limit)

        return self.execute_query(query, (gang_code,))

    def get_all_gangs(self) -> List[Dict[str, Any]]:
        """Get all available gang codes"""
        query = '''
            SELECT DISTINCT
                "HR_GANGLN"."GangCode",
                COUNT("HR_GANGLN"."GangMember") as member_count
            FROM "HR_GANGLN"
            GROUP BY "HR_GANGLN"."GangCode"
            ORDER BY "HR_GANGLN"."GangCode"
        '''

        return self.execute_query(query)

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False

    def close_connection(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

# Global MSSQL service instance
mssql_service = MSSQLService()
