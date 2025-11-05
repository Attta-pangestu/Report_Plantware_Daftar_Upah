#!/usr/bin/env python3
"""
Configuration Manager for Database Connections
Handles loading and validation of database configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict


@dataclass
class DatabaseConfig:
    """Database configuration data structure"""
    driver: str = "mssql"
    server: str = "localhost"
    port: int = 1433
    username: str = ""
    password: str = ""
    database_name: str = ""
    trusted_connection: bool = False
    encrypt: bool = False
    connection_timeout: int = 30
    command_timeout: int = 60
    pool_size: int = 5
    max_overflow: int = 10


class ConfigManager:
    """
    Database Configuration Manager

    Handles loading, validation, and management of database configurations
    from JSON files with support for multiple environments.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager

        Args:
            config_path: Path to configuration file. If None, uses default path.
        """
        if config_path is None:
            # Default to project config file
            base_path = Path(__file__).parent.parent.parent
            config_path = base_path / "Explore_database" / "config.json"

        self.config_path = Path(config_path)
        self._config: Optional[DatabaseConfig] = None
        self._raw_config: Dict[str, Any] = {}

    def load_config(self) -> DatabaseConfig:
        """
        Load configuration from JSON file

        Returns:
            DatabaseConfig: Loaded and validated configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            ValueError: If configuration is invalid
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._raw_config = json.load(f)

            # Extract database configuration
            if 'database' not in self._raw_config:
                raise ValueError("Missing 'database' section in configuration")

            db_config = self._raw_config['database']

            # Create DatabaseConfig object
            self._config = DatabaseConfig(
                driver=db_config.get('driver', 'mssql'),
                server=db_config.get('server', 'localhost'),
                port=db_config.get('port', 1433),
                username=db_config.get('username', ''),
                password=db_config.get('password', ''),
                database_name=db_config.get('database_name', ''),
                trusted_connection=db_config.get('trusted_connection', False),
                encrypt=db_config.get('encrypt', False),
                connection_timeout=db_config.get('connection_timeout', 30),
                command_timeout=db_config.get('command_timeout', 60),
                pool_size=db_config.get('pool_size', 5),
                max_overflow=db_config.get('max_overflow', 10)
            )

            # Validate configuration
            self._validate_config()

            print(f"[OK] Configuration loaded from: {self.config_path}")
            return self._config

        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in config file: {e}", e.doc, e.pos)

    def _validate_config(self) -> None:
        """
        Validate loaded configuration

        Raises:
            ValueError: If configuration is invalid
        """
        if not self._config:
            raise ValueError("No configuration loaded")

        # Required fields
        required_fields = ['server', 'database_name']
        for field in required_fields:
            if not getattr(self._config, field):
                raise ValueError(f"Required field '{field}' is missing or empty")

        # Validate port
        if not (1 <= self._config.port <= 65535):
            raise ValueError(f"Invalid port number: {self._config.port}")

        # Validate timeouts
        if self._config.connection_timeout <= 0:
            raise ValueError(f"Invalid connection timeout: {self._config.connection_timeout}")

        if self._config.command_timeout <= 0:
            raise ValueError(f"Invalid command timeout: {self._config.command_timeout}")

        # Validate pool settings
        if self._config.pool_size <= 0:
            raise ValueError(f"Invalid pool size: {self._config.pool_size}")

        # If using trusted connection, username/password not required
        if not self._config.trusted_connection:
            if not self._config.username:
                raise ValueError("Username is required when not using trusted connection")
            if not self._config.password:
                raise ValueError("Password is required when not using trusted connection")

        print("[OK] Configuration validation passed")

    def get_config(self) -> DatabaseConfig:
        """
        Get loaded configuration

        Returns:
            DatabaseConfig: Current configuration

        Raises:
            ValueError: If no configuration has been loaded
        """
        if self._config is None:
            raise ValueError("No configuration loaded. Call load_config() first.")
        return self._config

    def get_connection_string(self) -> str:
        """
        Build database connection string from configuration

        Returns:
            str: Formatted connection string

        Raises:
            ValueError: If no configuration has been loaded
        """
        config = self.get_config()

        # Build connection string components
        components = [
            f"DRIVER={{{config.driver}}}",
            f"SERVER={config.server},{config.port}",
            f"DATABASE={config.database_name}",
            f"TrustConnection={'yes' if config.trusted_connection else 'no'}",
            f"Encrypt={'yes' if config.encrypt else 'no'}"
        ]

        # Add authentication
        if not config.trusted_connection:
            components.extend([
                f"UID={config.username}",
                f"PWD={config.password}"
            ])

        # Add timeouts
        if config.connection_timeout:
            components.append(f"Timeout={config.connection_timeout}")

        return ";".join(components)

    def get_dsn_config(self) -> Dict[str, Any]:
        """
        Get configuration as DSN parameters

        Returns:
            Dict[str, Any]: DSN configuration dictionary
        """
        config = self.get_config()

        dsn_config = {
            'driver': config.driver,
            'server': config.server,
            'port': config.port,
            'database': config.database_name,
            'trusted_connection': config.trusted_connection,
            'encrypt': config.encrypt,
            'timeout': config.connection_timeout
        }

        if not config.trusted_connection:
            dsn_config.update({
                'uid': config.username,
                'pwd': config.password
            })

        return dsn_config

    def save_config(self, config: DatabaseConfig, output_path: Optional[Path] = None) -> None:
        """
        Save configuration to JSON file

        Args:
            config: Configuration to save
            output_path: Output path. If None, uses original config path.
        """
        if output_path is None:
            output_path = self.config_path

        # Convert to dictionary
        config_dict = {
            'database': asdict(config)
        }

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)

        print(f"[OK] Configuration saved to: {output_path}")

    def create_connection_string_test(self) -> Dict[str, str]:
        """
        Create multiple connection string formats for testing

        Returns:
            Dict[str, str]: Different connection string formats
        """
        config = self.get_config()

        connection_strings = {
            'full_dsn': self.get_connection_string(),
            'short_dsn': (
                f"DRIVER={{{config.driver}}};"
                f"SERVER={config.server};"
                f"DATABASE={config.database_name};"
                f"UID={config.username};"
                f"PWD={config.password}"
            ),
            'trusted_dsn': (
                f"DRIVER={{{config.driver}}};"
                f"SERVER={config.server};"
                f"DATABASE={config.database_name};"
                f"Trusted_Connection=yes"
            ),
            'pyodbc_params': {
                'driver': config.driver,
                'server': config.server,
                'port': config.port,
                'database': config.database_name,
                'uid': config.username,
                'pwd': config.password,
                'trusted_connection': config.trusted_connection,
                'timeout': config.connection_timeout
            }
        }

        return connection_strings

    def get_environment_config(self, environment: str = "production") -> DatabaseConfig:
        """
        Load configuration for specific environment

        Args:
            environment: Environment name (development, staging, production)

        Returns:
            DatabaseConfig: Environment-specific configuration
        """
        # Look for environment-specific config file
        env_config_path = self.config_path.parent / f"config_{environment}.json"

        if env_config_path.exists():
            env_manager = ConfigManager(env_config_path)
            return env_manager.load_config()

        # Fall back to default config with environment modifications
        config = self.get_config()

        if environment == "development":
            # Development-specific modifications
            config.database_name = f"{config.database_name}_dev"
            config.pool_size = 2
        elif environment == "staging":
            # Staging-specific modifications
            config.database_name = f"{config.database_name}_staging"
            config.pool_size = 3

        return config

    def __str__(self) -> str:
        """String representation of configuration"""
        if self._config is None:
            return "ConfigManager: No configuration loaded"

        config = self._config
        return (
            f"ConfigManager: "
            f"Driver={config.driver}, "
            f"Server={config.server}:{config.port}, "
            f"Database={config.database_name}, "
            f"Trusted={config.trusted_connection}"
        )

    def __repr__(self) -> str:
        """Detailed string representation"""
        return f"ConfigManager(config_path={self.config_path})"


def main():
    """Test configuration manager"""
    print("=" * 60)
    print("DATABASE CONFIGURATION MANAGER TEST")
    print("=" * 60)

    try:
        # Initialize config manager
        config_manager = ConfigManager()
        print(f"Config Manager: {config_manager}")

        # Load configuration
        print("\n1. Loading configuration...")
        config = config_manager.load_config()
        print(f"Configuration: {config}")

        # Show connection string
        print("\n2. Connection String:")
        conn_str = config_manager.get_connection_string()
        print(f"   {conn_str}")

        # Show DSN config
        print("\n3. DSN Configuration:")
        dsn_config = config_manager.get_dsn_config()
        for key, value in dsn_config.items():
            print(f"   {key}: {value}")

        # Test environment configs
        print("\n4. Environment Configurations:")
        for env in ['development', 'staging', 'production']:
            env_config = config_manager.get_environment_config(env)
            print(f"   {env}: {env_config.database_name}")

        print("\n[OK] Configuration manager test completed successfully")

    except Exception as e:
        print(f"\n[ERROR] Configuration manager test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()