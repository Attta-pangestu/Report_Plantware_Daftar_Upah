#!/usr/bin/env python3

"""
Test script untuk validasi struktur ABSENSI baru
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(__file__))

from simplified_method import SimplifiedHeaderService

def test_absensi_structure():
    """Test ABSENSI structure generation"""
    print("=" * 60)
    print("TEST STRUKTUR ABSENSI BARU")
    print("=" * 60)
    
    try:
        # Initialize service
        service = SimplifiedHeaderService()
        print("[OK] SimplifiedHeaderService initialized successfully")
        
        # Test column definitions
        cols = service.get_column_definitions(month=5, year=2025, gang_code='H1H')
        print(f"[OK] Generated {len(cols)} column definitions")
        
        # Find ABSENSI column
        absensi_col = None
        for col in cols:
            if isinstance(col, dict) and 'ABSENSI' in col.get('headerName', ''):
                absensi_col = col
                break
        
        if absensi_col:
            print("[OK] ABSENSI column FOUND")
            print(f"   Header: {absensi_col['headerName']}")
            
            if 'children' in absensi_col:
                children = absensi_col['children']
                print(f"   Children: {len(children)} sections")
                
                expected_sections = [
                    'KEHADIRAN', 'JUMLAH HK', 'CUTI TAHUNAN', 
                    'SAKIT + HAID', 'MINGGU', 'NASIONAL', 'IZIN', 'CTH', 'ALPA'
                ]
                
                found_sections = []
                print("   Sections:")
                for child in children:
                    child_name = child.get('headerName', '')
                    found_sections.append(child_name)
                    print(f"     ✓ {child_name}")
                
                # Validate all expected sections are present
                missing = set(expected_sections) - set(found_sections)
                if missing:
                    print(f"   ❌ Missing sections: {list(missing)}")
                    return False
                else:
                    print("   ✅ All expected sections present!")
            else:
                print("   ❌ No children found in ABSENSI")
                return False
        else:
            print("❌ ABSENSI column NOT FOUND")
            return False
        
        # Check positioning (should be after NAMA)
        print("\n📍 Checking positioning...")
        nama_idx = None
        absensi_idx = None
        
        for i, col in enumerate(cols):
            col_name = col.get('headerName', '')
            if col_name == 'NAMA':
                nama_idx = i
            elif col_name == 'ABSENSI':
                absensi_idx = i
        
        if nama_idx is not None and absensi_idx is not None:
            if absensi_idx > nama_idx:
                print("✅ ABSENSI positioned AFTER NAMA")
            else:
                print(f"❌ ABSENSI positioned BEFORE NAMA (index {absensi_idx} vs {nama_idx})")
                return False
        else:
            print("❌ Could not determine positioning")
            return False
        
        print("\n🎉 ALL TESTS PASSED!")
        print("=" * 60)
        print("SUMMARY:")
        print("  • ABSENSI structure generated successfully")
        print("  • All 9 expected sections present:")
        print("    - KEHADIRAN (hari_kerja)")  
        print("    - JUMLAH HK")
        print("    - CUTI TAHUNAN")
        print("    - SAKIT + HAID")
        print("    - MINGGU")
        print("    - NASIONAL")
        print("    - IZIN")
        print("    - CTH")
        print("    - ALPA")
        print("  • ABSENSI positioned correctly after NAMA")
        print("  • Ready for frontend consumption")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_absensi_structure()
    sys.exit(0 if success else 1)
