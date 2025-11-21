#!/usr/bin/env python3
"""
Script Test Koneksi Remote SQL Server
Server: 10.0.0.110,1433
Username: sa
Password: ptrj@123
Database: db_ptrj
"""

import pyodbc
import socket
import sys
from datetime import datetime

def test_network_connection():
    """Test koneksi jaringan ke server"""
    print("🔍 Testing Network Connection")
    print("=" * 50)

    server = "10.0.0.110"
    port = 1433

    try:
        # Test ping
        print(f"Pinging {server}...")
        result = socket.create_connection((server, port), timeout=5)
        print(f"✅ Network connection successful to {server}:{port}")
        result.close()
        return True
    except socket.error as e:
        print(f"❌ Network connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Network error: {e}")
        return False

def test_sql_connection():
    """Test koneksi SQL Server"""
    print("\n🔍 Testing SQL Server Connection")
    print("=" * 50)

    server = "10.0.0.110,1433"
    database = "db_ptrj"
    username = "sa"
    password = "ptrj@123"
    driver = "{ODBC Driver 17 for SQL Server}"

    # Connection string
    conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};Encrypt=no;"

    print(f"Server: {server}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")
    print(f"Driver: {driver}")
    print()

    try:
        print("Attempting to connect...")
        conn = pyodbc.connect(conn_str, timeout=10)
        print("✅ SQL Server connection successful!")

        # Test query
        cursor = conn.cursor()

        # Get SQL Server version
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        print(f"📊 SQL Server Version: {version[:80]}...")

        # Get database name
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f"🗄️ Connected Database: {db_name}")

        # Count tables
        cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
        table_count = cursor.fetchone()[0]
        print(f"📋 Total Tables: {table_count}")

        # Test specific tables
        important_tables = ['employees', 'gangs', 'divisions']
        for table in important_tables:
            cursor.execute(f"SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='{table}'")
            exists = cursor.fetchone()[0]
            if exists > 0:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Table '{table}': {count} records")
            else:
                print(f"❌ Table '{table}': Not found")

        # Test sample query
        try:
            cursor.execute("SELECT TOP 1 * FROM employees ORDER BY NEWID()")
            sample = cursor.fetchone()
            if sample:
                print("✅ Sample data query successful")
        except:
            print("⚠️ Cannot query sample data (table might be empty)")

        conn.close()
        print("✅ Connection closed successfully")
        return True

    except pyodbc.Error as e:
        print(f"❌ SQL Server connection failed: {e}")
        print(f"Error Code: {e.args[0]}")
        if len(e.args) > 1:
            error_msg = e.args[1]
            print(f"Error Message: {error_msg}")

            # Specific error analysis
            if "18456" in str(e):
                print("💡 This is a login error. Possible causes:")
                print("   - Username or password is incorrect")
                print("   - SQL Server Authentication is disabled")
                print("   - 'sa' account is disabled")
            elif "08001" in str(e):
                print("💡 This is a connection error. Possible causes:")
                print("   - Server is not running")
                print("   - Firewall blocking the connection")
                print("   - SQL Server port is not 1433")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_different_credentials():
    """Test dengan beberapa kredensial alternatif"""
    print("\n🔍 Testing Alternative Credentials")
    print("=" * 50)

    server = "10.0.0.110,1433"
    database = "db_ptrj"
    driver = "{ODBC Driver 17 for SQL Server}"

    # List of alternative credentials to try
    alternatives = [
        {"username": "sa", "password": "ptrj@123"},
        {"username": "sa", "password": "admin"},
        {"username": "sa", "password": "password"},
        {"username": "sa", "password": "sa"},
        {"username": "admin", "password": "ptrj@123"},
        {"username": "ptrj", "password": "ptrj@123"},
    ]

    for i, cred in enumerate(alternatives, 1):
        print(f"\n{i}. Testing {cred['username']}/{'*' * len(cred['password'])}")

        conn_str = f"DRIVER={driver};SERVER={server};DATABASE={database};UID={cred['username']};PWD={cred['password']};Encrypt=no;"

        try:
            conn = pyodbc.connect(conn_str, timeout=5)
            print(f"   ✅ SUCCESS: Connection established!")
            conn.close()
            return cred
        except pyodbc.Error as e:
            print(f"   ❌ FAILED: {str(e)[:100]}...")
            continue

    print(f"\n❌ No working credentials found!")
    return None

def generate_connection_script():
    """Generate script untuk koneksi yang berhasil"""
    print("\n📝 Generating Connection Script")
    print("=" * 50)

    script_content = '''# Connection String yang Berhasil
import pyodbc

conn_str = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=10.0.0.110,1433;DATABASE=db_ptrj;UID=sa;PWD=ptrj@123;Encrypt=no;"

# Test connection
try:
    conn = pyodbc.connect(conn_str)
    print("✅ Connection successful!")

    # Sample query
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM employees")
    count = cursor.fetchone()[0]
    print(f"Total employees: {count}")

    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
'''

    with open("connection_script.py", "w") as f:
        f.write(script_content)

    print("✅ Connection script generated: connection_script.py")

def main():
    """Main function"""
    print("🚀 REMOTE SQL SERVER CONNECTION TEST")
    print("Server: 10.0.0.110,1433")
    print("Username: sa")
    print("Password: ptrj@123")
    print("Database: db_ptrj")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Test network
    network_ok = test_network_connection()

    if not network_ok:
        print("\n❌ Network connection failed. Please check:")
        print("   - Server is reachable")
        print("   - Port 1433 is open")
        print("   - Firewall settings")
        return False

    # Step 2: Test SQL connection
    sql_ok = test_sql_connection()

    if sql_ok:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Remote SQL Server connection is working properly!")
        generate_connection_script()
        return True
    else:
        # Step 3: Test alternative credentials
        print("\n🔄 Trying alternative credentials...")
        working_cred = test_different_credentials()

        if working_cred:
            print(f"\n🎉 FOUND WORKING CREDENTIALS!")
            print(f"✅ Username: {working_cred['username']}")
            print(f"✅ Password: {'*' * len(working_cred['password'])}")
            return True
        else:
            print("\n❌ ALL CONNECTION TESTS FAILED!")
            print("\n💡 Troubleshooting steps:")
            print("1. Check if SQL Server is running on 10.0.0.110")
            print("2. Verify SQL Server Authentication is enabled (mixed mode)")
            print("3. Ensure 'sa' account is enabled and password is correct")
            print("4. Check firewall settings on both client and server")
            print("5. Verify TCP/IP is enabled in SQL Server Configuration")
            return False

if __name__ == "__main__":
    success = main()
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if success:
        print("🎯 RESULT: SUCCESS - Remote connection is working!")
        sys.exit(0)
    else:
        print("❌ RESULT: FAILED - Check troubleshooting steps above")
        sys.exit(1)