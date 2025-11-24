import json
from app.services.header_service import HeaderService

# Test dengan gang C1H dan bulan Oktober 2025
header_service = HeaderService()

# Test column definitions
col_defs = header_service.get_column_definitions(month=10, year=2025, gang_code='C1H')

# Create a simplified response that will be sent to frontend
response = {
    "columnDefs": col_defs
}

print('=== FRONTEND RESPONSE STRUCTURE ===')
print(json.dumps(response, indent=2))

# Extract just the POTONGAN groups for analysis
potongan_response = []
for col in col_defs:
    if isinstance(col, dict) and 'headerName' in col and 'POTONGAN' in col['headerName'].upper():
        potongan_response.append(col)

print('\n=== POTONGAN GROUPS FOR FRONTEND ===')
print(json.dumps(potongan_response, indent=2))
