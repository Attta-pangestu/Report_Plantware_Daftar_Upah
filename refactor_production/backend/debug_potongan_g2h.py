#!/usr/bin/env python3
"""
Debug script to investigate why dynamic potongan values are zero for G2H, May 2025.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.services.database import Database
from database.services.queries import Queries

def debug_potongan_data():
    """Debug potongan data for G2H, May 2025."""
    print("DEBUG: Potongan Data Investigation for G2H, May 2025")
    print("=" * 60)

    gang_code = "G2H"
    month = 5
    year = 2025

    try:
        db = Database.instance()
        q = Queries()

        # Date range for May 2025
        start_date = f"{year}-{str(month).zfill(2)}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{str(month+1).zfill(2)}-01"

        print(f"Gang: {gang_code}")
        print(f"Period: {start_date} to {end_date}")
        print()

        # 1. Test the filtered query used for dynamic headers
        print("1. Testing filtered query (dynamic_potongan_headers_filtered):")
        sql_entry = q.get('potongan', 'dynamic_potongan_headers_filtered')

        if sql_entry and 'sql' in sql_entry:
            print(f"SQL: {sql_entry['sql'][:100]}...")
            rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])

            print(f"Found {len(rows) if rows else 0} distinct potongan types:")
            if rows:
                for i, row in enumerate(rows):
                    print(f"  {i+1}. {row[0]}")
            else:
                print("  No results found")
        print()

        # 2. Test query with amounts to see if there's actual data
        print("2. Testing query with amounts (potongan_headers_by_month):")
        sql_entry2 = q.get('potongan', 'potongan_headers_by_month')

        if sql_entry2 and 'sql' in sql_entry2:
            print(f"SQL: {sql_entry2['sql'][:100]}...")
            rows2 = db.query_all(sql_entry2['sql'], [gang_code, start_date, end_date])

            print(f"Found {len(rows2) if rows2 else 0} potongan types with amounts:")
            if rows2:
                for i, row in enumerate(rows2):
                    doc_desc = row[0]
                    total_amount = row[1] if len(row) > 1 else 0
                    print(f"  {i+1}. {doc_desc}: {total_amount}")
            else:
                print("  No results found")
        print()

        # 3. Test a broader query to see all potongan transactions
        print("3. Testing broader query (dynamic_headers_by_gang_month_optimized):")
        sql_entry3 = q.get('potongan', 'dynamic_headers_by_gang_month_optimized')

        if sql_entry3 and 'sql' in sql_entry3:
            print(f"SQL: {sql_entry3['sql'][:100]}...")
            rows3 = db.query_all(sql_entry3['sql'], [gang_code, start_date, end_date])

            print(f"Found {len(rows3) if rows3 else 0} broader potongan results:")
            if rows3:
                for i, row in enumerate(rows3[:10]):  # Limit to first 10
                    print(f"  {i+1}. {row[0]}")
                if len(rows3) > 10:
                    print(f"  ... and {len(rows3) - 10} more")
            else:
                print("  No results found")
        print()

        # 4. Check specific potongan items that should have data
        print("4. Checking specific potongan items:")
        specific_items = [
            "POTONGAN ALAT PANEN",
            "POTONGAN PREMI",
            "POTONGAN PREMI HARVESTING"
        ]

        # Get a more detailed query for specific items
        detailed_sql = """
        SELECT DISTINCT
            t.EmpCode,
            e.EmpName,
            t.DocDesc,
            ln.Amount,
            COUNT(*) as transaction_count
        FROM "PR_ADTRANS_ARC" AS t
        JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
        LEFT JOIN "HR_EMPLOYEE" e ON t.EmpCode = e.EmpCode
        WHERE t.EmpCode IN (
            SELECT "HR_EMPLOYEE"."EmpCode"
            FROM "HR_EMPLOYEE"
            JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
            WHERE "HR_GANGLN"."GangCode" = ?
        )
        AND t.DocDate >= ?
        AND t.DocDate < ?
        AND t.DocDesc LIKE 'POT%'
        AND (
            t.DocDesc = ? OR t.DocDesc = ? OR t.DocDesc = ?
        )
        GROUP BY t.EmpCode, e.EmpName, t.DocDesc, ln.Amount
        ORDER BY t.DocDesc, t.EmpCode
        """

        for item in specific_items:
            print(f"\n  Checking: {item}")
            item_rows = db.query_all(detailed_sql, [gang_code, start_date, end_date, item, item, item])

            if item_rows:
                total_amount = sum(row[3] if len(row) > 3 else 0 for row in item_rows)
                emp_count = len(set(row[0] for row in item_rows))
                print(f"    - Found {len(item_rows)} transactions for {emp_count} employees")
                print(f"    - Total amount: {total_amount}")

                # Show first few examples
                for i, row in enumerate(item_rows[:3]):
                    emp_code = row[0]
                    emp_name = row[1] if len(row) > 1 else "Unknown"
                    amount = row[3] if len(row) > 3 else 0
                    print(f"      Example {i+1}: {emp_code} - {emp_name} - {amount}")
            else:
                print(f"    - No transactions found")

        return True

    except Exception as e:
        print(f"Error during debug: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_potongan_data()
    if success:
        print("\nDebug completed successfully!")
    else:
        print("\nDebug failed!")