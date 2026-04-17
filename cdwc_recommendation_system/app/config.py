"""Configurable weights and settings for the recommendation engine."""

WEIGHTS = {
    "skill_overlap": 0.35,
    "competency": 0.25,
    "experience": 0.20,
    "role_match": 0.20,
}

TOP_K = 5

ROLE_LEVELS = ["junior", "mid", "senior", "lead", "principal"]

# Role eligibility: candidate role_level index must be >= required role_level index
# e.g. a "senior" can fill a "mid" role, but not vice versa
