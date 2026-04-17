"""Feature engineering: compute similarity scores between a project requirement and a candidate."""

from typing import Any
from app.config import ROLE_LEVELS


def skill_overlap_score(candidate_skills: list[str], required_skills: list[str]) -> float:
    """Jaccard-style overlap: |intersection| / |required|. Returns 0.0–1.0."""
    if not required_skills:
        return 1.0
    candidate_set = set(s.lower() for s in candidate_skills)
    required_set = set(s.lower() for s in required_skills)
    overlap = candidate_set & required_set
    return len(overlap) / len(required_set)


def competency_similarity(candidate_score: float, required_level: float) -> float:
    """1 - normalized absolute difference. Scale 0–5. Returns 0.0–1.0."""
    max_scale = 5.0
    diff = abs(candidate_score - required_level) / max_scale
    return max(0.0, 1.0 - diff)


def experience_similarity(candidate_years: int, min_experience: int) -> float:
    """Returns 1.0 if candidate meets or exceeds requirement, decays linearly below."""
    if min_experience <= 0:
        return 1.0
    if candidate_years >= min_experience:
        return 1.0
    return candidate_years / min_experience


def role_match_score(candidate_role: str, required_role: str) -> float:
    """Returns 1.0 for exact match, 0.5 if candidate is higher, 0.0 if lower."""
    candidate_role = candidate_role.lower()
    required_role = required_role.lower()
    if candidate_role not in ROLE_LEVELS or required_role not in ROLE_LEVELS:
        return 0.0
    c_idx = ROLE_LEVELS.index(candidate_role)
    r_idx = ROLE_LEVELS.index(required_role)
    if c_idx == r_idx:
        return 1.0
    if c_idx > r_idx:
        return 0.5
    return 0.0


def compute_feature_scores(
    candidate: dict[str, Any],
    required_skills: list[str],
    required_competency_level: float,
    min_experience: int,
    role_level: str,
) -> dict[str, float]:
    """Compute all feature scores for a single candidate."""
    return {
        "skill_overlap": skill_overlap_score(candidate["skills"], required_skills),
        "competency": competency_similarity(candidate["competency_score"], required_competency_level),
        "experience": experience_similarity(candidate["years_experience"], min_experience),
        "role_match": role_match_score(candidate["role_level"], role_level),
    }
