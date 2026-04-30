"""
Convert DUMMY_SMA HRIS.xlsx into DUMMY_SMA_HRIS_sample.json,
preserving the existing JSON structure.
"""

import json
import math
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
XLSX_PATH = DATA_DIR / "DUMMY_SMA HRIS.xlsx"
JSON_PATH = DATA_DIR / "DUMMY_SMA_HRIS_sample.json"

SKIP_SHEETS = {"XDO_METADATA"}

COLUMN_MAP = {
    "Dummy ID": "dummy_id",
    "Employee Name": "employee_name",
    "Skill Group": "skill_group",
    "Job Grade (JG)": "job_grade",
    "Job Grade": "job_grade",
    "Salary Grade (SG)": "salary_grade",
    "Salary Grade": "salary_grade",
    "Year in SG": "year_in_sg",
    "SMA Completion Status": "sma_completion_status",
    "Overall CBS %": "overall_cbs_pct",
    "Technical CBS %": "technical_cbs_pct",
    "Leadership CBS %": "leadership_cbs_pct",
    "Superior Name": "superior_name",
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
        rename[col] = COLUMN_MAP.get(s, s.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("%", "pct"))
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
                cleaned = {}
                for k, v in rec.items():
                    cv = clean_value(v)
                    if cv is not None and cv != "":
                        # Match original structure: dummy_id as int, pct rounded to 4dp
                        if k == "dummy_id" and isinstance(cv, float):
                            cv = int(cv)
                        elif k.endswith("_pct") and isinstance(cv, float):
                            cv = round(cv, 4)
                        cleaned[k] = cv
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
