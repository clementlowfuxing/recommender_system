"""
Synthetic ground truth generation for evaluation without labeled data.

Three strategies:
  1. Rule-based oracle  — deterministic "ideal" ranking from known rules
  2. Expert simulation  — simulated SME judgments with configurable noise
  3. Perturbation tests — verify ranking stability under small input changes

The core problem: we have no labeled data (no historical "this candidate was
correct for this requirement"). So we construct ground truth synthetically
using the system's own feature space, then measure whether the engine's
ranking agrees with that synthetic truth.
"""

from __future__ import annotations

import math
import random
from typing import Any

import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from app.data_loader import load_employees
from app.config import ROLE_LEVELS


# ─────────────────────────────────────────────────────────────────────
# Strategy 1: Rule-Based Oracle
# ─────────────────────────────────────────────────────────────────────

def rule_based_relevance(
    candidate: dict[str, Any],
    required_skills: list[str],
    required_competency: float,
    min_experience: int,
    role_level: str,
) -> bool:
    """Determine if a candidate is 'relevant' using hard rules.

    A candidate is relevant if ALL of:
      - has ≥ 50% skill overlap with required skills
      - competency_score ≥ required_competency - 1.0
      - years_experience ≥ min_experience
      - role_level index ≥ required role_level index
    """
    # Skill overlap
    c_skills = set(s.lower() for s in candidate["skills"])
    r_skills = set(s.lower() for s in required_skills)
    overlap = len(c_skills & r_skills) / len(r_skills) if r_skills else 1.0
    if overlap < 0.5:
        return False

    # Competency
    if candidate["competency_score"] < (required_competency - 1.0):
        return False

    # Experience
    if candidate["years_experience"] < min_experience:
        return False

    # Role level
    c_idx = ROLE_LEVELS.index(candidate["role_level"].lower()) if candidate["role_level"].lower() in ROLE_LEVELS else -1
    r_idx = ROLE_LEVELS.index(role_level.lower()) if role_level.lower() in ROLE_LEVELS else 0
    if c_idx < r_idx:
        return False

    return True


def generate_oracle_labels(
    employees: list[dict[str, Any]],
    required_skills: list[str],
    required_competency: float,
    min_experience: int,
    role_level: str,
) -> dict[str, bool]:
    """Return {employee_id: is_relevant} for all employees."""
    return {
        emp["employee_id"]: rule_based_relevance(
            emp, required_skills, required_competency, min_experience, role_level
        )
        for emp in employees
    }


# ─────────────────────────────────────────────────────────────────────
# Strategy 2: Expert Simulation
# ─────────────────────────────────────────────────────────────────────

def simulate_expert_judgment(
    oracle_labels: dict[str, bool],
    noise_rate: float = 0.1,
    seed: int = 42,
) -> dict[str, bool]:
    """Simulate a single SME's judgment by flipping oracle labels with noise.

    Args:
        oracle_labels: ground truth from rule-based oracle
        noise_rate: probability of flipping each label (0.0 = perfect expert)
        seed: for reproducibility

    Returns:
        {employee_id: expert_judgment}
    """
    rng = random.Random(seed)
    result = {}
    for emp_id, label in oracle_labels.items():
        if rng.random() < noise_rate:
            result[emp_id] = not label
        else:
            result[emp_id] = label
    return result


def simulate_panel(
    oracle_labels: dict[str, bool],
    n_experts: int = 3,
    noise_rate: float = 0.1,
    base_seed: int = 42,
) -> dict[str, bool]:
    """Simulate a panel of SMEs and return majority-vote labels."""
    votes: dict[str, list[bool]] = {eid: [] for eid in oracle_labels}
    for i in range(n_experts):
        expert = simulate_expert_judgment(oracle_labels, noise_rate, seed=base_seed + i)
        for eid, judgment in expert.items():
            votes[eid].append(judgment)
    return {
        eid: sum(v) > len(v) / 2
        for eid, v in votes.items()
    }


# ─────────────────────────────────────────────────────────────────────
# Strategy 3: Synthetic Test Queries
# ─────────────────────────────────────────────────────────────────────

SKILL_POOL = [
    "python", "java", "javascript", "sql", "machine_learning",
    "docker", "aws", "react", "statistics", "tensorflow",
    "kubernetes", "typescript", "spring", "data_analysis", "tableau",
]


def generate_test_queries(n: int = 20, seed: int = 42) -> list[dict[str, Any]]:
    """Generate n diverse synthetic project requirements."""
    rng = random.Random(seed)
    queries = []
    for i in range(n):
        n_skills = rng.randint(1, 4)
        skills = rng.sample(SKILL_POOL, n_skills)
        queries.append({
            "query_id": f"Q-{i+1:03d}",
            "required_skills": skills,
            "required_competency_level": round(rng.uniform(2.5, 4.8), 1),
            "min_experience": rng.randint(0, 8),
            "role_level": rng.choice(ROLE_LEVELS),
            "availability_required": rng.choice([True, True, True, False]),
        })
    return queries
