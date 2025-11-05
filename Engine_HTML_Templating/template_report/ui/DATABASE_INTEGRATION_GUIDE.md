# Database Integration Guide for Daftar Upah Template

## Overview

This guide explains how to integrate the Daftar Upah HTML template with your SQL Server database to populate employee information (NIK, Name, Gender) directly from the HR database.

## Database Query

The system uses this SQL query to fetch employee data:

```sql
SELECT TOP 100
    "HR_EMPLOYEE"."EmpCode",
    "HR_EMPLOYEE"."EmpName",
    "HR_EMPLOYEE"."Gender",
    "HR_EMPLOYEE"."LocCode"
FROM "HR_EMPLOYEE"
JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
WHERE "HR_GANGLN"."GangCode" = 'H1H'
```

### Field Mapping

| Database Field | Template Field | Description | Mapping Logic |
|---------------|---------------|-------------|---------------|
| `HR_EMPLOYEE.EmpCode` | `nik` | Employee Code | Direct mapping |
| `HR_EMPLOYEE.EmpName` | `nama` | Employee Name | Direct mapping |
| `HR_EMPLOYEE.Gender` | `jenis_kelamin` | Gender | **1 → L**, **0 → P** |
| `HR_EMPLOYEE.LocCode` | `loc_code` | Location Code | Direct mapping |

## Gender Mapping Implementation

```python
def _map_gender(self, gender_value) -> str:
    """
    Map database gender value to template format
    Input: 1 or 0 from database
    Output: 'L' for male, 'P' for female
    """
    if gender_value == 1 or str(gender_value).upper() == 'L':
        return 'L'  # Laki-laki
    elif gender_value == 0 or str(gender_value).upper() == 'P':
        return 'P'  # Perempuan
    else:
        return 'L'  # Default to L if unknown
```

## Files Created

### 1. Database Integration Module
**File**: `database_integration.py`
- Handles SQL Server database connections
- Executes the employee query
- Maps database fields to template format
- Implements gender mapping logic

### 2. Template Engine with Database Support
**File**: `daftar_upah_engine_db.py`
- Integrates database employee data with payroll information
- Merges database fields (nik, nama, jenis_kelamin) with sample payroll data
- Generates reports with real employee information

### 3. Demo Version (Works Without Database)
**File**: `daftar_upah_engine_demo.py`
- Simulates database integration using sample data
- Demonstrates field mapping and gender conversion
- Shows expected output format
- **Ready to test immediately**

## Usage

### Demo Version (Immediate Testing)
```bash
# Test database field mapping without database connection
python daftar_upah_engine_demo.py

# Specify gang code
python daftar_upah_engine_demo.py --gang H1H

# Custom output file
python daftar_upah_engine_demo.py --output test_report.html
```

### Production Version (Requires Database)
```bash
# Install required database driver
pip install pyodbc

# Run with database connection
python daftar_upah_engine_db.py --gang H1H

# Specify custom parameters
python daftar_upah_engine_db.py \
  --gang H1H \
  --limit 50 \
  --output payroll_h1h.html
```

## Database Configuration

Update `config.json` in the `Explore_database` folder:

```json
{
  "database": {
    "driver": "mssql",
    "server": "localhost",
    "port": 1433,
    "username": "sa",
    "password": "your_password",
    "database_name": "db_ptrj",
    "trusted_connection": false,
    "encrypt": false
  }
}
```

## Data Flow

1. **Database Query**: Fetch employee data from `HR_EMPLOYEE` and `HR_GANGLN` tables
2. **Field Mapping**: Convert database fields to template format
3. **Gender Mapping**: Convert Gender (1/0) to jenis_kelamin (L/P)
4. **Data Merging**: Combine employee info with payroll data
5. **Template Rendering**: Generate HTML report with real employee data

## Expected Output

The generated report will contain:

| NO | L/P | NIK | NAMA | ... payroll columns ... |
|----|-----|-----|------|------------------------|
| 1  | L   | EMP001 | AHMAD SUBEKTI | ... payroll data ... |
| 2  | P   | EMP002 | SITI NURHALIZA | ... payroll data ... |
| 3  | L   | EMP003 | BUDI SANTOSO | ... payroll data ... |

## Column Population Details

### NIK Column
- **Source**: `HR_EMPLOYEE.EmpCode`
- **Format**: Direct string copy
- **Example**: "EMP001", "EMP002"

### Nama Column
- **Source**: `HR_EMPLOYEE.EmpName`
- **Format**: Direct string copy
- **Example**: "AHMAD SUBEKTI", "SITI NURHALIZA"

### Jenis Kelamin Column
- **Source**: `HR_EMPLOYEE.Gender`
- **Mapping**: 1 → L, 0 → P
- **Example**: 1 → "L", 0 → "P"

## Testing the Integration

### Step 1: Test Demo Version
```bash
python daftar_upah_engine_demo.py
```
This will show you how the field mapping works without requiring database connection.

### Step 2: Verify Database Connection
```bash
python database_integration.py
```
This will test your database connection and show available gangs.

### Step 3: Generate Production Report
```bash
python daftar_upah_engine_db.py --gang H1H
```
This will generate a report with real employee data from your database.

## Troubleshooting

### Database Connection Issues
- **Error**: "Data source name not found"
- **Solution**: Install SQL Server driver: `pip install pyodbc`

### Query Issues
- **Error**: "Invalid object name 'HR_EMPLOYEE'"
- **Solution**: Verify table names and database schema

### Field Mapping Issues
- **Error**: Missing employee names or codes
- **Solution**: Check if query returns expected columns

## Customization

### Modify Gang Filter
Change the WHERE clause in the SQL query:
```sql
WHERE "HR_GANGLN"."GangCode" = 'YOUR_GANG_CODE'
```

### Add More Fields
Add fields to the SELECT statement and update the mapping logic:
```sql
SELECT
    "HR_EMPLOYEE"."EmpCode",
    "HR_EMPLOYEE"."EmpName",
    "HR_EMPLOYEE"."Gender",
    "HR_EMPLOYEE"."LocCode",
    "HR_EMPLOYEE"."Department"  -- New field
```

### Change Gender Mapping
Update the `_map_gender()` function in `database_integration.py`:
```python
def _map_gender(self, gender_value) -> str:
    if gender_value == 'M':  # If database uses 'M'/'F'
        return 'L'
    elif gender_value == 'F':
        return 'P'
    # ... other mapping logic
```

## Production Deployment

1. **Install Dependencies**: `pip install pyodbc`
2. **Configure Database**: Update `config.json`
3. **Test Connection**: Run `database_integration.py`
4. **Generate Report**: Use `daftar_upah_engine_db.py`
5. **Schedule Reports**: Set up cron jobs or scheduled tasks

## Security Notes

- Store database credentials securely
- Use parameterized queries (already implemented)
- Limit database user permissions to read-only
- Validate input parameters (gang codes, limits)

The integration is now ready for production use with proper field mapping and gender conversion as specified!