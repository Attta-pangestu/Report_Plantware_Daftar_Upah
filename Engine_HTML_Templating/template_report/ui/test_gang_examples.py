#!/usr/bin/env python3
"""
Test Cases for Gang Description Decoder
"""

from gang_description import get_gang_description, list_all_gangs

def test_specific_cases():
    """Test specific gang codes as requested by user"""
    print("=== Test Kode Gang Spesifik ===")

    # Test case 1: H1H (existing gang from previous implementation)
    print("\n1. Test H1H:")
    result = get_gang_description("H1H")
    print(f"   Success: {result['success']}")
    if result['success']:
        print(f"   Formatted: {result['formatted_description']}")
        print(f"   Company: {result['company_name']}")
        print(f"   Location: {result['location_code']}")
    else:
        print(f"   Message: {result['message']}")
        if result['error']:
            print(f"   Error: {result['error']}")

    # Test case 2: Non-existent gang
    print("\n2. Test Non-Existent Gang (ZZZ):")
    result = get_gang_description("ZZZ")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")

    # Test case 3: Test with different gang codes
    print("\n3. Test Various Gang Codes:")
    test_codes = ["H1H", "H2H", "H3H", "H4H", "H5H", "A1H", "B1H"]

    for code in test_codes:
        result = get_gang_description(code)
        status = "[OK]" if result['success'] else "[FAIL]"
        print(f"   {status} {code}: {result['message']}")
        if result['success']:
            print(f"      -> {result['formatted_description']}")

def test_format_validation():
    """Test format validation"""
    print("\n=== Test Format Validation ===")

    from gang_description import GangDescriptionDecoder
    decoder = GangDescriptionDecoder()

    test_cases = [
        ("H1H", True, "Valid existing gang"),
        ("XXX", True, "Valid format but non-existent"),
        ("", False, "Empty string"),
        ("H123", True, "Valid format"),
        ("H 1", True, "Valid with space"),
        ("A1B2C3", True, "Valid alphanumeric"),
        ("1234567890", True, "Valid numbers only"),
        ("!@#$%", False, "Invalid characters only"),
        ("H" * 15, False, "Too long"),
    ]

    for code, expected, description in test_cases:
        result = decoder.validate_gang_code(code)
        status = "[OK]" if result == expected else "[FAIL]"
        print(f"   {status} '{code}': {description}")

def test_integration_example():
    """Test integration example"""
    print("\n=== Example Integration in Report Generation ===")

    def get_report_header(gang_code):
        """Example function for report header generation"""
        result = get_gang_description(gang_code)

        if result['success']:
            return {
                'title': 'DAFTAR UPAH KARYAWAN',
                'company': result['formatted_description'],
                'period': 'MEI 2025',
                'location': result['location_code'],
                'status': 'success'
            }
        else:
            return {
                'title': 'DAFTAR UPAH KARYAWAN',
                'company': 'PT. Rebinmas Jaya | GANG UNKNOWN',
                'period': 'MEI 2025',
                'location': gang_code,
                'status': 'warning',
                'message': result['message']
            }

    # Test integration
    header = get_report_header("H1H")
    print("Report Header Generated:")
    for key, value in header.items():
        print(f"   {key}: {value}")

    # Test with invalid gang
    header_invalid = get_report_header("NONEXIST")
    print("\nReport Header (Invalid Gang):")
    for key, value in header_invalid.items():
        print(f"   {key}: {value}")

def main():
    """Main test function"""
    print("GANG DESCRIPTION DECODER - COMPREHENSIVE TEST")
    print("=" * 60)

    try:
        test_specific_cases()
        test_format_validation()
        test_integration_example()

        print("\n" + "=" * 60)
        print("[SUCCESS] All tests completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()