import json
from app.services.header_service import HeaderService

# Test dengan gang C1H dan bulan Oktober 2025
header_service = HeaderService()
headers = header_service.generate_dynamic_headers(month=10, year=2025, gang_code='C1H')

print('=== DYNAMIC HEADERS RESULT ===')
dyn_premi = headers.get('table_structure', {}).get('dynamic_docdesc_premi', [])
dyn_potongan = headers.get('table_structure', {}).get('dynamic_docdesc_potongan', [])

print(f'Dynamic Premi: {dyn_premi}')
print(f'Dynamic Potongan: {dyn_potongan}')

# Test column definitions
col_defs = header_service.get_column_definitions(month=10, year=2025, gang_code='C1H')
print(f'\n=== COLUMN DEFINITIONS COUNT ===')
print(f'Total column definitions: {len(col_defs)}')

# Check if potongan columns exist
potongan_count = 0
for col in col_defs:
    if 'headerName' in str(col) and ('POTONGAN' in str(col).upper() or 'POT' in str(col).upper()):
        potongan_count += 1
        print(f'Found potongan column: {col.get("headerName", col.get("field", "unknown"))}')

print(f'Total potongan-related columns: {potongan_count}')
