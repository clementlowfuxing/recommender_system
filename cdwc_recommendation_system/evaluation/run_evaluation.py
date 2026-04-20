"""Run the full evaluation pipeline and print results."""

import json
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from evaluation.pipeline import run_full_evaluation


def main():
    print("Running CDWC Recommendation Engine Evaluation...")
    print("=" * 60)

    results = run_full_evaluation(n_queries=20, k=5, seed=42)

    # Summary
    agg = results["aggregated_metrics"]
    print("\nAGGREGATED METRICS (across 20 test queries)")
    print("-" * 60)
    print(f"{'Metric':<30} {'Mean':>8} {'Min':>8} {'Max':>8}")
    print("-" * 60)
    for metric, vals in agg.items():
        label = metric.replace("_", " ").title()
        print(f"{label:<30} {vals['mean']:>8.2%} {vals['min']:>8.2%} {vals['max']:>8.2%}")

    # Stability
    stab = results["ranking_stability"]
    print(f"\n{'Ranking Stability (Kendall τ)':<30} {stab['avg_kendall_tau']:>8.4f}")
    print(f"  ({stab['interpretation']})")

    # PRD targets
    print("\n" + "=" * 60)
    print("PRD TARGET COMPARISON")
    print("-" * 60)
    p3 = agg["precision_at_3"]["mean"]
    p5 = agg["precision_at_5"]["mean"]
    print(f"Precision@3:  {p3:.2%}  (target ≥ 80%)  {'✓ PASS' if p3 >= 0.80 else '✗ BELOW TARGET'}")
    print(f"Precision@5:  {p5:.2%}  (target ≥ 70%)  {'✓ PASS' if p5 >= 0.70 else '✗ BELOW TARGET'}")

    # Save full results
    output_path = Path(_root) / "data" / "evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull results saved to: {output_path}")


if __name__ == "__main__":
    main()
