#!/usr/bin/env python3
"""
Main Database Connector Interface
Unified interface for all database operations with comprehensive features
"""

from typing import Any, Dict, List, Optional, Union, Type, TypeVar, Callable
from pathlib import Path
from contextlib import contextmanager
from dataclasses import dataclass, field
import json
from datetime import datetime

from config_manager import ConfigManager, DatabaseConfig
from connection_manager import ConnectionManager, ConnectionPoolConfig
from query_executor import QueryExecutor, QueryResult, QueryBuilder, QueryType
from data_mapper import BaseModel, model_registry, ModelRegistry
from error_handling import ErrorHandler, DatabaseLogger, ErrorContext, with_error_handling, with_retry


T = TypeVar('T', bound=BaseModel)


@dataclass
class DatabaseConnectorConfig:
    """Configuration for database connector"""
    config_path: Optional[str] = None
    log_file: Optional[Path] = None
    log_level: str = "INFO"
    enable_console_logging: bool = True
    enable_error_handling: bool = True
    enable_retry_logic: bool = True
    connection_pool_size: int = 5
    connection_timeout: int = 30
    command_timeout: int = 60
    max_retry_attempts: int = 3
    retry_delay: float = 1.0


class DatabaseConnector:
    """
    Main Database Connector Interface

    Provides unified access to all database functionality:
    - Configuration management
    - Connection pooling
    - Query execution
    - Data mapping (ORM-like features)
    - Error handling and logging
    - Performance monitoring
    """

    def __init__(self, config: Optional[DatabaseConnectorConfig] = None):
        """
        Initialize database connector

        Args:
            config: Database connector configuration
        """
        self.config = config or DatabaseConnectorConfig()
        self.is_initialized = False

        # Core components (initialized later)
        self.config_manager: Optional[ConfigManager] = None
        self.connection_manager: Optional[ConnectionManager] = None
        self.query_executor: Optional[QueryExecutor] = None
        self.error_handler: Optional[ErrorHandler] = None
        self.logger: Optional[DatabaseLogger] = None
        self.model_registry: ModelRegistry = model_registry

        # Performance metrics
        self.metrics = {
            'initialization_time': None,
            'total_queries': 0,
            'total_execution_time': 0.0,
            'connections_created': 0,
            'errors_handled': 0,
            'last_activity': None
        }

    def initialize(self) -> bool:
        """
        Initialize all database components

        Returns:
            bool: True if initialization successful
        """
        start_time = datetime.now()

        try:
            print("[PROCESS] Initializing Database Connector...")

            # 1. Initialize configuration manager
            print("  [1] Loading configuration...")
            self.config_manager = ConfigManager(self.config.config_path)
            db_config = self.config_manager.load_config()

            # 2. Initialize logger
            print("  [2] Setting up logging...")
            self.logger = DatabaseLogger(
                name="database_connector",
                log_level=getattr(__import__('logging'), self.config.log_level.upper()),
                log_file=self.config.log_file,
                enable_console=self.config.enable_console_logging
            )

            # 3. Initialize error handler
            print("  [3] Setting up error handling...")
            if self.config.enable_error_handling:
                self.error_handler = ErrorHandler(self.logger)

                # Set up retry policies
                self.error_handler.set_retry_policy(
                    "connection",
                    max_attempts=self.config.max_retry_attempts,
                    base_delay=self.config.retry_delay
                )
                self.error_handler.set_retry_policy(
                    "timeout",
                    max_attempts=self.config.max_retry_attempts,
                    base_delay=self.config.retry_delay
                )

            # 4. Initialize connection manager
            print("  [4] Setting up connection pool...")
            pool_config = ConnectionPoolConfig(
                min_connections=1,
                max_connections=self.config.connection_pool_size,
                connection_timeout=self.config.connection_timeout,
                retry_attempts=self.config.max_retry_attempts
            )

            self.connection_manager = ConnectionManager(db_config, pool_config)

            # 5. Initialize query executor
            print("  [5] Setting up query executor...")
            self.query_executor = QueryExecutor(self.connection_manager)

            # 6. Initialize models
            print("  [6] Setting up data models...")
            self._setup_models()

            self.is_initialized = True
            self.metrics['initialization_time'] = (datetime.now() - start_time).total_seconds()
            self.metrics['last_activity'] = datetime.now()

            print(f"[OK] Database Connector initialized successfully in {self.metrics['initialization_time']:.3f}s")
            return True

        except Exception as e:
            print(f"[ERROR] Database Connector initialization failed: {e}")
            if self.logger:
                self.logger.logger.error(f"Initialization failed: {e}")
            return False

    def _setup_models(self):
        """Setup data models"""
        if self.query_executor:
            BaseModel.set_query_executor(self.query_executor)

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            bool: True if connection test successful
        """
        if not self.is_initialized:
            print("[ERROR] Database connector not initialized")
            return False

        try:
            context = ErrorContext(
                component="DatabaseConnector",
                operation="test_connection"
            )

            if self.connection_manager.test_connection():
                print("[OK] Database connection test successful")

                # Get database info
                db_info = self.connection_manager.get_database_info()
                print(f"   Database: {db_info.get('database_name', 'Unknown')}")
                print(f"   Server: {db_info.get('server_name', 'Unknown')}")
                print(f"   Active connections: {db_info.get('active_connections', 0)}")

                return True
            else:
                print("[ERROR] Database connection test failed")
                return False

        except Exception as e:
            print(f"[ERROR] Connection test failed: {e}")
            if self.error_handler:
                self.error_handler.handle_error(e)
            return False

    def execute_query(self, query: str, params: Optional[List[Any]] = None,
                      fetch_mode: str = "all", query_type: QueryType = QueryType.SELECT) -> QueryResult:
        """
        Execute SQL query with all features enabled

        Args:
            query: SQL query string
            params: Query parameters
            fetch_mode: Fetch mode
            query_type: Type of query

        Returns:
            QueryResult: Query result with metadata
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        context = ErrorContext(
            component="DatabaseConnector",
            operation="execute_query"
        )

        try:
            start_time = datetime.now()
            self.metrics['total_queries'] += 1

            # Log query start
            if self.logger:
                self.logger.log_query(query, params, 0, True)

            # Execute query
            result = self.query_executor.execute_query(query, params, fetch_mode, query_type)

            # Update metrics
            execution_time = result.execution_time
            self.metrics['total_execution_time'] += execution_time
            self.metrics['last_activity'] = datetime.now()

            # Log query completion
            if self.logger:
                self.logger.log_query(query, params, execution_time, result.success)

            return result

        except Exception as e:
            self.metrics['last_activity'] = datetime.now()

            if self.error_handler:
                db_error = self.error_handler.handle_error(e, context, query, params)
                self.metrics['errors_handled'] += 1
                raise e
            else:
                raise e

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get comprehensive table information

        Args:
            table_name: Name of the table

        Returns:
            Dictionary with table information
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.get_table_info(table_name)

    def get_database_schema(self) -> Dict[str, Any]:
        """
        Get complete database schema

        Returns:
            Dictionary with schema information
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.get_database_schema()

    def create_query_builder(self) -> QueryBuilder:
        """
        Create a new query builder

        Returns:
            QueryBuilder: New query builder instance
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.create_query_builder()

    def execute_stored_procedure(self, procedure_name: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        Execute stored procedure

        Args:
            procedure_name: Name of stored procedure
            params: Procedure parameters

        Returns:
            QueryResult: Procedure execution result
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.execute_stored_procedure(procedure_name, params)

    # Simplified query methods
    def select(self, table: str, where_clause: Optional[str] = None, params: Optional[List[Any]] = None,
               order_by: Optional[str] = None, limit: Optional[int] = None) -> QueryResult:
        """Execute SELECT query with simplified syntax"""
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.select(table, where_clause, params, order_by, limit)

    def insert(self, table: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> QueryResult:
        """Execute INSERT query"""
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.insert(table, data)

    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: Optional[List[Any]] = None) -> QueryResult:
        """Execute UPDATE query"""
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.update(table, data, where_clause, where_params)

    def delete(self, table: str, where_clause: str, where_params: Optional[List[Any]] = None) -> QueryResult:
        """Execute DELETE query"""
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.delete(table, where_clause, where_params)

    def execute_batch(self, queries: List[tuple], query_type: QueryType = QueryType.SELECT) -> QueryResult:
        """Execute multiple queries in a transaction"""
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return self.query_executor.execute_batch(queries, query_type)

    # Model operations
    def find_model(self, model_class: Type[T], record_id: Any) -> Optional[T]:
        """
        Find model instance by ID

        Args:
            model_class: Model class
            record_id: Record ID

        Returns:
            Model instance or None
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return model_class.find_by_id(record_id)

    def find_all_models(self, model_class: Type[T], where_clause: Optional[str] = None,
                       params: Optional[List[Any]] = None, limit: Optional[int] = None) -> List[T]:
        """
        Find all model instances matching criteria

        Args:
            model_class: Model class
            where_clause: WHERE clause
            params: WHERE parameters
            limit: LIMIT value

        Returns:
            List of model instances
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return model_class.find_all(where_clause, params, limit)

    def save_model(self, model: BaseModel) -> bool:
        """
        Save model instance to database

        Args:
            model: Model instance

        Returns:
            bool: True if save successful
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return model.save()

    def delete_model(self, model: BaseModel) -> bool:
        """
        Delete model instance from database

        Args:
            model: Model instance

        Returns:
            bool: True if delete successful
        """
        if not self.is_initialized:
            raise RuntimeError("Database connector not initialized")

        return model.delete()

    # Employee data methods (specific to Daftar Upah system)
    def get_employees_by_gang(self, gang_code: str = 'H1H', limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get employees by gang code using the standard query

        Args:
            gang_code: Gang code
            limit: Maximum number of records

        Returns:
            List of employee dictionaries
        """
        query = f"""
        SELECT TOP {limit}
            "HR_EMPLOYEE"."EmpCode",
            "HR_EMPLOYEE"."EmpName",
            "HR_EMPLOYEE"."Gender",
            "HR_EMPLOYEE"."LocCode"
        FROM "HR_EMPLOYEE"
        JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
        WHERE "HR_GANGLN"."GangCode" = ?
        ORDER BY "HR_EMPLOYEE"."EmpName"
        """

        result = self.execute_query(query, [gang_code])
        return result.data

    def get_all_gangs(self) -> List[str]:
        """
        Get all available gang codes

        Returns:
            List of gang codes
        """
        query = """
        SELECT DISTINCT "GangCode"
        FROM "HR_GANGLN"
        ORDER BY "GangCode"
        """

        result = self.execute_query(query)
        return [row['GangCode'] for row in result.data]

    def get_employee_count_by_gang(self, gang_code: str) -> int:
        """
        Get employee count for specific gang

        Args:
            gang_code: Gang code

        Returns:
            Number of employees
        """
        query = """
        SELECT COUNT(*) as employee_count
        FROM "HR_EMPLOYEE"
        JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode"
        WHERE "HR_GANGLN"."GangCode" = ?
        """

        result = self.execute_query(query, [gang_code], "one")
        return result['employee_count'] if result else 0

    # Performance and monitoring methods
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive performance metrics

        Returns:
            Dictionary with performance metrics
        """
        metrics = self.metrics.copy()

        if self.connection_manager:
            pool_stats = self.connection_manager.get_stats()
            metrics['connection_pool'] = {
                'total_connections': pool_stats.total_connections,
                'active_connections': pool_stats.active_connections,
                'available_connections': pool_stats.connections.qsize(),
                'failed_connections': pool_stats.failed_connections
            }

        if self.query_executor:
            query_stats = self.query_executor.get_performance_stats()
            metrics['query_performance'] = query_stats

        if self.error_handler:
            error_stats = self.error_handler.get_error_statistics()
            metrics['error_statistics'] = error_stats

        return metrics

    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get detailed connection status

        Returns:
            Dictionary with connection status
        """
        if not self.is_initialized:
            return {
                'initialized': False,
                'connected': False
            }

        status = {
            'initialized': True,
            'connected': False,
            'last_activity': self.metrics['last_activity'].isoformat() if self.metrics['last_activity'] else None,
            'total_queries': self.metrics['total_queries']
        }

        # Test connection
        status['connected'] = self.test_connection()

        # Add database info
        try:
            db_info = self.connection_manager.get_database_info()
            status['database_info'] = db_info
        except Exception:
            pass

        return status

    def export_metrics(self, output_file: Optional[Path] = None) -> Path:
        """
        Export metrics to JSON file

        Args:
            output_file: Output file path

        Returns:
            Path to exported file
        """
        if output_file is None:
            output_file = Path(__file__).parent / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        metrics = self.get_performance_metrics()

        # Convert datetime objects to strings
        def convert_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {k: convert_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime(item) for item in obj]
            return obj

        metrics_serializable = convert_datetime(metrics)

        with open(output_file, 'w') as f:
            json.dump(metrics_serializable, f, indent=2)

        print(f"[OK] Metrics exported to: {output_file}")
        return output_file

    def cleanup(self):
        """Cleanup database connector resources"""
        if self.connection_manager:
            self.connection_manager.close()

        if self.logger:
            self.logger.logger.info("Database connector cleanup completed")

        self.is_initialized = False

    def __enter__(self):
        """Context manager entry"""
        if not self.is_initialized:
            self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()

    def __del__(self):
        """Cleanup on deletion"""
        self.cleanup()

    def __str__(self) -> str:
        """String representation"""
        status = "Initialized" if self.is_initialized else "Not Initialized"
        return f"DatabaseConnector({status}, Queries: {self.metrics['total_queries']})"

    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"DatabaseConnector(initialized={self.is_initialized}, metrics={self.metrics})"


def main():
    """Test database connector"""
    print("=" * 60)
    print("DATABASE CONNECTOR TEST")
    print("=" * 60)

    try:
        # Initialize connector
        config = DatabaseConnectorConfig(
            log_file=Path(__file__).parent / "test_connector.log",
            connection_pool_size=3
        )

        with DatabaseConnector(config) as connector:
            print(f"[OK] Database connector: {connector}")

            # Test connection
            print("\n1. Testing connection...")
            if connector.test_connection():
                print("[OK] Connection successful")
            else:
                print("✗ Connection failed")
                return

            # Test simple query
            print("\n2. Testing simple query...")
            result = connector.select("sys.tables", "TABLE_TYPE = ?", ["BASE TABLE"], limit=5)
            print(f"   Found {result.affected_rows} tables")
            print(f"   Query time: {result.execution_time:.3f}s")

            # Test query builder
            print("\n3. Testing query builder...")
            builder = connector.create_query_builder()
            query, params = builder.table("sys.tables")\
                .select("name", "create_date")\
                .where("TABLE_TYPE = ?", "BASE TABLE")\
                .order_by("create_date", "DESC")\
                .limit(3)\
                .build()

            result = connector.execute_query(query, params)
            print(f"   Built query returned {len(result.data)} rows")

            # Test employee data methods
            print("\n4. Testing employee data methods...")
            try:
                gangs = connector.get_all_gangs()
                print(f"   Found {len(gangs)} gangs: {gangs[:3]}")

                if gangs:
                    gang_code = gangs[0]
                    employees = connector.get_employees_by_gang(gang_code, 5)
                    print(f"   Found {len(employees)} employees in gang {gang_code}")
                    employee_count = connector.get_employee_count_by_gang(gang_code)
                    print(f"   Total employees in gang {gang_code}: {employee_count}")

            except Exception as e:
                print(f"   Employee data test skipped: {e}")

            # Test performance metrics
            print("\n5. Performance metrics:")
            metrics = connector.get_performance_metrics()
            print(f"   Total queries: {metrics['total_queries']}")
            print(f"   Total execution time: {metrics['total_execution_time']:.3f}s")
            print(f"   Connections created: {metrics.get('connections_created', 0)}")
            print(f"   Errors handled: {metrics.get('errors_handled', 0)}")

            # Test connection status
            print("\n6. Connection status:")
            status = connector.get_connection_status()
            print(f"   Initialized: {status['initialized']}")
            print(f"   Connected: {status['connected']}")
            print(f"   Last activity: {status['last_activity']}")

            # Export metrics
            print("\n7. Exporting metrics...")
            metrics_file = connector.export_metrics()
            print(f"   Metrics exported to: {metrics_file}")

        print("\n[OK] Database connector test completed successfully")

    except Exception as e:
        print(f"\n[ERROR] Database connector test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()