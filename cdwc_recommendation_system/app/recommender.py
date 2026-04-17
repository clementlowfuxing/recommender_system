"""Core ranking engine: filter, score, rank candidates."""

from typing import Any
from app.config import WEIGHTS, TOP_K, ROLE_LEVELS
from app.features import compute_feature_scores
from app.data_loader import load_employees


def _passes_hard_filters(
    candidate: dict[str, Any],
    availability_required: bool,
    role_level: str,
) -> bool:
    """Return True if candidate passes hard constraints."""
    """If the project requires availability and the candidate isn't available → rejected
        If the candidate's role level is below the required level 
        (e.g., a "mid" can't fill a "senior" slot) → rejected"""
    # Availability check
    if availability_required and not candidate["availability"]:
        return False
    # Role eligibility: candidate must be at or above required level
    c_role = candidate["role_level"].lower()
    r_role = role_level.lower()
    if c_role in ROLE_LEVELS and r_role in ROLE_LEVELS:
        if ROLE_LEVELS.index(c_role) < ROLE_LEVELS.index(r_role):
            return False
    return True


def _weighted_score(feature_scores: dict[str, float]) -> float:
    """Compute weighted total score from individual feature scores."""
    total = 0.0
    for feature, score in feature_scores.items():
        total += score * WEIGHTS.get(feature, 0.0)
    return round(total, 4)


def recommend(
    required_skills: list[str],
    required_competency_level: float,
    min_experience: int,
    role_level: str,
    availability_required: bool,
    top_k: int = TOP_K,
) -> dict[str, Any]:
    """Run the full recommendation pipeline and return ranked results."""
    employees = load_employees()

    # Step 1: Hard filtering
    eligible = [
        emp for emp in employees
        if _passes_hard_filters(emp, availability_required, role_level)
    ]

    # Step 2: Score each candidate
    scored = []
    for emp in eligible:
        features = compute_feature_scores(
            emp, required_skills, required_competency_level, min_experience, role_level
        )
        total = _weighted_score(features)
        scored.append({
            "employee_id": emp["employee_id"],
            "name": emp["name"],
            "department": emp["department"],
            "role_level": emp["role_level"],
            "skills": emp["skills"],
            "competency_score": emp["competency_score"],
            "years_experience": emp["years_experience"],
            "availability": emp["availability"],
            "score_breakdown": features,
            "total_score": total,
        })

    # Step 3: Rank by total score descending
    scored.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "total_candidates_evaluated": len(employees),
        "candidates_after_filtering": len(eligible),
        "top_k": top_k,
        "recommendations": scored[:top_k],
    }
