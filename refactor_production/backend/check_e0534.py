#!/usr/bin/env python3
"""
Check E0534 actual PREMI data
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.services.database import Database

def check_e0534():
    """Check E0534 actual PREMI data"""
    try:
        db = Database.instance()
        
        query = '''
        SELECT DISTINCT t.EmpCode, t.DocDesc, ln."Amount"
        FROM "PR_ADTRANS_ARC" AS t
        JOIN "PR_ADTRANSLN_ARC" AS ln ON t.ID = ln.MasterID
        WHERE t.EmpCode = 'E0534'
        AND t.DocDate >= '2025-08-01'
        AND t.DocDate < '2025-09-01'
        AND UPPER(t.DocDesc) LIKE '%TUNJANGAN PREMI%'
        ORDER BY t.DocDesc
        '''
        
        print('E0534 PREMI data (Aug 2025):')
        rows = db.query_all(query)
        
        if rows:
            for row in rows:
                emp_code = row[0]
                doc_desc = row[1]
                amount = row[2]
                print(f'  {doc_desc}: {amount}')
                
                # Check which field it should go to
                if 'KERANI PANEN' in doc_desc.upper():
                    print(f'    -> Should go to premi_2 (TUNJANGAN PREMI KERANI PANEN)')
                elif 'MANDOR PANEN' in doc_desc.upper():
                    print(f'    -> Should go to premi_3 (TUNJANGAN PREMI MANDOR PANEN)')
                elif 'HARVESTING' in doc_desc.upper():
                    print(f'    -> Should go to premi_1 (TUNJANGAN PREMI HARVESTING)')
                elif 'PRUNING' in doc_desc.upper():
                    print(f'    -> Should go to premi_1 (TUNJANGAN PREMI PRUNING)')
        else:
            print('  No TUNJANGAN PREMI data found for E0534')
        
        return True
        
    except Exception as e:
        print(f'Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    check_e0534()
