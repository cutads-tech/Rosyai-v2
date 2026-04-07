import json
import os

DB_FILE = "apps_db.json"

def load_apps():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_apps(apps):
    with open(DB_FILE, "w") as f:
        json.dump(apps, f, indent=2)

def remember_app(name, path):
    apps = load_apps()
    apps[name.lower()] = path
    save_apps(apps)

def get_app(name):
    return load_apps().get(name.lower())