#!/usr/bin/env python3
"""
Debug method SimplifiedHeaderService secara langsung
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from database.services.database import Database
from database.services.queries import Queries
from database.services.cache import Cache

def debug_method_directly():
    """Debug method SimplifiedHeaderService langsung"""
    print("=== DEBUGGING METHOD DIRECTLY ===")
    
    try:
        # Recreate method logic
        month = 1
        year = 2024
        gang_code = "A1H"
        
        # Enhanced cache key
        cache_key = f"dyn_premi:{gang_code}:{year}-{str(month).zfill(2)}"
        print(f"Cache key: {cache_key}")
        
        cache = Cache.instance()
        cached = cache.get(cache_key)
        if cached is not None:
            print(f"Cache hit: {cached}")
            return cached
        else:
            print("Cache miss - executing query")

        db = Database.instance()
        q = Queries()
        
        # Get optimized query for PREMI
        sql_entry = q.get('premi', 'dynamic_headers_by_gang_month_optimized')
        if sql_entry and 'sql' in sql_entry:
            print(f"Query found: {sql_entry['sql'][:100]}...")
            
            start_date = f"{year}-{str(month).zfill(2)}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{str(month+1).zfill(2)}-01"
            
            print(f"Parameters: [{gang_code}, {start_date}, {end_date}]")
            
            rows = db.query_all(sql_entry['sql'], [gang_code, start_date, end_date])
            
            print(f"Query results: {len(rows) if rows else 0} rows")
            
            # Handle case where db.query_all returns None
            if rows is not None:
                # Predefined excluded items
                excluded_lower = {
                    'koreksi', 'potongan pph21', 'potongan spsi', 'pph21', 'spsi',
                    'tunjangan jabatan', 'tunjangan masa kerja', 'pruning', 'brondol', 'pph 21'
                }

                print(f"Excluded items: {excluded_lower}")
                
                headers = []
                for r in rows:
                    if r and r[0]:
                        docdesc = str(r[0]).strip()
                        if docdesc.lower() not in excluded_lower:
                            headers.append(docdesc)
                            print(f"  Added: '{docdesc}'")
                        else:
                            print(f"  Excluded: '{docdesc}'")

                print(f"Filtered headers: {headers}")

                # Remove duplicates and limit to 7 items
                seen = set()
                unique_headers = [h for h in headers if h not in seen and not seen.add(h)]
                result = unique_headers[:7]
                
                print(f"Final result: {result}")
                
                # Cache the result
                cache.set(cache_key, result, ttl=3600)
                print("Result cached")
                
                return result
            else:
                print("Query returned None")
                return []
        else:
            print("ERROR: Query not found in JSON")
            return []
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    result = debug_method_directly()
    print(f"\nFinal result: {result}")
    
    if result:
        print(f"\n[SUCCESS] Method working! Found {len(result)} dynamic PREMI items:")
        for i, item in enumerate(result):
            print(f"  {i+1}. {item}")
    else:
        print(f"\n[INFO] Method executed but found no dynamic PREMI items")
        print("This confirms the issue is in the method logic, not the cache")
