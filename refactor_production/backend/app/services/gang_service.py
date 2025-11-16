from typing import List, Optional
from app.services.mssql_service import mssql_service

class GangService:
    # GangCode to Division mapping sesuai kebutuhan user
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
        "IJL": ["L"],
        "STF-OFFICE": ["O"],
        "SECURITY": ["SEC"]
    }

    # Reverse mapping for lookup
    PREFIX_TO_DIVISION = {}
    for division, prefixes in DIVISION_MAPPING.items():
        for prefix in prefixes:
            PREFIX_TO_DIVISION[prefix] = division

    def __init__(self):
        self.mssql_service = mssql_service

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
        if up.startswith('L'):
            return "IJL"
        if up.startswith('O'):
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
            # Check if gang starts with any of the division prefixes
            for prefix in prefixes:
                if gang_upper.startswith(prefix):
                    filtered_gangs.append(gang)
                    break

        return sorted(list(set(filtered_gangs)))  # Remove duplicates and sort

    def fetch_gangs_from_database(self, division: Optional[str] = None, search: Optional[str] = None, force: bool = False) -> List[str]:
        """
        Fetch gangs from database with optional division filtering and LIKE search.

        Args:
            division: Filter gangs by division (uses GangCode mapping)
            search: Search term with LIKE operator (flexible search)
            force: Force refresh from database, ignore cache

        Returns:
            List of gang codes filtered and searched according to parameters
        """
        try:
            # Get all gangs from database
            gangs_data = self.mssql_service.get_all_gangs()
            codes = [gang["GangCode"] for gang in gangs_data if gang.get("GangCode")]

            # Apply division filter if specified
            if division:
                codes = self.filter_gangs_by_division(codes, division)

            # Apply search filter if provided (case-insensitive LIKE)
            if search and codes:
                search_term = search.upper().strip()
                # More flexible search - can match anywhere in gang code
                codes = [c for c in codes if search_term in c.upper()]

            # Sort results
            return sorted(codes)

        except Exception as e:
            print(f"Error fetching gangs from database: {e}")
            # Fallback to mock data if database fails
            return self.get_mock_gangs_data(division, search)

    def get_mock_gangs_data(self, division: Optional[str] = None, search: Optional[str] = None) -> List[str]:
        """Fallback mock data when database is unavailable"""
        mock_gangs = [
            # PG1A Division (A)
            "A001", "A002", "A003", "A101", "A102", "A201", "A202",
            # PG1B Division (B)
            "B001", "B002", "B003", "B101", "B102", "B201", "B202",
            # PG2A Division (C)
            "C001", "C002", "C003", "C101", "C102", "C201", "C202",
            # PG2B Division (D)
            "D001", "D002", "D003", "D101", "D102", "D201", "D202",
            # DME Division (E)
            "E001", "E002", "E003", "E101", "E102", "E201", "E202",
            # ARA Division (F)
            "F001", "F002", "F003", "F101", "F102", "F201", "F202",
            # ARB1 Division (G)
            "G001", "G002", "G003", "G101", "G102", "G201", "G202",
            # ARB2 Division (H)
            "H001", "H002", "H003", "H101", "H102", "H201", "H202",
            # INFRA Division (I)
            "I001", "I002", "I003", "I101", "I102", "I201", "I202",
            # AREC Division (J)
            "J001", "J002", "J003", "J101", "J102", "J201", "J202",
            # IJL Division (L)
            "L001", "L002", "L003", "L101", "L102", "L201", "L202",
            # STF-OFFICE Division (O)
            "O001", "O002", "O003", "O101", "O102", "O201", "O202",
            # SECURITY Division (SEC)
            "SEC001", "SEC002", "SEC003", "SEC101", "SEC102"
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
