from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any


RUNTIME_DIR = Path(__file__).resolve().parent.parent / "runtime"
DATA_FILE = RUNTIME_DIR / "data.json"
DATA_LOCK = Lock()
DEFAULT_DATA = {
    "tasks": [],
    "works": [],
    "assets": [],
    "users": [],
}


def ensure_runtime() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT_DATA, ensure_ascii=False, indent=2), encoding="utf-8")


def read_data() -> dict[str, Any]:
    ensure_runtime()
    with DATA_LOCK:
      return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def write_data(data: dict[str, Any]) -> None:
    ensure_runtime()
    with DATA_LOCK:
        DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_collection(name: str) -> list[dict[str, Any]]:
    return read_data().get(name, [])


def write_collection(name: str, items: list[dict[str, Any]]) -> None:
    data = read_data()
    data[name] = items
    write_data(data)


def upsert_collection_item(name: str, item: dict[str, Any], key: str = "id") -> dict[str, Any]:
    items = list_collection(name)
    next_items = [entry for entry in items if entry.get(key) != item.get(key)]
    next_items.append(item)
    write_collection(name, next_items)
    return item


def find_collection_item(name: str, predicate) -> dict[str, Any] | None:
    return next((item for item in list_collection(name) if predicate(item)), None)
