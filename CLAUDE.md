# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a payroll reporting system ("Daftar Upah Reporting") for PT Rebinmas that generates employee payroll data in both Excel and HTML formats. The system processes employee payroll data including salaries, allowances, deductions, and attendance information.

## Architecture

The project consists of several main components:

### 1. Excel Templating Engine (`Engine_Templating/`)
- **Core Engine**: `engine/template_engine.py` - Main Excel generation engine with placeholder support
- **Helper Functions**: `engine/helpers.py` - Utility functions for formatting, validation, and parsing
- **CLI Interface**: `engine/cli.py` - Command-line interface for template operations
- **Features**:
  - Placeholder syntax: `${field}` for single values
  - Looping: `${data_upah[]}` to repeat template rows
  - Calculations: `${sum(field)}`, `${count(data_upah)}`, `${expr: field1 + field2}`
  - Formatting: `${format(field,"currency")}`, `${format(field,"date:%Y-%m-%d")}`

### 2. HTML Templating Engine (`Engine_HTML_Templating/`)
- **Template Engine**: `template_engine.py` - HTML report generation
- **Excel Integration**: `excel_engine.py`, `read_excel.py` - Excel file processing
- **F4 Print Engine**: `f4_print_engine.py` - Specialized formatting for F4 printing
- **Simple Engine**: `simple_engine.py` - Simplified template processing

### 3. Database Integration (`Explore_database/`)
- **Connection**: `test_connection.py` - Database connectivity testing
- **Configuration**: `config.json` - Database connection settings (MSSQL)
- **Query Testing**: `test_query/test.sql` - SQL query examples

### 4. Context Portal (`context_portal/`)
- **Database**: SQLite database for context management
- **Migrations**: Alembic database migrations in `alembic/`
- **Logging**: Application logs in `logs/`

### 5. Template References (`Template_Referensi/`)
- **Empty Templates**: `Template_Kosong/` - Base Excel templates
- **Sample Files**: Reference HTML and CSS files for formatting

## Common Development Commands

### Excel Template Generation
```bash
# Install dependencies
pip install -r Engine_Templating/requirements.txt

# Create dummy template with placeholders
python -m Engine_Templating.engine.cli make-dummy-template

# Generate sample data (default 50 rows)
python -m Engine_Templating.engine.cli gen-data --rows 50 --out Engine_Templating/data/sample_daftar_upah.json

# Generate Excel report from template
python -m Engine_Templating.engine.cli generate \
  --template Engine_Templating/templates/Dummy_Template_Daftar_Upah.xlsx \
  --json Engine_Templating/data/sample_daftar_upah.json \
  --out Engine_Templating/output/Daftar_Upah_Output.xlsx

# Generate using original template as reference
python -m Engine_Templating.engine.cli generate \
  --template "path/to/original/Template_Daftar_Upah.xlsx" \
  --json Engine_Templating/data/sample_daftar_upah.json \
  --out Engine_Templating/output/Daftar_Upah_Output_From_Original.xlsx
```

### HTML Report Generation
```bash
cd Engine_HTML_Templating
python template_engine.py  # Generates daftar_upah_report.html
```

### Database Operations
```bash
cd Explore_database
python test_connection.py  # Test database connectivity
```

## Data Structure

### Employee Data Format
```json
{
  "bulan": "MEI",
  "tahun": "2025",
  "perusahaan": "Company Name",
  "periode": "May 2025",
  "disetujui_oleh": "Manager Name",
  "data_upah": [
    {
      "no": 1,
      "nama": "Employee Name",
      "jabatan": "Position",
      "tanggal": "2025-05-01",
      "gaji_pokok": 3000000,
      "tunjangan": 500000,
      "potongan": 200000,
      "total_gaji": 3300000,
      "catatan": "Notes"
    }
  ]
}
```

### Complex Payroll Structure (HTML Engine)
```json
{
  "karyawan": [
    {
      "jenis_kelamin": "L",
      "nik": "1234567890",
      "nama": "EMPLOYEE NAME",
      "cuti": {
        "sakit": {"hari": 0, "jumlah": 0},
        "haid": {"hari": 0, "jumlah": 0}
      },
      "tunjangan": {
        "beras": {"tarif": 0, "jumlah": 0},
        "jabatan": {"tarif": 0, "jumlah": 0}
      },
      "potongan": {
        "astek": {"pekerja": 0, "majikan": 0, "jumlah": 0}
      },
      "upah_kotor": 0,
      "upah_bersih": 0
    }
  ]
}
```

## Template Conventions

### Excel Templates
- **Header cells**: `${perusahaan}`, `${periode}`, `${disetujui_oleh}`
- **Loop marker**: `${data_upah[]}` in any cell to indicate data row start
- **Template row**: Placeholders like `${no}`, `${nama}`, `${format(total_gaji,"currency")}`
- **Footer calculations**: `${sum(total_gaji)}`, `${count(data_upah)}`

### HTML Templates
- **Variables**: `{variable_name}` for simple replacement
- **Employee rows**: `{employee_rows}` placeholder for looped content
- **Nested data**: `{{total.cuti.sakit.hari}}` for complex structures
- **Currency formatting**: Handled automatically by engine

## Database Configuration

The system connects to MSSQL database with these settings:
- **Server**: localhost:1433 (configurable in `Explore_database/config.json`)
- **Database**: db_ptrj
- **Authentication**: SQL Server Authentication
- **Driver**: mssql

## Dependencies

### Core Excel Engine
- `openpyxl>=3.1.2` - Excel file manipulation
- `python-dateutil>=2.9.0` - Date parsing utilities

### Database Integration
- `pyodbc` - Database connectivity

## Output Locations

- **Excel Reports**: `Engine_Templating/output/`
- **HTML Reports**: `Engine_HTML_Templating/output/`
- **Sample Data**: `Engine_Templating/data/`
- **Generated Templates**: `Engine_Templating/templates/`

## Testing and Validation

- Generate 50-row dataset to verify basic functionality
- Test with >1000 rows for performance validation
- Verify placeholder filling and formatting in both Excel and HTML outputs
- Test database connectivity before running data extraction queries