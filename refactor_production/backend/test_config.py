#!/usr/bin/env python3
"""
Test remote database configuration
"""

from database.config.settings import get_db_config, connection_string
import pyodbc

def test_config():
    print("=== Testing Default Remote Configuration ===")
    print()

    config = get_db_config()
    print("Database Config:")
    for key, value in config.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(str(value))}")
        else:
            print(f"  {key}: {value}")

    print()
    print("Connection String (masked):")
    conn_str = connection_string()
    masked_str = conn_str.replace(config['password'], '***')
    print(masked_str)
    print()

    print("Testing connection...")
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES")
        count = cursor.fetchone()[0]
        print(f"SUCCESS! Connected to remote database with {count} tables")

        # Test some tables
        important_tables = ['employees', 'gangs', 'divisions']
        for table in important_tables:
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='{table}'")
            exists = cursor.fetchone()[0]
            if exists > 0:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                table_count = cursor.fetchone()[0]
                print(f"  Table '{table}': {table_count} records")
            else:
                print(f"  Table '{table}': Not found")

        conn.close()
        return True

    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    success = test_config()
    print()
    if success:
        print("SUCCESS: Remote configuration is working!")
    else:
        print("FAILED: Configuration test failed")