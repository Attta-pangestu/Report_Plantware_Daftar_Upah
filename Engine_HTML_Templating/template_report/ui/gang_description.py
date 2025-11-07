#!/usr/bin/env python3
"""
Gang Description Decoder Module

This module provides functionality to decode and retrieve gang descriptions
from the getLIsttGang.sql query file.

Author: Claude Code Assistant
Date: 2025-11-07
"""

import os
import json
import pyodbc
from pathlib import Path
from typing import Optional, Dict, Any


class GangDescriptionDecoder:
    """
    A class to decode and retrieve gang descriptions from SQL query and database.
    """

    def __init__(self, config_file_path: str = None):
        """
        Initialize the Gang Description Decoder.

        Args:
            config_file_path (str): Path to database configuration file
        """
        if config_file_path is None:
            # Default config file path
            self.config_file_path = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Explore_database/config.json"
        else:
            self.config_file_path = config_file_path

        self.query_file_path = "D:/Gawean Rebinmas/Monitoring Database/Plantware_Auto_Report/Daftar_Upah_Reporting/Engine_HTML_Templating/template_report/query/Gang/getLIsttGang.sql"

    def get_gang_description(self, gang_code: str) -> Dict[str, Any]:
        """
        Mendapatkan deskripsi lengkap gang berdasarkan kode gang.

        Args:
            gang_code (str): Kode gang yang akan dicari (contoh: "H1H")

        Returns:
            Dict[str, Any]: Dictionary berisi:
                - success (bool): Status keberhasilan pencarian
                - gang_code (str): Kode gang yang dicari
                - description (str): Deskripsi gang dari database
                - formatted_description (str): Deskripsi lengkap format: "PT. Rebinmas Jaya | [lokasi] [gang_code]"
                - company_name (str): "PT. Rebinmas Jaya"
                - location_code (str): Kode lokasi dari deskripsi gang
                - message (str): Pesan status atau error
                - error (str): Error message jika terjadi kesalahan

        Example:
            >>> decoder = GangDescriptionDecoder()
            >>> result = decoder.get_gang_description("H1H")
            >>> print(result['formatted_description'])
            "PT. Rebinmas Jaya | H1H KEBUN H1H"
        """
        result = {
            'success': False,
            'gang_code': gang_code,
            'description': None,
            'formatted_description': None,
            'company_name': 'PT. Rebinmas Jaya',
            'location_code': None,
            'message': '',
            'error': None
        }

        try:
            # Clean input gang code
            gang_code_clean = gang_code.strip().upper()
            result['gang_code'] = gang_code_clean

            # Get description from database
            description = self._get_description_from_database(gang_code_clean)

            if description:
                # Clean up description by removing extra spaces
                description_clean = description.strip()
                result['description'] = description_clean
                result['location_code'] = gang_code_clean
                result['formatted_description'] = f"{result['company_name']} | {description_clean} {gang_code_clean}"
                result['success'] = True
                result['message'] = "Deskripsi gang berhasil ditemukan"
            else:
                result['message'] = f"Gang '{gang_code_clean}' tidak ditemukan"

        except FileNotFoundError as e:
            result['error'] = f"File tidak ditemukan: {str(e)}"
            result['message'] = "Error: File konfigurasi atau query tidak ditemukan"
        except json.JSONDecodeError as e:
            result['error'] = f"Error parsing JSON config: {str(e)}"
            result['message'] = "Error: Format file konfigurasi tidak valid"
        except pyodbc.Error as e:
            result['error'] = f"Database error: {str(e)}"
            result['message'] = "Error: Koneksi database atau query gagal"
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
            result['message'] = "Error: Terjadi kesalahan yang tidak diharapkan"

        return result

    def _get_description_from_database(self, gang_code: str) -> Optional[str]:
        """
        Query database untuk mendapatkan deskripsi gang.

        Args:
            gang_code (str): Kode gang yang akan dicari

        Returns:
            Optional[str]: Deskripsi gang atau None jika tidak ditemukan
        """
        try:
            # Load database configuration
            with open(self.config_file_path, 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"

            # Connect to database
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Execute query
            query = 'SELECT "Description" FROM "HR_GANG" WHERE "GangCode" = ?'
            cursor.execute(query, gang_code)

            # Fetch result
            row = cursor.fetchone()

            # Close connection
            cursor.close()
            conn.close()

            if row and row[0]:
                return row[0]
            else:
                return None

        except Exception:
            # Re-raise to be handled by the main function
            raise

    def list_all_gangs(self) -> Dict[str, Any]:
        """
        Mendapatkan daftar semua gang yang tersedia di database.

        Returns:
            Dict[str, Any]: Dictionary berisi:
                - success (bool): Status keberhasilan
                - gangs (list): List semua gang dengan kode dan deskripsi
                - total (int): Jumlah total gang
                - message (str): Pesan status
                - error (str): Error message jika ada

        Example:
            >>> decoder = GangDescriptionDecoder()
            >>> result = decoder.list_all_gangs()
            >>> print(f"Total gang: {result['total']}")
        """
        result = {
            'success': False,
            'gangs': [],
            'total': 0,
            'message': '',
            'error': None
        }

        try:
            # Load database configuration
            with open(self.config_file_path, 'r') as f:
                config = json.load(f)

            # Access nested database config
            db_config = config['database']

            # Create connection string
            conn_str = f"DRIVER={{{db_config['driver']}}};SERVER={db_config['server']};PORT={db_config['port']};DATABASE={db_config['database_name']};UID={db_config['username']};PWD={db_config['password']}"

            # Connect to database
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Execute query
            query = 'SELECT "GangCode", "Description" FROM "HR_GANG" ORDER BY "GangCode"'
            cursor.execute(query)

            # Fetch all results
            rows = cursor.fetchall()

            # Process results
            gangs = []
            for row in rows:
                if row and len(row) >= 2:
                    # Clean up description by removing extra spaces
                    description_clean = row[1].strip()
                    gang_info = {
                        'gang_code': row[0],
                        'description': description_clean,
                        'formatted_description': f"PT. Rebinmas Jaya | {description_clean} {row[0]}"
                    }
                    gangs.append(gang_info)

            # Close connection
            cursor.close()
            conn.close()

            result['gangs'] = gangs
            result['total'] = len(gangs)
            result['success'] = True
            result['message'] = f"Berhasil mendapatkan {len(gangs)} gang"

        except Exception as e:
            result['error'] = str(e)
            result['message'] = "Error: Gagal mendapatkan daftar gang"

        return result

    def validate_gang_code(self, gang_code: str) -> bool:
        """
        Validasi format kode gang.

        Args:
            gang_code (str): Kode gang yang akan divalidasi

        Returns:
            bool: True jika format valid, False jika tidak

        Example:
            >>> decoder = GangDescriptionDecoder()
            >>> decoder.validate_gang_code("H1H")
            True
            >>> decoder.validate_gang_code("")
            False
        """
        if not gang_code:
            return False

        # Basic validation: should be alphanumeric, not too short/long
        gang_clean = gang_code.strip()

        if len(gang_clean) < 1 or len(gang_clean) > 10:
            return False

        # Should contain at least one letter and/or number
        if not any(c.isalnum() for c in gang_clean):
            return False

        return True


# Convenience functions for direct usage
def get_gang_description(gang_code: str, config_file_path: str = None) -> Dict[str, Any]:
    """
    Convenience function to get gang description.

    Args:
        gang_code (str): Kode gang yang akan dicari
        config_file_path (str, optional): Path ke file konfigurasi database

    Returns:
        Dict[str, Any]: Result dictionary with gang information

    Example:
        >>> result = get_gang_description("H1H")
        >>> if result['success']:
        ...     print(result['formatted_description'])
    """
    decoder = GangDescriptionDecoder(config_file_path)
    return decoder.get_gang_description(gang_code)


def list_all_gangs(config_file_path: str = None) -> Dict[str, Any]:
    """
    Convenience function to list all gangs.

    Args:
        config_file_path (str, optional): Path ke file konfigurasi database

    Returns:
        Dict[str, Any]: Result dictionary with all gangs information

    Example:
        >>> result = list_all_gangs()
        >>> if result['success']:
        ...     print(f"Total: {result['total']} gang")
    """
    decoder = GangDescriptionDecoder(config_file_path)
    return decoder.list_all_gangs()


if __name__ == "__main__":
    # Example usage and testing
    print("=== Gang Description Decoder - Example Usage ===")
    print()

    # Test 1: Get specific gang description
    print("1. Mendapatkan deskripsi gang H1H:")
    result = get_gang_description("H1H")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    if result['success']:
        print(f"   Formatted: {result['formatted_description']}")
    print()

    # Test 2: Get non-existent gang
    print("2. Mendapatkan deskripsi gang XXX:")
    result = get_gang_description("XXX")
    print(f"   Success: {result['success']}")
    print(f"   Message: {result['message']}")
    print()

    # Test 3: List all gangs
    print("3. Daftar semua gang:")
    all_gangs = list_all_gangs()
    if all_gangs['success']:
        print(f"   Total gang: {all_gangs['total']}")
        for i, gang in enumerate(all_gangs['gangs'][:5], 1):  # Show first 5 only
            print(f"   {i}. {gang['gang_code']} - {gang['formatted_description']}")
        if all_gangs['total'] > 5:
            print(f"   ... dan {all_gangs['total'] - 5} gang lainnya")
    else:
        print(f"   Error: {all_gangs['message']}")
    print()

    # Test 4: Validation
    print("4. Validasi kode gang:")
    decoder = GangDescriptionDecoder()
    test_codes = ["H1H", "XXX", "", "H123", "H 1"]
    for code in test_codes:
        valid = decoder.validate_gang_code(code)
        print(f"   '{code}': {'Valid' if valid else 'Invalid'}")

    print("\n=== End of Example ===")