# Daftar Upah HTML Template Engine

A comprehensive HTML templating system for generating payroll reports compatible with the Excel-generated reference structure.

## Overview

This template engine processes payroll data from JSON files and generates professional HTML reports that maintain the same structure and formatting as the original Excel templates. It's specifically designed for PT Rebinmas payroll reporting with support for complex payroll calculations, multiple deduction/allowance types, and print-ready formatting.

## Features

- **Excel-Compatible Structure**: Maintains the same table structure as Excel-exported templates
- **Large Dataset Support**: Efficiently handles hundreds of employee records
- **Comprehensive Payroll Fields**: Supports all payroll components including:
  - Various leave types (annual, sick, menstrual, national, maternity, etc.)
  - Multiple allowance categories (rice, position, tenure, overtime, etc.)
  - Complete deduction calculations (ASTEK, BPJS, tax, loans)
  - Attendance tracking
- **Professional Formatting**: Print-ready CSS with proper currency formatting
- **Flexible Template System**: Easy to modify and extend
- **Error Handling**: Robust error handling with informative messages

## File Structure

```
ui/
├── daftar_upah_template.html      # Main HTML template
├── daftar_upah_engine.py          # Template engine implementation
├── test_template_engine.py        # Testing script
├── README.md                      # This documentation
└── output/                        # Generated reports directory
    ├── daftar_upah_report_large.html
    └── daftar_upah_report_mei-2025.html
```

## Data Format

The engine expects JSON data in this format:

```json
{
  "bulan": "MEI",
  "tahun": "2025",
  "catatan": "Payroll period notes",
  "upah_dasar": "Base wage information",
  "karyawan": [
    {
      "jenis_kelamin": "L",
      "nik": "1234567890",
      "nama": "EMPLOYEE NAME",
      "cuti_tahun_hari": 0,
      "cuti_tahun_jumlah": 0,
      "cuti_sakit_hari": 0,
      "cuti_sakit_jumlah": 0,
      "cuti_haid_hari": 0,
      "cuti_haid_jumlah": 0,
      "cuti_minggu_hari": 0,
      "cuti_minggu_jumlah": 0,
      "cuti_nasional_hari": 2,
      "cuti_nasional_jumlah": 0,
      "cuti_hamil_hari": 0,
      "cuti_hamil_jumlah": 0,
      "cuti_izin_hari": 1,
      "cuti_izin_jumlah": 0,
      "jumlah_hk": 22,
      "tunjangan_beras": 15000,
      "tunjangan_beras_jumlah": 330000,
      "tunjangan_jabatan": 5000,
      "tunjangan_jabatan_hk": 22,
      "tunjangan_masa_kerja": 2000,
      "tunjangan_masa_kerja_jumlah": 44000,
      "tunjangan_lembur": 250000,
      "tunjangan_premi": 150000,
      "tunjangan_koreksi": 0,
      "upah_kotor": 4840000,
      "potongan_astek_pekerja": 200000,
      "potongan_astek_majikan": 300000,
      "potongan_astek_jumlah": 500000,
      "potongan_bpjs_kesehatan": 100000,
      "potongan_bpjs_pekerja": 50000,
      "potongan_bpjs_pensiun": 75000,
      "potongan_bpjs_majikan": 75000,
      "potongan_bpjs_jumlah": 225000,
      "potongan_pph21": 150000,
      "potongan_premi_kontan": 0,
      "potongan_lebih_potong_pajak_thr": 0,
      "potongan_pinjaman_uang": 200000,
      "upah_bersih": 3750000,
      "tidak_hadir_cth": 0,
      "tidak_hadir_alpa": 0
    }
  ]
}
```

## Usage

### Command Line Interface

```bash
# Basic usage with default files
python daftar_upah_engine.py

# Specify custom template and data files
python daftar_upah_engine.py --template custom_template.html --data custom_data.json

# Specify output filename
python daftar_upah_engine.py --output payroll_report.html

# View all options
python daftar_upah_engine.py --help
```

### Programmatic Usage

```python
from daftar_upah_engine import DaftarUpahTemplateEngine

# Initialize engine
engine = DaftarUpahTemplateEngine()

# Generate report
result = engine.generate_report(
    template_file="daftar_upah_template.html",
    data_file="../large_data.json",
    output_file="my_payroll_report.html"
)

if result:
    print(f"Report generated: {result}")
```

## Template Customization

The HTML template (`daftar_upah_template.html`) can be customized by:

1. **Modifying CSS styles**: Change colors, fonts, spacing in the `<style>` section
2. **Adding new columns**: Update both table headers and employee row rendering
3. **Changing layout**: Modify the table structure in the template
4. **Adding new sections**: Include additional header or footer information

### Adding New Payroll Fields

1. Add the field to the JSON data structure
2. Update the table headers in the HTML template
3. Modify the `render_employee_row()` method in `daftar_upah_engine.py`
4. Update the `calculate_totals()` method if needed

## Output Features

- **Print Optimization**: CSS includes @page rules for proper printing
- **Responsive Design**: Table adapts to different screen sizes
- **Currency Formatting**: Automatic Rupiah formatting with proper thousand separators
- **Professional Styling**: Clean, corporate appearance suitable for official reports
- **Automatic Calculations**: Totals are calculated automatically for all numeric columns

## Performance

- **Memory Efficient**: Processes large datasets without excessive memory usage
- **Fast Rendering**: Optimized template rendering for quick report generation
- **Scalable**: Tested with datasets of 1000+ employee records

## Error Handling

The engine includes comprehensive error handling for:
- Missing template files
- Invalid JSON data
- Missing required fields
- File permission issues
- Path resolution problems

## Dependencies

- Python 3.7+
- No external libraries required (uses only Python standard library)

## Testing

Use the included test script to verify functionality:

```bash
python test_template_engine.py
```

This will generate a test report using the `large_data.json` file.

## Output Directory

Generated reports are saved to the `output/` directory by default. The directory is created automatically if it doesn't exist.

## Integration with Main Project

This template engine is designed to integrate with the main Daftar Upah reporting system:

- Compatible with existing data structures
- Maintains Excel template compatibility
- Supports the same payroll calculation logic
- Can be called from the main reporting pipeline

## Support

For issues or questions:
1. Check this README documentation
2. Review the example outputs in the `output/` directory
3. Test with the provided sample data files
4. Verify template syntax if making customizations