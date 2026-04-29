"""
HR Data Masking Script
======================
Masks sensitive fields (name, employee_id, email) in HR JSON/Excel data files.

Approach:
- Pseudonymization with a stored mapping (key file).
- Deterministic: same input always maps to same masked value.
- Reversible ONLY if you have the mapping key file.

Usage:
    python scripts/mask_data.py --input data/employees.json --output data/employees_masked.json
    python scripts/mask_data.py --input data/employees.json --output data/employees_masked.json --unmask
    python scripts/mask_data.py --input data/DUMMY_SMA_HRIS.xlsx --output data/DUMMY_SMA_HRIS_masked.xlsx
"""

import argparse
import hashlib
import json
import os
import string
import random
from pathlib import Path

MAPPING_FILE = "data/.masking_key.json"

# Fields to mask (add more as needed)
FIELDS_NAME = ["name", "employee_name", "superior_name"]
FIELDS_ID = ["employee_id", "dummy_id"]
FIELDS_EMAIL = ["email", "employee_email", "work_email"]


def load_mapping() -> dict:
    """Load existing mapping from key file, or return empty structure."""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"names": {}, "ids": {}, "emails": {}}


def save_mapping(mapping: dict):
    """Persist the mapping key file."""
    os.makedirs(os.path.dirname(MAPPING_FILE), exist_ok=True)
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    print(f"[INFO] Mapping key saved to: {MAPPING_FILE}")


def generate_fake_name(seed: str) -> str:
    """Generate a consistent fake name from a seed."""
    first_names = [
        "Alex", "Jordan", "Morgan", "Casey", "Riley",
        "Taylor", "Quinn", "Avery", "Cameron", "Dakota",
        "Skyler", "Reese", "Finley", "Rowan", "Sage",
        "Harper", "Emery", "Kendall", "Blake", "Drew",
    ]
    last_names = [
        "Smith", "Lee", "Park", "Wong", "Silva",
        "Nakamura", "Andersen", "Novak", "Okafor", "Reyes",
        "Fischer", "Larsen", "Tanaka", "Moreau", "Petrov",
        "Kumar", "Hassan", "Olsen", "Varga", "Dumont",
    ]
    rng = random.Random(seed)
    return f"{rng.choice(first_names)} {rng.choice(last_names)}"


def generate_fake_id(original: str, seed: str) -> str:
    """Generate a format-preserving masked ID."""
    rng = random.Random(seed)
    if isinstance(original, int):
        # Numeric ID: generate random number with same digit count
        digits = len(str(original))
        return rng.randint(10 ** (digits - 1), 10**digits - 1)
    # String ID like "EMP001": preserve prefix, randomize digits
    prefix = "".join(c for c in str(original) if c.isalpha())
    num_part = "".join(c for c in str(original) if c.isdigit())
    if num_part:
        masked_num = str(rng.randint(0, 10 ** len(num_part) - 1)).zfill(len(num_part))
        return f"MSK{masked_num}"
    return f"MSK{rng.randint(100, 999)}"


def generate_fake_email(seed: str) -> str:
    """Generate a consistent fake email."""
    rng = random.Random(seed)
    user = "".join(rng.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{user}@masked.example.com"


def get_seed(value) -> str:
    """Create a deterministic seed from the original value."""
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def mask_value(value, field_type: str, mapping: dict):
    """Mask a single value and store in mapping. Ensures uniqueness of masked values."""
    if value is None or str(value).strip() == "":
        return value

    str_val = str(value)
    category = {"name": "names", "id": "ids", "email": "emails"}[field_type]

    # Already masked? Return existing masked value
    if str_val in mapping[category]:
        return mapping[category][str_val]

    existing_masked = set(mapping[category].values())
    seed = get_seed(str_val)
    attempt = 0

    while True:
        current_seed = f"{seed}_{attempt}" if attempt > 0 else seed
        if field_type == "name":
            masked = generate_fake_name(current_seed)
        elif field_type == "id":
            masked = generate_fake_id(value, current_seed)
        elif field_type == "email":
            masked = generate_fake_email(current_seed)
        else:
            return value

        # Ensure no duplicate masked values (needed for reversibility)
        if masked not in existing_masked:
            break
        attempt += 1

    mapping[category][str_val] = masked
    return masked


def unmask_value(value, field_type: str, mapping: dict):
    """Reverse a masked value using the mapping."""
    if value is None or str(value).strip() == "":
        return value

    category = {"name": "names", "id": "ids", "email": "emails"}[field_type]
    # Build reverse lookup
    reverse = {v: k for k, v in mapping[category].items()}

    str_val = str(value)
    if str_val in reverse:
        original = reverse[str_val]
        # Preserve type for numeric IDs
        if field_type == "id" and isinstance(value, int):
            return int(original)
        return original
    return value


def process_record(record: dict, mapping: dict, unmask: bool = False) -> dict:
    """Mask or unmask sensitive fields in a single record."""
    fn = unmask_value if unmask else mask_value
    result = dict(record)

    for field in FIELDS_NAME:
        if field in result:
            result[field] = fn(result[field], "name", mapping)

    for field in FIELDS_ID:
        if field in result:
            result[field] = fn(result[field], "id", mapping)

    for field in FIELDS_EMAIL:
        if field in result:
            result[field] = fn(result[field], "email", mapping)

    return result


def process_json(input_path: str, output_path: str, unmask: bool = False):
    """Process a JSON file (array of records)."""
    mapping = load_mapping()

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        result = [process_record(rec, mapping, unmask) for rec in data]
    elif isinstance(data, dict):
        result = process_record(data, mapping, unmask)
    else:
        raise ValueError("Unsupported JSON structure. Expected list or dict.")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    save_mapping(mapping)
    action = "Unmasked" if unmask else "Masked"
    print(f"[OK] {action} data written to: {output_path}")


def process_excel(input_path: str, output_path: str, unmask: bool = False):
    """Process an Excel file, masking all sheets."""
    try:
        import pandas as pd
    except ImportError:
        print("[ERROR] pandas and openpyxl required for Excel. Install with:")
        print("  pip install pandas openpyxl")
        return

    mapping = load_mapping()
    fn = unmask_value if unmask else mask_value

    xls = pd.ExcelFile(input_path)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name)

            for col in df.columns:
                col_lower = col.lower().replace(" ", "_")
                if any(f in col_lower for f in FIELDS_NAME):
                    df[col] = df[col].apply(lambda v: fn(v, "name", mapping))
                elif any(f in col_lower for f in FIELDS_ID):
                    df[col] = df[col].apply(lambda v: fn(v, "id", mapping))
                elif any(f in col_lower for f in FIELDS_EMAIL):
                    df[col] = df[col].apply(lambda v: fn(v, "email", mapping))

            df.to_excel(writer, sheet_name=sheet_name, index=False)

    save_mapping(mapping)
    action = "Unmasked" if unmask else "Masked"
    print(f"[OK] {action} Excel written to: {output_path}")


def main():
    global MAPPING_FILE

    parser = argparse.ArgumentParser(description="Mask/unmask sensitive HR data fields.")
    parser.add_argument("--input", "-i", required=True, help="Input file path (JSON or Excel)")
    parser.add_argument("--output", "-o", required=True, help="Output file path")
    parser.add_argument("--unmask", action="store_true", help="Reverse masking using the key file")
    parser.add_argument("--key", default=MAPPING_FILE, help=f"Path to mapping key file (default: {MAPPING_FILE})")
    args = parser.parse_args()

    MAPPING_FILE = args.key

    ext = Path(args.input).suffix.lower()
    if ext == ".json":
        process_json(args.input, args.output, args.unmask)
    elif ext in (".xlsx", ".xls"):
        process_excel(args.input, args.output, args.unmask)
    else:
        print(f"[ERROR] Unsupported file type: {ext}. Use .json or .xlsx")


if __name__ == "__main__":
    main()
