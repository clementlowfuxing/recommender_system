"""
Orchestrator: glue between the chat parser, the recommendation engine,
and the response formatter.

Flow:
  user message → parser.extract() → validate → recommender.recommend()
                                   → formatter.format_response() → reply
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Ensure project root importable
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from app.config import ROLE_LEVELS
from app.recommender import recommend
from chat.parser import BaseParser, get_parser
from chat.formatter import format_response

# Defaults applied when the parser returns nothing for optional fields
DEFAULTS: dict[str, Any] = {
    "required_competency_level": 3.0,
    "min_experience": 0,
    "role_level": "mid",
    "availability_required": True,
}


def _validate(query: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate and normalise extracted fields.

    Returns (cleaned_query, list_of_warnings).
    Raises ValueError if required fields are missing.
    """
    warnings: list[str] = []

    # --- required_skills (mandatory) ---
    skills = query.get("required_skills", [])
    if not skills:
        raise ValueError(
            "I couldn't identify any skills in your request. "
            "Could you mention the specific skills you need? "
            "(e.g. Python, SQL, machine learning)"
        )

    # --- apply defaults for optional fields ---
    cleaned: dict[str, Any] = {"required_skills": skills}
    for key, default in DEFAULTS.items():
        val = query.get(key)
        if val is None or val == "":
            cleaned[key] = default
            warnings.append(f"{key} not specified — using default ({default})")
        else:
            cleaned[key] = val

    # --- role_level validation ---
    role = str(cleaned["role_level"]).lower()
    if role not in ROLE_LEVELS:
        cleaned["role_level"] = "mid"
        warnings.append(f"Unrecognised role '{role}' — defaulting to 'mid'")
    else:
        cleaned["role_level"] = role

    # --- competency clamp ---
    comp = float(cleaned["required_competency_level"])
    cleaned["required_competency_level"] = max(0.0, min(comp, 5.0))

    # --- experience clamp ---
    cleaned["min_experience"] = max(0, int(cleaned["min_experience"]))

    return cleaned, warnings


class Orchestrator:
    """Stateless orchestrator — one call per user message."""

    def __init__(self, parser: BaseParser | None = None):
        self.parser = parser or get_parser()

    def handle(self, user_message: str) -> str:
        """Full pipeline: parse → validate → recommend → format."""
        # Step 1: extract structured query
        try:
            raw_query = self.parser.extract(user_message)
        except Exception as e:
            return f"Sorry, I had trouble understanding that: {e}"

        # Step 2: validate
        try:
            query, warnings = _validate(raw_query)
        except ValueError as e:
            return str(e)

        # Step 3: call recommendation engine (direct import, no HTTP)
        try:
            result = recommend(
                required_skills=query["required_skills"],
                required_competency_level=query["required_competency_level"],
                min_experience=query["min_experience"],
                role_level=query["role_level"],
                availability_required=query["availability_required"],
            )
        except Exception as e:
            return f"The recommendation engine returned an error: {e}"

        # Step 4: format response
        reply = format_response(result, query)

        # Prepend extraction summary so user can verify
        extracted = (
            f"Understood: skills={query['required_skills']}, "
            f"competency≥{query['required_competency_level']}, "
            f"experience≥{query['min_experience']} yrs, "
            f"role={query['role_level']}, "
            f"available={'yes' if query['availability_required'] else 'any'}\n"
        )
        if warnings:
            extracted += "Notes: " + "; ".join(warnings) + "\n"

        return extracted + "\n" + reply
