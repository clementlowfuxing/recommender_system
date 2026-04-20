"""
Evaluation metrics for the CDWC Talent Recommendation Engine.

All metrics operate on:
  - ranked_ids:  list of employee_ids in the order the engine ranked them
  - relevance:   dict {employee_id: bool} — ground truth (oracle or SME)

Mathematical formulations are documented in each function's docstring.

Metrics implemented:
  1. Precision@K
  2. Recall@K
  3. NDCG@K  (Normalized Discounted Cumulative Gain)
  4. Diversity (intra-list department diversity)
  5. Fairness (department representation ratio)
  6. Ranking Stability (Kendall's tau under weight perturbation)
"""

from __future__ import annotations

import math
from typing import Any
from collections import Counter


# ─────────────────────────────────────────────────────────────────────
# 1. Precision@K
# ─────────────────────────────────────────────────────────────────────

def precision_at_k(
    ranked_ids: list[str],
    relevance: dict[str, bool],
    k: int,
) -> float:
    """Fraction of top-K results that are relevant.

    Formula:
        Precision@K = |{relevant items in top K}| / K

    Args:
        ranked_ids: engine's ranked list of employee_ids
        relevance: {employee_id: True/False}
        k: cutoff

    Returns:
        float in [0.0, 1.0]
    """
    top_k = ranked_ids[:k]
    relevant_count = sum(1 for eid in top_k if relevance.get(eid, False))
    return relevant_count / k if k > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────
# 2. Recall@K
# ─────────────────────────────────────────────────────────────────────

def recall_at_k(
    ranked_ids: list[str],
    relevance: dict[str, bool],
    k: int,
) -> float:
    """Fraction of all relevant items that appear in top-K.

    Formula:
        Recall@K = |{relevant items in top K}| / |{all relevant items}|

    Returns 1.0 if there are no relevant items (vacuous truth).
    """
    total_relevant = sum(1 for v in relevance.values() if v)
    if total_relevant == 0:
        return 1.0
    top_k = ranked_ids[:k]
    hits = sum(1 for eid in top_k if relevance.get(eid, False))
    return hits / total_relevant


# ─────────────────────────────────────────────────────────────────────
# 3. NDCG@K (Normalized Discounted Cumulative Gain)
# ─────────────────────────────────────────────────────────────────────

def _dcg(relevance_scores: list[float], k: int) -> float:
    """Discounted Cumulative Gain.

    Formula:
        DCG@K = Σ_{i=1}^{K} rel_i / log₂(i + 1)
    """
    total = 0.0
    for i, rel in enumerate(relevance_scores[:k]):
        total += rel / math.log2(i + 2)  # i+2 because i is 0-indexed
    return total


def ndcg_at_k(
    ranked_ids: list[str],
    relevance: dict[str, bool],
    k: int,
) -> float:
    """Normalized Discounted Cumulative Gain.

    Formula:
        NDCG@K = DCG@K / IDCG@K

    Where IDCG@K is the DCG of the ideal ranking (all relevant items first).

    Uses binary relevance: rel_i = 1.0 if relevant, 0.0 otherwise.
    Returns 1.0 if IDCG is 0 (no relevant items).
    """
    # Actual DCG
    actual_rels = [1.0 if relevance.get(eid, False) else 0.0 for eid in ranked_ids[:k]]
    dcg = _dcg(actual_rels, k)

    # Ideal DCG: sort all relevance scores descending
    ideal_rels = sorted(
        [1.0 if v else 0.0 for v in relevance.values()],
        reverse=True,
    )
    idcg = _dcg(ideal_rels, k)

    return dcg / idcg if idcg > 0 else 1.0


# ─────────────────────────────────────────────────────────────────────
# 4. Diversity (Intra-List Department Diversity)
# ─────────────────────────────────────────────────────────────────────

def diversity_score(
    recommendations: list[dict[str, Any]],
) -> float:
    """Measure how diverse the top-K list is by department representation.

    Formula:
        Diversity = |unique departments in top K| / K

    A score of 1.0 means every candidate is from a different department.
    A score of 1/K means all candidates are from the same department.
    """
    if not recommendations:
        return 0.0
    departments = [r["department"] for r in recommendations]
    return len(set(departments)) / len(departments)


# ─────────────────────────────────────────────────────────────────────
# 5. Fairness (Department Representation Ratio)
# ─────────────────────────────────────────────────────────────────────

def fairness_score(
    recommendations: list[dict[str, Any]],
    all_eligible: list[dict[str, Any]],
) -> float:
    """Measure whether department representation in top-K reflects the eligible pool.

    Formula:
        For each department d:
            pool_ratio_d = |employees in d in eligible pool| / |eligible pool|
            topk_ratio_d = |employees in d in top K| / K

        Fairness = 1 - (1/D) × Σ |topk_ratio_d - pool_ratio_d|

    Where D = number of departments in the eligible pool.

    Score of 1.0 = perfect proportional representation.
    Score near 0.0 = severe over/under-representation.
    """
    if not recommendations or not all_eligible:
        return 0.0

    k = len(recommendations)
    n = len(all_eligible)

    pool_depts = Counter(e["department"] for e in all_eligible)
    topk_depts = Counter(r["department"] for r in recommendations)

    all_depts = set(pool_depts.keys())
    d = len(all_depts)
    if d == 0:
        return 1.0

    total_deviation = 0.0
    for dept in all_depts:
        pool_ratio = pool_depts.get(dept, 0) / n
        topk_ratio = topk_depts.get(dept, 0) / k
        total_deviation += abs(topk_ratio - pool_ratio)

    return max(0.0, 1.0 - total_deviation / d)


# ─────────────────────────────────────────────────────────────────────
# 6. Ranking Stability (Kendall's Tau)
# ─────────────────────────────────────────────────────────────────────

def kendall_tau(ranking_a: list[str], ranking_b: list[str]) -> float:
    """Kendall's Tau rank correlation between two rankings.

    Formula:
        τ = (concordant - discordant) / (n × (n-1) / 2)

    Where:
        concordant = pairs (i,j) where both rankings agree on order
        discordant = pairs (i,j) where rankings disagree

    Returns:
        float in [-1.0, 1.0]. 1.0 = identical rankings, -1.0 = reversed.
    """
    # Build position maps (only for items in both lists)
    common = set(ranking_a) & set(ranking_b)
    if len(common) < 2:
        return 1.0

    items = sorted(common)
    pos_a = {item: i for i, item in enumerate(ranking_a) if item in common}
    pos_b = {item: i for i, item in enumerate(ranking_b) if item in common}

    concordant = 0
    discordant = 0
    n = len(items)
    for i in range(n):
        for j in range(i + 1, n):
            a_diff = pos_a[items[i]] - pos_a[items[j]]
            b_diff = pos_b[items[i]] - pos_b[items[j]]
            if a_diff * b_diff > 0:
                concordant += 1
            elif a_diff * b_diff < 0:
                discordant += 1
            # ties (a_diff or b_diff == 0) are neither

    total_pairs = n * (n - 1) / 2
    return (concordant - discordant) / total_pairs if total_pairs > 0 else 1.0


def ranking_stability(
    base_ranking: list[str],
    perturbed_rankings: list[list[str]],
) -> float:
    """Average Kendall's Tau between a base ranking and multiple perturbed rankings.

    Formula:
        Stability = (1/P) × Σ_{p=1}^{P} τ(base, perturbed_p)

    Where P = number of perturbation runs.

    Returns:
        float in [-1.0, 1.0]. Higher = more stable.
    """
    if not perturbed_rankings:
        return 1.0
    taus = [kendall_tau(base_ranking, pr) for pr in perturbed_rankings]
    return sum(taus) / len(taus)
