import json
from app.services.header_service import HeaderService

# Test dengan gang C1H dan bulan Oktober 2025
header_service = HeaderService()

# Test column definitions
col_defs = header_service.get_column_definitions(month=10, year=2025, gang_code='C1H')

print('=== POTONGAN GROUP STRUCTURE ===')
for i, col in enumerate(col_defs):
    header_name = col.get('headerName', '')
    if 'POTONGAN' in header_name.upper():
        print(f'\nPOTONGAN Group {i+1}: {header_name}')
        children = col.get('children', [])
        for j, child in enumerate(children):
            child_header = child.get('headerName', 'No Header')
            if isinstance(child, dict) and 'children' in child:
                print(f'  {j+1}. {child_header}')
                for k, grandchild in enumerate(child.get('children', [])):
                    field = grandchild.get('field', 'no_field')
                    print(f'    {k+1}. {grandchild.get("headerName", "No Name")} (field: {field})')
            else:
                field = child.get('field', 'no_field')
                print(f'  {j+1}. {child_header} (field: {field})')
                
# Find all pot_dynamic fields in the entire structure
print('\n=== ALL POT_DYNAMIC FIELDS ===')
pot_dynamic_fields = []
def find_pot_dynamic(obj, path=""):
    if isinstance(obj, dict):
        if 'field' in obj and 'pot_dynamic' in obj.get('field', ''):
            pot_dynamic_fields.append(f"{path}.{obj['field']}")
        for key, value in obj.items():
            find_pot_dynamic(value, f"{path}.{key}" if path else key)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            find_pot_dynamic(item, f"{path}[{i}]")

find_pot_dynamic(col_defs)
print(f'All pot_dynamic fields: {pot_dynamic_fields}')
