#!/usr/bin/env python3
"""
Quick Test Koneksi Remote SQL Server
"""

import pyodbc

def quick_test():
    print("QUICK CONNECTION TEST")
    print("=" * 30)

    server = "10.0.0.110,1433"
    database = "db_ptrj"
    username = "sa"
    password = "ptrj@123"

    conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=no;"

    print(f"Server: {server}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print()

    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        print("CONNECTION SUCCESSFUL!")

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES")
        table_count = cursor.fetchone()[0]
        print(f"Total tables: {table_count}")

        conn.close()
        return True

    except Exception as e:
        print(f"CONNECTION FAILED: {e}")
        return False

if __name__ == "__main__":
    if quick_test():
        print("\nRemote database is accessible!")
    else:
        print("\nCheck:")
        print("1. Server is running")
        print("2. Credentials are correct")
        print("3. Network connection")
        print("4. SQL Server authentication mode")

    print("\nTest completed.")