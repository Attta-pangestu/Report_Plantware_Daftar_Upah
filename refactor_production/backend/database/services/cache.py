import time
import threading

class Cache:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._store = {}

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = Cache()
            return cls._instance

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None
        value, exp = item
        if exp and exp < time.time():
            del self._store[key]
            return None
        return value

    def set(self, key: str, value, ttl: int = 300):
        exp = time.time() + ttl if ttl > 0 else None
        self._store[key] = (value, exp)

    def clear(self, key: str = None):
        if key:
            self._store.pop(key, None)
        else:
            self._store.clear()
