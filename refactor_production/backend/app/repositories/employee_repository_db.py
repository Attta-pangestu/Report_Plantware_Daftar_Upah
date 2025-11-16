from typing import List, Optional, Dict, Any
from database.services.database import Database
from database.services.queries import Queries

def _map_gender(v) -> str:
    try:
        i = int(v)
        if i == 1:
            return 'L'
        if i == 2:
            return 'P'
        return 'L'
    except Exception:
        return 'L'

class EmployeeRepositoryDB:
    def __init__(self):
        self.db = Database.instance()
        self.queries = Queries()

    def list(self, skip: int = 0, limit: int = 100, gang_code: Optional[str] = None, loc_code: Optional[str] = None) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        if gang_code:
            q = self.queries.get('employees', 'employees_by_gang')
            rows = self.db.query_all(q['sql'], (str(gang_code).strip(),))
            for r in rows:
                emp = {
                    'nik': str(r[0]).strip(),
                    'nama': str(r[1]).strip(),
                    'jenis_kelamin': _map_gender(r[2]),
                    'loc_code': str(r[3]).strip(),
                    'gang_code': str(r[4]).strip(),
                    'gaji_pokok': 0.0
                }
                items.append(emp)
        if loc_code:
            items = [x for x in items if x.get('loc_code') == loc_code]
        return items[skip:skip+limit]
