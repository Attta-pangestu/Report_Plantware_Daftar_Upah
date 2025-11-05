#!/usr/bin/env python3
"""
Data Mapper - ORM-like Data Mapping and Transformation
Provides object-relational mapping capabilities with custom field mapping and validation
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Callable, Union
from dataclasses import dataclass, field, fields, asdict
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
import json
import inspect
from abc import ABC, abstractmethod

from query_executor import QueryExecutor, QueryResult


T = TypeVar('T', bound='BaseModel')


class DataType(Enum):
    """Supported data types for field mapping"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    JSON = "json"
    TEXT = "text"


@dataclass
class FieldMapping:
    """Field mapping configuration"""
    field_name: str
    column_name: str
    data_type: DataType
    required: bool = False
    default: Any = None
    transformer: Optional[Callable[[Any], Any]] = None
    validator: Optional[Callable[[Any], bool]] = None
    is_primary_key: bool = False
    auto_generated: bool = False
    read_only: bool = False
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None


class ValidationError(Exception):
    """Data validation error"""
    pass


class BaseModel(ABC):
    """Base model class for ORM-like functionality"""

    _table_name: Optional[str] = None
    _field_mappings: Dict[str, FieldMapping] = {}
    _query_executor: Optional[QueryExecutor] = None

    def __init__(self, **kwargs):
        """Initialize model with field values"""
        self._set_fields(**kwargs)
        self._validate()

    def _set_fields(self, **kwargs):
        """Set field values from keyword arguments"""
        for field_name, field_mapping in self._field_mappings.items():
            value = kwargs.get(field_name, field_mapping.default)
            setattr(self, field_name, value)

    def _validate(self):
        """Validate model data"""
        for field_name, field_mapping in self._field_mappings.items():
            value = getattr(self, field_name)

            # Check required fields
            if field_mapping.required and (value is None or value == ""):
                raise ValidationError(f"Required field '{field_name}' is missing")

            # Run custom validator
            if field_mapping.validator and value is not None:
                if not field_mapping.validator(value):
                    raise ValidationError(f"Validation failed for field '{field_name}' with value '{value}'")

            # Check data type constraints
            self._validate_field_type(field_name, value, field_mapping)

    def _validate_field_type(self, field_name: str, value: Any, field_mapping: FieldMapping):
        """Validate field type and constraints"""
        if value is None:
            return

        try:
            if field_mapping.data_type == DataType.INTEGER:
                int(value)
            elif field_mapping.data_type == DataType.FLOAT:
                float(value)
            elif field_mapping.data_type == DataType.DECIMAL:
                decimal.Decimal(value)
            elif field_mapping.data_type == DataType.BOOLEAN:
                bool(value)
            elif field_mapping.data_type == DataType.DATE:
                if isinstance(value, str):
                    datetime.strptime(value, '%Y-%m-%d')
                elif not isinstance(value, date):
                    raise ValueError("Invalid date format")
            elif field_mapping.data_type == DataType.DATETIME:
                if isinstance(value, str):
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif not isinstance(value, datetime):
                    raise ValueError("Invalid datetime format")
            elif field_mapping.data_type == DataType.JSON:
                if isinstance(value, str):
                    json.loads(value)
                elif not isinstance(value, (dict, list)):
                    raise ValueError("Invalid JSON format")

            # Check length constraint
            if field_mapping.max_length and isinstance(value, str):
                if len(value) > field_mapping.max_length:
                    raise ValidationError(f"Field '{field_name}' exceeds maximum length of {field_mapping.max_length}")

        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            raise ValidationError(f"Invalid data type for field '{field_name}': {e}")

    @classmethod
    def set_query_executor(cls, query_executor: QueryExecutor):
        """Set query executor for model operations"""
        cls._query_executor = query_executor

    @classmethod
    def get_table_name(cls) -> str:
        """Get table name for this model"""
        return cls._table_name or cls.__name__.lower()

    @classmethod
    def create_table_sql(cls) -> str:
        """Generate CREATE TABLE SQL for this model"""
        if not cls._field_mappings:
            raise ValueError("No field mappings defined")

        column_definitions = []
        primary_keys = []

        for field_name, field_mapping in cls._field_mappings.items():
            # Map data types to SQL types
            sql_type = cls._map_data_type_to_sql(field_mapping)
            nullable = "NOT NULL" if field_mapping.required else "NULL"

            # Default value
            default = ""
            if field_mapping.default is not None:
                if field_mapping.data_type == DataType.STRING:
                    default = f" DEFAULT '{field_mapping.default}'"
                elif field_mapping.data_type == DataType.BOOLEAN:
                    default = f" DEFAULT {1 if field_mapping.default else 0}"
                else:
                    default = f" DEFAULT {field_mapping.default}"

            # Auto-increment for primary key
            auto_increment = ""
            if field_mapping.is_primary_key and field_mapping.auto_generated:
                auto_increment = " IDENTITY(1,1)"

            column_def = f"{field_mapping.column_name} {sql_type} {nullable}{default}{auto_increment}"
            column_definitions.append(column_def)

            if field_mapping.is_primary_key:
                primary_keys.append(field_mapping.column_name)

        # Add primary key constraint
        if primary_keys:
            pk_columns = ', '.join(primary_keys)
            pk_constraint = f", PRIMARY KEY ({pk_columns})"
            column_definitions.append(pk_constraint)

        table_name = cls.get_table_name()
        columns_joined = ',\n    '.join(column_definitions)
        create_sql = f"CREATE TABLE {table_name} (\n    {columns_joined}\n)"

        return create_sql

    @classmethod
    def _map_data_type_to_sql(cls, field_mapping: FieldMapping) -> str:
        """Map Python data type to SQL data type"""
        type_mapping = {
            DataType.STRING: f"NVARCHAR({field_mapping.max_length or 255})",
            DataType.TEXT: "NVARCHAR(MAX)",
            DataType.INTEGER: "INT",
            DataType.FLOAT: "FLOAT",
            DataType.DECIMAL: f"DECIMAL({field_mapping.precision or 18}, {field_mapping.scale or 2})",
            DataType.BOOLEAN: "BIT",
            DataType.DATE: "DATE",
            DataType.DATETIME: "DATETIME",
            DataType.JSON: "NVARCHAR(MAX)"
        }

        return type_mapping.get(field_mapping.data_type, "NVARCHAR(255)")

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create model instance from dictionary"""
        # Transform field names using mapping
        transformed_data = {}
        for field_name, field_mapping in cls._field_mappings.items():
            if field_mapping.column_name in data:
                value = data[field_mapping.column_name]

                # Apply transformer if defined
                if field_mapping.transformer:
                    value = field_mapping.transformer(value)

                transformed_data[field_name] = value

        return cls(**transformed_data)

    @classmethod
    def from_database_row(cls: Type[T], row: Dict[str, Any]) -> T:
        """Create model instance from database row"""
        return cls.from_dict(row)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for field_name, field_mapping in self._field_mappings.items():
            value = getattr(self, field_name)

            # Apply reverse transformer if needed
            if field_mapping.transformer and hasattr(field_mapping.transformer, 'reverse'):
                value = field_mapping.transformer.reverse(value)

            result[field_name] = value

        return result

    def to_database_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for database operations"""
        result = {}
        for field_name, field_mapping in self._field_mappings.items():
            if field_mapping.read_only or field_mapping.auto_generated:
                continue

            value = getattr(self, field_name)
            result[field_mapping.column_name] = value

        return result

    @classmethod
    def find_by_id(cls: Type[T], record_id: Any) -> Optional[T]:
        """Find record by primary key"""
        if not cls._query_executor:
            raise ValueError("Query executor not set")

        # Find primary key field
        pk_field = None
        for field_name, field_mapping in cls._field_mappings.items():
            if field_mapping.is_primary_key:
                pk_field = field_mapping
                break

        if not pk_field:
            raise ValueError("No primary key defined")

        table_name = cls.get_table_name()
        query = f"SELECT * FROM {table_name} WHERE {pk_field.column_name} = ?"

        result = cls._query_executor.execute_query(query, [record_id], "one")
        if result:
            return cls.from_database_row(result)
        return None

    @classmethod
    def find_all(cls: Type[T], where_clause: Optional[str] = None,
                 params: Optional[List[Any]] = None, limit: Optional[int] = None) -> List[T]:
        """Find all records matching criteria"""
        if not cls._query_executor:
            raise ValueError("Query executor not set")

        table_name = cls.get_table_name()
        query = f"SELECT * FROM {table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if limit:
            query += f" TOP ({limit})"

        result = cls._query_executor.execute_query(query, params, "all")
        return [cls.from_database_row(row) for row in result.data]

    @classmethod
    def find_where(cls: Type[T], **criteria) -> List[T]:
        """Find records using keyword criteria"""
        if not criteria:
            return cls.find_all()

        where_clauses = []
        params = []

        for field_name, value in criteria.items():
            if field_name in cls._field_mappings:
                field_mapping = cls._field_mappings[field_name]
                where_clauses.append(f"{field_mapping.column_name} = ?")
                params.append(value)

        where_clause = " AND ".join(where_clauses)
        return cls.find_all(where_clause, params)

    def save(self) -> bool:
        """Save model to database (insert or update)"""
        if not self._query_executor:
            raise ValueError("Query executor not set")

        # Check if this is an insert or update
        pk_field = None
        pk_value = None

        for field_name, field_mapping in self._field_mappings.items():
            if field_mapping.is_primary_key:
                pk_field = field_mapping
                pk_value = getattr(self, field_name)
                break

        if pk_field and pk_value is not None:
            # Update existing record
            return self._update()
        else:
            # Insert new record
            return self._insert()

    def _insert(self) -> bool:
        """Insert new record"""
        table_name = self.get_table_name()
        data_dict = self.to_database_dict()

        columns = list(data_dict.keys())
        placeholders = ["?" for _ in columns]
        values = list(data_dict.values())

        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        result = self._query_executor.execute_query(query, values)

        # Get auto-generated primary key if applicable
        pk_field = None
        for field_name, field_mapping in self._field_mappings.items():
            if field_mapping.is_primary_key and field_mapping.auto_generated:
                pk_field = field_mapping
                break

        if pk_field:
            # Get last inserted ID
            id_result = self._query_executor.execute_query("SELECT @@IDENTITY as last_id", [], "one")
            if id_result and id_result['last_id']:
                setattr(self, pk_field.field_name, id_result['last_id'])

        return result.success

    def _update(self) -> bool:
        """Update existing record"""
        table_name = self.get_table_name()
        data_dict = self.to_database_dict()

        # Find primary key
        pk_field = None
        pk_value = None

        for field_name, field_mapping in self._field_mappings.items():
            if field_mapping.is_primary_key:
                pk_field = field_mapping
                pk_value = getattr(self, field_name)
                break

        if not pk_field or pk_value is None:
            raise ValueError("Cannot update: No primary key value")

        # Build UPDATE query
        set_clauses = []
        values = []

        for column_name, value in data_dict.items():
            if column_name != pk_field.column_name:
                set_clauses.append(f"{column_name} = ?")
                values.append(value)

        # Add primary key to values
        values.append(pk_value)

        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {pk_field.column_name} = ?"

        result = self._query_executor.execute_query(query, values)
        return result.success

    def delete(self) -> bool:
        """Delete record from database"""
        if not self._query_executor:
            raise ValueError("Query executor not set")

        # Find primary key
        pk_field = None
        pk_value = None

        for field_name, field_mapping in self._field_mappings.items():
            if field_mapping.is_primary_key:
                pk_field = field_mapping
                pk_value = getattr(self, field_name)
                break

        if not pk_field or pk_value is None:
            raise ValueError("Cannot delete: No primary key value")

        table_name = self.get_table_name()
        query = f"DELETE FROM {table_name} WHERE {pk_field.column_name} = ?"

        result = self._query_executor.execute_query(query, [pk_value])
        return result.success

    @classmethod
    def create_table(cls) -> bool:
        """Create table for this model"""
        if not cls._query_executor:
            raise ValueError("Query executor not set")

        create_sql = cls.create_table_sql()
        result = cls._query_executor.execute_query(create_sql)
        return result.success

    def __str__(self) -> str:
        """String representation of model"""
        class_name = self.__class__.__name__
        fields = []

        for field_name, field_mapping in self._field_mappings.items():
            if field_mapping.is_primary_key:
                value = getattr(self, field_name)
                fields.append(f"{field_name}={value}")
                break

        return f"<{class_name}: {', '.join(fields)}>"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"{self.__class__.__name__}({self.to_dict()})"


class ModelRegistry:
    """Registry for model classes and metadata"""

    def __init__(self):
        self._models: Dict[str, Type[BaseModel]] = {}
        self._table_mappings: Dict[str, str] = {}

    def register(self, model_class: Type[BaseModel]):
        """Register a model class"""
        class_name = model_class.__name__
        table_name = model_class.get_table_name()

        self._models[class_name] = model_class
        self._table_mappings[table_name] = class_name

        print(f"[OK] Registered model: {class_name} -> {table_name}")

    def get_model_class(self, table_name: str) -> Optional[Type[BaseModel]]:
        """Get model class by table name"""
        class_name = self._table_mappings.get(table_name)
        return self._models.get(class_name) if class_name else None

    def get_all_models(self) -> Dict[str, Type[BaseModel]]:
        """Get all registered models"""
        return self._models.copy()

    def create_tables(self) -> Dict[str, bool]:
        """Create tables for all registered models"""
        results = {}

        for class_name, model_class in self._models.items():
            try:
                success = model_class.create_table()
                results[class_name] = success
                status = "[OK]" if success else "✗"
                print(f"{status} Created table for {class_name}")
            except Exception as e:
                results[class_name] = False
                print(f"✗ Failed to create table for {class_name}: {e}")

        return results


# Global model registry
model_registry = ModelRegistry()


def model(table_name: str = None):
    """Decorator to register a model class"""
    def decorator(model_class: Type[BaseModel]):
        if table_name:
            model_class._table_name = table_name
        model_registry.register(model_class)
        return model_class

    return decorator


def field(column_name: str, data_type: DataType = DataType.STRING, **kwargs):
    """Decorator to define field mapping"""
    def decorator(cls):
        if not hasattr(cls, '_field_mappings'):
            cls._field_mappings = {}

        # Get the field name from the function being decorated
        frame = inspect.currentframe().f_back
        field_name = None

        # Look for the field assignment in the class definition
        for line in inspect.getsourcelines(frame.f_code)[0]:
            if 'field(' in line:
                # Extract field name from assignment
                match = __import__('re').search(r'(\w+)\s*=\s*field\(', line)
                if match:
                    field_name = match.group(1)
                    break

        if field_name:
            cls._field_mappings[field_name] = FieldMapping(
                field_name=field_name,
                column_name=column_name,
                data_type=data_type,
                **kwargs
            )

        return cls

    return decorator


# Example model definitions for Daftar Upah system
@model("HR_EMPLOYEE")
class HREmployee(BaseModel):
    """HR Employee model"""

    # Field mappings would be defined here using decorators
    # For example:
    # EmpCode = field("EmpCode", DataType.STRING, required=True, max_length=20, is_primary_key=True)
    # EmpName = field("EmpName", DataType.STRING, required=True, max_length=100)
    # Gender = field("Gender", DataType.INTEGER, required=True)  # 1=L, 0=P
    # LocCode = field("LocCode", DataType.STRING, max_length=20)


@model("HR_GANGLN")
class HRGangln(BaseModel):
    """HR Gang Line model"""

    # Field mappings would be defined here
    # For example:
    # GangCode = field("GangCode", DataType.STRING, required=True, max_length=10)
    # GangMember = field("GangMember", DataType.STRING, required=True, max_length=20)


def main():
    """Test data mapper"""
    print("=" * 60)
    print("DATA MAPPER TEST")
    print("=" * 60)

    try:
        from connection_manager import ConnectionManager
        from query_executor import QueryExecutor

        # Initialize database components
        with ConnectionManager() as conn_manager:
            query_executor = QueryExecutor(conn_manager)

            # Set query executor for models
            BaseModel.set_query_executor(query_executor)

            print("[OK] Data mapper initialized")

            # Test model registry
            print("\n1. Testing model registry...")
            models = model_registry.get_all_models()
            print(f"   Registered models: {list(models.keys())}")

            # Test field mapping manually (since decorators aren't working in this context)
            print("\n2. Testing field mapping...")

            # Create a simple test model
            class TestEmployee(BaseModel):
                _table_name = "test_employees"
                _field_mappings = {
                    'id': FieldMapping('id', 'id', DataType.INTEGER, required=True, is_primary_key=True, auto_generated=True),
                    'name': FieldMapping('name', 'name', DataType.STRING, required=True, max_length=100),
                    'gender': FieldMapping('gender', 'gender', DataType.INTEGER, required=True),
                    'salary': FieldMapping('salary', 'salary', DataType.DECIMAL, precision=18, scale=2),
                    'hire_date': FieldMapping('hire_date', 'hire_date', DataType.DATE)
                }

            # Test model creation
            employee = TestEmployee(name="Test Employee", gender=1, salary=5000000.00, hire_date="2024-01-01")
            print(f"   Created employee: {employee}")
            print(f"   Employee data: {employee.to_dict()}")
            print(f"   Database data: {employee.to_database_dict()}")

            # Test SQL generation
            print("\n3. Testing SQL generation...")
            create_sql = TestEmployee.create_table_sql()
            print(f"   CREATE TABLE SQL generated successfully")
            print(f"   Table name: {TestEmployee.get_table_name()}")

            # Test data transformation
            print("\n4. Testing data transformation...")
            db_data = {
                'id': 1,
                'name': 'Database Employee',
                'gender': 0,
                'salary': 6000000.00,
                'hire_date': '2024-02-01'
            }

            employee_from_db = TestEmployee.from_database_row(db_data)
            print(f"   Employee from DB: {employee_from_db}")

            # Test validation
            print("\n5. Testing validation...")
            try:
                invalid_employee = TestEmployee(name="", gender=1, salary="invalid")
                print("   ✗ Validation should have failed")
            except ValidationError as e:
                print(f"   [OK] Validation correctly failed: {e}")

            print("\n[OK] Data mapper test completed successfully")

    except Exception as e:
        print(f"\n[ERROR] Data mapper test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()