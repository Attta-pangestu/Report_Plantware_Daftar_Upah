import requests
import json

# Test the actual API endpoint
url = "http://127.0.0.1:8002/reports/column-definitions?month=10&year=2025&gang_code=C1H"

try:
    # Try with authentication
    headers = {
        'Authorization': 'Bearer test-token',  # Adjust if needed
        'Content-Type': 'application/json'
    }
    response = requests.get(url, headers=headers, timeout=30)
    print(f'Status Code: {response.status_code}')
    
    if response.status_code == 200:
        data = response.json()
        print('\n=== API RESPONSE ANALYSIS ===')
        
        # Find POTONGAN groups
        potongan_groups = []
        for i, col in enumerate(data):
            if isinstance(col, dict) and col.get('headerName') and 'POTONGAN' in col['headerName'].upper():
                potongan_groups.append((i, col))
        
        print(f'Found {len(potongan_groups)} POTONGAN groups:')
        for idx, (pos, col) in enumerate(potongan_groups):
            print(f'\n--- POTONGAN Group {idx+1} (Position {pos}) ---')
            print(f'Header: {col.get("headerName")}')
            children = col.get('children', [])
            print(f'Children count: {len(children)}')
            
            for j, child in enumerate(children):
                child_header = child.get('headerName', f'Child_{j}')
                print(f'  {j+1}. {child_header}')
                if isinstance(child, dict) and 'children' in child:
                    for k, grandchild in enumerate(child.get('children', [])):
                        field = grandchild.get('field', 'no_field')
                        gc_header = grandchild.get('headerName', f'Grandchild_{k}')
                        print(f'    {k+1}. {gc_header} (field: {field})')
                        
                        # Check for pot_dynamic fields
                        if 'pot_dynamic' in field:
                            print(f'    *** FOUND POT_DYNAMIC FIELD: {field}')
                else:
                    field = child.get('field', 'no_field')
                    if field != 'no_field':
                        print(f'    Field: {field}')
                        if 'pot_dynamic' in field:
                            print(f'    *** FOUND POT_DYNAMIC FIELD: {field}')
    else:
        print(f'Error: {response.status_code}')
        print(f'Response: {response.text}')
        
except Exception as e:
    print(f'Error connecting to API: {e}')
