"""
Structured API response → human-readable text.

Formats the recommendation engine's JSON output into a conversational
response.  All data comes from the API — nothing is fabricated.
"""

from typing import Any


def format_response(result: dict[str, Any], query: dict[str, Any]) -> str:
    """Convert engine output to a readable chat message."""
    recs = result.get("recommendations", [])
    total = result.get("total_candidates_evaluated", 0)
    filtered = result.get("candidates_after_filtering", 0)

    if not recs:
        return (
            f"I evaluated {total} employees and {filtered} passed the hard filters, "
            "but none matched your criteria well enough to recommend. "
            "Try relaxing the role level, experience, or skill requirements."
        )

    lines = [
        f"I evaluated {total} employees. After filtering for "
        f"{'availability and ' if query.get('availability_required') else ''}"
        f"role eligibility, {filtered} candidates remained.\n",
        f"Here are the top {len(recs)} matches:\n",
    ]

    for i, c in enumerate(recs, 1):
        bd = c["score_breakdown"]
        lines.append(
            f"  {i}. {c['name']}  —  score {c['total_score']:.2f}\n"
            f"     {c['department']} · {c['role_level']} · "
            f"{c['years_experience']} yrs exp\n"
            f"     Skills: {', '.join(c['skills'])}\n"
            f"     Breakdown → skill overlap {bd['skill_overlap']:.0%}, "
            f"competency {bd['competency']:.0%}, "
            f"experience {bd['experience']:.0%}, "
            f"role match {bd['role_match']:.0%}\n"
        )

    return "\n".join(lines)
