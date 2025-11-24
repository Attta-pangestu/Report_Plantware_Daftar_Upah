#!/usr/bin/env python3
"""
Debug exclude logic step by step
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.services.database import Database

def debug_exclude_logic():
    """Debug exclude logic step by step"""
    print("=== DEBUGGING EXCLUDE LOGIC STEP BY STEP ===")
    
    try:
        db = Database.instance()
        
        gang_code = 'E2T'
        start_date = '2025-05-01'
        end_date = '2025-06-01'
        
        print(f"Testing: {gang_code}, May 2025")
        print("=" * 60)
        
        # Get all items
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
        
        if not rows:
            print("No items found")
            return
        
        print("All items:")
        all_headers = [str(r[0]).strip() for r in rows if r and r[0]]
        for i, header in enumerate(all_headers):
            print(f"  {i+1:2d}. {header}")
        print()
        
        # Test exclude logic
        print("Testing exclude logic:")
        excluded_keywords = ['BERAS', 'PPH', 'SPSI']  # Exclude basic deductions, but NOT POTONGAN
        
        for i, header in enumerate(all_headers):
            header_upper = header.upper()
            
            # More precise exclude logic
            should_exclude = False
            
            # Exclude items starting with 'POTONGAN' (not containing)
            if header_upper.startswith('POTONGAN'):
                should_exclude = True
                print(f"  {i+1:2d}. {header} -> EXCLUDED (starts with POTONGAN)")
                continue
            
            # Exclude items containing specific keywords
            for keyword in excluded_keywords:
                if keyword in header_upper:
                    should_exclude = True
                    print(f"  {i+1:2d}. {header} -> EXCLUDED (contains {keyword})")
                    break
            
            if not should_exclude:
                print(f"  {i+1:2d}. {header} -> INCLUDED")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_exclude_logic()
