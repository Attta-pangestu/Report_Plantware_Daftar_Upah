#!/usr/bin/env python3
"""
Script untuk testing koneksi ke remote database server
"""
import pyodbc
from database.config.settings import connection_string, get_db_config

def test_connection():
    print("Testing Remote Database Connection")
    print("=" * 50)

    # Get config
    config = get_db_config('remote')
    print(f"Server: {config['server']}")
    print(f"Port: {config['port']}")
    print(f"Database: {config['database_name']}")
    print(f"Username: {config['username']}")
    print(f"Password: {'*' * len(config['password']) if config['password'] else '(empty)'}")
    print(f"Trusted Connection: {config['trusted_connection']}")
    print()

    # Test connection string
    conn_str = connection_string('remote')
    print(f"Connection String: {conn_str}")
    print()

    # Try to connect
    try:
        print("Attempting to connect...")
        conn = pyodbc.connect(conn_str, timeout=10)
        print("Connection successful!")

        # Test query
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"SQL Server Version: {version[:100]}...")

        # Test database access
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
        table_count = cursor.fetchone()[0]
        print(f"Total Tables: {table_count}")

        # Test employee table if exists
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='employees'")
        if cursor.fetchone()[0] > 0:
            cursor.execute("SELECT COUNT(*) FROM employees")
            emp_count = cursor.fetchone()[0]
            print(f"Total Employees: {emp_count}")

        conn.close()
        print("Connection closed successfully")

    except pyodbc.Error as e:
        print(f"Connection failed: {e}")
        print(f"Error Code: {e.args[0]}")
        if len(e.args) > 1:
            print(f"Error Message: {e.args[1]}")
        return False

    return True

if __name__ == "__main__":
    test_connection()