#!/usr/bin/env python3
"""
Test script to validate that the dynamic premi headers work correctly for C1H, May 2025.
"""

import requests
import json

def test_c1h_premi_headers():
    """Test that dynamic premi headers are now correct for C1H, May 2025."""
    base_url = "http://localhost:8004"

    print("Testing Dynamic Premi Headers for C1H, May 2025")
    print("=" * 50)

    try:
        # Step 1: Login
        print("1. Logging in...")
        login_data = {"username": "admin", "password": "admin"}
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)

        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            return False

        access_token = login_response.json().get('access_token')
        headers = {"Authorization": f"Bearer {access_token}"}
        print("Login successful")

        # Step 2: Get columns for C1H
        print("\n2. Getting columns for C1H...")
        columns_response = requests.get(
            f"{base_url}/payroll/columns?gang_code=C1H&month=5&year=2025",
            headers=headers
        )

        if columns_response.status_code != 200:
            print(f"Columns API failed: {columns_response.status_code}")
            return False

        columns_data = columns_response.json()
        print("Columns API successful")

        # Step 3: Find PREMI structure
        print("\n3. Analyzing PREMI structure...")

        premi_group = None
        for group in columns_data:
            if isinstance(group, dict) and group.get('headerName') == 'PREMI':
                premi_group = group
                break

        if not premi_group:
            print("ERROR: No PREMI group found")
            return False

        premi_children = premi_group.get('children', [])
        print(f"Found {len(premi_children)} premi items:")

        # Expected items that should be filtered OUT
        excluded_items = [
            "POTONGAN ALAT PANEN",
            "POTONGAN PREMI",
            "POTONGAN PREMI HARVESTING",
            "TUNJANGAN BERAS",
            "TUNJANGAN JABATAN",
            "TUNJANGAN MASA KERJA",
            "PPH21",
            "SPSI"
        ]

        found_items = []
        for child in premi_children:
            header_name = child.get('headerName', 'Unknown')
            found_items.append(header_name)
            print(f"  - {header_name}")

        # Check that excluded items are NOT present
        print(f"\n4. Checking for excluded items...")
        found_excluded = False
        for item in found_items:
            item_upper = item.upper()
            for excluded in excluded_items:
                if excluded in item_upper or any(ex_word in item_upper for ex_word in excluded.split()):
                    print(f"  ERROR: Found excluded item: {item}")
                    found_excluded = True

        if found_excluded:
            print("ERROR: Some excluded items were found in PREMI headers")
            return False

        print("SUCCESS: No excluded items found in PREMI headers")

        # Step 5: Test actual payroll data for premi values
        print("\n5. Testing actual payroll data for premi...")
        payroll_response = requests.get(
            f"{base_url}/payroll/report?gang_code=C1H&month=5&year=2025&page=1&page_size=3",
            headers=headers
        )

        if payroll_response.status_code != 200:
            print(f"Payroll API failed: {payroll_response.status_code}")
            return False

        payroll_data = payroll_response.json()
        if isinstance(payroll_data, dict):
            data_rows = payroll_data.get('data', [])
        else:
            data_rows = payroll_data

        if not data_rows:
            print("ERROR: No payroll data returned")
            return False

        print(f"Found {len(data_rows)} payroll records")

        # Check for premi fields in actual data
        non_zero_premi_found = False
        for i, row in enumerate(data_rows[:2]):
            print(f"\nRecord {i+1} - {row.get('nama', 'Unknown')}:")

            # Check standard premi fields
            standard_premi_fields = ['premi_brondol', 'premi_pruning', 'premi_angkut_material', 'premi_angkut_tbs', 'premi_harvesting_incentive', 'premi_pupuk']
            for field in standard_premi_fields:
                value = row.get(field, 0)
                if value > 0:
                    print(f"  {field}: {value}")
                    non_zero_premi_found = True

            # Check dynamic premi fields
            for j in range(1, 8):  # premi_dynamic_1 through premi_dynamic_7
                field_name = f'premi_dynamic_{j}'
                value = row.get(field_name, 0)
                if value > 0:
                    print(f"  {field_name}: {value}")
                    non_zero_premi_found = True

        if not non_zero_premi_found:
            print("\nINFO: All premi values are zero for this gang/period (this might be normal)")

        print("\nSUCCESS: Dynamic Premi Headers optimization is working correctly!")
        return True

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_c1h_premi_headers()
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")