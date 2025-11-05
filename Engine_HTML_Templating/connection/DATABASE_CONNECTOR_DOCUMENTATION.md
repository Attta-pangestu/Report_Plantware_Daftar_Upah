# Database Connector Framework - Complete Documentation

## Overview

The Database Connector Framework is a comprehensive, enterprise-grade database access layer built for the Daftar Upah payroll system. It provides professional database operations with connection pooling, ORM-like features, error handling, and performance monitoring.

## Architecture

The framework consists of 7 main components:

### 1. Configuration Manager (`config_manager.py`)
**Purpose**: Manages database configuration with validation and multiple environment support.

**Key Features**:
- JSON configuration loading and validation
- Multiple environment support (dev/staging/prod)
- Connection string generation
- Configuration validation

**Usage**:
```python
from config_manager import ConfigManager

config_manager = ConfigManager("config.json")
config = config_manager.load_config()
conn_str = config_manager.get_connection_string()
```

### 2. Connection Manager (`connection_manager.py`)
**Purpose**: Advanced connection pooling with health monitoring and retry logic.

**Key Features**:
- Connection pooling with configurable pool sizes
- Health checks and automatic connection cleanup
- Connection timeout and retry logic
- Performance statistics tracking

**Usage**:
```python
from connection_manager import ConnectionManager

with ConnectionManager(config) as conn_mgr:
    with conn_mgr.get_connection() as conn:
        result = conn.execute("SELECT * FROM table")
```

### 3. Query Executor (`query_executor.py`)
**Purpose**: Advanced SQL query execution with ORM-like features and result mapping.

**Key Features**:
- Parameterized queries with automatic type handling
- Query builder for dynamic SQL generation
- Batch operations and transaction support
- Performance analysis and execution plans
- Multiple fetch modes (all, one, many, scalar)

**Usage**:
```python
from query_executor import QueryExecutor, QueryBuilder

executor = QueryExecutor(connection_manager)

# Simple query
result = executor.execute_query("SELECT * FROM HR_EMPLOYEE WHERE Gender = ?", [1])

# Query builder
builder = executor.create_query_builder()
query, params = builder.table("HR_EMPLOYEE")\
    .select("EmpCode", "EmpName", "Gender")\
    .where("Gender = ?", 1)\
    .order_by("EmpName")\
    .limit(10)\
    .build()
result = executor.execute_query(query, params)
```

### 4. Data Mapper (`data_mapper.py`)
**Purpose**: ORM-like data mapping with validation and type conversion.

**Key Features**:
- Model-based database operations
- Field validation and type conversion
- Automatic CRUD operations
- Relationship mapping
- Table creation from models

**Usage**:
```python
from data_mapper import BaseModel, FieldMapping, DataType, field

@model("HR_EMPLOYEE")
class HREmployee(BaseModel):
    EmpCode = field("EmpCode", DataType.STRING, required=True, max_length=20, is_primary_key=True)
    EmpName = field("EmpName", DataType.STRING, required=True, max_length=100)
    Gender = field("Gender", DataType.INTEGER, required=True)  # 1=L, 0=P

# Create and save
employee = HREmployee(EmpCode="EMP001", EmpName="John Doe", Gender=1)
employee.save()

# Find and update
emp = HREmployee.find_by_id("EMP001")
emp.EmpName = "Jane Doe"
emp.save()
```

### 5. Error Handling (`error_handling.py`)
**Purpose**: Comprehensive error handling with logging, retry logic, and alerting.

**Key Features**:
- Error classification and severity levels
- Automatic retry with exponential backoff
- Comprehensive logging with performance tracking
- Alert management for critical errors
- Error statistics and monitoring

**Usage**:
```python
from error_handling import ErrorHandler, DatabaseLogger, with_error_handling, with_retry

logger = DatabaseLogger("my_app")
error_handler = ErrorHandler(logger)

@with_error_handling(component="Payroll", operation="CalculateSalaries")
@with_retry(error_types=["connection", "timeout"], max_attempts=3)
def calculate_salaries():
    # Database operations here
    pass
```

### 6. Database Connector (`database_connector.py`)
**Purpose**: Main unified interface providing access to all framework features.

**Key Features**:
- Single point of access to all database operations
- Automatic initialization and cleanup
- Performance metrics collection
- Employee-specific methods for Daftar Upah system
- Context manager support

**Usage**:
```python
from database_connector import DatabaseConnector, DatabaseConnectorConfig

# Initialize
config = DatabaseConnectorConfig(
    log_file=Path("app.log"),
    connection_pool_size=5,
    max_retry_attempts=3
)

connector = DatabaseConnector(config)
connector.initialize()

# Use as context manager
with DatabaseConnector(config) as connector:
    # Simple query
    result = connector.execute_query("SELECT * FROM HR_EMPLOYEE")

    # Employee-specific methods
    employees = connector.get_employees_by_gang("H1H", 50)
    gangs = connector.get_all_gangs()

    # Model operations
    employee = connector.find_model(HREmployee, "EMP001")
```

### 7. Package Interface (`__init__.py`)
**Purpose**: Clean package interface with convenience functions.

**Key Features**:
- Single import access to all components
- Convenience functions for common operations
- Version and metadata information
- Example usage documentation

**Usage**:
```python
import connection

# Quick connector creation
connector = connection.create_connector(pool_size=5)

# Quick operations
success = connection.test_connection("config.json")
db_info = connection.get_database_info("config.json")
```

## Employee Data Integration

The framework is specifically designed for the Daftar Upah system with built-in support for employee data:

### Standard Employee Query
```python
# Get employees by gang
employees = connector.get_employees_by_gang("H1H", 100)

# Result format
[
    {
        "EmpCode": "EMP001",
        "EmpName": "AHMAD SUBEKTI",
        "Gender": 1,  # 1 = Male, 0 = Female
        "LocCode": "LOC001"
    },
    ...
]
```

### Gender Mapping
The framework includes built-in gender mapping as specified:

```python
def map_gender(gender_value) -> str:
    """
    Maps database gender value to template format
    Input: 1 or 0 from database
    Output: 'L' for male (1), 'P' for female (0)
    """
    if gender_value == 1:
        return 'L'  # Laki-laki
    elif gender_value == 0:
        return 'P'  # Perempuan
    else:
        return 'L'  # Default to L
```

### Gang Operations
```python
# Get all available gangs
gangs = connector.get_all_gangs()
# Result: ["H1H", "H2H", "H3H", ...]

# Get employee count for specific gang
count = connector.get_employee_count_by_gang("H1H")
# Result: 25
```

## Configuration

### Database Configuration (`config.json`)
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
    "encrypt": false,
    "connection_timeout": 30,
    "command_timeout": 60,
    "pool_size": 5,
    "max_overflow": 10
  }
}
```

### Connector Configuration
```python
from database_connector import DatabaseConnectorConfig

config = DatabaseConnectorConfig(
    config_path="path/to/config.json",
    log_file=Path("database.log"),
    log_level="INFO",
    enable_console_logging=True,
    enable_error_handling=True,
    enable_retry_logic=True,
    connection_pool_size=5,
    connection_timeout=30,
    command_timeout=60,
    max_retry_attempts=3,
    retry_delay=1.0
)
```

## Performance Features

### Connection Pooling
- Configurable pool sizes (min/max connections)
- Automatic health checks and cleanup
- Connection timeout handling
- Performance statistics

### Query Optimization
- Parameterized queries for security
- Execution plan analysis
- Query performance tracking
- Slow query identification

### Caching and Monitoring
- Query result caching
- Performance metrics collection
- Error rate monitoring
- Resource usage tracking

## Error Handling

### Error Classification
- **Connection Errors**: Database connectivity issues
- **Query Errors**: SQL syntax and execution problems
- **Validation Errors**: Data validation failures
- **Timeout Errors**: Operation timeouts
- **Permission Errors**: Access control issues

### Retry Logic
- Exponential backoff for retries
- Configurable retry attempts per error type
- Automatic connection recovery
- Transaction rollback on errors

### Logging and Alerting
- Comprehensive query logging
- Error classification and severity levels
- Performance metrics logging
- Critical error alerting

## Usage Patterns

### Basic Database Operations
```python
# Simple SELECT
result = connector.execute_query(
    "SELECT * FROM HR_EMPLOYEE WHERE Gender = ?",
    [1]
)

# INSERT
result = connector.insert("HR_EMPLOYEE", {
    "EmpCode": "EMP002",
    "EmpName": "Jane Doe",
    "Gender": 0
})

# UPDATE
result = connector.update(
    "HR_EMPLOYEE",
    {"EmpName": "Updated Name"},
    "EmpCode = ?",
    ["EMP001"]
)

# DELETE
result = connector.delete("HR_EMPLOYEE", "EmpCode = ?", ["EMP001"])
```

### Advanced Query Building
```python
builder = connector.create_query_builder()

# Complex query with joins
query, params = builder.table("HR_EMPLOYEE e")\
    .select("e.EmpCode", "e.EmpName", "g.GangCode")\
    .join("HR_GANGLN g", "e.EmpCode = g.GangMember")\
    .where("e.Gender = ?", 1)\
    .where("g.GangCode = ?", "H1H")\
    .order_by("e.EmpName")\
    .limit(50)\
    .build()

result = connector.execute_query(query, params)
```

### Batch Operations
```python
queries = [
    ("INSERT INTO HR_EMPLOYEE (EmpCode, EmpName) VALUES (?, ?)", ["EMP001", "John"]),
    ("INSERT INTO HR_EMPLOYEE (EmpCode, EmpName) VALUES (?, ?)", ["EMP002", "Jane"]),
    ("INSERT INTO HR_EMPLOYEE (EmpCode, EmpName) VALUES (?, ?)", ["EMP003", "Bob"])
]

result = connector.execute_batch(queries)
```

### Transaction Management
```python
with connector as conn:
    # All operations in this block are in a single transaction
    conn.execute_query("INSERT INTO table1 ...")
    conn.execute_query("UPDATE table2 ...")
    conn.execute_query("DELETE FROM table3 ...")
    # Automatic commit on success, rollback on error
```

## Integration with Daftar Upah Template

### Complete Integration Example
```python
from database_connector import DatabaseConnector

# Initialize connector
connector = DatabaseConnector()
connector.initialize()

def generate_payroll_report(gang_code="H1H"):
    """Generate payroll report with real employee data"""

    # Get employee data from database
    db_employees = connector.get_employees_by_gang(gang_code, 100)

    # Map to template format with gender conversion
    mapped_employees = []
    for emp in db_employees:
        mapped_emp = {
            'nik': emp['EmpCode'],
            'nama': emp['EmpName'],
            'jenis_kelamin': 'L' if emp['Gender'] == 1 else 'P',
            'loc_code': emp['LocCode']
        }
        mapped_employees.append(mapped_emp)

    # Merge with payroll data and generate report
    # ... (use with template engine)

    return mapped_employees

# Generate report
employees = generate_payroll_report("H1H")
print(f"Generated report for {len(employees)} employees")
```

## File Structure

```
connection/
├── __init__.py                 # Package interface
├── config_manager.py          # Configuration management
├── connection_manager.py       # Connection pooling
├── query_executor.py          # Query execution and building
├── data_mapper.py              # ORM-like data mapping
├── error_handling.py           # Error handling and logging
├── database_connector.py       # Main interface
├── test_framework.py           # Testing framework
└── DATABASE_CONNECTOR_DOCUMENTATION.md
```

## Installation and Setup

### Prerequisites
- Python 3.7+
- pyodbc package for SQL Server connectivity
- Access to SQL Server database

### Installation
```bash
# Install required packages
pip install pyodbc

# Place the connection package in your project
cp -r connection/ your_project/path/

# Update database configuration
# Edit config.json with your database details
```

### Basic Setup
```python
from database_connector import DatabaseConnector

# Quick setup and test
connector = DatabaseConnector()
if connector.initialize():
    if connector.test_connection():
        print("Database connector ready!")
    else:
        print("Database connection failed")
else:
    print("Failed to initialize database connector")
```

## Best Practices

### 1. Connection Management
- Use context managers for automatic cleanup
- Configure appropriate pool sizes
- Monitor connection statistics
- Handle connection errors gracefully

### 2. Query Performance
- Use parameterized queries
- Implement query result caching
- Monitor slow queries
- Use query builder for complex SQL

### 3. Error Handling
- Implement proper error classification
- Use retry logic for recoverable errors
- Log all database operations
- Monitor error rates and patterns

### 4. Security
- Always use parameterized queries
- Validate input parameters
- Implement proper access controls
- Use least privilege database users

### 5. Monitoring
- Track query performance metrics
- Monitor connection pool health
- Log errors and warnings
- Set up alerts for critical issues

## Troubleshooting

### Common Issues

**Connection Errors**:
- Check database server status
- Verify network connectivity
- Validate connection string format
- Check user permissions

**Query Errors**:
- Validate SQL syntax
- Check table and column names
- Verify parameter types and counts
- Review error messages for details

**Performance Issues**:
- Monitor query execution times
- Check connection pool utilization
- Review slow query logs
- Optimize frequently used queries

**Memory Issues**:
- Monitor connection pool size
- Check for connection leaks
- Review result set sizes
- Implement result streaming for large datasets

## Conclusion

The Database Connector Framework provides a robust, production-ready solution for database operations in the Daftar Upah system. It offers:

- **Professional Architecture**: Separation of concerns with clear interfaces
- **High Performance**: Connection pooling and query optimization
- **Comprehensive Error Handling**: Retry logic, logging, and monitoring
- **Developer Friendly**: ORM-like features and query builders
- **Production Ready**: Complete testing and documentation

The framework is designed to scale with your application needs while maintaining data integrity and performance standards.