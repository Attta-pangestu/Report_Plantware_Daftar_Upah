import json
from app.services.header_service import HeaderService

# Test untuk mengisolasi masalah rendering
header_service = HeaderService()

# Generate column definitions - test with Gang C1H Bulan Mei
col_defs = header_service.get_column_definitions(month=5, year=2025, gang_code='C1H')

# Also show dynamic headers for debugging
headers = header_service.generate_dynamic_headers(month=5, year=2025, gang_code='C1H')
dyn_premi = headers.get('table_structure', {}).get('dynamic_docdesc_premi', [])
dyn_potongan = headers.get('table_structure', {}).get('dynamic_docdesc_potongan', [])

print(f'Dynamic Premi: {dyn_premi}')
print(f'Dynamic Potongan: {dyn_potongan}')

# Check pot_dynamic_children content
print('\n=== POT_DYNAMIC_CHILDREN ANALYSIS ===')
pot_dynamic_children = []
# Manually reproduce the logic to see what's happening
for i, name in enumerate(dyn_potongan[:7], 1):
    nm = (name if isinstance(name, str) else '').strip()
    up = nm.upper()
    # Hanya yang mengandung "POTONGAN" yang masuk ke POTONGAN LAINNYA
    if any(pot_keyword in up for pot_keyword in ['POTONGAN', 'POT']):
        pf = f"pot_dynamic_{i}"
        pot_dynamic_children.append({
            'headerName': (nm or f"POTONGAN {i}"),
            'children': [{
                'headerName': 'JUMLAH',
                'field': pf,
                'width': 100,
                'type': 'numericColumn',
                'cellStyle': {
                    'textAlign': 'right',
                    'backgroundColor': '#ffebee',
                    'color': '#c62828'
                }
            }]
        })
        print(f'Child {i}: {nm} -> {pf}')
    else:
        print(f'Skipped: {nm} (tidak mengandung POTONGAN)')

print(f'Total pot_dynamic_children: {len(pot_dynamic_children)}')
print()

# Buat response yang minimal untuk debugging
minimal_response = []

# Ambil hanya POTONGAN groups
for col in col_defs:
    if isinstance(col, dict) and col.get('headerName') and 'POTONGAN' in col['headerName'].upper():
        minimal_response.append(col)

print('=== MINIMAL POTONGAN RESPONSE FOR DEBUGGING ===')
print(json.dumps(minimal_response, indent=2))

# Analisis struktur POTONGAN LAINNYA
print('\n=== POTONGAN LAINNYA ANALYSIS ===')
for i, col in enumerate(minimal_response):
    header_name = col.get('headerName', '')
    print(f'POTONGAN Group {i+1}: {header_name}')
    
    if header_name == 'POTONGAN LAINNYA':
        print('*** FOUND POTONGAN LAINNYA ***')
        children = col.get('children', [])
        print(f'Children count: {len(children)}')
        
        for j, child in enumerate(children):
            child_header = child.get('headerName', '')
            print(f'  Child {j+1}: {child_header}')
            
            if isinstance(child, dict) and 'children' in child:
                grandkids = child.get('children', [])
                print(f'  Grandchildren count: {len(grandkids)}')
                
                for k, grandkid in enumerate(grandkids):
                    field = grandkid.get('field', 'NO_FIELD')
                    gc_header = grandkid.get('headerName', '')
                    print(f'    {k+1}. {gc_header} (field: {field})')
                    
                    if field.startswith('pot_dynamic'):
                        print(f'    *** VALID POT_DYNAMIC FIELD: {field}')
            else:
                field = child.get('field', 'NO_FIELD')
                print(f'  Field: {field}')
                
                if field.startswith('pot_dynamic'):
                    print(f'  *** VALID POT_DYNAMIC FIELD: {field}')

# Generate test data rows
print('\n=== TEST DATA ROWS FOR FRONTEND ===')
test_data = [
    {
        "nik": "C0526",
        "nama": "Test User 1", 
        "gaji_pokok": 2000000,
        "total_tunjangan": 500000,
        "total_premi": 1000000,
        "pot_bpjs_pekerja_total": 200000,
        "pot_spsi": 40000,
        "pot_pph21": 140300,
        "pot_koreksi": 0,
        "pot_dynamic_1": 140300,  # PPH21
        "pot_dynamic_2": 40000,   # POTONGAN SPSI
        "jumlah_upah_kotor": 3500000,
        "total_potongan": 380300,
        "upah_bersih": 3119700
    },
    {
        "nik": "C0680", 
        "nama": "Test User 2",
        "gaji_pokok": 2000000,
        "total_tunjangan": 500000,
        "total_premi": 1000000,
        "pot_bpjs_pekerja_total": 200000,
        "pot_spsi": 40000,
        "pot_pph21": 527590,
        "pot_koreksi": 0,
        "pot_dynamic_1": 527590,  # PPH21
        "pot_dynamic_2": 40000,   # POTONGAN SPSI
        "jumlah_upah_kotor": 3500000,
        "total_potongan": 767590,
        "upah_bersih": 2732410
    }
]

print('Test data dengan pot_dynamic fields:')
for i, row in enumerate(test_data):
    print(f'Row {i+1}:')
    for key, value in row.items():
        if key.startswith('pot_dynamic'):
            print(f'  {key}: {value}')
    print()

# Simpan sebagai file JSON untuk testing
debug_package = {
    "columnDefs": minimal_response,
    "rowData": test_data,
    "metadata": {
        "month": 10,
        "year": 2025,
        "gang_code": "C1H",
        "description": "Debug package for POTONGAN LAINNYA rendering issue"
    }
}

with open('debug_potongan.json', 'w', encoding='utf-8') as f:
    json.dump(debug_package, f, indent=2, ensure_ascii=False)

print('Debug package saved to: debug_potongan.json')
