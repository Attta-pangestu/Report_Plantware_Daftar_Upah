#!/usr/bin/env python3
"""
Debug service filtering logic
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from simplified_method import SimplifiedHeaderService
from database.services.cache import Cache

def debug_service_filtering():
    """Debug service filtering logic"""
    print("=== DEBUGGING SERVICE FILTERING LOGIC ===")
    
    try:
        service = SimplifiedHeaderService()
        
        month = 5  # Mei
        year = 2025
        gang_code = 'E2T'
        
        print(f"Testing: {gang_code}, {month}/{year}")
        print()
        
        # Clear ALL cache
        cache = Cache.instance()
        cache.clear()  # Clear ALL cache entries (no parameter)
        print("All cache cleared")
        
        print("Cache cleared")
        print()
        
        # Direct call to _compute_dynamic_premi_headers_db (no override)
        print("Calling _compute_dynamic_premi_headers_db directly...")
        
        headers = service._compute_dynamic_premi_headers_db(month=month, year=year, gang_code=gang_code)
        
        print(f"Final filtered headers result: {len(headers) if headers else 0} items")
        for i, header in enumerate(headers or []):
            print(f"  {i+1:2d}. {header}")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_service_filtering()
