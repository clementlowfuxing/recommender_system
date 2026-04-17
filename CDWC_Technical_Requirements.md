# CDWC Agent — Technical Requirements Document

## 1. Data Layer Requirements

### Talent Profile Ingestion
- Ingest structured talent data from CSV/Excel exports provided by HR
- Support the full talent profile schema: `employee_id`, `name`, `department`, `role_title`, `role_level`, `skills`, `competency_levels` (map: skill → 1–5), `years_of_experience`, `certifications`, `availability_status`, `availability_date`, `location`, `current_project`, `last_updated`
- All required fields must be present; flag (do not silently exclude) profiles with missing optional fields

### Data Quality & Completeness
- Generate a data quality report during initial load (Sprint 1 deliverable)


## 2. Technology Stack (POC)

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| API Framework | FastAPI + Uvicorn |
| Data Validation | Pydantic |
| Similarity Computation | scikit-learn (cosine_similarity), numpy, custom functions |
| Chat UI | Streamlit (web), CLI (terminal) |
| LLM Integration | OpenAI API (opt-in) or mock parser (default) |
| Data Storage | JSON files (POC), SQLite/PostgreSQL (production path) |
| Feature Encoding | scikit-learn encoders, numpy |
| Testing | pytest, FastAPI TestClient |

