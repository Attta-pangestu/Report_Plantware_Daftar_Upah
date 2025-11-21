import os
import json
from pathlib import Path
from typing import Optional

def _config_path():
    base = Path(__file__).resolve().parents[2]
    return base / 'config.json'

def get_db_config(profile: Optional[str] = None):
    cfg_path = _config_path()
    with cfg_path.open('r') as f:
        cfg = json.load(f)

    selected = None
    if profile is None:
        profile = os.getenv('DB_PROFILE')

    if profile:
        profiles = cfg.get('database_profiles') or {}
        selected = profiles.get(profile)

    if selected is None:
        selected = cfg.get('database') or {}

    env = {
        'driver': os.getenv('DB_DRIVER'),
        'server': os.getenv('DB_SERVER'),
        'port': os.getenv('DB_PORT'),
        'database_name': os.getenv('DB_NAME'),
        'username': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASS'),
    }

    merged = {
        'driver': env['driver'] or selected.get('driver'),
        'server': env['server'] or selected.get('server'),
        'port': int(env['port']) if env['port'] else selected.get('port'),
        'database_name': env['database_name'] or selected.get('database_name'),
        'username': env['username'] or selected.get('username'),
        'password': env['password'] or selected.get('password') or '',
        'trusted_connection': selected.get('trusted_connection', False),
        'encrypt': selected.get('encrypt', False),
    }

    return merged

def connection_string(profile: Optional[str] = None):
    db = get_db_config(profile)
    base = f"DRIVER={{{db['driver']}}};SERVER={db['server']},{db['port']};DATABASE={db['database_name']};"
    if db.get('trusted_connection'):
        base += "Trusted_Connection=yes;"
    else:
        base += f"UID={db['username']};PWD={db['password']};"
    base += f"Encrypt={'yes' if db.get('encrypt') else 'no'};"
    return base
