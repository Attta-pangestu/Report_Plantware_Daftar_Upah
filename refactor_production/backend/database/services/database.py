import threading
import queue
import pyodbc
import time
from typing import Any, Iterable, Optional, Tuple, List
from .logger import get_logger
from ..config.settings import connection_string

class Database:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, pool_size: int = 20):  # Increased pool size for 50+ users
        self._logger = get_logger()
        self._pool = queue.Queue(maxsize=pool_size)
        self._pool_size = pool_size
        self._connection_timeout = 60  # Increased timeout for complex queries
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool with retry logic"""
        for i in range(self._pool_size):
            try:
                conn = self._create_conn()
                self._pool.put(conn)
                self._logger.info(f"Database connection {i+1}/{self._pool_size} established")
            except Exception as e:
                self._logger.error(f"Failed to create database connection {i+1}: {e}")
                # Put None as placeholder to maintain pool size
                self._pool.put(None)

    @classmethod
    def instance(cls, pool_size: int = 20):
        with cls._lock:
            if cls._instance is None:
                cls._instance = Database(pool_size)
            return cls._instance

    def _create_conn(self):
        """Create database connection with enhanced settings and retry logic"""
        s = connection_string()
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                # Enhanced connection settings for better reliability
                conn = pyodbc.connect(s, timeout=self._connection_timeout)

                # Set connection attributes for better reliability (with fallback for older pyodbc versions)
                try:
                    conn.set_attr(pyodbc.SQL_ATTR_CONNECTION_TIMEOUT, self._connection_timeout)
                    conn.autocommit = True  # Better performance for read operations
                except AttributeError:
                    # Fallback for older pyodbc versions
                    pass

                self._logger.info(f"Successfully created database connection (attempt {attempt + 1})")
                return conn

            except Exception as e:
                if attempt == max_retries - 1:
                    self._logger.error(f"Failed to create database connection after {max_retries} attempts: {e}")
                    raise
                else:
                    self._logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff

        try:
            conn.set_attr(pyodbc.SQL_ATTR_QUERY_TIMEOUT, 60)
        except AttributeError:
            # Fallback for older pyodbc versions
            pass

        return conn

    def _get_healthy_connection(self, max_retries=3):
        """Get a healthy connection with retry logic"""
        for attempt in range(max_retries):
            try:
                conn = self._pool.get(timeout=30)  # Increased timeout for high load

                # If we got None (placeholder), try to create a new connection
                if conn is None:
                    try:
                        conn = self._create_conn()
                        self._logger.info(f"Created new database connection (attempt {attempt + 1})")
                    except Exception as e:
                        self._logger.error(f"Failed to create new connection: {e}")
                        # Put None back and continue to next attempt
                        self._pool.put(None)
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(1)
                        continue

                # Test if connection is still alive
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    return conn
                except Exception as e:
                    self._logger.warning(f"Connection health check failed: {e}")
                    try:
                        conn.close()
                    except:
                        pass

                    # Try to create new connection
                    try:
                        new_conn = self._create_conn()
                        self._logger.info(f"Replaced unhealthy connection (attempt {attempt + 1})")
                        return new_conn
                    except Exception as create_error:
                        self._logger.error(f"Failed to create replacement connection: {create_error}")
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(1)
                        continue

            except queue.Empty:
                self._logger.error("Connection pool timeout - no available connections")
                raise Exception("Database connection pool exhausted")
            except Exception as e:
                self._logger.error(f"Error getting connection: {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)

    def acquire(self):
        return self._get_healthy_connection()

    def release(self, conn):
        if conn is None:
            return

        try:
            # Verify connection is still healthy before returning to pool
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            self._pool.put(conn, timeout=5)
        except Exception as e:
            self._logger.warning(f"Connection unhealthy during release, closing: {e}")
            try:
                conn.close()
            except:
                pass
            # Put None placeholder to maintain pool size
            try:
                self._pool.put(None, timeout=5)
            except:
                pass

    def execute(self, sql: str, params: Optional[Iterable[Any]] = None):
        conn = self.acquire()
        retry_count = 0
        max_retries = 2

        while retry_count <= max_retries:
            try:
                cur = conn.cursor()
                if params:
                    cur.execute(sql, *params)
                else:
                    cur.execute(sql)
                return cur
            except pyodbc.OperationalError as e:
                self._logger.error(f"Database operational error (attempt {retry_count + 1}): {e}")
                retry_count += 1

                if retry_count > max_retries:
                    raise

                # Try to get a new connection
                try:
                    conn.close()
                except:
                    pass

                conn = self._get_healthy_connection()
            except Exception as e:
                self._logger.error(f"Database error: {e}")
                raise
            finally:
                if retry_count == 0:  # Only release if no retry occurred
                    pass  # Cursor will be closed by calling methods

    def query_all(self, sql: str, params: Optional[Iterable[Any]] = None) -> List[Tuple]:
        cur = None
        try:
            with self.get_connection_context() as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(sql, *params)
                else:
                    cur.execute(sql)
                rows = cur.fetchall()
                return rows
        except Exception as e:
            self._logger.error(f"Query all failed: {e}")
            raise
        finally:
            if cur:
                try:
                    cur.close()
                except:
                    pass

    def query_one(self, sql: str, params: Optional[Iterable[Any]] = None) -> Optional[Tuple]:
        cur = None
        try:
            with self.get_connection_context() as conn:
                cur = conn.cursor()
                if params:
                    cur.execute(sql, *params)
                else:
                    cur.execute(sql)
                row = cur.fetchone()
                return row
        except Exception as e:
            self._logger.error(f"Query one failed: {e}")
            raise
        finally:
            if cur:
                try:
                    cur.close()
                except:
                    pass

    class _Tx:
        def __init__(self, db: 'Database'):
            self._db = db
            self._conn = None
            self.cursor = None

        def __enter__(self):
            # Get healthy connection for transaction
            self._conn = self._db._get_healthy_connection()
            self._conn.autocommit = False
            self.cursor = self._conn.cursor()
            return self.cursor

        def __exit__(self, exc_type, exc, tb):
            try:
                if exc_type is None:
                    self._conn.commit()
                else:
                    self._conn.rollback()
                    self._db._logger.error(f"Transaction rolled back due to: {exc}")
            except Exception as e:
                self._db._logger.error(f"Error in transaction cleanup: {e}")
            finally:
                try:
                    if self.cursor:
                        self.cursor.close()
                finally:
                    self._db.release(self._conn)

    def transaction(self):
        return Database._Tx(self)

    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            conn = self._get_healthy_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            self.release(conn)
            return result and result[0] == 1
        except Exception as e:
            self._logger.error(f"Connection test failed: {e}")
            return False

    class _ConnectionContext:
        """Context manager for single connection reuse within a request scope"""
        def __init__(self, db: 'Database'):
            self._db = db
            self._conn = None

        def __enter__(self):
            self._conn = self._db._get_healthy_connection()
            return self._conn

        def __exit__(self, exc_type, exc, tb):
            if exc_type:
                self._db._logger.error(f"Connection context error: {exc}")
            # Always release connection back to pool
            self._db.release(self._conn)

    def get_connection_context(self):
        """Get a context manager for connection reuse"""
        return self._ConnectionContext(self)
