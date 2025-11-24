#!/usr/bin/env python3
"""
Quick test to verify potongan values are appearing correctly.
"""

import requests
import json

def quick_test():
    base_url = "http://localhost:8004"

    try:
        # Login
        login_data = {"username": "admin", "password": "admin"}
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)

        if login_response.status_code != 200:
            print(f"Login failed: {login_response.status_code}")
            return False

        access_token = login_response.json().get('access_token')
        headers = {"Authorization": f"Bearer {access_token}"}

        # Get payroll data for first few employees
        payroll_response = requests.get(
            f"{base_url}/payroll/report?gang_code=G2H&month=5&year=2025&page=1&page_size=5",
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

        print("Checking potongan values for first 5 employees:")
        print("=" * 60)

        non_zero_found = False
        for i, row in enumerate(data_rows):
            name = row.get('nama', 'Unknown')
            print(f"\n{i+1}. {name}")

            # Check pot_dynamic fields
            for j in range(1, 4):  # pot_dynamic_1, pot_dynamic_2, pot_dynamic_3
                field_name = f'pot_dynamic_{j}'
                value = row.get(field_name, 0)
                if value > 0:
                    print(f"   {field_name}: {value} ✓")
                    non_zero_found = True
                else:
                    print(f"   {field_name}: {value}")

        if non_zero_found:
            print("\n✅ SUCCESS: Non-zero potongan values found!")
            return True
        else:
            print("\n⚠️  WARNING: All potongan values are zero")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    quick_test()