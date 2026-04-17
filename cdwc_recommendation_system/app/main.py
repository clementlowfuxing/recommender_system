"""FastAPI entry point for the CDWC Talent Recommendation Engine."""

import sys
from pathlib import Path
from typing import Any

# Ensure project root is on sys.path so `app.*` imports work when running directly
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from app.recommender import recommend
from app import config
from app.history import record, get_all, get_by_id

app = FastAPI(
    title="CDWC Talent Recommendation Engine",
    description="Similarity-based employee-to-project matching system.",
    version="2.0.0",
)


# ── Request / Response Models ─────────────────────────────────────────

class ProjectRequirement(BaseModel):
    required_skills: list[str] = Field(
        ..., examples=[["python", "machine_learning", "sql"]]
    )
    required_competency_level: float = Field(..., ge=0, le=5, examples=[4.0])
    min_experience: int = Field(..., ge=0, examples=[5])
    role_level: str = Field(..., examples=["senior"])
    availability_required: bool = Field(True, examples=[True])


class WeightsUpdate(BaseModel):
    skill_overlap: float = Field(0.35, ge=0, le=1)
    competency: float = Field(0.25, ge=0, le=1)
    experience: float = Field(0.20, ge=0, le=1)
    role_match: float = Field(0.20, ge=0, le=1)


class WeightsResponse(BaseModel):
    weights: dict[str, float]
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Liveness check."""
    return {"status": "ok"}


# ── POST /recommend ───────────────────────────────────────────────────

@app.post("/recommend")
def post_recommend(req: ProjectRequirement):
    """Accept a project requirement and return top-K ranked candidates.

    The engine applies hard filters (availability, role eligibility),
    computes per-dimension similarity scores, aggregates them using
    the current weight configuration, and returns the top-K candidates
    sorted by total score descending.

    Every request/response pair is persisted to the audit history.
    """
    result = recommend(
        required_skills=req.required_skills,
        required_competency_level=req.required_competency_level,
        min_experience=req.min_experience,
        role_level=req.role_level,
        availability_required=req.availability_required,
    )
    # Audit trail
    request_id = record(
        request=req.model_dump(),
        response=result,
    )
    result["request_id"] = request_id
    return result


# ── GET /history ──────────────────────────────────────────────────────

@app.get("/history")
def get_history(
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """Return paginated audit history of all recommendation requests.

    Each entry contains the original request payload, the engine's full
    response (candidates, scores, breakdowns), a timestamp, and a
    unique request_id.  Entries are returned newest-first.
    """
    return get_all(limit=limit, offset=offset)


@app.get("/history/{request_id}")
def get_history_entry(request_id: str):
    """Retrieve a single history entry by its request_id."""
    entry = get_by_id(request_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
    return entry


# ── GET /config/weights ───────────────────────────────────────────────

@app.get("/config/weights")
def get_weights():
    """Return the current scoring weights used by the recommendation engine."""
    return {"weights": dict(config.WEIGHTS)}


# ── PUT /config/weights ───────────────────────────────────────────────

@app.put("/config/weights", response_model=WeightsResponse)
def put_weights(body: WeightsUpdate):
    """Update the scoring weights at runtime.

    Weights must sum to 1.0 (±0.01 tolerance).  Changes take effect
    immediately on the next /recommend call.  The previous weights are
    overwritten in memory (restart resets to defaults).
    """
    new = body.model_dump()
    total = sum(new.values())
    if abs(total - 1.0) > 0.01:
        raise HTTPException(
            status_code=422,
            detail=f"Weights must sum to 1.0 (got {total:.4f})",
        )
    config.WEIGHTS.update(new)
    return WeightsResponse(
        weights=dict(config.WEIGHTS),
        message="Weights updated successfully",
    )


# ── Entrypoint ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
