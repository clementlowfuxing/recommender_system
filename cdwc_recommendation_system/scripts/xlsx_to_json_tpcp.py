"""
Convert DUMMY_TPCP_Assessment_latest.xlsx into DUMMY_TPCP_Assessment_sample.json.

The sheet has a wide structure:
  - Metadata columns (Dummy ID, Employee Staff Name, Business, OPU, ...)
  - Competency cells grouped as Base (B1-B25), Key (K1-K15), Pacing (P1-P10), Emerging (E1-E10)
  - A second block (suffixed _73..132) representing a second assessor/round
  - Aggregate totals and result columns (Total Base Met, Base %, Passed TPCP, ...)

Output: one record per row, with a cleaned snake_case key for every non-null column.
"""

import json
import math
import re
from pathlib import Path
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
XLSX_PATH = DATA_DIR / "DUMMY_TPCP_Assessment_latest.xlsx"
JSON_PATH = DATA_DIR / "DUMMY_TPCP_Assessment_sample.json"

# Explicit mapping for the metadata + result columns.
# Competency cells (B1, K2, P3, E4, B173, K198, ...) fall through to the auto-cleaner.
COLUMN_MAP = {
    "Dummy ID": "dummy_id",
    "Assessment No": "assessment_no",
    "Assessment Year": "assessment_year",
    "Assessment Date": "assessment_date",
    "Assessment Time": "assessment_time",
    "Result Released To OPU Date": "result_released_to_opu_date",
    "Employee Staff Name": "employee_name",
    "Age": "age",
    "Assessment SG": "assessment_sg",
    "Business": "business",
    "OPU": "opu",
    "Division": "division",
    "Skill Group": "skill_group",
    "Discipline": "discipline",
    "Sub Discipline": "sub_discipline",
    "SKG AOS": "skg_aos",
    "TI&R Version": "tir_version",
    "Assessment Level": "assessment_level",
    "Assessment Type": "assessment_type",
    "Reassessment No": "reassessment_no",
    "Assessor Type": "assessor_type",
    "Total Base Met": "total_base_met",
    "Total Base TI": "total_base_ti",
    "Total Key Met": "total_key_met",
    "Total Key TI": "total_key_ti",
    "Total \nPacing Met\n": "total_pacing_met",
    "Total Pacing TI": "total_pacing_ti",
    "Total \nEmerging Met": "total_emerging_met",
    "Total Emerging TI": "total_emerging_ti",
    "Base %": "base_pct",
    "Key %": "key_pct",
    "Pacing%": "pacing_pct",
    "Emerging %": "emerging_pct",
    "% CTI Met": "cti_met_pct",
    "CTI Met": "cti_met",
    "Passed TPCP": "passed_tpcp",
    "Qualified Level": "qualified_level",
    "Result Aging": "result_aging",
}


def clean_value(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):
        return v.item()
    return v


def clean_key(raw: str) -> str:
    """Default key cleaner for columns not in COLUMN_MAP."""
    s = str(raw).strip()
    s = re.sub(r"\s+", "_", s)
    s = s.replace("%", "pct").replace("#", "num")
    s = re.sub(r"[^\w]", "_", s)
    s = re.sub(r"_+", "_", s).strip("_").lower()
    return s


def build_rename_map(columns):
    rename = {}
    for col in columns:
        s = str(col).strip()
        rename[col] = COLUMN_MAP.get(s, clean_key(s))
    return rename


def main():
    xl = pd.ExcelFile(XLSX_PATH, engine="openpyxl")
    print(f"Processing {len(xl.sheet_names)} sheet(s): {xl.sheet_names}")

    total = 0
    first = True

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        f.write("[\n")

        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet)
            df = df.rename(columns=build_rename_map(df.columns))
            df = df.dropna(how="all")

            count = 0
            for rec in df.to_dict(orient="records"):
                cleaned = {}
                for k, v in rec.items():
                    cv = clean_value(v)
                    if cv is None or cv == "":
                        continue
                    # Integer-ify whole floats for IDs, counts, and years
                    if isinstance(cv, float) and cv.is_integer():
                        if (k == "dummy_id"
                                or k == "assessment_year"
                                or k == "age"
                                or k.startswith("total_")
                                or k == "result_aging"
                                or k == "reassessment_no"):
                            cv = int(cv)
                    # Round percentages to 4 dp for compactness
                    if isinstance(cv, float) and k.endswith("_pct"):
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
    print(f"\nTotal: {total} records → {JSON_PATH.name} ({size_mb:.2f} MB)")


if __name__ == "__main__":
    main()
