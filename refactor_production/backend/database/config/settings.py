import os
import json
from pathlib import Path

def _config_path():
    base = Path(__file__).resolve().parents[4]
    return base / 'Explore_database' / 'config.json'

def get_db_config():
    env = {
        'driver': os.getenv('DB_DRIVER'),
        'server': os.getenv('DB_SERVER'),
        'port': os.getenv('DB_PORT'),
        'database_name': os.getenv('DB_NAME'),
        'username': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
    }
    if all(env.values()):
        return env
    cfg = _config_path()
    with cfg.open('r') as f:
        data = json.load(f)['database']
    return {
        'driver': data['driver'],
        'server': data['server'],
        'port': data['port'],
        'database_name': data['database_name'],
        'username': data['username'],
        'password': data['password'],
    }

def connection_string():
    db = get_db_config()
    return f"DRIVER={{{db['driver']}}};SERVER={db['server']},{db['port']};DATABASE={db['database_name']};UID={db['username']};PWD={db['password']}"
