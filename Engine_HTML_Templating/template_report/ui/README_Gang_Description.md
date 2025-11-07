# Gang Description Decoder

## Overview

Module ini menyediakan fungsi untuk mendapatkan deskripsi gang dari database berdasarkan kode gang.

## Quick Usage

### Import
```python
from gang_description import get_gang_description, list_all_gangs
```

### Get Gang Description
```python
# Get specific gang description
result = get_gang_description("H1H")

if result['success']:
    print(f"Deskripsi: {result['formatted_description']}")
    # Output: PT. Rebinmas Jaya | HARVESTING AIK BANGEK H1H
else:
    print(f"Error: {result['message']}")
```

### List All Gangs
```python
# Get all available gangs
all_gangs = list_all_gangs()

if all_gangs['success']:
    print(f"Total: {all_gangs['total']} gang")
    for gang in all_gangs['gangs']:
        print(f"{gang['gang_code']}: {gang['formatted_description']}")
```

## Function Reference

### `get_gang_description(gang_code: str) -> Dict[str, Any]`

**Parameters:**
- `gang_code` (str): Kode gang yang akan dicari (contoh: "H1H")

**Returns:**
Dictionary dengan key:
- `success` (bool): Status keberhasilan
- `gang_code` (str): Kode gang
- `description` (str): Deskripsi gang dari database
- `formatted_description` (str): Format lengkap: "PT. Rebinmas Jaya | [deskripsi] [gang_code]"
- `company_name` (str): "PT. Rebinmas Jaya"
- `location_code` (str): Kode lokasi
- `message` (str): Pesan status
- `error` (str): Error message (jika ada)

**Example:**
```python
result = get_gang_description("H1H")
# Returns:
# {
#     'success': True,
#     'gang_code': 'H1H',
#     'description': 'HARVESTING AIK BANGEK',
#     'formatted_description': 'PT. Rebinmas Jaya | HARVESTING AIK BANGEK H1H',
#     'company_name': 'PT. Rebinmas Jaya',
#     'location_code': 'H1H',
#     'message': 'Deskripsi gang berhasil ditemukan',
#     'error': None
# }
```

### `list_all_gangs() -> Dict[str, Any]`

**Returns:**
Dictionary dengan key:
- `success` (bool): Status keberhasilan
- `gangs` (list): List semua gang
- `total` (int): Jumlah total gang
- `message` (str): Pesan status
- `error` (str): Error message (jika ada)

## Error Handling

Fungsi ini menangani beberapa error cases:
- Gang tidak ditemukan: `{'success': False, 'message': "Gang 'XXX' tidak ditemukan"}`
- File tidak ada: `{'success': False, 'error': "File tidak ditemukan: ..."}`
- Database error: `{'success': False, 'error': "Database error: ..."}`

## Examples

### Basic Usage
```python
from gang_description import get_gang_description

# Test with existing gang
result = get_gang_description("H1H")
print(result['formatted_description'])
# PT. Rebinmas Jaya | HARVESTING AIK BANGEK H1H

# Test with non-existing gang
result = get_gang_description("NONEXIST")
print(result['message'])
# Gang 'NONEXIST' tidak ditemukan
```

### Integration with Other Systems
```python
def get_company_header(gang_code: str) -> str:
    """Get formatted company header for reports"""
    result = get_gang_description(gang_code)

    if result['success']:
        return result['formatted_description']
    else:
        # Fallback to default
        return "PT. Rebinmas Jaya | GANG UNKNOWN"

# Usage in report generation
header = get_company_header("H1H")
print(header)
# PT. Rebinmas Jaya | HARVESTING AIK BANGEK H1H
```

## Database Connection

Fungsi ini menggunakan konfigurasi database dari file:
`D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json`

Pastikan file konfigurasi tersedia dan database dapat diakses.

## Dependencies

- Python 3.6+
- pyodbc
- json
- pathlib

## Testing

Run the module directly to see example usage:
```bash
python gang_description.py
```