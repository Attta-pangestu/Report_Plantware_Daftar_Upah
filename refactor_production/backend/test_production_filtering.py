#!/usr/bin/env python3
"""
Test production filtering (without override)
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from simplified_method import SimplifiedHeaderService
from database.services.cache import Cache

def test_production_filtering():
    """Test production filtering"""
    print("=== TESTING PRODUCTION FILTERING (NO OVERRIDE) ===")
    
    try:
        service = SimplifiedHeaderService()
        
        month = 5  # Mei
        year = 2025
        gang_code = 'E2T'
        
        print(f"Testing: {gang_code}, {month}/{year}")
        print()
        
        # Clear ALL cache
        cache = Cache.instance()
        cache.clear()
        print("All cache cleared")
        print()
        
        # Set environment variable to disable cache
        import os
        os.environ['DISABLE_CACHE'] = 'true'
        print("Cache disabled via environment variable")
        print()
        
        # Test direct method call
        print("Calling _compute_dynamic_premi_headers_db (production, cache disabled)...")
        headers = service._compute_dynamic_premi_headers_db(month=month, year=year, gang_code=gang_code)
        
        # Restore cache setting
        os.environ['DISABLE_CACHE'] = 'false'
        
        print(f"Production result: {len(headers) if headers else 0} items")
        for i, header in enumerate(headers or []):
            print(f"  {i+1:2d}. {header}")
        
        print()
        
        # Expected result
        expected = ['TUNJANGAN INSENTIF PANEN', 'TUNJANGAN PREMI', 'TUNJANGAN PREMI HARVESTING', 'TUNJANGAN PREMI PRUNING']
        
        if headers:
            success = set(headers) == set(expected)
            print(f"Expected: {expected}")
            print(f"Actual:   {headers}")
            print(f"Match:    {'✅ SUCCESS' if success else '❌ FAILED'}")
            
            if success:
                print("\n🎉 PRODUCTION FILTERING WORKS!")
                return True
            else:
                missing = set(expected) - set(headers)
                extra = set(headers) - set(expected)
                
                if missing:
                    print(f"Missing: {missing}")
                if extra:
                    print(f"Extra: {extra}")
                
                return False
        else:
            print("❌ NO HEADERS RETURNED")
            return False
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_production_filtering()
    
    if success:
        print(f"\n[SUCCESS] Production filtering ready!")
    else:
        print(f"\n[ISSUE] Need further investigation")
