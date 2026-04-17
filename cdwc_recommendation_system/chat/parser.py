"""
NL → Structured query extraction.

Two implementations:
  - MockParser:  keyword-based, zero dependencies, always available
  - LLMParser:   uses OpenAI chat completions (requires OPENAI_API_KEY)

Both return the same dict shape consumed by the orchestrator.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from app.config import ROLE_LEVELS

# ── Skill vocabulary (lowercase) used by the mock parser ──────────────
KNOWN_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node",
    "sql", "machine_learning", "data_analysis", "tensorflow",
    "statistics", "docker", "kubernetes", "aws", "terraform",
    "tableau", "spring", "css", "mongodb", "flask", "fastapi",
]

# Common aliases → canonical skill name
SKILL_ALIASES: dict[str, str] = {
    "ml": "machine_learning",
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "postgres": "sql",
    "postgresql": "sql",
    "data analysis": "data_analysis",
    "machine learning": "machine_learning",
}


class BaseParser(ABC):
    """Interface every parser must implement."""

    @abstractmethod
    def extract(self, user_message: str) -> dict[str, Any]:
        """Return a dict with keys matching the /recommend API contract."""


# ───────────────────────────────────────────────────────────────────────
# Mock (rule-based) parser — works offline, no API key needed
# ───────────────────────────────────────────────────────────────────────
class MockParser(BaseParser):
    """Keyword / regex extraction — good enough for demo & testing."""

    def extract(self, user_message: str) -> dict[str, Any]:
        text = user_message.lower()

        skills = self._extract_skills(text)
        competency = self._extract_competency(text)
        experience = self._extract_experience(text)
        role = self._extract_role(text)
        availability = self._extract_availability(text)

        return {
            "required_skills": skills,
            "required_competency_level": competency,
            "min_experience": experience,
            "role_level": role,
            "availability_required": availability,
        }

    # ── private helpers ────────────────────────────────────────────────
    def _extract_skills(self, text: str) -> list[str]:
        found: list[str] = []
        # Check aliases first (multi-word before single-word)
        for alias, canonical in sorted(SKILL_ALIASES.items(), key=lambda x: -len(x[0])):
            if alias in text:
                if canonical not in found:
                    found.append(canonical)
        # Then check known single-word skills
        for skill in KNOWN_SKILLS:
            if re.search(rf"\b{re.escape(skill)}\b", text) and skill not in found:
                found.append(skill)
        return found

    def _extract_competency(self, text: str) -> float:
        # Look for explicit numbers like "competency 4" or "level 3.5"
        m = re.search(r"(?:competency|level)\s*[:=]?\s*(\d+\.?\d*)", text)
        if m:
            return min(float(m.group(1)), 5.0)
        # Qualitative keywords
        if any(w in text for w in ("expert", "advanced", "strong")):
            return 4.5
        if "intermediate" in text:
            return 3.0
        if any(w in text for w in ("beginner", "entry")):
            return 1.5
        return 3.0  # default

    def _extract_experience(self, text: str) -> int:
        m = re.search(r"(\d+)\+?\s*(?:years?|yrs?)", text)
        if m:
            return int(m.group(1))
        return 0  # default

    def _extract_role(self, text: str) -> str:
        for role in reversed(ROLE_LEVELS):  # check highest first
            if role in text:
                return role
        return "mid"  # default

    def _extract_availability(self, text: str) -> bool:
        if any(w in text for w in ("unavailable", "not available", "include unavailable")):
            return False
        return True  # default


# ───────────────────────────────────────────────────────────────────────
# LLM-backed parser (OpenAI) — opt-in via OPENAI_API_KEY env var
# ───────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a query extraction assistant for a talent recommendation system.

Given a user's natural language request, extract ONLY these fields as JSON:
{
  "required_skills": ["skill1", "skill2"],
  "required_competency_level": <float 0-5, default 3.0>,
  "min_experience": <int, default 0>,
  "role_level": "<junior|mid|senior|lead|principal, default mid>",
  "availability_required": <bool, default true>
}

RULES:
- Map common aliases: ML→machine_learning, JS→javascript, K8s→kubernetes
- If a field is not mentioned, use the default shown above.
- Return ONLY valid JSON, no explanation.
"""


class LLMParser(BaseParser):
    """Uses OpenAI chat completions for extraction."""

    def __init__(self, model: str = "gpt-4o-mini"):
        try:
            from openai import OpenAI  # type: ignore
        except ImportError:
            raise ImportError("pip install openai  to use LLMParser")
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model

    def extract(self, user_message: str) -> dict[str, Any]:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0,
        )
        raw = resp.choices[0].message.content or "{}"
        # Strip markdown fences if present
        raw = re.sub(r"```json\s*", "", raw)
        raw = re.sub(r"```\s*", "", raw)
        return json.loads(raw)


def get_parser() -> BaseParser:
    """Factory: return LLMParser if OPENAI_API_KEY is set, else MockParser."""
    if os.environ.get("OPENAI_API_KEY"):
        return LLMParser()
    return MockParser()
