#!/usr/bin/env python3
"""
Test script to verify that dynamic potongan field mapping is working correctly.
This script tests the simplified method to ensure pot_dynamic fields are properly mapped.
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simplified_method import SimplifiedHeaderService

def test_dynamic_potongan_mapping():
    """Test that dynamic potongan headers are mapped to pot_dynamic fields correctly."""
    print("Testing Dynamic Potongan Field Mapping")
    print("=" * 50)

    # Create SimplifiedHeaderService instance
    service = SimplifiedHeaderService()

    # Test with the same parameters as the frontend uses
    gang_code = "C1H"
    month = 5
    year = 2025

    print(f"Testing with: gang_code={gang_code}, month={month}, year={year}")
    print()

    try:
        # Get dynamic headers (this includes dyn_potongan data)
        headers = service.generate_dynamic_headers(month=month, year=year, gang_code=gang_code)

        print("Generated Headers Structure:")
        table_structure = headers.get('table_structure', {})
        dynamic_docdesc = table_structure.get('dynamic_docdesc', {})
        dyn_premi = dynamic_docdesc.get('premi', [])
        dyn_potongan = dynamic_docdesc.get('potongan', [])
        dyn_potongan_pattern = dynamic_docdesc.get('potongan_pattern', [])

        print(f"  dyn_premi: {dyn_premi}")
        print(f"  dyn_potongan: {dyn_potongan}")
        print(f"  dyn_potongan_pattern: {dyn_potongan_pattern}")
        print()

        # Get column definitions
        columns = service.get_column_definitions(month=month, year=year, gang_code=gang_code)

        print("Column Definitions for POTONGAN LAINNYA:")
        print("=" * 40)

        # Find POTONGAN group
        potongan_group = None
        for group in columns:
            if isinstance(group, dict) and group.get('headerName') == 'POTONGAN':
                potongan_group = group
                break

        if potongan_group and 'children' in potongan_group:
            # Find POTONGAN LAINNYA subgroup
            potongan_lainnya_group = None
            for child in potongan_group['children']:
                if isinstance(child, dict) and child.get('headerName') == 'POTONGAN LAINNYA':
                    potongan_lainnya_group = child
                    break

            if potongan_lainnya_group and 'children' in potongan_lainnya_group:
                for i, potongan_item in enumerate(potongan_lainnya_group['children']):
                    header_name = potongan_item.get('headerName', 'Unknown')

                    # The field is in the children array of this potongan item
                    children = potongan_item.get('children', [])
                    if children:
                        field_name = children[0].get('field', 'No field')
                    else:
                        field_name = 'No field'

                    print(f"  {i+1}. Header: {header_name}")
                    print(f"     Field: {field_name}")

                    # Check if field name matches expected pattern
                    expected_pattern = f"pot_dynamic_{i+1}"
                    if field_name == expected_pattern:
                        print(f"     CORRECT - matches {expected_pattern}")
                    else:
                        print(f"     ERROR - expected {expected_pattern}, got {field_name}")
                    print()
            else:
                print("No POTONGAN LAINNYA group found")
        else:
            print("No POTONGAN group found")

        # Test field mapping method directly
        print("\nDirect Field Mapping Tests:")
        print("=" * 30)

        test_potongan_names = [
            "POTONGAN ALAT PANEN",
            "POTONGAN PREMI",
            "POTONGAN PREMI HARVESTING",
            "POTONGAN TIDAK DIKENAL"
        ]

        for pot_name in test_potongan_names:
            mapped_field = service._map_potongan_field(pot_name)
            print(f"  {pot_name} -> {mapped_field}")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_dynamic_potongan_mapping()
    if success:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1)