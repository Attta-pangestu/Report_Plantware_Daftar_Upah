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

    def list_fields_by_gang(self, gang_code: str, fields: List[str], skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        colmap = {
            'nik': 'HR_EMPLOYEE.EmpCode',
            'nama': 'HR_EMPLOYEE.EmpName',
            'jenis_kelamin': 'HR_EMPLOYEE.Gender',
            'loc_code': 'HR_EMPLOYEE.LocCode',
            'gang_code': 'HR_GANGLN.GangCode'
        }
        allowed = [f for f in fields if f in colmap]
        if not allowed:
            allowed = ['nik', 'nama']
        select_cols = ', '.join([f'"{colmap[f]}"' for f in allowed])
        sql = f'SELECT {select_cols} FROM "HR_EMPLOYEE" JOIN "HR_GANGLN" ON "HR_GANGLN"."GangMember" = "HR_EMPLOYEE"."EmpCode" WHERE "HR_GANGLN"."GangCode" = ? ORDER BY "HR_EMPLOYEE"."EmpName"'
        rows = self.db.query_all(sql, (str(gang_code).strip(),))
        out: List[Dict[str, Any]] = []
        for r in rows:
            item: Dict[str, Any] = {}
            for i, f in enumerate(allowed):
                if f == 'jenis_kelamin':
                    item[f] = _map_gender(r[i])
                else:
                    item[f] = str(r[i]).strip()
            out.append(item)
        return out[skip:skip+limit]

    def get_by_nik(self, nik: str) -> Optional[Dict[str, Any]]:
        sql = 'SELECT "EmpCode","EmpName","Gender","LocCode" FROM "HR_EMPLOYEE" WHERE "EmpCode" = ?'
        row = self.db.query_one(sql, (str(nik).strip(),))
        if not row:
            return None
        return {
            'nik': str(row[0]).strip(),
            'nama': str(row[1]).strip(),
            'jenis_kelamin': _map_gender(row[2]),
            'loc_code': str(row[3]).strip()
        }
