import json
from app.services.header_service import HeaderService

# Test dengan gang C1H dan bulan Oktober 2025
header_service = HeaderService()

# Test column definitions
col_defs = header_service.get_column_definitions(month=10, year=2025, gang_code='C1H')

print('=== DETAILED COLUMN DEFINITIONS ===')
for i, col in enumerate(col_defs):
    print(f'\n--- Column {i+1} ---')
    print(json.dumps(col, indent=2))

# Check for POTONGAN structure specifically
print('\n=== POTONGAN GROUPS DETAIL ===')
for col in col_defs:
    header_name = col.get('headerName', '')
    if 'POTONGAN' in header_name.upper():
        print(f'\nFound POTONGAN group: {header_name}')
        print('Children:')
        children = col.get('children', [])
        for j, child in enumerate(children):
            print(f'  {j+1}. {json.dumps(child, indent=4)}')
            
# Check for pot_dynamic fields
print('\n=== POT DYNAMIC FIELDS ===')
pot_dynamic_fields = []
for col in col_defs:
    if 'field' in col and 'pot_dynamic' in col['field']:
        pot_dynamic_fields.append(col['field'])
    elif 'children' in col:
        for child in col.get('children', []):
            if 'field' in child and 'pot_dynamic' in child['field']:
                pot_dynamic_fields.append(child['field'])
            elif 'children' in child:
                for grandchild in child.get('children', []):
                    if 'field' in grandchild and 'pot_dynamic' in grandchild['field']:
                        pot_dynamic_fields.append(grandchild['field'])

print(f'Found pot_dynamic fields: {pot_dynamic_fields}')
