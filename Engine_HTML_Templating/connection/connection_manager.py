#!/usr/bin/env python3
"""
Database Connection Manager
Handles database connections with connection pooling, retry logic, and error handling
"""

import pyodbc
import time
import threading
from contextlib import contextmanager
from typing import Optional, Dict, Any, List, Callable
from queue import Queue, Empty
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from config_manager import ConfigManager, DatabaseConfig


@dataclass
class ConnectionStats:
    """Database connection statistics"""
    total_connections: int = 0
    active_connections: int = 0
    failed_connections: int = 0
    connection_timeouts: int = 0
    queries_executed: int = 0
    query_errors: int = 0
    last_connection_time: Optional[datetime] = None
    total_query_time: float = 0.0


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration"""
    min_connections: int = 1
    max_connections: int = 10
    max_idle_time: int = 300  # seconds
    connection_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: float = 1.0
    health_check_interval: int = 60  # seconds


class PooledConnection:
    """Pooled database connection wrapper"""

    def __init__(self, connection: pyodbc.Connection, pool: 'ConnectionPool', created_at: datetime):
        self.connection = connection
        self.pool = pool
        self.created_at = created_at
        self.last_used = datetime.now()
        self.in_use = False
        self.is_valid = True

    def execute(self, query: str, params: Optional[tuple] = None) -> pyodbc.Cursor:
        """Execute query using this connection"""
        if not self.is_valid:
            raise Exception("Connection is no longer valid")

        self.last_used = datetime.now()
        cursor = self.connection.cursor()

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        return cursor

    def commit(self):
        """Commit transaction"""
        if self.is_valid:
            self.connection.commit()

    def rollback(self):
        """Rollback transaction"""
        if self.is_valid:
            self.connection.rollback()

    def close(self):
        """Return connection to pool"""
        if self.is_valid and self.in_use:
            self.in_use = False
            self.pool.return_connection(self)

    def __enter__(self):
        """Context manager entry"""
        self.in_use = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.close()


class ConnectionPool:
    """Database connection pool"""

    def __init__(self, config: DatabaseConfig, pool_config: ConnectionPoolConfig):
        self.config = config
        self.pool_config = pool_config
        self.connections: Queue[PooledConnection] = Queue()
        self.all_connections: List[PooledConnection] = []
        self.stats = ConnectionStats()
        self._lock = threading.Lock()
        self._closed = False

        # Initialize pool with minimum connections
        self._initialize_pool()

        # Start health check thread
        self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self._health_check_thread.start()

    def _initialize_pool(self):
        """Initialize pool with minimum connections"""
        for _ in range(self.pool_config.min_connections):
            try:
                conn = self._create_connection()
                self.connections.put(conn)
                self.all_connections.append(conn)
            except Exception as e:
                print(f"[WARN] Failed to create initial connection: {e}")

    def _create_connection(self) -> PooledConnection:
        """Create new database connection"""
        start_time = time.time()

        try:
            # Build connection string
            conn_str = self._build_connection_string()

            # Create connection
            connection = pyodbc.connect(
                conn_str,
                timeout=self.pool_config.connection_timeout,
                autocommit=False
            )

            # Create pooled connection wrapper
            pooled_conn = PooledConnection(
                connection=connection,
                pool=self,
                created_at=datetime.now()
            )

            self.stats.total_connections += 1
            self.stats.last_connection_time = datetime.now()

            creation_time = time.time() - start_time
            print(f"[OK] Connection created in {creation_time:.2f}s")

            return pooled_conn

        except Exception as e:
            self.stats.failed_connections += 1
            raise Exception(f"Failed to create database connection: {e}")

    def _build_connection_string(self) -> str:
        """Build connection string from config"""
        components = [
            f"DRIVER={{{self.config.driver}}}",
            f"SERVER={self.config.server},{self.config.port}",
            f"DATABASE={self.config.database_name}",
            f"TrustConnection={'yes' if self.config.trusted_connection else 'no'}",
            f"Encrypt={'yes' if self.config.encrypt else 'no'}"
        ]

        if not self.config.trusted_connection:
            components.extend([
                f"UID={self.config.username}",
                f"PWD={self.config.password}"
            ])

        return ";".join(components)

    @contextmanager
    def get_connection(self) -> PooledConnection:
        """Get connection from pool"""
        if self._closed:
            raise Exception("Connection pool is closed")

        conn = None
        try:
            # Try to get existing connection
            try:
                conn = self.connections.get_nowait()
            except Empty:
                # Pool empty, try to create new connection
                if len(self.all_connections) < self.pool_config.max_connections:
                    conn = self._create_connection()
                    self.all_connections.append(conn)
                else:
                    # Wait for available connection
                    conn = self.connections.get(timeout=self.pool_config.connection_timeout)

            # Validate connection
            if not self._is_connection_valid(conn):
                self._close_connection(conn)
                conn = self._create_connection()
                self.all_connections.append(conn)

            conn.in_use = True
            self.stats.active_connections += 1

            yield conn

        except Empty:
            self.stats.connection_timeouts += 1
            raise Exception(f"Connection timeout after {self.pool_config.connection_timeout}s")

        except Exception as e:
            self.stats.failed_connections += 1
            raise e

        finally:
            if conn:
                conn.in_use = False
                self.stats.active_connections -= 1
                self.return_connection(conn)

    def return_connection(self, conn: PooledConnection):
        """Return connection to pool"""
        if conn.is_valid and not self._closed:
            try:
                self.connections.put_nowait(conn)
            except:
                # Pool full, connection will be garbage collected
                pass

    def _is_connection_valid(self, conn: PooledConnection) -> bool:
        """Check if connection is still valid"""
        try:
            if not conn.connection:
                return False

            # Simple query to test connection
            cursor = conn.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()

            return True

        except Exception:
            conn.is_valid = False
            return False

    def _close_connection(self, conn: PooledConnection):
        """Close and remove connection from pool"""
        try:
            if conn.connection:
                conn.connection.close()
        except Exception:
            pass

        conn.is_valid = False
        if conn in self.all_connections:
            self.all_connections.remove(conn)

    def _health_check_loop(self):
        """Background health check for connections"""
        while not self._closed:
            try:
                current_time = datetime.now()
                connections_to_close = []

                with self._lock:
                    for conn in self.all_connections:
                        # Check idle time
                        idle_time = (current_time - conn.last_used).total_seconds()
                        if idle_time > self.pool_config.max_idle_time:
                            connections_to_close.append(conn)
                        # Check connection validity
                        elif not conn.in_use and not self._is_connection_valid(conn):
                            connections_to_close.append(conn)

                # Close old/invalid connections
                for conn in connections_to_close:
                    self._close_connection(conn)

                # Maintain minimum connections
                current_size = len([c for c in self.all_connections if c.is_valid])
                if current_size < self.pool_config.min_connections:
                    for _ in range(self.pool_config.min_connections - current_size):
                        try:
                            conn = self._create_connection()
                            self.connections.put(conn)
                            self.all_connections.append(conn)
                        except Exception as e:
                            print(f"[WARN] Failed to create connection during health check: {e}")

            except Exception as e:
                print(f"[WARN] Health check error: {e}")

            # Wait before next check
            time.sleep(self.pool_config.health_check_interval)

    def close(self):
        """Close all connections and shutdown pool"""
        self._closed = True

        # Close all connections
        for conn in self.all_connections:
            self._close_connection(conn)

        # Clear queues and lists
        while not self.connections.empty():
            try:
                self.connections.get_nowait()
            except Empty:
                break

        self.all_connections.clear()
        print("[OK] Connection pool closed")

    def get_stats(self) -> ConnectionStats:
        """Get connection pool statistics"""
        self.stats.active_connections = len([c for c in self.all_connections if c.in_use])
        return self.stats

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


class ConnectionManager:
    """
    Database Connection Manager with pooling and retry logic

    Provides high-level database connection management with:
    - Connection pooling
    - Automatic retry logic
    - Error handling and logging
    - Connection health monitoring
    - Statistics tracking
    """

    def __init__(self, config: Optional[DatabaseConfig] = None, config_path: Optional[str] = None):
        """
        Initialize connection manager

        Args:
            config: Database configuration object
            config_path: Path to configuration file
        """
        if config is None:
            # Load configuration from file
            config_manager = ConfigManager(config_path)
            config = config_manager.load_config()

        self.config = config
        self.pool_config = ConnectionPoolConfig(
            min_connections=1,
            max_connections=config.pool_size,
            connection_timeout=config.connection_timeout,
            command_timeout=config.command_timeout
        )

        self.pool = ConnectionPool(config, self.pool_config)
        self.query_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_time': 0.0
        }

    @contextmanager
    def get_connection(self):
        """Get database connection from pool"""
        with self.pool.get_connection() as conn:
            yield conn

    def execute_query(self, query: str, params: Optional[tuple] = None,
                      fetch_mode: str = "all") -> List[Dict[str, Any]]:
        """
        Execute SQL query with retry logic

        Args:
            query: SQL query string
            params: Query parameters
            fetch_mode: Fetch mode ("all", "one", "many", "scalar")

        Returns:
            Query results based on fetch_mode
        """
        start_time = time.time()
        last_exception = None

        for attempt in range(self.pool_config.retry_attempts):
            try:
                with self.get_connection() as conn:
                    cursor = conn.execute(query, params)

                    # Handle different fetch modes
                    if fetch_mode == "all":
                        rows = cursor.fetchall()
                        columns = [column[0] for column in cursor.description]
                        results = [dict(zip(columns, row)) for row in rows]

                    elif fetch_mode == "one":
                        row = cursor.fetchone()
                        if row:
                            columns = [column[0] for column in cursor.description]
                            results = dict(zip(columns, row))
                        else:
                            results = None

                    elif fetch_mode == "many":
                        rows = cursor.fetchmany()
                        columns = [column[0] for column in cursor.description]
                        results = [dict(zip(columns, row)) for row in rows]

                    elif fetch_mode == "scalar":
                        row = cursor.fetchone()
                        results = row[0] if row else None

                    else:
                        raise ValueError(f"Invalid fetch_mode: {fetch_mode}")

                    # Update statistics
                    query_time = time.time() - start_time
                    self.query_stats['total_queries'] += 1
                    self.query_stats['successful_queries'] += 1
                    self.query_stats['total_time'] += query_time

                    return results

            except Exception as e:
                last_exception = e
                self.query_stats['total_queries'] += 1
                self.query_stats['failed_queries'] += 1

                if attempt < self.pool_config.retry_attempts - 1:
                    wait_time = self.pool_config.retry_delay * (2 ** attempt)
                    print(f"[WARN] Query failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
                else:
                    break

        raise Exception(f"Query failed after {self.pool_config.retry_attempts} attempts: {last_exception}")

    def execute_batch(self, queries: List[tuple]) -> List[List[Dict[str, Any]]]:
        """
        Execute multiple queries in a single transaction

        Args:
            queries: List of (query, params) tuples

        Returns:
            List of result sets
        """
        results = []

        with self.get_connection() as conn:
            try:
                for query, params in queries:
                    cursor = conn.execute(query, params)
                    rows = cursor.fetchall()
                    columns = [column[0] for column in cursor.description]
                    result = [dict(zip(columns, row)) for row in rows]
                    results.append(result)

                conn.commit()

            except Exception as e:
                conn.rollback()
                raise Exception(f"Batch query failed: {e}")

        return results

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            result = self.execute_query("SELECT 1 as test, @@VERSION as version", fetch_mode="one")
            if result:
                print(f"[OK] Database connection test successful")
                print(f"  Server: {result['version'][:50]}...")
                return True
            return False

        except Exception as e:
            print(f"✗ Database connection test failed: {e}")
            return False

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information"""
        info = {}

        try:
            # Database version
            version_result = self.execute_query("SELECT @@VERSION as version", fetch_mode="one")
            info['version'] = version_result['version'] if version_result else 'Unknown'

            # Database name
            db_result = self.execute_query("SELECT DB_NAME() as database_name", fetch_mode="one")
            info['database_name'] = db_result['database_name'] if db_result else 'Unknown'

            # Server name
            server_result = self.execute_query("SELECT @@SERVERNAME as server_name", fetch_mode="one")
            info['server_name'] = server_result['server_name'] if server_result else 'Unknown'

            # Connection count
            conn_result = self.execute_query(
                "SELECT COUNT(*) as connection_count FROM sys.dm_exec_sessions WHERE is_user_process = 1",
                fetch_mode="one"
            )
            info['active_connections'] = conn_result['connection_count'] if conn_result else 0

        except Exception as e:
            info['error'] = str(e)

        return info

    def get_stats(self) -> Dict[str, Any]:
        """Get connection and query statistics"""
        pool_stats = self.pool.get_stats()

        stats = {
            'connection_pool': {
                'total_connections': pool_stats.total_connections,
                'active_connections': pool_stats.active_connections,
                'failed_connections': pool_stats.failed_connections,
                'connection_timeouts': pool_stats.connection_timeouts,
                'last_connection_time': pool_stats.last_connection_time.isoformat() if pool_stats.last_connection_time else None,
                'pool_size': len(self.pool.all_connections),
                'available_connections': self.pool.connections.qsize()
            },
            'queries': self.query_stats.copy()
        }

        # Calculate average query time
        if self.query_stats['total_queries'] > 0:
            stats['queries']['average_time'] = self.query_stats['total_time'] / self.query_stats['total_queries']
        else:
            stats['queries']['average_time'] = 0.0

        return stats

    def close(self):
        """Close connection manager and cleanup resources"""
        self.pool.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Cleanup on deletion"""
        self.close()


def main():
    """Test connection manager"""
    print("=" * 60)
    print("DATABASE CONNECTION MANAGER TEST")
    print("=" * 60)

    try:
        # Initialize connection manager
        with ConnectionManager() as conn_manager:
            print("[OK] Connection manager initialized")

            # Test connection
            print("\n1. Testing database connection...")
            if conn_manager.test_connection():
                print("[OK] Connection test passed")
            else:
                print("✗ Connection test failed")
                return

            # Get database info
            print("\n2. Getting database information...")
            db_info = conn_manager.get_database_info()
            for key, value in db_info.items():
                print(f"   {key}: {value}")

            # Execute test query
            print("\n3. Executing test query...")
            result = conn_manager.execute_query(
                "SELECT TOP 5 name, create_date FROM sys.tables ORDER BY create_date DESC",
                fetch_mode="all"
            )
            print(f"   Found {len(result)} tables")
            for table in result[:3]:
                print(f"   - {table['name']} ({table['create_date']})")

            # Get statistics
            print("\n4. Connection statistics:")
            stats = conn_manager.get_stats()
            print(f"   Total connections: {stats['connection_pool']['total_connections']}")
            print(f"   Active connections: {stats['connection_pool']['active_connections']}")
            print(f"   Available connections: {stats['connection_pool']['available_connections']}")
            print(f"   Total queries: {stats['queries']['total_queries']}")
            print(f"   Average query time: {stats['queries']['average_time']:.3f}s")

        print("\n[OK] Connection manager test completed successfully")

    except Exception as e:
        print(f"\n[ERROR] Connection manager test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()