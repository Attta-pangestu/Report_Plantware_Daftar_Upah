#!/usr/bin/env python3
"""
Database Connection Package
Comprehensive database connection and management framework

This package provides:
- Configuration management
- Connection pooling
- Query execution
- Data mapping (ORM-like features)
- Error handling and logging
- Performance monitoring

Classes:
- DatabaseConnector: Main interface for all database operations
- ConfigManager: Database configuration management
- ConnectionManager: Connection pooling and management
- QueryExecutor: Advanced query execution with ORM features
- ErrorHandler: Comprehensive error handling
- DatabaseLogger: Enhanced logging for database operations

Usage:
    from connection import DatabaseConnector, DatabaseConnectorConfig

    config = DatabaseConnectorConfig()
    connector = DatabaseConnector(config)
    connector.initialize()

    # Use connector for database operations
    result = connector.execute_query("SELECT * FROM table")
"""

# Core classes
from .database_connector import DatabaseConnector, DatabaseConnectorConfig
from .config_manager import ConfigManager, DatabaseConfig
from .connection_manager import ConnectionManager, ConnectionPoolConfig, PooledConnection
from .query_executor import QueryExecutor, QueryResult, QueryBuilder, QueryType
from .data_mapper import BaseModel, ModelRegistry, FieldMapping, DataType, model, field
from .error_handling import (
    ErrorHandler, DatabaseLogger, ErrorContext, ErrorSeverity, ErrorCategory,
    DatabaseError, with_error_handling, with_retry, AlertManager
)

# Version info
__version__ = "1.0.0"
__author__ = "Database Connector Team"
__description__ = "Comprehensive database connection framework for Daftar Upah system"

# Package exports
__all__ = [
    # Main interface
    'DatabaseConnector',
    'DatabaseConnectorConfig',

    # Configuration
    'ConfigManager',
    'DatabaseConfig',

    # Connection management
    'ConnectionManager',
    'ConnectionPoolConfig',
    'PooledConnection',

    # Query execution
    'QueryExecutor',
    'QueryResult',
    'QueryBuilder',
    'QueryType',

    # Data mapping
    'BaseModel',
    'ModelRegistry',
    'FieldMapping',
    'DataType',
    'model',
    'field',

    # Error handling
    'ErrorHandler',
    'DatabaseLogger',
    'ErrorContext',
    'ErrorSeverity',
    'ErrorCategory',
    'DatabaseError',
    'with_error_handling',
    'with_retry',
    'AlertManager',

    # Version and metadata
    '__version__',
    '__author__',
    '__description__'
]

# Quick access to main functionality
def create_connector(config_path: str = None, log_file: str = None, pool_size: int = 5):
    """
    Quick connector creation function

    Args:
        config_path: Path to configuration file
        log_file: Path to log file
        pool_size: Connection pool size

    Returns:
        DatabaseConnector: Initialized connector
    """
    from pathlib import Path

    config = DatabaseConnectorConfig(
        config_path=config_path,
        log_file=Path(log_file) if log_file else None,
        connection_pool_size=pool_size
    )

    connector = DatabaseConnector(config)
    connector.initialize()

    return connector

# Package-level convenience functions
def test_connection(config_path: str = None):
    """
    Test database connection

    Args:
        config_path: Path to configuration file

    Returns:
        bool: True if connection successful
    """
    connector = create_connector(config_path)
    return connector.test_connection()

def get_database_info(config_path: str = None):
    """
    Get database information

    Args:
        config_path: Path to configuration file

    Returns:
        Dict: Database information
    """
    with create_connector(config_path) as connector:
        return connector.get_connection_status()

# Example usage documentation
EXAMPLE_USAGE = '''
# Basic usage
from connection import DatabaseConnector

connector = DatabaseConnector()
connector.initialize()
connector.test_connection()

# Execute query
result = connector.execute_query("SELECT * FROM HR_EMPLOYEE")
print(f"Found {result.affected_rows} employees")

# Use query builder
builder = connector.create_query_builder()
query, params = builder.table("HR_EMPLOYEE")\\
    .select("EmpCode", "EmpName", "Gender")\\
    .where("Gender = ?", 1)\\
    .order_by("EmpName")\\
    .limit(10)\\
    .build()

result = connector.execute_query(query, params)

# Employee-specific methods
employees = connector.get_employees_by_gang("H1H", 50)
gangs = connector.get_all_gangs()

# Context manager usage
with DatabaseConnector() as connector:
    result = connector.execute_query("SELECT COUNT(*) FROM HR_EMPLOYEE")
    print(f"Total employees: {result.data[0]['']}")

# Error handling
from connection import with_error_handling, with_retry

@with_error_handling(component="MyApp", operation="get_data")
@with_retry(error_types=["connection", "timeout"])
def get_employee_data():
    with DatabaseConnector() as connector:
        return connector.get_employees_by_gang("H1H")

# Data mapping (when models are defined)
# employee = connector.find_model(HREmployee, "EMP001")
# employee.name = "Updated Name"
# connector.save_model(employee)
'''

# Print package info when imported
if __name__ != "__main__":
    print(f"Database Connection Package v{__version__} - {__description__}")