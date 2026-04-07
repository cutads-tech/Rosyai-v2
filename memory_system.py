import json
import os
import time

MEMORY_FILE = "rosy_memory.json"


def _load() -> dict:
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[memory_system] Save error: {e}")
def remember(key: str, value: str = None) -> str:
    data = _load()
    if value is None:
        # single-arg usage: treat whole string as a note
        auto_key = f"note_{int(time.time())}"
        data[auto_key] = {"value": key, "ts": time.time()}
        _save(data)
        return f"Note yaad kar liya: '{key}'"
    else:
        data[key.strip().lower()] = {"value": value.strip(), "ts": time.time()}
        _save(data)
        return f"Yaad kar liya: {key} = {value}"


def recall(key: str) -> str:
    """Retrieve value for key. Returns string always (not None)."""
    data = _load()
    k = key.strip().lower()

    # Exact match
    if k in data:
        entry = data[k]
        return entry["value"] if isinstance(entry, dict) else str(entry)

    # Fuzzy partial match
    for stored_key, entry in data.items():
        if k in stored_key or stored_key in k:
            val = entry["value"] if isinstance(entry, dict) else str(entry)
            return f"('{stored_key}' ke baare mein) {val}"

    return "Mujhe yaad nahi hai."


def list_memories() -> list:
    """Return all stored memories as list of (key, value) tuples."""
    data = _load()
    result = []
    for k, v in data.items():
        val = v["value"] if isinstance(v, dict) else str(v)
        result.append((k, val))
    return result


def forget(key: str) -> str:
    """Delete a memory entry."""
    data = _load()
    k = key.strip().lower()
    if k in data:
        del data[k]
        _save(data)
        return f"'{key}' bhool gayi."
    return f"'{key}' yaad hi nahi tha."
