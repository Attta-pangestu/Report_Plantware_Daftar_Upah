from typing import List, Optional
from database.services.database import Database
from database.services.queries import Queries
from database.services.cache import Cache

class GangService:
    DIVISION_MAPPING = {
        "PG1A": ["A"],
        "PG1B": ["B"],
        "PG2A": ["C"],
        "PG2B": ["D"],
        "DME": ["E"],
        "ARA": ["F"],
        "ARB1": ["G"],
        "ARB2": ["H"],
        "INFRA": ["I"],
        "AREC": ["J"],
        "IJL": ["IJL"],
        "STF-OFFICE": ["STF"],
        "SECURITY": ["SEC"]
    }

    # Reverse mapping for lookup
    PREFIX_TO_DIVISION = {}
    for division, prefixes in DIVISION_MAPPING.items():
        for prefix in prefixes:
            PREFIX_TO_DIVISION[prefix] = division

    def __init__(self):
        self.db = Database.instance()
        self.queries = Queries()
        self.cache = Cache.instance()

    def get_all_divisions(self) -> List[str]:
        """Get list of all available divisions"""
        return list(self.DIVISION_MAPPING.keys())

    def get_divisions_for_prefix(self, gang_code: str) -> Optional[str]:
        """Get division for a specific gang code prefix"""
        if not gang_code:
            return None

        up = gang_code.upper()
        if up.startswith('SEC'):
            return "SECURITY"
        if up.startswith('IJL'):
            return "IJL"
        if up.startswith('STF'):
            return "STF-OFFICE"
        first_char = up[0]
        return self.PREFIX_TO_DIVISION.get(first_char)

    def get_gang_prefixes_for_division(self, division: str) -> List[str]:
        """Get gang code prefixes for a specific division"""
        return self.DIVISION_MAPPING.get(division, [])

    def filter_gangs_by_division(self, gangs: List[str], division: str) -> List[str]:
        """Filter gang list by division"""
        if not division:
            return gangs

        prefixes = self.get_gang_prefixes_for_division(division)
        if not prefixes:
            return []

        filtered_gangs = []
        for gang in gangs:
            gang_upper = gang.upper()
            # Handle special case for SECURITY
            if division == "SECURITY":
                if gang_upper.startswith('SEC'):
                    filtered_gangs.append(gang)
            else:
                # Check if gang starts with any of the division prefixes
                for prefix in prefixes:
                    if gang_upper.startswith(prefix):
                        filtered_gangs.append(gang)
                        break

        return sorted(list(set(filtered_gangs)))  # Remove duplicates and sort

    async def fetch_gangs_from_database(self, division: Optional[str] = None, search: Optional[str] = None, force: bool = False) -> List[str]:
        try:
            key = f"gangs:{division or 'all'}"
            if not force:
                cached = self.cache.get(key)
                if cached is not None:
                    return cached
            if division:
                prefixes = self.get_gang_prefixes_for_division(division)
                if not prefixes:
                    return []
                q = self.queries.get('gangs', 'gangs_by_prefix')
                # Use first prefix for LIKE; SECURITY handled by 'SEC%'
                like = prefixes[0] + '%'
                rows = self.db.query_all(q['sql'], (like,))
                codes = [str(r[0]).strip() for r in rows]
            else:
                q = self.queries.get('gangs', 'gangs_all')
                rows = self.db.query_all(q['sql'])
                codes = [str(r[0]).strip() for r in rows]

            if search:
                s = search.upper()
                codes = [c for c in codes if s in c.upper()]

            result = sorted(codes)
            self.cache.set(key, result, ttl=300)
            return result
        except Exception:
            return self.get_mock_gangs_data(division, search)

    def get_mock_gangs_data(self, division: Optional[str] = None, search: Optional[str] = None) -> List[str]:
        """Fallback mock data when database is unavailable"""
        mock_gangs = [
            # PG1A Division
            "A001", "A002", "A003", "A101", "A102",
            # PG1B Division
            "B001", "B002", "B003", "B101", "B102",
            # PG2A Division
            "C001", "C002", "C003", "C101", "C102",
            # PG2B Division
            "D001", "D002", "D003", "D101", "D102",
            # DME Division
            "E001", "E002", "E003", "E101", "E102",
            # ARA Division
            "F001", "F002", "F003", "F101", "F102",
            # ARB1 Division
            "G001", "G002", "G003", "G101", "G102",
            # ARB2 Division
            "H001", "H002", "H003", "H101", "H102",
            # INFRA Division
            "I001", "I002", "I003", "I101", "I102",
            # AREC Division
            "J001", "J002", "J003", "J101", "J102",
            # IJL Division
            "L001", "L002", "L003", "L101", "L102",
            # STF-OFFICE Division
            "O001", "O002", "O003", "O101", "O102",
            # SECURITY Division
            "SEC001", "SEC002", "SEC003"
        ]

        # Apply search filter if provided
        if search:
            search_upper = search.upper()
            mock_gangs = [g for g in mock_gangs if search_upper in g]

        # Apply division filter if specified
        if division:
            filtered_gangs = self.filter_gangs_by_division(mock_gangs, division)
            return filtered_gangs

        return sorted(mock_gangs)

    def get_gang_info(self, gang_code: str) -> dict:
        """Get detailed information about a specific gang"""
        division = self.get_divisions_for_prefix(gang_code)

        return {
            "gang_code": gang_code,
            "division": division,
            "prefix": gang_code[0] if gang_code else None,
            "is_security": gang_code.upper().startswith('SEC') if gang_code else False
        }
