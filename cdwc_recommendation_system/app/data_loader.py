"""Load employee dataset from local JSON file."""

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "employees.json"


def load_employees() -> list[dict[str, Any]]:
    """Load and return the employee dataset."""
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
