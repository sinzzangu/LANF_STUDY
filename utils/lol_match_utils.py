import json
from pathlib import Path
from utils import riot_api

USERS_FILE = Path("data/registered_users.json")
MATCHES_FILE = Path("data/internal_matches.json")

USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
MATCHES_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_json(path):
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_registered_users():
    return load_json(USERS_FILE)

def save_registered_users(data):
    save_json(USERS_FILE, data)

def load_matches():
    return load_json(MATCHES_FILE)

def save_matches(data):
    save_json(MATCHES_FILE, data)