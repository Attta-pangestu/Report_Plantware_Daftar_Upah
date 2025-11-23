import json
import subprocess
import sys

# Get the data from curl
result = subprocess.run([
    'curl', '-s',
    'http://localhost:8002/payroll/columns?month=5&year=2025&gang_code=H1H',
    '-H', 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImRpdmlzaW9ucyI6WyJQRzFBIiwiUEdxQiIsIlBHMkEiLCJQRzJCIiwiRE1FIiwiQVJBIiwiQVJCMSIsIkFSQjIiLCJJTkZSQSIsIkFSRUMiLCJJSkwiLCJTVEYtT0ZGSUNFIiwiU0VDVVJJVFkiXSwiZXhwIjoxNzYzOTAyMDYwfQ.WnWMzsRD25LEZTgieMbydHQu4borgvBWVP3nIOvaEAE'
], capture_output=True, text=True)

data = json.loads(result.stdout)
columns = data.get('columns', [])

print(f"Total columns: {len(columns)}")
print("\nColumn list:")
for col in columns:
    field = col.get('field', 'NO_FIELD')
    header = col.get('headerName', 'NO_HEADER')
    print(f"{field}: {header}")

print("\nChecking for attendance fields:")
attendance_fields = ['hari_kerja', 'cuti_tahunan_hari', 'cuti_sakit_haid_hari', 'cuti_minggu_hari', 'cuti_nasional_hari', 'tidak_hadir_cth', 'tidak_hadir_alpa', 'jumlah_hk']
for field in attendance_fields:
    exists = any(col.get('field') == field for col in columns)
    print(f"{field}: {'YES' if exists else 'NO'}")