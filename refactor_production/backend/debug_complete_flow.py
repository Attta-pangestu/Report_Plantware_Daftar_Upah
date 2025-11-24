#!/usr/bin/env python3
"""
Debug complete flow
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.services.database import Database
from database.services.queries import Queries

def debug_complete_flow():
    """Debug complete flow"""
    print("=== DEBUGGING COMPLETE FLOW ===")
    
    try:
        db = Database.instance()
        q = Queries()
        
        gang_code = 'E2T'
        start_date = '2025-05-01'
        end_date = '2025-06-01'
        
        print(f"Testing: {gang_code}, May 2025")
        print("=" * 60)
        
        # 1. Check query in service
        sql_entry = q.get('premi', 'dynamic_headers_by_gang_month_optimized')
        print("1. Query from service:")
        print(f"   SQL: {sql_entry['sql'][:100]}...")
        print()
        
        # 2. Execute query
        print("2. Query results:")
        rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])
        print(f"   Total: {len(rows) if rows else 0} items")
        for i, row in enumerate(rows or []):
            print(f"   {i+1:2d}. {row[0]}")
        print()
        
        # 3. Check if there's any limit in result
        if rows:
            # Check direct query without any service layer
            direct_query = '''
            SELECT DISTINCT t.DocDesc
            FROM PR_ADTRANS_ARC AS t
            JOIN PR_ADTRANSLN_ARC AS ln ON t.ID = ln.MasterID
            JOIN HR_GANGLN AS g ON g.GangMember = t.EmpCode
            WHERE g.GangCode = ?
            AND t.DocDate >= ?
            AND t.DocDate < ?
            AND COALESCE(ln.Amount,0) > 0
            AND t.DocDesc IS NOT NULL
            ORDER BY t.DocDesc
            '''
            
            print("3. Direct query results:")
            direct_rows = db.query_all(direct_query, [gang_code, start_date, end_date])
            print(f"   Total: {len(direct_rows) if direct_rows else 0} items")
            for i, row in enumerate(direct_rows or []):
                print(f"   {i+1:2d}. {row[0]}")
            print()
            
            # 4. Compare results
            service_items = {row[0] for row in rows or []}
            direct_items = {row[0] for row in direct_rows or []}
            
            missing_in_service = direct_items - service_items
            extra_in_service = service_items - direct_items
            
            print("4. Comparison:")
            if missing_in_service:
                print(f"   Missing in service: {len(missing_in_service)} items")
                for item in missing_in_service:
                    print(f"     - {item}")
            
            if extra_in_service:
                print(f"   Extra in service: {len(extra_in_service)} items")
                for item in extra_in_service:
                    print(f"     - {item}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_complete_flow()
