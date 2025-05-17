import json
import os
from typing import Any, Dict


def get_cache_path(category: str) -> str:
    safe_cat = category.replace("/", "_").replace(" ", "_")
    cache_dir = os.path.join(os.path.dirname(__file__), "cache")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"{safe_cat}_freq.json")


def load_result_cache(category: str) -> Dict[str, Any]:
    path = get_cache_path(category)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None


def save_result_cache(category: str, result: Dict[str, Any]):
    path = get_cache_path(category)
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
