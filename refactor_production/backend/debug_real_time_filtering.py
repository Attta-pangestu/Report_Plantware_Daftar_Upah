#!/usr/bin/env python3
"""
Debug real time filtering by overriding method
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from simplified_method import SimplifiedHeaderService
from database.services.database import Database
from database.services.queries import Queries
from database.services.cache import Cache

def debug_real_time_filtering():
    """Debug real time filtering by overriding method"""
    print("=== DEBUGGING REAL TIME FILTERING ===")
    
    try:
        service = SimplifiedHeaderService()
        
        month = 5  # Mei
        year = 2025
        gang_code = 'E2T'
        
        print(f"Testing: {gang_code}, {month}/{year}")
        print()
        
        # Clear cache
        cache = Cache.instance()
        cache.clear()
        print("Cache cleared")
        print()
        
        # Override method to add detailed debug
        def debug_compute_method(month, year, gang_code):
            print(f"  DEBUG: _compute_dynamic_premi_headers_db START")
            
            # Get DB connection
            db = Database.instance()
            q = Queries()
            
            # Get query
            sql_entry = q.get('premi', 'dynamic_headers_by_gang_month_optimized')
            start_date = f"{year}-{str(month).zfill(2)}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{str(month+1).zfill(2)}-01"

            print(f"  DEBUG: Query params: {gang_code}, {start_date}, {end_date}")
            
            # Execute query
            rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])
            
            print(f"  DEBUG: DB returned {len(rows) if rows else 0} rows")
            
            # Get all headers
            all_headers = []
            if rows is not None:
                for r in rows:
                    if r and r[0]:
                        all_headers.append(str(r[0]).strip())
                        print(f"    DB ROW: {str(r[0]).strip()}")
            
            print(f"  DEBUG: All headers: {all_headers}")
            
            # Apply filtering - exclude items already in TUNJANGAN section and basic deductions
            excluded_keywords = ['BERAS', 'PPH', 'SPSI', 'TUNJANGAN JABATAN', 'TUNJANGAN MASA KERJA']
            filtered_headers = []
            
            for header in all_headers:
                header_upper = header.upper()
                
                # More precise exclude logic
                should_exclude = False
                
                # Exclude items starting with 'POTONGAN' (not containing)
                if header_upper.startswith('POTONGAN'):
                    should_exclude = True
                    print(f"    FILTER: {header} -> EXCLUDED (starts with POTONGAN)")
                    continue
                
                # Exclude items containing specific keywords
                for keyword in excluded_keywords:
                    if keyword in header_upper:
                        should_exclude = True
                        print(f"    FILTER: {header} -> EXCLUDED (contains {keyword})")
                        break
                
                if not should_exclude:
                    filtered_headers.append(header)
                    print(f"    FILTER: {header} -> INCLUDED")
            
            print(f"  DEBUG: Filtered headers: {filtered_headers}")
            
            # Remove duplicates and limit to 7
            seen = set()
            unique_headers = []
            for h in filtered_headers:
                if h not in seen:
                    unique_headers.append(h)
                    seen.add(h)
            result = unique_headers[:7]
            
            print(f"  DEBUG: Final result: {result}")
            
            return result
        
        # Override the method
        service._compute_dynamic_premi_headers_db = debug_compute_method
        
        print("Calling overridden method...")
        headers = service._compute_dynamic_premi_headers_db(month=month, year=year, gang_code=gang_code)
        
        print(f"\nFinal result: {len(headers) if headers else 0} items")
        for i, header in enumerate(headers or []):
            print(f"  {i+1:2d}. {header}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_real_time_filtering()
