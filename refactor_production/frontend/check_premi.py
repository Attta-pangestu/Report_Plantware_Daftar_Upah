#!/usr/bin/env python3
import json
import sys

try:
    data = json.load(sys.stdin)
    if data and len(data) > 0:
        record = data[0]
        print('Premi fields found in API response:')
        premi_fields = []
        for key in sorted(record.keys()):
            if 'premi' in key and key != 'total_premi':
                value = record[key]
                if value != 0:  # Only show non-zero values
                    print(f'  {key}: {value}')
                    premi_fields.append(key)
        print(f'Total non-zero premi fields: {len(premi_fields)}')
        print(f'total_premi value: {record.get("total_premi", 0)}')

        # Verify calculation
        calculated_total = sum(record.get(field, 0) for field in premi_fields)
        api_total = record.get('total_premi', 0)
        print(f'Calculated total: {calculated_total}')
        print(f'Match: {calculated_total == api_total}')
    else:
        print('No data or error')
except Exception as e:
    print(f'Error: {e}')