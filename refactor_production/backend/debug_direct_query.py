#!/usr/bin/env python3
"""
Debug query yang digunakan SimplifiedHeaderService
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.services.database import Database
from database.services.queries import Queries

def debug_direct_query():
    """Debug query secara langsung"""
    print("=== DEBUGGING DIRECT QUERY ===")
    
    try:
        db = Database.instance()
        q = Queries()
        
        # Test exact query yang digunakan SimplifiedHeaderService
        gang_code = "A1H"
        month = 1
        year = 2024
        
        start_date = f"{year}-{str(month).zfill(2)}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{str(month+1).zfill(2)}-01"
        
        print(f"Parameters:")
        print(f"  Gang Code: {gang_code}")
        print(f"  Start Date: {start_date}")
        print(f"  End Date: {end_date}")
        print()
        
        # Test PREMI query dari JSON file
        sql_entry = q.get('premi', 'dynamic_headers_by_gang_month_optimized')
        if sql_entry and 'sql' in sql_entry:
            print(f"PREMI Query from JSON:")
            print(f"  {sql_entry['sql']}")
            print()
            
            rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])
            
            print(f"PREMI Results: {len(rows) if rows else 0} items")
            if rows:
                for i, row in enumerate(rows[:5]):
                    print(f"  {i+1}. {row[0]}")
            else:
                print("  No results found")
        else:
            print("ERROR: PREMI query not found in JSON")
        
        print()
        print("=" * 60)
        print()
        
        # Test POTONGAN query dari JSON file
        sql_entry = q.get('potongan', 'dynamic_headers_by_gang_month_optimized')
        if sql_entry and 'sql' in sql_entry:
            print(f"POTONGAN Query from JSON:")
            print(f"  {sql_entry['sql']}")
            print()
            
            rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])
            
            print(f"POTONGAN Results: {len(rows) if rows else 0} items")
            if rows:
                for i, row in enumerate(rows[:5]):
                    print(f"  {i+1}. {row[0]}")
            else:
                print("  No results found")
        else:
            print("ERROR: POTONGAN query not found in JSON")
        
        print()
        print("=" * 60)
        print()
        
        # Test manual query yang kita tahu berhasil
        print("MANUAL QUERY TEST (yang sebelumnya berhasil):")
        
        manual_premi_sql = """
        SELECT DISTINCT t.DocDesc 
        FROM PR_ADTRANS_ARC AS t 
        JOIN PR_ADTRANSLN_ARC AS ln ON t.ID = ln.MasterID 
        JOIN HR_GANGLN AS g ON g.GangMember = t.EmpCode 
        WHERE g.GangCode = ? 
        AND t.DocDate >= ? AND t.DocDate < ?
        AND COALESCE(ln.Amount,0) > 0 
        AND t.DocDesc IS NOT NULL 
        AND UPPER(t.DocDesc) NOT LIKE '%TUNJANGAN%' 
        AND UPPER(t.DocDesc) NOT LIKE '%BERAS%' 
        AND UPPER(t.DocDesc) NOT LIKE '%PPH%' 
        AND UPPER(t.DocDesc) NOT LIKE '%SPSI%'
        ORDER BY t.DocDesc
        """
        
        manual_rows = db.query_all(manual_premi_sql, [gang_code, start_date, end_date])
        
        print(f"MANUAL PREMI Results: {len(manual_rows) if manual_rows else 0} items")
        if manual_rows:
            for i, row in enumerate(manual_rows[:5]):
                print(f"  {i+1}. {row[0]}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_direct_query()
    if success:
        print("\n[OK] Direct query debug completed!")
    else:
        print("\n[ERROR] Direct query debug failed!")
        sys.exit(1)
