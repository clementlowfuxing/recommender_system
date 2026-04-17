# CDWC Agent — Product Requirements Document (PRD)

## Proof of Concept: Similarity-Based Talent Matching Engine

**Version:** 1.1
**Date:** April 16, 2026
**Status:** Draft for Engineering Review
**Sprint Cycle:** 4 Sprints (2 weeks each)

---

## 1. Product Overview

The CDWC Agent is a deterministic decision-support system that matches internal talent profiles against structured project requirements using similarity-based computation and weighted scoring. It produces a ranked list of the top 3–5 candidates for any given project requirement, with full explainability of how each score was derived.

The system's primary interaction interface is a **Conversational Chat Layer** that allows CDWC members to express project needs in natural language. The chat layer translates user queries into structured inputs, passes them to the deterministic recommendation engine, and formats the engine's structured output into human-readable responses. The recommendation engine remains the sole source of all ranking and scoring decisions.

**What it is:**
- A structured data matching engine
- A ranking and scoring system with configurable weights
- An explainable, auditable recommendation tool
- A conversational interface for natural language access to talent search

**What it is NOT:**
- An LLM-driven decision-maker — the chatbot is only an input parser and output formatter
- A predictive model
- An automated decision-maker
- A RAG or external knowledge-based system

The system operates exclusively on numerical and categorical data. There is no text processing, no natural language understanding, and no probabilistic generation. Outputs are deterministic — identical inputs always produce identical outputs.

---

## 2. Users

### Primary Users

| User Role | Description | Interaction Mode |
|---|---|---|
| **CDWC Committee Members** | Senior leaders responsible for talent deployment decisions. They define project requirements and review candidate recommendations. | Input project requirements, review ranked candidates, validate or override recommendations. |
| **HR Subject Matter Experts (SMEs)** | HR professionals with deep knowledge of the talent pool. They validate system outputs, calibrate weights, and maintain data quality. | Review recommendations for accuracy, provide feedback on rankings, participate in evaluation sessions, flag data quality issues. |

### Secondary Users (Future Phases)

| User Role | Description |
|---|---|
| **HR Data Administrators** | Maintain and update talent profile data. Ensure data completeness and accuracy. |
| **Hiring Managers** | Self-service access to talent recommendations for their projects (Phase 3+). |

---

## 3. User Stories

### Epic 1: Project Requirement Input

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-01 | As a CDWC member, I want to input a structured project requirement so that the system can match it against the talent pool. | Requirement form captures: required skills, competency levels, experience range, role type, availability window. Validation prevents submission of incomplete requirements. | P0 |
| US-02 | As a CDWC member, I want to save and reuse project requirement templates so that I don't re-enter common configurations. | Templates can be saved, named, loaded, and edited. | P2 |

### Epic 2: Candidate Matching & Ranking

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-03 | As a CDWC member, I want to receive a ranked list of top 3–5 candidates for my project requirement so that I can make an informed staffing decision. | System returns top K candidates ranked by composite similarity score. K is configurable (default 5). Results returned in < 5 seconds. | P0 |
| US-04 | As a CDWC member, I want to see a similarity score for each candidate so that I can understand how well they match the requirement. | Each candidate displays a composite score (0–100) and individual dimension scores. | P0 |
| US-05 | As a CDWC member, I want to see an explainable breakdown of each candidate's score so that I can understand why they were ranked in that position. | Breakdown shows: skill match %, competency match %, experience match %, availability status, and any hard-filter flags. | P0 |
| US-06 | As a CDWC member, I want to filter candidates by department, location, or role before running the match so that I can narrow the search space. | Pre-filters are optional. Filtered candidates are excluded before similarity computation. | P1 |

### Epic 3: Validation & Feedback

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-07 | As an HR SME, I want to mark each recommended candidate as "suitable" or "not suitable" so that we can measure system accuracy. | Binary feedback captured per candidate per request. Feedback stored for Precision@K calculation. | P0 |
| US-08 | As an HR SME, I want to suggest a candidate the system missed so that we can identify coverage gaps. | SME can add a candidate ID with a note. System logs the miss for analysis. | P1 |
| US-09 | As a CDWC member, I want to see a history of past requests and their outcomes so that I can track decisions over time. | Request history shows: date, requirement summary, top candidates, SME feedback, final decision. | P2 |

### Epic 4: Weight Configuration

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-10 | As an HR SME, I want to adjust the weights assigned to each scoring dimension so that the system reflects our priorities. | Weights are configurable per dimension (skills, competency, experience, availability). Changes take effect on next query. Defaults are documented. | P1 |
| US-11 | As an HR SME, I want to see how changing weights affects the ranking for a given requirement so that I can calibrate effectively. | "What-if" mode: adjust weights and re-run the same requirement to compare rankings side-by-side. | P2 |

### Epic 5: Conversational Interface (NEW)

| ID | User Story | Acceptance Criteria | Priority |
|---|---|---|---|
| US-12 | As a CDWC member, I want to ask for talent recommendations using natural language so that I don't need to manually fill structured input fields. | Chat interface accepts free-text queries. System extracts skills, experience, role level, and availability from the query. Extracted fields are passed to the `/recommend` API. | P1 |
| US-13 | As a CDWC member, I want the system to interpret my query and return ranked candidates automatically so that I get results in a single conversational step. | System returns top-K candidates with scores and a natural language summary. Response includes score breakdowns. All data originates from the recommendation engine — no hallucinated attributes. | P1 |
| US-14 | As a CDWC member, I want to review the structured query the chatbot extracted from my input so that I can verify it understood my intent correctly. | Before calling the API, the chat layer displays the extracted structured fields. User can confirm, edit, or re-phrase. | P1 |
| US-15 | As a CDWC member, I want the chatbot to ask clarifying questions when my query is ambiguous so that the system doesn't make incorrect assumptions. | If required fields cannot be confidently extracted, the chat layer prompts for clarification rather than guessing. | P2 |

---

## 4. Functional Requirements

### 4.1 Input: Structured Project Requirement

The system accepts a project requirement as a structured object with the following fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `required_skills` | Array of strings (from controlled vocabulary) | Yes | Skills needed for the project (e.g., "Python", "Project Management", "Financial Analysis") |
| `competency_levels` | Map: skill → level (1–5) | Yes | Minimum competency level required per skill |
| `experience_min_years` | Integer | Yes | Minimum years of relevant experience |
| `experience_max_years` | Integer | No | Maximum years (for targeting mid-level, etc.) |
| `role_type` | String (from controlled vocabulary) | Yes | Target role (e.g., "Senior Analyst", "Team Lead") |
| `department_preference` | Array of strings | No | Preferred departments (optional filter) |
| `availability_window` | Date range | Yes | When the candidate must be available |
| `location_preference` | String | No | Preferred work location (optional filter) |

### 4.2 Talent Filtering

Before similarity computation, the system applies hard filters to exclude ineligible candidates:

1. **Availability filter:** Exclude candidates whose availability status conflicts with the required window
2. **Role filter:** Exclude candidates whose role category does not match the requirement (if strict matching is enabled)
3. **Department filter:** If department preference is specified, exclude candidates outside those departments
4. **Data completeness filter:** Flag (but do not exclude by default) candidates with incomplete profiles

Hard filters are applied as boolean gates. They reduce the candidate pool before the computationally expensive similarity step.

### 4.3 Similarity Computation

For each candidate passing hard filters, compute a composite similarity score:

```
composite_score = Σ (weight_i × dimension_score_i) for i in dimensions
```

**Dimensions:**

| Dimension | Scoring Method | Weight (Default) |
|---|---|---|
| Skill Match | Cosine similarity between requirement skill vector and candidate skill vector (binary encoding) | 0.35 |
| Competency Match | Normalized distance between required competency levels and candidate competency levels per matched skill | 0.25 |
| Experience Match | Gaussian proximity score centered on the midpoint of the required experience range | 0.20 |
| Availability Match | Binary (1 if available in window, 0.5 if partially available, 0 if unavailable) | 0.15 |
| Certification Bonus | Bonus score for relevant certifications (additive, capped) | 0.05 |

Weights are configurable and must sum to 1.0. Default weights are set based on initial SME consultation and can be adjusted through the weight configuration interface (US-10).

### 4.4 Ranking Engine

1. Sort candidates by composite score (descending)
2. Return top K candidates (K configurable, default = 5)
3. For each candidate, return:
   - Composite score (0–100, normalized)
   - Per-dimension scores
   - Per-dimension contribution to composite score
   - Hard filter status (passed/flagged)
   - Data completeness indicator

### 4.5 Output Format

```json
{
  "request_id": "REQ-2026-0042",
  "timestamp": "2026-04-14T10:30:00Z",
  "project_requirement": { ... },
  "candidates": [
    {
      "rank": 1,
      "employee_id": "EMP-1234",
      "composite_score": 87.3,
      "breakdown": {
        "skill_match": { "score": 92.0, "weight": 0.35, "contribution": 32.2 },
        "competency_match": { "score": 85.0, "weight": 0.25, "contribution": 21.3 },
        "experience_match": { "score": 78.0, "weight": 0.20, "contribution": 15.6 },
        "availability_match": { "score": 100.0, "weight": 0.15, "contribution": 15.0 },
        "certification_bonus": { "score": 65.0, "weight": 0.05, "contribution": 3.3 }
      },
      "flags": [],
      "data_completeness": 0.95
    }
  ],
  "total_candidates_evaluated": 342,
  "total_after_hard_filters": 87,
  "weights_used": { ... }
}
```

---

## 4.6 Chat Layer: Conversational Interface (NEW)

### 4.6.1 Input Handling

The chat interface accepts natural language queries and extracts structured fields:

| Extracted Field | Type | Required | Default if Absent |
|---|---|---|---|
| `required_skills` | Array of strings | Yes (must extract at least one) | — (prompt user for clarification) |
| `required_competency_level` | Float (0–5) | No | 3.0 |
| `min_experience` | Integer | No | 0 |
| `role_level` | String (junior/mid/senior/lead/principal) | No | "mid" |
| `availability_required` | Boolean | No | true |

The chat layer uses an LLM to parse natural language into these fields. If required fields cannot be extracted with confidence, the system asks clarifying questions.

### 4.6.2 Orchestration

1. Chat layer extracts structured fields from user query
2. Orchestrator validates fields against schema and controlled vocabularies
3. Orchestrator constructs a valid JSON payload matching the `/recommend` API contract
4. Orchestrator calls `POST /recommend` with the structured payload
5. Orchestrator receives the structured JSON response from the engine

### 4.6.3 Output Handling

The chat layer converts the API's structured response into a human-readable format:

- Displays top candidates with names, departments, and roles
- Shows total scores and per-dimension score breakdowns
- Provides a short natural language explanation of why each candidate ranked where they did
- All displayed data must originate from the API response — no fabricated attributes or scores

### 4.6.4 Chat Layer Constraints

- The chat layer MUST NOT perform ranking or scoring
- The chat layer MUST NOT infer candidate attributes not present in the API response
- The chat layer MUST NOT override or reorder the engine's rankings
- The chat layer MUST NOT access the data layer directly — all data flows through the API
- If the LLM cannot extract a valid query, it must ask for clarification rather than guess

---

## 5. Non-Functional Requirements

| Requirement | Specification | Rationale |
|---|---|---|
| **Determinism** | Identical inputs must produce identical outputs across all runs. No randomness, no stochastic components. | Trust and auditability. |
| **Explainability** | Every score must be decomposable into per-dimension contributions with human-readable labels. | CDWC members must understand and challenge recommendations. |
| **Response time** | End-to-end computation (filter + similarity + ranking) must complete in < 5 seconds for a talent pool of up to 10,000 profiles. | Usability during committee sessions. |
| **Data privacy** | Employee data must not leave the system boundary. No external API calls with PII. Access restricted to authorized CDWC and HR users. | Compliance with internal data governance policies. |
| **Audit logging** | Every request, response, and SME feedback action must be logged with timestamp, user ID, and full payload. | Accountability and continuous improvement. |
| **Availability** | System must be available during business hours (99% uptime during POC). | Committee sessions are scheduled; downtime during sessions is unacceptable. |
| **Configurability** | Weights, K value, hard filter rules, and controlled vocabularies must be configurable without code changes. | Enable SME-driven calibration without engineering dependency. |
| **Chat response latency** | End-to-end chat interaction (NL parsing + API call + response formatting) must complete in < 3 seconds. | Conversational UX requires near-instant feedback. |
| **Deterministic recommendations** | All candidate rankings and scores are produced exclusively by the recommendation engine, never by the chat layer. | Prevents LLM from influencing decision logic. |
| **No hallucinated attributes** | The chat layer must not display candidate skills, scores, or qualifications that are not present in the API response. | Trust and accuracy — users must be able to verify every displayed data point against the engine's output. |

---

## 6. Data Requirements

### 6.1 Talent Profile Schema

| Field | Type | Source | Required |
|---|---|---|---|
| `employee_id` | String (unique) | HRIS export | Yes |
| `name` | String | HRIS export | Yes |
| `department` | String (categorical) | HRIS export | Yes |
| `role_title` | String (categorical) | HRIS export | Yes |
| `role_level` | String (categorical: Junior/Mid/Senior/Lead/Principal) | HRIS export | Yes |
| `skills` | Array of strings (controlled vocabulary) | Skills inventory | Yes |
| `competency_levels` | Map: skill → level (1–5) | Competency assessment | Yes |
| `years_of_experience` | Integer | HRIS export | Yes |
| `certifications` | Array of strings | Training records | No |
| `availability_status` | Enum: Available / Partially Available / Unavailable | Resource management | Yes |
| `availability_date` | Date | Resource management | Conditional |
| `location` | String (categorical) | HRIS export | Yes |
| `current_project` | String | Resource management | No |
| `last_updated` | Date | System-generated | Yes |

### 6.2 Project Requirement Schema

(As defined in Section 4.1)

### 6.3 Feature Encoding

| Feature | Encoding Method |
|---|---|
| Skills | Multi-hot binary vector over controlled skill vocabulary (e.g., 150 skills → 150-dimensional binary vector) |
| Competency levels | Ordinal encoding (1–5) per skill, zero-padded for skills not held |
| Experience | Numerical (integer years) |
| Role level | Ordinal encoding (Junior=1, Mid=2, Senior=3, Lead=4, Principal=5) |
| Availability | Categorical encoding (Available=1.0, Partial=0.5, Unavailable=0.0) |
| Certifications | Multi-hot binary vector over controlled certification vocabulary |
| Department | One-hot encoding (used for filtering, not similarity) |
| Location | One-hot encoding (used for filtering, not similarity) |

### 6.4 Controlled Vocabularies

The system requires maintained controlled vocabularies for:
- Skills (e.g., 100–200 standardized skill names)
- Certifications (e.g., 30–50 recognized certifications)
- Role titles and levels
- Departments
- Locations

These vocabularies must be defined in Sprint 1 in collaboration with HR SMEs and stored as configurable reference data.

---

## 7. Algorithm Design

### 7.1 Feature Vector Definition

**Project requirement vector (R):**
```
R = [skill_vector (binary), competency_vector (ordinal), experience (numerical), role_level (ordinal), availability_window (date)]
```

**Talent profile vector (T):**
```
T = [skill_vector (binary), competency_vector (ordinal), experience (numerical), role_level (ordinal), availability_status (categorical)]
```

Both vectors are constructed over the same feature space to enable direct comparison.

### 7.2 Similarity Functions

**Skill Match — Cosine Similarity:**
```
skill_score = cosine_similarity(R.skill_vector, T.skill_vector)
            = (R · T) / (||R|| × ||T||)
```
This captures how well the candidate's skill set overlaps with the requirement, normalized for vector magnitude.

**Competency Match — Weighted Distance:**
```
competency_score = 1 - (Σ max(0, R.competency[i] - T.competency[i]) / (max_level × n_required_skills))
```
Only penalizes where the candidate falls below the required level. Meeting or exceeding the requirement scores full marks for that skill.

**Experience Match — Gaussian Proximity:**
```
midpoint = (experience_min + experience_max) / 2
sigma = (experience_max - experience_min) / 2  (minimum sigma = 2)
experience_score = exp(-0.5 × ((T.experience - midpoint) / sigma)²)
```
Candidates near the midpoint of the desired range score highest. Candidates outside the range score progressively lower.

**Availability Match — Rule-Based:**
```
if T.availability_status == "Available" AND T.availability_date <= R.availability_window.start:
    availability_score = 1.0
elif T.availability_status == "Partially Available":
    availability_score = 0.5
else:
    availability_score = 0.0
```

**Certification Bonus — Additive:**
```
certification_score = |intersection(R.preferred_certs, T.certifications)| / |R.preferred_certs|
```
If no certifications are specified in the requirement, this dimension scores 0 and its weight is redistributed proportionally.

### 7.3 Composite Score & Ranking

```
composite_score = Σ (w_i × score_i) × 100

where:
  w_skills + w_competency + w_experience + w_availability + w_certification = 1.0
```

Candidates are sorted by `composite_score` descending. Ties are broken by data completeness (higher completeness preferred), then by `employee_id` (deterministic tiebreaker).

---

## 8. Evaluation Methodology

### 8.1 Human SME Validation

For each test query:
1. System produces top K candidates
2. HR SMEs independently rate each candidate as "Suitable" or "Not Suitable" for the requirement
3. Results are compared to compute Precision@K

**Validation protocol:**
- Minimum 20 test queries covering diverse project types
- Minimum 3 SMEs per query (majority vote for ground truth)
- SMEs evaluate without seeing system scores (blind review) in at least one round

### 8.2 Precision@K

```
Precision@K = (Number of SME-validated suitable candidates in top K) / K
```

| Metric | Target |
|---|---|
| Precision@3 | ≥ 80% |
| Precision@5 | ≥ 70% |

### 8.3 Ranking Comparison

For queries where the CDWC has made historical staffing decisions:
- Compare the system's top K against the actual selected candidate
- Measure: "Was the actual selected candidate in the system's top K?" (Hit Rate@K)
- Target: Hit Rate@5 ≥ 60%

### 8.4 Backtesting (If Historical Data Exists)

If historical project-to-candidate assignment data is available:
1. Reconstruct project requirements from historical records
2. Run the matching engine against the talent pool as it existed at that time (if snapshots are available)
3. Measure whether the historically selected candidate appears in the system's top K
4. Analyze cases where the system disagrees with historical decisions — these may reveal either system weaknesses or historical suboptimal decisions

### 8.5 Weight Sensitivity Analysis

- Systematically vary weights (±10% per dimension) and measure impact on Precision@K
- Identify which dimensions have the highest leverage on accuracy
- Use findings to guide weight calibration with SMEs

---

## 9. System Architecture (High-Level)

```
┌─────────────────────────────────────────────────────────────────┐
│                        CDWC Agent System                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Chat Interface Layer (NEW)                   │  │
│  │  ┌──────────────┐    ┌──────────────────────────────┐   │  │
│  │  │ Chat UI      │    │ LLM Processing Module        │   │  │
│  │  │ (Streamlit / │───▶│ • NL → structured extraction │   │  │
│  │  │  CLI)        │    │ • Structured → NL formatting │   │  │
│  │  └──────────────┘    └──────────────┬───────────────┘   │  │
│  └─────────────────────────────────────┼────────────────────┘  │
│                                        │ structured JSON        │
│  ┌─────────────────────────────────────▼────────────────────┐  │
│  │              Orchestrator Service (NEW)                   │  │
│  │  • Validates extracted fields against schema              │  │
│  │  • Applies defaults for missing optional fields           │  │
│  │  • Routes request to /recommend API                       │  │
│  │  • Handles errors and fallback prompts                    │  │
│  └─────────────────────────────────────┬────────────────────┘  │
│                                        │ API call               │
│  ┌──────────────┐    ┌─────────────────▼────────────────────┐  │
│  │   UI Layer    │    │           API Layer (REST)            │  │
│  │  (Optional)   │───▶│  POST /recommend                     │  │
│  │  Web Dashboard│    │  POST /match                         │  │
│  └──────────────┘    │  GET  /candidates/{id}               │  │
│                      │  POST /feedback                       │  │
│                      │  GET  /history                         │  │
│                      │  PUT  /config/weights                  │  │
│                      └──────────────┬───────────────────────┘  │
│                                     │                           │
│                      ┌──────────────▼───────────────────────┐  │
│                      │        Core Engine                    │  │
│                      │                                       │  │
│                      │  ┌─────────────┐  ┌───────────────┐  │  │
│                      │  │ Hard Filter  │  │ Feature        │  │  │
│                      │  │ Module       │  │ Encoder        │  │  │
│                      │  └──────┬──────┘  └───────┬───────┘  │  │
│                      │         │                  │          │  │
│                      │         ▼                  ▼          │  │
│                      │  ┌─────────────────────────────────┐ │  │
│                      │  │     Similarity Engine            │ │  │
│                      │  │  (Cosine + Weighted Scoring)     │ │  │
│                      │  └──────────────┬──────────────────┘ │  │
│                      │                 │                     │  │
│                      │                 ▼                     │  │
│                      │  ┌─────────────────────────────────┐ │  │
│                      │  │     Ranking Engine               │ │  │
│                      │  │  (Top K + Score Breakdown)       │ │  │
│                      │  └─────────────────────────────────┘ │  │
│                      └──────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Data Layer                             │  │
│  │                                                           │  │
│  │  ┌────────────┐  ┌─────────────┐  ┌──────────────────┐  │  │
│  │  │ Talent     │  │ Reference   │  │ Request/Feedback │  │  │
│  │  │ Profiles   │  │ Data        │  │ Logs             │  │  │
│  │  │ (CSV/DB)   │  │ (Vocabs,    │  │ (Audit Trail)    │  │  │
│  │  │            │  │  Weights)   │  │                  │  │  │
│  │  └────────────┘  └─────────────┘  └──────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Descriptions

| Component | Responsibility | Technology (Recommended for POC) |
|---|---|---|
| **Chat Interface** | Natural language input/output for CDWC members | Streamlit chat widget or CLI |
| **LLM Processing Module** | Extract structured fields from NL; format engine output to NL | Local LLM or API-based (e.g., OpenAI, Bedrock) with strict system prompt |
| **Orchestrator Service** | Validate, default, and route structured queries to the API | Python |
| **UI Layer** | Simple web form for requirement input and results display (alternative to chat) | React or Streamlit (optional for POC) |
| **API Layer** | RESTful endpoints for all system interactions | Python FastAPI |
| **Hard Filter Module** | Apply boolean exclusion rules before similarity computation | Python (pandas filtering) |
| **Feature Encoder** | Transform raw talent/requirement data into comparable feature vectors | Python (scikit-learn encoders, numpy) |
| **Similarity Engine** | Compute per-dimension similarity scores | Python (scikit-learn cosine_similarity, custom functions) |
| **Ranking Engine** | Aggregate scores, sort, select top K, format output | Python |
| **Data Layer** | Store and retrieve talent profiles, reference data, and audit logs | PostgreSQL or SQLite (POC), CSV for initial data load |

---

## 10. Out of Scope

The following are explicitly excluded from the POC and deferred to future phases:

| Item | Reason for Exclusion |
|---|---|
| **LLM / RAG / Generative AI** | The recommendation engine must be deterministic and hallucination-free. The chat layer uses an LLM strictly for input parsing and output formatting — it does not perform ranking, scoring, or decision logic. No RAG or external knowledge base is used. |
| **LLM-based ranking or autonomous decision-making** | The LLM does not rank candidates, override engine scores, or make staffing decisions. All recommendations originate from the deterministic engine. |
| **Text processing / NLP** | No text data (resumes, descriptions) is available or required. All inputs are numerical or categorical. |
| **Predictive ML models** | No labeled target variable exists. Supervised learning requires historical outcome data that is not available for the POC. |
| **Real-time HRIS integration** | Data will be provided as structured exports (CSV/Excel). Live integration adds complexity without POC value. |
| **Automated decision-making** | All recommendations require human validation. The system does not approve, assign, or notify candidates. |
| **Mobile application** | Not required for committee-based usage during POC. |
| **Multi-language support** | English only for POC. |
| **Performance prediction** | The system matches capabilities, not outcomes. Predicting project success is a separate problem. |

---

## 10.1 API Integration (NEW)

### `/recommend` API Contract

The chat layer and orchestrator interact with the recommendation engine exclusively through the REST API.

**Endpoint:** `POST /recommend`

**Request body:**
```json
{
  "required_skills": ["python", "machine_learning", "sql"],
  "required_competency_level": 4.0,
  "min_experience": 5,
  "role_level": "senior",
  "availability_required": true
}
```

**Response body:**
```json
{
  "total_candidates_evaluated": 20,
  "candidates_after_filtering": 8,
  "top_k": 5,
  "recommendations": [
    {
      "employee_id": "EMP007",
      "name": "Grace Okafor",
      "department": "Engineering",
      "role_level": "senior",
      "skills": ["java", "python", "sql", "machine_learning"],
      "competency_score": 4.2,
      "years_experience": 7,
      "availability": true,
      "score_breakdown": {
        "skill_overlap": 1.0,
        "competency": 0.96,
        "experience": 1.0,
        "role_match": 1.0
      },
      "total_score": 0.99
    }
  ]
}
```

**Error handling:**
- `422 Unprocessable Entity` — invalid or missing required fields
- `500 Internal Server Error` — engine failure (chat layer displays a user-friendly error message)
- The orchestrator retries once on transient failures before surfacing the error to the user

---

## 10.2 Prompt Design (NEW)

### System Prompt for Chat Layer

The LLM used in the chat interface operates under a strict system prompt:

```
You are a talent search assistant for the CDWC recommendation system.

RULES:
1. Your ONLY job is to extract structured search parameters from the user's
   natural language query and format the engine's results into readable responses.
2. You MUST extract these fields: required_skills (required), 
   required_competency_level (default 3.0), min_experience (default 0),
   role_level (default "mid"), availability_required (default true).
3. You MUST NOT rank, score, or evaluate candidates yourself.
4. You MUST NOT fabricate candidate names, skills, scores, or any attributes.
5. You MUST only present data that appears in the API response.
6. If the user's query is ambiguous or missing required information (especially
   skills), ask a clarifying question instead of guessing.
7. When presenting results, include the candidate's name, department, total
   score, and a brief explanation of their score breakdown.
8. Never reference external knowledge, training data, or information outside
   the API response.
```

### Extraction Rules

- Skills must be mapped to the controlled vocabulary (e.g., "ML" → "machine_learning", "JS" → "javascript")
- If the user mentions a competency expectation (e.g., "expert level"), map to the 0–5 scale (expert ≈ 4.5)
- If the user does not specify experience, default to 0 (no minimum)
- If the user does not specify role level, default to "mid"

---

## 11. Risks & Assumptions

### Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Talent data is incomplete or inconsistent across departments | Matching accuracy degrades; some candidates unfairly excluded or ranked | Sprint 1 data audit. Define minimum completeness threshold (e.g., 80% of required fields). Flag incomplete profiles in output rather than silently excluding. |
| Controlled vocabularies don't cover all relevant skills | Candidates with unlisted skills are invisible to the system | Collaborative vocabulary definition with HR SMEs in Sprint 1. Include an "Other" category and review process for vocabulary expansion. |
| Default weights don't reflect actual CDWC priorities | Rankings don't match expert expectations | Weights are configurable. Plan calibration sessions in Sprint 3. Sensitivity analysis identifies high-leverage dimensions. |
| SMEs disagree on candidate suitability during validation | Precision@K measurement is noisy | Use majority vote (3+ SMEs). Track inter-rater agreement. Discuss disagreements to refine evaluation criteria. |
| System performance degrades with large talent pools | Response time exceeds 5-second target | Profile and optimize in Sprint 3. Pre-compute feature vectors. Use efficient similarity libraries (scikit-learn, FAISS if needed). |
| **LLM hallucination in chat layer** | Chat interface displays fabricated candidate attributes, scores, or qualifications not present in the engine's output | Strict system prompt enforces grounded responses. Output validation checks all referenced data against API response. No external knowledge base or RAG. |
| **Query misinterpretation** | Chat layer extracts incorrect skills, experience, or role level from ambiguous user input | Orchestrator validates against schema. Chat asks clarifying questions on low-confidence extractions. User reviews extracted query before execution. Structured form fallback always available. |

### Assumptions

| Assumption | Dependency |
|---|---|
| Structured talent data (skills, competency, experience, availability) is available in exportable format | HR / HRIS team provides data extract |
| A controlled vocabulary of skills and certifications can be defined within Sprint 1 | HR SMEs are available for collaborative definition |
| CDWC members and HR SMEs are available for validation sessions in Sprint 4 | Committee scheduling |
| The talent pool for POC is ≤ 10,000 profiles | Data volume from HR |
| Historical staffing decisions are available for backtesting (nice-to-have, not required) | HR records |
| Python-based technology stack is acceptable for POC | Engineering team alignment |

---

## 12. Sprint Plan

### Sprint 1: Data & Feature Engineering (Weeks 1–2)

| Task | Description | Owner | Deliverable |
|---|---|---|---|
| Data acquisition | Obtain structured talent data export from HR/HRIS | Data Engineer + HR | Raw data files (CSV/Excel) |
| Data audit | Profile data for completeness, consistency, and quality issues | Data Engineer | Data quality report with completeness metrics per field |
| Vocabulary definition | Define controlled vocabularies for skills, certifications, roles, departments | Data Engineer + HR SMEs | Vocabulary reference files |
| Schema definition | Finalize talent profile schema and project requirement schema | Data Engineer + Product | Schema documentation |
| Feature encoding pipeline | Build encoding functions for all feature types (multi-hot, ordinal, numerical, categorical) | Data Engineer | Encoding module with unit tests |
| Data loading | Load and encode talent profiles into the system's data store | Data Engineer | Encoded talent dataset ready for similarity computation |

**Sprint 1 Exit Criteria:** Encoded talent dataset loaded. Data quality report reviewed. Vocabularies approved by HR SMEs.

### Sprint 2: Similarity Engine (Weeks 3–4)

| Task | Description | Owner | Deliverable |
|---|---|---|---|
| Similarity functions | Implement cosine similarity (skills), weighted distance (competency), Gaussian proximity (experience), rule-based (availability), additive (certifications) | ML Engineer | Similarity module with unit tests |
| Hard filter module | Implement pre-computation filters (availability, role, department, data completeness) | ML Engineer | Filter module with unit tests |
| Composite scoring | Implement weighted aggregation with configurable weights | ML Engineer | Scoring module with unit tests |
| Ranking logic | Implement top-K selection with tiebreaking and score breakdown formatting | ML Engineer | Ranking module with unit tests |
| Integration test | End-to-end test: requirement input → filter → similarity → ranking → output | ML Engineer | Passing integration tests with sample data |
| Weight configuration | Implement configurable weight storage and loading | ML Engineer | Configuration module |

**Sprint 2 Exit Criteria:** End-to-end matching pipeline works on sample data. All similarity functions tested. Configurable weights operational.

### Sprint 3: Ranking, API, UI & Chat Interface (Weeks 5–6)

| Task | Description | Owner | Deliverable |
|---|---|---|---|
| API development | Build REST API endpoints: `/recommend`, `/match`, `/candidates/{id}`, `/feedback`, `/history`, `/config/weights` | Backend Engineer | FastAPI application with endpoint documentation |
| Output formatting | Implement JSON response format with full score breakdowns (as specified in Section 4.5) | Backend Engineer | Formatted API responses |
| Audit logging | Implement request/response/feedback logging with timestamps and user IDs | Backend Engineer | Logging module writing to persistent store |
| Basic UI (optional) | Simple web form for requirement input and results display | Frontend Engineer | Streamlit or React dashboard |
| Chat interface — UI scaffold | Build chat UI (Streamlit chat widget or CLI) for natural language input/output | Frontend Engineer | Chat interface connected to orchestrator |
| Chat interface — LLM integration | Integrate LLM for NL → structured extraction and structured → NL formatting | ML Engineer | Working extraction and formatting pipeline |
| Chat interface — orchestrator | Build orchestrator to validate extracted fields, apply defaults, and call `/recommend` API | Backend Engineer | Orchestrator module with schema validation |
| Performance optimization | Profile response time. Optimize for < 5 second target on 10K profiles | ML Engineer | Performance benchmarks |
| Weight calibration session | Workshop with HR SMEs to review default weights and adjust based on sample outputs | Product + HR SMEs | Calibrated weight configuration |

**Sprint 3 Exit Criteria:** API operational and documented. Chat interface functional with NL input → ranked output flow. Response time < 5 seconds. Audit logging active. Weights calibrated with SME input.

### Sprint 4: Evaluation, Chat Refinement & Demo (Weeks 7–8)

| Task | Description | Owner | Deliverable |
|---|---|---|---|
| Test query design | Create 20+ diverse test queries covering different project types, skill combinations, and edge cases | Product + HR SMEs | Test query set |
| SME validation sessions | Run test queries through the system. SMEs independently rate each recommended candidate. | Product + HR SMEs | Validation results dataset |
| Precision@K calculation | Compute Precision@3 and Precision@5 from validation results | Data Engineer | Evaluation metrics report |
| Chat response formatting | Refine LLM response templates for clarity, accuracy, and score presentation | ML Engineer | Polished chat output templates |
| Chat extraction testing | Test NL extraction accuracy across diverse query phrasings; measure extraction precision | ML Engineer | Extraction accuracy report |
| Backtesting (if data available) | Run historical requirements through the system and compare against actual decisions | Data Engineer | Backtesting results report |
| Weight sensitivity analysis | Vary weights ±10% and measure impact on Precision@K | ML Engineer | Sensitivity analysis report |
| Bug fixes & refinement | Address issues found during evaluation | Engineering team | Updated system |
| Leadership demo | Present system capabilities, evaluation results, and roadmap to CDWC and HR leadership | Product + Engineering | Demo presentation, evaluation report, go/no-go recommendation |
| Documentation | Finalize algorithm documentation, API documentation, chat prompt design, and user guide | Product + Engineering | Documentation package |

**Sprint 4 Exit Criteria:** Precision@K targets met (or gap analysis documented). Chat interface tested with diverse queries. Leadership demo completed. Go/no-go recommendation delivered.

---

### Sprint Summary

```
Sprint 1 (Wk 1-2)     Sprint 2 (Wk 3-4)     Sprint 3 (Wk 5-6)     Sprint 4 (Wk 7-8)
──────────────────  →  ──────────────────  →  ──────────────────  →  ──────────────────
Data acquisition       Similarity functions   REST API               Test query design
Data audit             Hard filters           Output formatting      SME validation
Vocabulary definition  Composite scoring      Audit logging          Precision@K calc
Schema definition      Ranking logic          Chat UI scaffold       Chat extraction testing
Feature encoding       Integration tests      LLM integration        Chat response refinement
Data loading           Weight config          Orchestrator           Backtesting
                                              Performance tuning     Sensitivity analysis
                                              Weight calibration     Leadership demo
```

---

**Document Prepared For:** Engineering Team, Product Team, HR Data Team
**Dependencies:** HR data export, SME availability for vocabulary definition and validation sessions
**Next Step:** Sprint 1 kickoff upon leadership approval of Steering Document
