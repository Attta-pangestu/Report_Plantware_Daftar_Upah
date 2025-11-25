#!/usr/bin/env python3
import json
import sys
import requests

# First login to get token
login_response = requests.post("http://localhost:8004/auth/login",
                               json={"username": "admin", "password": "admin"})
if login_response.status_code != 200:
    print("Login failed")
    sys.exit(1)

token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}

# Test the columns API
response = requests.get("http://localhost:8004/payroll/columns?gang=H1H&month=5&year=2025", headers=headers)
if response.status_code == 200:
    data = response.json()
    print('Response type:', type(data))
    if isinstance(data, list):
        absensi = [d for d in data if d.get('headerName') == 'ABSENSI']
        print('ABSENSI found:', len(absensi) > 0)
        if absensi:
            print('Children count:', len(absensi[0].get('children', [])))
            print('First 5 children:')
            for child in absensi[0].get('children', [])[:5]:
                print(f" - {child.get('headerName', 'N/A')} ({child.get('field', 'N/A')})")
        else:
            print('No ABSENSI group found in column definitions')
            print('Available groups:', [d.get('headerName') for d in data])
    else:
        print('Response keys:', data.keys() if hasattr(data, 'keys') else 'No keys')
else:
    print(f"API request failed with status {response.status_code}")
    print(response.text)