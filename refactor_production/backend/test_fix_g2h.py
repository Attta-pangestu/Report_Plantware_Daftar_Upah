#!/usr/bin/env python3
"""
Test script to validate that the potongan fix works for G2H, May 2025.
"""

import requests
import json

def test_g2h_potongan_fix():
    """Test that potongan values are now correct for G2H, May 2025."""
    base_url = "http://localhost:8004"

    print("Testing Potongan Fix for G2H, May 2025")
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

        # Step 2: Get columns for G2H
        print("\n2. Getting columns for G2H...")
        columns_response = requests.get(
            f"{base_url}/payroll/columns?gang_code=G2H&month=5&year=2025",
            headers=headers
        )

        if columns_response.status_code != 200:
            print(f"Columns API failed: {columns_response.status_code}")
            return False

        columns_data = columns_response.json()
        print("Columns API successful")

        # Step 3: Find POTONGAN LAINNYA structure
        print("\n3. Analyzing POTONGAN LAINNYA structure...")

        potongan_group = None
        for group in columns_data:
            if isinstance(group, dict) and group.get('headerName') == 'POTONGAN':
                potongan_group = group
                break

        if not potongan_group:
            print("ERROR: No POTONGAN group found")
            return False

        potongan_lainnya_group = None
        for child in potongan_group.get('children', []):
            if isinstance(child, dict) and child.get('headerName') == 'POTONGAN LAINNYA':
                potongan_lainnya_group = child
                break

        if not potongan_lainnya_group:
            print("ERROR: No POTONGAN LAINNYA group found")
            return False

        potongan_children = potongan_lainnya_group.get('children', [])
        print(f"Found {len(potongan_children)} dynamic potongan items:")

        expected_items = [
            "POTONGAN ALAT PANEN",
            "POTONGAN PREMI",
            "POTONGAN PREMI HARVESTING"
        ]

        expected_fields = ['pot_dynamic_1', 'pot_dynamic_2', 'pot_dynamic_3']

        all_found = True
        for i, expected_item in enumerate(expected_items):
            found = False
            for child in potongan_children:
                if child.get('headerName') == expected_item:
                    field_children = child.get('children', [])
                    if field_children:
                        field_name = field_children[0].get('field')
                        expected_field = expected_fields[i]

                        if field_name == expected_field:
                            print(f"  OK {expected_item} -> {field_name}")
                            found = True
                        else:
                            print(f"  ERROR {expected_item} -> {field_name} (expected {expected_field})")
                            all_found = False
                    else:
                        print(f"  ERROR {expected_item} -> No field found")
                        all_found = False
                    break

            if not found:
                print(f"  ERROR {expected_item} -> Not found")
                all_found = False

        if not all_found:
            print("\nERROR: Not all expected potongan items found with correct field mapping")
            return False

        # Step 4: Test actual payroll data
        print("\n4. Testing actual payroll data...")
        payroll_response = requests.get(
            f"{base_url}/payroll/report?gang_code=G2H&month=5&year=2025&page=1&page_size=3",
            headers=headers
        )

        if payroll_response.status_code != 200:
            print(f"Payroll API failed: {payroll_response.status_code}")
            return False

        payroll_data = payroll_response.json()
        # Handle both dict and list response formats
        if isinstance(payroll_data, dict):
            data_rows = payroll_data.get('data', [])
        else:
            data_rows = payroll_data  # Direct list

        if not data_rows:
            print("ERROR: No payroll data returned")
            return False

        print(f"Found {len(data_rows)} payroll records")

        # Check for non-zero values in pot_dynamic fields
        non_zero_found = False
        for i, row in enumerate(data_rows[:2]):  # Check first 2 records
            print(f"\nRecord {i+1} - {row.get('nama', 'Unknown')}:")

            for j in range(3):  # Check pot_dynamic_1, pot_dynamic_2, pot_dynamic_3
                field_name = f'pot_dynamic_{j+1}'
                value = row.get(field_name, 0)
                print(f"  {field_name}: {value}")

                if value > 0:
                    non_zero_found = True

        if not non_zero_found:
            print("\nWARNING: All pot_dynamic values are zero!")
            print("This might indicate the data extraction is still not working correctly.")
            return False

        print("\nSUCCESS: Potongan fix is working correctly!")
        return True

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_g2h_potongan_fix()
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")