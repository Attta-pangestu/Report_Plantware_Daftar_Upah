#!/usr/bin/env python3
"""
Test script to verify the columns API is returning correct potongan field mappings.
"""

import requests
import json

def test_columns_api():
    """Test the /payroll/columns API endpoint."""
    base_url = "http://localhost:8003"

    print("Testing Columns API for Dynamic Potongan Field Mapping")
    print("=" * 60)

    try:
        # Step 1: Login to get authentication token (development mode)
        print("1. Logging in...")
        login_data = {"username": "admin", "password": "admin"}
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)

        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            return False

        login_result = login_response.json()
        access_token = login_result.get('access_token')

        if not access_token:
            print("No access token received")
            return False

        print("Login successful")

        # Step 2: Get columns API
        print("2. Getting columns...")
        headers = {"Authorization": f"Bearer {access_token}"}
        columns_url = f"{base_url}/payroll/columns?gang_code=C1H&month=5&year=2025"

        columns_response = requests.get(columns_url, headers=headers)

        if columns_response.status_code != 200:
            print(f"Columns API failed: {columns_response.status_code}")
            print(f"Response: {columns_response.text}")
            return False

        columns_data = columns_response.json()
        print("Columns API successful")

        # Step 3: Analyze POTONGAN section
        print("3. Analyzing POTONGAN section...")

        potongan_group = None
        for group in columns_data:
            if isinstance(group, dict) and group.get('headerName') == 'POTONGAN':
                potongan_group = group
                break

        if not potongan_group:
            print("ERROR: No POTONGAN group found in columns")
            return False

        print("Found POTONGAN group")

        # Find POTONGAN LAINNYA subgroup
        potongan_lainnya_group = None
        for child in potongan_group.get('children', []):
            if isinstance(child, dict) and child.get('headerName') == 'POTONGAN LAINNYA':
                potongan_lainnya_group = child
                break

        if not potongan_lainnya_group:
            print("ERROR: No POTONGAN LAINNYA group found")
            return False

        print("Found POTONGAN LAINNYA group")

        # Check dynamic potongan items
        potongan_children = potongan_lainnya_group.get('children', [])

        if not potongan_children:
            print("ERROR: No dynamic potongan items found")
            return False

        print(f"Found {len(potongan_children)} dynamic potongan items:")

        expected_fields = ['pot_dynamic_1', 'pot_dynamic_2', 'pot_dynamic_3']
        all_correct = True

        for i, potongan_item in enumerate(potongan_children):
            header_name = potongan_item.get('headerName', 'Unknown')

            # Get the field from the children array
            children = potongan_item.get('children', [])
            if children:
                field_name = children[0].get('field', 'No field')
            else:
                field_name = 'No field'
                all_correct = False

            expected_field = expected_fields[i] if i < len(expected_fields) else f"pot_dynamic_{i+1}"

            print(f"  {i+1}. {header_name}")
            print(f"     Field: {field_name}")

            if field_name == expected_field:
                print(f"     CORRECT")
            else:
                print(f"     ERROR - expected {expected_field}")
                all_correct = False

        if all_correct:
            print("\nSUCCESS: All dynamic potongan field mappings are CORRECT!")
            return True
        else:
            print("\nERROR: Some field mappings are incorrect")
            return False

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_columns_api()
    if success:
        print("\nAPI test completed successfully!")
    else:
        print("\nAPI test failed!")