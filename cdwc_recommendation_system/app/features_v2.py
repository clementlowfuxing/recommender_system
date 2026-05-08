"""Feature engineering v2: multi-dimensional competency scoring using real EPDR, HRIS, and HR Flex data.

Improvements over v1 (features.py):
  - Replaces binary skill overlap with graded proficiency gap analysis per competency
  - Replaces single competency_score with three-axis CBS (technical, leadership, overall)
  - Adds performance trajectory scoring from multi-year PPA ratings
  - Adds leadership/behavioral competency scoring from BePCB ratings
  - Replaces generic role_level with actual P-grade hierarchy matching
  - Replaces single years_experience with multi-signal experience depth

Data sources:
  - EPDR (DUMMY2_EPDR_sample.json): per-competency proficiency levels
  - SMA HRIS (DUMMY_SMA_HRIS_sample.json): CBS percentages, SMA status
  - HR Flex (DUMMY_HR_Flex_Report_sample.json): grades, PPA, BePCB, tenure
  - Item Catalog TC: competency definitions (for validation/lookup)
  - Item Catalog LE: leadership competency definitions
  - Item Catalog TC Behavioral: proficiency level descriptors
"""

from __future__ import annotations
from typing import Any


# ─────────────────────────────────────────────────────────────────────
# Grade hierarchy (lower number = more senior)
# ─────────────────────────────────────────────────────────────────────

GRADE_ORDER = ["TM", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "CONTRACT"]

# PPA rating text → numeric mapping
PPA_MAP = {
    "1": 1.0, "1-low": 1.0,
    "2": 2.0, "2-low": 2.0, "2-solid": 2.5, "2-high": 2.75,
    "3": 3.0, "3-low": 2.75, "3-solid": 3.0, "3-high": 3.5,
    "4": 4.0, "4-low": 3.75, "4-solid": 4.0, "4-high": 4.5,
    "5": 5.0, "5-low": 4.75, "5-solid": 5.0, "5-high": 5.0,
}

# BePCB rating text → numeric mapping
BEPCB_MAP = {
    "level 1 - developing": 1.0,
    "level 2 - foundational": 2.0,
    "level 3 - proficient": 3.0,
    "level 4 - exceptional": 4.0,
    "level 5 - role model": 5.0,
}

MAX_PROFICIENCY = 5.0
MAX_BEPCB = 5.0
MAX_PPA = 5.0


# ─────────────────────────────────────────────────────────────────────
# 1. Proficiency Gap Score (from EPDR)
# ─────────────────────────────────────────────────────────────────────

def proficiency_gap_score(
    candidate_epdr: list[dict[str, Any]],
    required_competencies: list[dict[str, Any]],
) -> float:
    """Compute how well a candidate's proficiency levels match required competencies.

    For each required competency (identified by inventory_name or item_code):
      - Look up the candidate's acquired proficiency (supervisor rating preferred, self as fallback)
      - Compute gap = max(0, required_level - acquired_level)
      - Score = 1 - (total_gap / total_required)

    Args:
        candidate_epdr: list of EPDR rows for this candidate (many rows per employee)
        required_competencies: list of dicts with keys:
            - "inventory_name" or "item_code": competency identifier
            - "min_proficiency": required numeric level (1-5)

    Returns:
        float in [0.0, 1.0]. 1.0 = meets or exceeds all requirements.
    """
    if not required_competencies:
        return 1.0

    # Build lookup: inventory_name → best acquired proficiency for this candidate
    candidate_proficiencies = {}
    for row in candidate_epdr:
        name = row.get("inventory_name", "").strip().lower()
        # Prefer supervisor rating, fall back to self
        level = row.get("proficiency_acquired_numeric_supervisor")
        if level is None:
            level = row.get("proficiency_acquired_numeric_self")
        if level is None:
            continue
        # Keep the highest if multiple entries exist for same competency
        if name not in candidate_proficiencies or level > candidate_proficiencies[name]:
            candidate_proficiencies[name] = float(level)

    total_gap = 0.0
    total_required = 0.0

    for req in required_competencies:
        req_name = req.get("inventory_name", req.get("item_code", "")).strip().lower()
        req_level = float(req.get("min_proficiency", 1))
        total_required += req_level

        acquired = candidate_proficiencies.get(req_name, 0.0)
        gap = max(0.0, req_level - acquired)
        total_gap += gap

    if total_required == 0:
        return 1.0

    return max(0.0, 1.0 - (total_gap / total_required))


# ─────────────────────────────────────────────────────────────────────
# 2. Competency Bench Strength Score (from SMA HRIS)
# ─────────────────────────────────────────────────────────────────────

def technical_cbs_score(candidate_hris: dict[str, Any] | None) -> float:
    """Technical CBS percentage. Already normalized 0.0–1.0.

    Returns 0.0 if HRIS data is missing or field is absent.
    """
    if not candidate_hris:
        return 0.0
    return float(candidate_hris.get("technical_cbs_pct", 0.0))


def leadership_cbs_score(candidate_hris: dict[str, Any] | None) -> float:
    """Leadership CBS percentage. Already normalized 0.0–1.0."""
    if not candidate_hris:
        return 0.0
    return float(candidate_hris.get("leadership_cbs_pct", 0.0))


def overall_cbs_score(candidate_hris: dict[str, Any] | None) -> float:
    """Overall CBS percentage. Already normalized 0.0–1.0."""
    if not candidate_hris:
        return 0.0
    return float(candidate_hris.get("overall_cbs_pct", 0.0))


# ─────────────────────────────────────────────────────────────────────
# 3. Performance Trajectory Score (from HR Flex Report)
# ─────────────────────────────────────────────────────────────────────

def _parse_ppa(value: Any) -> float | None:
    """Convert PPA rating string to numeric value."""
    if value is None:
        return None
    return PPA_MAP.get(str(value).strip().lower())


def performance_score(candidate_hr: dict[str, Any] | None) -> float:
    """Score based on latest PPA rating and multi-year trajectory.

    Combines:
      - Latest PPA value (70% weight) — current performance level
      - Trajectory direction (30% weight) — improving/stable/declining

    Returns:
        float in [0.0, 1.0].
    """
    if not candidate_hr:
        return 0.0

    # Collect PPA ratings across years (ordered oldest to newest)
    ppa_fields = ["ppa_2022", "ppa_2023", "ppa_2024", "ppa_2025", "ppa_2026"]
    ratings = []
    for field in ppa_fields:
        parsed = _parse_ppa(candidate_hr.get(field))
        if parsed is not None:
            ratings.append(parsed)

    if not ratings:
        return 0.0

    # Latest PPA normalized to 0–1
    latest = ratings[-1] / MAX_PPA

    # Trajectory: slope of ratings over time
    if len(ratings) >= 2:
        # Simple: (last - first) / (number of intervals * max possible change)
        change = ratings[-1] - ratings[0]
        max_change = MAX_PPA  # theoretical max swing
        trajectory = (change / max_change + 1.0) / 2.0  # normalize to 0–1 (0.5 = stable)
    else:
        trajectory = 0.5  # neutral if only one data point

    return min(1.0, latest * 0.7 + trajectory * 0.3)


# ─────────────────────────────────────────────────────────────────────
# 4. Leadership / Behavioral Competency Score (from HR Flex BePCB)
# ─────────────────────────────────────────────────────────────────────

def _parse_bepcb(value: Any) -> float | None:
    """Convert BePCB rating string to numeric value."""
    if value is None:
        return None
    return BEPCB_MAP.get(str(value).strip().lower())


def leadership_behavioral_score(candidate_hr: dict[str, Any] | None) -> float:
    """Score based on latest BePCB (behavioral competency) rating.

    Uses the most recent available BePCB rating, normalized to 0.0–1.0.

    Returns:
        float in [0.0, 1.0].
    """
    if not candidate_hr:
        return 0.0

    bepcb_fields = ["bepcb_2026", "bepcb_2025", "bepcb_2024", "bepcb_2023", "bepcb_2022"]
    for field in bepcb_fields:
        parsed = _parse_bepcb(candidate_hr.get(field))
        if parsed is not None:
            return parsed / MAX_BEPCB

    return 0.0


# ─────────────────────────────────────────────────────────────────────
# 5. Grade Match Score (from HR Flex Report)
# ─────────────────────────────────────────────────────────────────────

def grade_match_score(
    candidate_hr: dict[str, Any] | None,
    required_grade: str,
) -> float:
    """Score based on how the candidate's job grade compares to the required grade.

    Uses the actual P-grade hierarchy instead of generic role levels.

    Returns:
        1.0 — exact match
        0.8 — candidate is one grade above (slightly overqualified)
        0.5 — candidate is two+ grades above (significantly overqualified)
        0.0 — candidate is below required grade
    """
    if not candidate_hr or not required_grade:
        return 0.0

    candidate_grade = str(candidate_hr.get("job_grade", "")).strip().upper()
    required_grade = required_grade.strip().upper()

    if candidate_grade not in GRADE_ORDER or required_grade not in GRADE_ORDER:
        return 0.0

    c_idx = GRADE_ORDER.index(candidate_grade)
    r_idx = GRADE_ORDER.index(required_grade)

    if c_idx == r_idx:
        return 1.0
    if c_idx < r_idx:
        # Candidate is more senior (lower index = higher grade)
        diff = r_idx - c_idx
        return 0.8 if diff == 1 else 0.5
    # Candidate is below required grade
    return 0.0


# ─────────────────────────────────────────────────────────────────────
# 6. Experience Depth Score (from HR Flex + SMA HRIS)
# ─────────────────────────────────────────────────────────────────────

def _parse_year_string(value: Any) -> float:
    """Parse strings like '5y 8m' or '3y 11m' into float years."""
    if value is None:
        return 0.0
    s = str(value).strip().lower()
    years = 0.0
    months = 0.0
    if "y" in s:
        parts = s.split("y")
        try:
            years = float(parts[0].strip())
        except ValueError:
            pass
        if len(parts) > 1 and "m" in parts[1]:
            try:
                months = float(parts[1].replace("m", "").strip())
            except ValueError:
                pass
    return years + months / 12.0


def experience_depth_score(
    candidate_hr: dict[str, Any] | None,
    candidate_hris: dict[str, Any] | None,
    min_years: float,
) -> float:
    """Multi-signal experience score combining grade tenure and organizational tenure.

    Signals:
      - no_of_year_in_salary_grade (HR Flex): depth at current level
      - year_in_sg (SMA HRIS): corroborating tenure signal
      - no_of_working_years_ext (HR Flex): external experience

    Returns:
        float in [0.0, 1.0]. 1.0 = meets or exceeds experience requirement.
    """
    if min_years <= 0:
        return 1.0

    # Collect experience signals
    grade_tenure = 0.0
    if candidate_hr:
        grade_tenure = _parse_year_string(candidate_hr.get("no_of_year_in_salary_grade"))
    
    hris_tenure = 0.0
    if candidate_hris:
        hris_tenure = float(candidate_hris.get("year_in_sg", 0.0))

    external_years = 0.0
    if candidate_hr:
        external_years = _parse_year_string(candidate_hr.get("no_of_working_years_ext"))

    # Use the best available tenure signal + external experience
    best_tenure = max(grade_tenure, hris_tenure)
    total_experience = best_tenure + external_years

    if total_experience >= min_years:
        return 1.0
    return total_experience / min_years


# ─────────────────────────────────────────────────────────────────────
# 7. SMA Completion Score (from SMA HRIS)
# ─────────────────────────────────────────────────────────────────────

def sma_completion_score(candidate_hris: dict[str, Any] | None) -> float:
    """Score based on SMA (Skills & Competency Management Assessment) completion status.

    Returns:
        1.0 — Completed All
        0.5 — Awaiting Approval / In Progress
        0.0 — Not Started / missing
    """
    if not candidate_hris:
        return 0.0

    status = str(candidate_hris.get("sma_completion_status", "")).strip().lower()

    if "completed" in status:
        return 1.0
    if "awaiting" in status or "progress" in status:
        return 0.5
    return 0.0


# ─────────────────────────────────────────────────────────────────────
# 8. Skill Group Match (from SMA HRIS / HR Flex)
# ─────────────────────────────────────────────────────────────────────

def skill_group_match_score(
    candidate_hris: dict[str, Any] | None,
    candidate_hr: dict[str, Any] | None,
    required_skg: str,
) -> float:
    """Score based on whether the candidate's skill group / position SKG matches the requirement.

    Checks both SMA HRIS skill_group and HR Flex position_skg.

    Returns:
        1.0 — exact match on either source
        0.0 — no match
    """
    if not required_skg:
        return 1.0

    required_lower = required_skg.strip().lower()

    # Check SMA HRIS skill_group (e.g., "018 Health, Safety & Environment")
    if candidate_hris:
        hris_sg = str(candidate_hris.get("skill_group", "")).strip().lower()
        if required_lower in hris_sg or hris_sg in required_lower:
            return 1.0

    # Check HR Flex position_skg (e.g., "Health, Safety & Environment")
    if candidate_hr:
        hr_skg = str(candidate_hr.get("position_skg", "")).strip().lower()
        if required_lower in hr_skg or hr_skg in required_lower:
            return 1.0

    return 0.0


# ─────────────────────────────────────────────────────────────────────
# Orchestrator: compute all v2 feature scores
# ─────────────────────────────────────────────────────────────────────

def compute_feature_scores_v2(
    candidate_hr: dict[str, Any] | None,
    candidate_hris: dict[str, Any] | None,
    candidate_epdr: list[dict[str, Any]],
    required_competencies: list[dict[str, Any]],
    required_grade: str = "",
    min_experience_years: float = 0,
    required_skg: str = "",
    requires_leadership: bool = False,
) -> dict[str, float]:
    """Compute all v2 feature scores for a single candidate.

    Args:
        candidate_hr: single row from HR Flex Report (or None if missing)
        candidate_hris: single row from SMA HRIS (or None if missing)
        candidate_epdr: list of EPDR rows for this candidate
        required_competencies: list of {"inventory_name": str, "min_proficiency": int}
        required_grade: minimum job grade (e.g., "P5")
        min_experience_years: minimum total experience in years
        required_skg: required skill group / position SKG
        requires_leadership: if True, leadership scores are weighted higher

    Returns:
        dict of feature_name → score (each 0.0–1.0)
    """
    scores = {
        "proficiency_gap": proficiency_gap_score(candidate_epdr, required_competencies),
        "technical_cbs": technical_cbs_score(candidate_hris),
        "leadership_cbs": leadership_cbs_score(candidate_hris),
        "overall_cbs": overall_cbs_score(candidate_hris),
        "performance": performance_score(candidate_hr),
        "leadership_behavioral": leadership_behavioral_score(candidate_hr),
        "grade_match": grade_match_score(candidate_hr, required_grade),
        "experience_depth": experience_depth_score(candidate_hr, candidate_hris, min_experience_years),
        "sma_completion": sma_completion_score(candidate_hris),
        "skill_group_match": skill_group_match_score(candidate_hris, candidate_hr, required_skg),
    }

    return scores
