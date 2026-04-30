"""
Convert all data sheets from DUMMY2_EPDR.xlsx into DUMMY2_EPDR_sample.json.
Streams records to avoid holding everything in memory at once.
"""

import json
import math
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
XLSX_PATH = DATA_DIR / "DUMMY2_EPDR.xlsx"
JSON_PATH = DATA_DIR / "DUMMY2_EPDR_sample.json"

SKIP_SHEETS = {"XDO_METADATA"}

COLUMN_MAP = {
    "Dummy ID": "dummy_id",
    "Employee Name": "employee_name",
    "Employee Group": "employee_group",
    "Employee Subgroup": "employee_subgroup",
    "Company": "company",
    "Assignment Status": "assignment_status",
    "Business Unit": "business_unit",
    "Department": "department",
    "Role": "role",
    "Position SKG": "position_skg",
    "Home SKG": "home_skg",
    "Discipline": "discipline",
    "Sub Discipline": "sub_discipline",
    "Inventory Type": "inventory_type",
    "Inventory Name": "inventory_name",
    "Min Proficiency Required": "min_proficiency_required",
    "Min Proficiency Required Numeric": "min_proficiency_required_numeric",
    "Proficiency Acquired (Self)": "proficiency_acquired_self",
    "Proficiency Acquired Numeric (Self)": "proficiency_acquired_numeric_self",
    "Proficiency Acquired Numeric (Supervisor)": "proficiency_acquired_numeric_supervisor",
    "Comment (Supervisor)": "comment_supervisor",
}


def clean_value(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def build_rename_map(columns):
    rename = {}
    for col in columns:
        s = str(col).strip()
        rename[col] = COLUMN_MAP.get(s, s.lower().replace(" ", "_").replace("(", "").replace(")", ""))
    return rename


def main():
    xl = pd.ExcelFile(XLSX_PATH, engine="openpyxl")
    data_sheets = [s for s in xl.sheet_names if s not in SKIP_SHEETS]
    print(f"Processing {len(data_sheets)} sheets...")

    total = 0
    first = True

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        f.write("[\n")

        for sheet in data_sheets:
            df = pd.read_excel(xl, sheet_name=sheet)
            df = df.rename(columns=build_rename_map(df.columns))
            df = df.dropna(how="all")

            count = 0
            for rec in df.to_dict(orient="records"):
                cleaned = {k: clean_value(v) for k, v in rec.items()
                           if clean_value(v) is not None and clean_value(v) != ""}
                if not cleaned:
                    continue

                if not first:
                    f.write(",\n")
                json.dump(cleaned, f, ensure_ascii=False, default=str)
                first = False
                count += 1

            total += count
            print(f"  {sheet}: {count} records")

        f.write("\n]")

    size_mb = JSON_PATH.stat().st_size / (1024 * 1024)
    print(f"\nTotal: {total} records → {JSON_PATH.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
