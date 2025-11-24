#!/usr/bin/env python3

"""
Simple test untuk validasi struktur ABSENSI baru
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from simplified_method import SimplifiedHeaderService

def test_absensi_structure():
    """Test ABSENSI structure generation"""
    print("=" * 50)
    print("TEST STRUKTUR ABSENSI BARU")
    print("=" * 50)
    
    try:
        service = SimplifiedHeaderService()
        print("[OK] Service initialized")
        
        cols = service.get_column_definitions(month=5, year=2025, gang_code='H1H')
        print(f"[OK] Generated {len(cols)} columns")
        
        # Find ABSENSI
        absensi_col = None
        for col in cols:
            if isinstance(col, dict) and 'ABSENSI' in col.get('headerName', ''):
                absensi_col = col
                break
        
        if not absensi_col:
            print("[ERROR] ABSENSI column NOT FOUND")
            return False
        
        print("[OK] ABSENSI column FOUND")
        
        if 'children' not in absensi_col:
            print("[ERROR] No children in ABSENSI")
            return False
        
        children = absensi_col['children']
        print(f"[INFO] ABSENSI has {len(children)} sections")
        
        expected = ['KEHADIRAN', 'JUMLAH HK', 'CUTI TAHUNAN', 'SAKIT + HAID', 'MINGGU', 'NASIONAL', 'IZIN', 'CTH', 'ALPA']
        found = []
        
        for child in children:
            name = child.get('headerName', '')
            found.append(name)
            print(f"  - {name}")
        
        missing = set(expected) - set(found)
        if missing:
            print(f"[ERROR] Missing: {list(missing)}")
            return False
        
        # Check positioning 
        nama_idx = None
        absensi_idx = None
        
        for i, col in enumerate(cols):
            name = col.get('headerName', '')
            if name == 'NAMA':
                nama_idx = i
            elif name == 'ABSENSI':
                absensi_idx = i
        
        if nama_idx is None:
            print("[ERROR] NAMA column not found")
            return False
            
        if absensi_idx is None:
            print("[ERROR] ABSENSI column indexing failed")
            return False
        
        if absensi_idx <= nama_idx:
            print(f"[ERROR] ABSENSI positioned BEFORE NAMA (NAMA idx={nama_idx}, ABSENSI idx={absensi_idx})")
            return False
        
        print(f"[OK] ABSENSI positioned AFTER NAMA (NAMA idx={nama_idx}, ABSENSI idx={absensi_idx})")
        
        print("\n" + "=" * 50)
        print("SUCCESS! ALL TESTS PASSED")
        print("ABSENSI Structure:")
        print("  - KEHADIRAN (hari_kerja)")  
        print("  - JUMLAH HK")
        print("  - CUTI TAHUNAN")
        print("  - SAKIT + HAID")
        print("  - MINGGU")  
        print("  - NASIONAL")
        print("  - IZIN")
        print("  - CTH")
        print("  - ALPA")
        print("Positioned correctly after NAMA column")
        print("Ready for frontend!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_absensi_structure()
    sys.exit(0 if success else 1)
