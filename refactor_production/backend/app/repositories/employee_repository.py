from typing import List, Optional, Dict, Any

class EmployeeRepository:
    def __init__(self):
        self._items: List[Dict[str, Any]] = []
        self._seq = 1
        self.create({"nik":"H0330","nama":"AFRIWANTONI","jenis_kelamin":"L","loc_code":"AB2","gang_code":"H1H","gaji_pokok":4005820.0})
        self.create({"nik":"H0510","nama":"AGUS SUTRIANA","jenis_kelamin":"L","loc_code":"AB2","gang_code":"H1H","gaji_pokok":4005820.0})
        # additional demo employees across divisions to populate gang list
        self.create({"nik":"A0001","nama":"DEMO A1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"A1A","gaji_pokok":3000000.0})
        self.create({"nik":"A0002","nama":"DEMO A2","jenis_kelamin":"P","loc_code":"AB1","gang_code":"A2A","gaji_pokok":3000000.0})
        self.create({"nik":"B0001","nama":"DEMO B1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"B1B","gaji_pokok":3000000.0})
        self.create({"nik":"C0001","nama":"DEMO C1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"C1C","gaji_pokok":3000000.0})
        self.create({"nik":"D0001","nama":"DEMO D1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"D1D","gaji_pokok":3000000.0})
        self.create({"nik":"E0001","nama":"DEMO E1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"E1E","gaji_pokok":3000000.0})
        self.create({"nik":"F0001","nama":"DEMO F1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"F1F","gaji_pokok":3000000.0})
        self.create({"nik":"G0001","nama":"DEMO G1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"G1G","gaji_pokok":3000000.0})
        self.create({"nik":"H0002","nama":"DEMO H2","jenis_kelamin":"L","loc_code":"AB1","gang_code":"H2H","gaji_pokok":3000000.0})
        self.create({"nik":"H0003","nama":"DEMO H3","jenis_kelamin":"L","loc_code":"AB1","gang_code":"H3H","gaji_pokok":3000000.0})
        self.create({"nik":"I0001","nama":"DEMO I1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"I1I","gaji_pokok":3000000.0})
        self.create({"nik":"J0001","nama":"DEMO J1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"J1J","gaji_pokok":3000000.0})
        self.create({"nik":"K0001","nama":"DEMO IJL1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"IJL1","gaji_pokok":3000000.0})
        self.create({"nik":"S0001","nama":"DEMO STF1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"STF1","gaji_pokok":3000000.0})
        self.create({"nik":"Z0001","nama":"DEMO SEC1","jenis_kelamin":"L","loc_code":"AB1","gang_code":"SEC1","gaji_pokok":3000000.0})
        # Additional demo employees matching DB gang codes (trimmed)
        self.create({"nik":"D1001","nama":"DEMO D1M","jenis_kelamin":"L","loc_code":"PG2B","gang_code":"D1M","gaji_pokok":3200000.0})
        self.create({"nik":"C1001","nama":"DEMO C1T","jenis_kelamin":"P","loc_code":"PG2A","gang_code":"C1T","gaji_pokok":3100000.0})

    def list(self, skip: int = 0, limit: int = 100, gang_code: Optional[str] = None, loc_code: Optional[str] = None):
        items = self._items
        if gang_code:
            items = [x for x in items if x.get("gang_code") == gang_code]
        if loc_code:
            items = [x for x in items if x.get("loc_code") == loc_code]
        return items[skip:skip+limit]

    def create(self, data: Dict[str, Any]):
        data = data.copy()
        data["id"] = self._seq
        self._seq += 1
        self._items.append(data)
        return data

    def get(self, id: int):
        for x in self._items:
            if x["id"] == id:
                return x
        return None

    def update(self, id: int, data: Dict[str, Any]):
        item = self.get(id)
        if not item:
            return None
        for k, v in data.items():
            if v is not None:
                item[k] = v
        return item

    def delete(self, id: int):
        before = len(self._items)
        self._items = [x for x in self._items if x["id"] != id]
        return len(self._items) < before
