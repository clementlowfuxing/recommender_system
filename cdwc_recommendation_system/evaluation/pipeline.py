"""
Evaluation pipeline: run all metrics across a set of test queries.

Architecture:
  1. Generate synthetic test queries
  2. For each query:
     a. Run the recommendation engine
     b. Generate oracle ground truth labels
     c. Simulate expert panel judgments
     d. Compute all metrics (precision, recall, NDCG, diversity, fairness)
  3. Run ranking stability tests (weight perturbation)
  4. Aggregate results into a summary report
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from app import config
from app.recommender import recommend
from app.data_loader import load_employees
from evaluation.ground_truth import (
    generate_oracle_labels,
    simulate_panel,
    generate_test_queries,
)
from evaluation.metrics import (
    precision_at_k,
    recall_at_k,
    ndcg_at_k,
    diversity_score,
    fairness_score,
    kendall_tau,
    ranking_stability,
)


def _run_single_query(query: dict[str, Any], k: int = 5) -> dict[str, Any]:
    """Run engine + compute all metrics for one query."""
    employees = load_employees()

    # Run engine
    result = recommend(
        required_skills=query["required_skills"],
        required_competency_level=query["required_competency_level"],
        min_experience=query["min_experience"],
        role_level=query["role_level"],
        availability_required=query["availability_required"],
        top_k=k,
    )
    recs = result["recommendations"]
    ranked_ids = [r["employee_id"] for r in recs]

    # Generate ground truth
    oracle = generate_oracle_labels(
        employees,
        query["required_skills"],
        query["required_competency_level"],
        query["min_experience"],
        query["role_level"],
    )
    panel = simulate_panel(oracle, n_experts=3, noise_rate=0.1)

    # Eligible pool (for fairness calculation)
    eligible = [
        emp for emp in employees
        if emp["employee_id"] in [r["employee_id"] for r in result["recommendations"]]
        or oracle.get(emp["employee_id"], False)
    ]
    # Use all post-filter candidates for fairness baseline
    all_scored = employees  # simplification: use full pool

    # Compute metrics against oracle
    oracle_metrics = {
        "precision_at_3": precision_at_k(ranked_ids, oracle, 3),
        "precision_at_5": precision_at_k(ranked_ids, oracle, k),
        "recall_at_5": recall_at_k(ranked_ids, oracle, k),
        "ndcg_at_5": ndcg_at_k(ranked_ids, oracle, k),
    }

    # Compute metrics against simulated panel
    panel_metrics = {
        "precision_at_3_panel": precision_at_k(ranked_ids, panel, 3),
        "precision_at_5_panel": precision_at_k(ranked_ids, panel, k),
        "recall_at_5_panel": recall_at_k(ranked_ids, panel, k),
        "ndcg_at_5_panel": ndcg_at_k(ranked_ids, panel, k),
    }

    # Diversity & fairness
    quality_metrics = {
        "diversity": diversity_score(recs),
        "fairness": fairness_score(recs, all_scored),
    }

    total_relevant = sum(1 for v in oracle.values() if v)

    return {
        "query_id": query.get("query_id", "unknown"),
        "query": query,
        "ranked_ids": ranked_ids,
        "total_relevant_oracle": total_relevant,
        "total_recommended": len(recs),
        **oracle_metrics,
        **panel_metrics,
        **quality_metrics,
    }


def _run_stability_test(
    query: dict[str, Any],
    n_perturbations: int = 10,
    perturbation_magnitude: float = 0.05,
    k: int = 5,
) -> dict[str, float]:
    """Test ranking stability by perturbing weights and measuring Kendall's tau."""
    import random
    rng = random.Random(99)

    # Base ranking
    base_result = recommend(
        required_skills=query["required_skills"],
        required_competency_level=query["required_competency_level"],
        min_experience=query["min_experience"],
        role_level=query["role_level"],
        availability_required=query["availability_required"],
        top_k=k,
    )
    base_ranking = [r["employee_id"] for r in base_result["recommendations"]]

    # Save original weights
    original_weights = dict(config.WEIGHTS)
    perturbed_rankings = []

    for _ in range(n_perturbations):
        # Perturb weights
        new_weights = {}
        for key, val in original_weights.items():
            delta = rng.uniform(-perturbation_magnitude, perturbation_magnitude)
            new_weights[key] = max(0.01, val + delta)
        # Normalize to sum to 1.0
        total = sum(new_weights.values())
        new_weights = {k_: v / total for k_, v in new_weights.items()}
        config.WEIGHTS.update(new_weights)

        result = recommend(
            required_skills=query["required_skills"],
            required_competency_level=query["required_competency_level"],
            min_experience=query["min_experience"],
            role_level=query["role_level"],
            availability_required=query["availability_required"],
            top_k=k,
        )
        perturbed_rankings.append([r["employee_id"] for r in result["recommendations"]])

    # Restore original weights
    config.WEIGHTS.update(original_weights)

    return {
        "avg_kendall_tau": ranking_stability(base_ranking, perturbed_rankings),
        "n_perturbations": n_perturbations,
        "perturbation_magnitude": perturbation_magnitude,
    }


def run_full_evaluation(
    n_queries: int = 20,
    k: int = 5,
    seed: int = 42,
) -> dict[str, Any]:
    """Run the complete evaluation pipeline."""
    queries = generate_test_queries(n=n_queries, seed=seed)

    # Per-query metrics
    query_results = []
    for q in queries:
        qr = _run_single_query(q, k=k)
        query_results.append(qr)

    # Aggregate metrics
    metric_keys = [
        "precision_at_3", "precision_at_5", "recall_at_5", "ndcg_at_5",
        "precision_at_3_panel", "precision_at_5_panel",
        "recall_at_5_panel", "ndcg_at_5_panel",
        "diversity", "fairness",
    ]
    aggregated = {}
    for key in metric_keys:
        values = [qr[key] for qr in query_results]
        aggregated[key] = {
            "mean": round(sum(values) / len(values), 4),
            "min": round(min(values), 4),
            "max": round(max(values), 4),
        }

    # Stability test (on first 5 queries)
    stability_results = []
    for q in queries[:5]:
        sr = _run_stability_test(q, n_perturbations=10, perturbation_magnitude=0.05, k=k)
        stability_results.append(sr)
    avg_stability = sum(s["avg_kendall_tau"] for s in stability_results) / len(stability_results)

    return {
        "config": {"n_queries": n_queries, "k": k, "seed": seed},
        "aggregated_metrics": aggregated,
        "ranking_stability": {
            "avg_kendall_tau": round(avg_stability, 4),
            "interpretation": "1.0 = perfectly stable, 0.0 = random, <0 = inversions",
        },
        "per_query_results": query_results,
        "stability_details": stability_results,
    }
