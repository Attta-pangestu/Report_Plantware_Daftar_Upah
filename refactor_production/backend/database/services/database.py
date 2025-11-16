import threading
import queue
import pyodbc
from typing import Any, Iterable, Optional, Tuple, List
from .logger import get_logger
from ..config.settings import connection_string

class Database:
    _instance = None
    _lock = threading.Lock()

    def __init__(self, pool_size: int = 5):
        self._logger = get_logger()
        self._pool = queue.Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self._pool.put(self._create_conn())

    @classmethod
    def instance(cls, pool_size: int = 5):
        with cls._lock:
            if cls._instance is None:
                cls._instance = Database(pool_size)
            return cls._instance

    def _create_conn(self):
        s = connection_string()
        return pyodbc.connect(s)

    def acquire(self):
        return self._pool.get()

    def release(self, conn):
        try:
            self._pool.put(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    def execute(self, sql: str, params: Optional[Iterable[Any]] = None):
        conn = self.acquire()
        try:
            cur = conn.cursor()
            if params:
                cur.execute(sql, *params)
            else:
                cur.execute(sql)
            return cur
        except Exception as e:
            self._logger.error(str(e))
            raise
        finally:
            self.release(conn)

    def query_all(self, sql: str, params: Optional[Iterable[Any]] = None) -> List[Tuple]:
        cur = self.execute(sql, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def query_one(self, sql: str, params: Optional[Iterable[Any]] = None) -> Optional[Tuple]:
        cur = self.execute(sql, params)
        row = cur.fetchone()
        cur.close()
        return row

    class _Tx:
        def __init__(self, db: 'Database'):
            self._db = db
            self._conn = None
            self.cursor = None

        def __enter__(self):
            self._conn = self._db.acquire()
            self._conn.autocommit = False
            self.cursor = self._conn.cursor()
            return self.cursor

        def __exit__(self, exc_type, exc, tb):
            try:
                if exc_type is None:
                    self._conn.commit()
                else:
                    self._conn.rollback()
            finally:
                try:
                    if self.cursor:
                        self.cursor.close()
                finally:
                    self._db.release(self._conn)

    def transaction(self):
        return Database._Tx(self)
