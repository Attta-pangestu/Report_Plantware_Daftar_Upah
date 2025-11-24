#!/usr/bin/env python3
"""
Debug filtering logic
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.services.database import Database

def debug_filtering():
    """Debug why POTONGAN PPH 21 is not excluded"""
    try:
        db = Database.instance()
        
        gang_code = 'E2T'
        start_date = '2025-05-01'
        end_date = '2025-06-01'
        
        print(f"Debugging filtering for {gang_code}, May 2025")
        print("=" * 60)
        
        # Query untuk semua items
        query = '''
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
        
        rows = db.query_all(query, [gang_code, start_date, end_date])
        print(f"All items in DB: {len(rows) if rows else 0}")
        for i, row in enumerate(rows or []):
            print(f"  {i+1:2d}. {row[0]}")
        
        print("\n" + "=" * 60)
        print("TESTING FILTERING LOGIC:")
        
        excluded_keywords = ['BERAS', 'PPH', 'SPSI', 'POTONGAN']
        
        for i, row in enumerate(rows or []):
            header = row[0]
            header_upper = header.upper()
            
            # Test filtering logic
            should_exclude = any(keyword in header_upper for keyword in excluded_keywords)
            
            print(f"  {i+1:2d}. {header}")
            print(f"      UPPERCASE: {header_upper}")
            print(f"      Should exclude: {should_exclude}")
            
            if should_exclude:
                found_keywords = [keyword for keyword in excluded_keywords if keyword in header_upper]
                print(f"      Found keywords: {found_keywords}")
            print()
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_filtering()
