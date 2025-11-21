#!/usr/bin/env python3
"""
Script untuk testing multiple user credentials
"""
import pyodbc

def test_credentials():
    server = "10.0.0.110,1433"
    database = "db_ptrj"
    driver = "{ODBC Driver 17 for SQL Server}"

    # List of potential credentials to try
    credentials = [
        ("sa", "ptrj@123"),
        ("sa", "windows0819"),
        ("sa", "sa"),
        ("sa", "admin"),
        ("sa", "password"),
        ("ptrj", "ptrj@123"),
        ("admin", "ptrj@123"),
        ("rebinmas", "ptrj@123"),
    ]

    print("Testing Multiple Database Credentials")
    print("=" * 50)

    for username, password in credentials:
        print(f"\nTrying Username: {username}")
        print(f"Password: {'*' * len(password)}")

        try:
            conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=no;"
            conn = pyodbc.connect(conn_str, timeout=5)
            print(f"SUCCESS: Connection established with {username}")

            # Test query
            cursor = conn.cursor()
            cursor.execute("SELECT @@VERSION")
            version = cursor.fetchone()[0]
            print(f"SQL Server Version: {version[:50]}...")

            conn.close()
            print(f"SUCCESS: Connection closed properly")
            return username, password

        except pyodbc.Error as e:
            print(f"FAILED: {e.args[1] if len(e.args) > 1 else str(e)}")
            continue

    print(f"\nNo working credentials found!")
    return None, None

if __name__ == "__main__":
    username, password = test_credentials()
    if username:
        print(f"\nWorking credentials found: {username} / {password}")