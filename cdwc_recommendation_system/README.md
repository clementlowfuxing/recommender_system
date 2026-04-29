# CDWC Talent Recommendation Engine

Similarity-based employee-to-project matching system. Fully local, deterministic, no external AI APIs.

## Quick Start

```bash
cd cdwc_recommendation_system
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Server starts at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

The `--reload` flag enables auto-restart on code changes (useful during development). Drop it in production.

## Test It

With the server running, in another terminal:

```bash
python scripts/test_request.py
```

Or use curl:

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "required_skills": ["python", "machine_learning", "sql"],
    "required_competency_level": 4.0,
    "min_experience": 5,
    "role_level": "senior",
    "availability_required": true
  }'
```

## Project Structure

```
cdwc_recommendation_system/
├── app/
│   ├── main.py            # FastAPI entry point
│   ├── recommender.py     # Core ranking engine
│   ├── features.py        # Feature engineering logic
│   ├── data_loader.py     # Dataset loading
│   ├── config.py          # Weights + settings
├── chat/
│   ├── cli.py             # Terminal chat interface
│   ├── streamlit_app.py   # Streamlit web chat UI
│   ├── orchestrator.py    # Parse → validate → recommend → format
│   ├── parser.py          # NL extraction (mock + OpenAI)
│   ├── formatter.py       # Engine output → readable text
├── frontend/
│   ├── index.html         # Vanilla JS web UI
│   ├── app.js             # API calls + DOM rendering
│   ├── style.css          # Styling
├── data/
│   └── employees.json     # 20-employee synthetic dataset
├── scripts/
│   ├── run_local.sh       # Shell launcher
│   └── test_request.py    # Test API request
├── requirements.txt
└── README.md
```

## Chat Interface

The chat layer lets you query the recommendation engine in plain English instead of constructing JSON.

### CLI Chat

```bash
python chat/cli.py
```

Then type something like:
```
You: I need a senior Python developer with ML experience, 5+ years
```

### Streamlit Web Chat

```bash
pip install -r requirements.txt
streamlit run chat/streamlit_app.py
```

Opens a browser-based chat at `http://localhost:8501`.

### Vanilla JS Web UI

With the server running (`uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload`), open:

```
http://localhost:8000/ui
```

This is a lightweight frontend served directly by FastAPI — no extra dependencies. It has two modes:

- **Form Search** — fill in skills, competency, experience, and role level, then hit Search. Calls `/recommend` directly.
- **Chat Search** — type a natural language query (same as Streamlit/CLI). Calls `/chat` which wraps the orchestrator pipeline.

### How the Chat Layer Works

1. Parser extracts structured fields from your natural language query (skills, experience, role, etc.)
2. Orchestrator validates the extracted fields, applies defaults, and calls the recommendation engine
3. Formatter converts the engine's ranked results into a readable response
4. All rankings come from the deterministic engine — the chat layer never scores or ranks candidates

By default, the mock parser (keyword-based, no API key needed) is used. Set `OPENAI_API_KEY` to enable LLM-powered extraction.

## How It Works

1. **Hard filtering** — removes candidates who are unavailable or below the required role level
2. **Feature scoring** — computes skill overlap, competency similarity, experience similarity, and role match
3. **Weighted aggregation** — combines scores using configurable weights (see `app/config.py`)
4. **Ranking** — returns top 5 candidates with full score breakdowns
