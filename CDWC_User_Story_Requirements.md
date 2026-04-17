# CDWC Agent — User Story Requirements

**Version:** 1.0
**Date:** April 16, 2026
**Derived From:** CDWC Agent PRD v1.1, CDWC Agent Steering Document v1.1
**Status:** Draft for Product & Engineering Review

---

## 1. User Personas

| Persona | Role | Goals | System Interaction |
|---|---|---|---|
| **Aisha (CDWC Committee Member)** | Senior leader on the talent deployment committee | Find the best-fit candidates quickly, understand why they were recommended, make defensible staffing decisions | Submits project requirements (via chat or form), reviews ranked candidates, approves or overrides recommendations |
| **Raj (HR Subject Matter Expert)** | HR professional with deep talent pool knowledge | Validate system accuracy, calibrate scoring weights, maintain data quality, flag gaps | Reviews recommendations, provides suitability feedback, adjusts weights, flags missing candidates |
| **Lena (HR Data Administrator)** | Data steward for talent profiles | Keep talent data complete, accurate, and current | Updates employee profiles, runs data quality reports, manages controlled vocabularies |
| **Marco (Hiring Manager)** | Department lead needing project staff (Phase 3+) | Self-service access to talent recommendations for his projects | Submits requirements, reviews candidates (future phase) |

---

## 2. Epic & User Story Map

```
Epic 1: Requirement Input ──── Epic 2: Matching & Ranking ──── Epic 3: Feedback & Audit
       │                              │                                │
    US-01 Structured input         US-03 Top-K ranking             US-07 Suitability feedback
    US-02 Templates                US-04 Similarity scores         US-08 Missed candidate
    US-16 Bulk requirements        US-05 Score breakdown           US-09 Request history
                                   US-06 Pre-filters               US-19 Export results
                                   US-17 Compare candidates        US-20 Decision recording

Epic 4: Weight Config ──── Epic 5: Chat Interface ──── Epic 6: Data & Admin
       │                          │                           │
    US-10 Adjust weights       US-12 NL query              US-21 Data quality dashboard
    US-11 What-if mode         US-13 Auto-interpret         US-22 Vocabulary management
    US-18 Weight presets       US-14 Extraction review      US-23 Profile completeness
                               US-15 Clarification          US-24 Bulk data import
                               US-25 Conversation history
                               US-26 Fallback to form
```

---

## 3. User Stories — Detailed

### Epic 1: Project Requirement Input

#### US-01: Structured Requirement Submission (P0)
**As** Aisha (CDWC member),
**I want** to input a structured project requirement with skills, competency levels, experience range, role type, and availability window,
**So that** the system can match it against the full talent pool.

| Acceptance Criteria |
|---|
| Form captures all required fields: required_skills, competency_levels, experience_min_years, role_type, availability_window |
| Optional fields available: experience_max_years, department_preference, location_preference |
| Validation rejects incomplete submissions with clear error messages indicating which fields are missing |
| Skills are selected from the controlled vocabulary (autocomplete or dropdown) |
| Submitted requirement is persisted in the audit log with a unique request_id |

**Technical Notes:** Maps to `POST /recommend` API. Pydantic schema validation on the backend.

---

#### US-02: Requirement Templates (P2)
**As** Aisha (CDWC member),
**I want** to save, name, and reuse project requirement templates,
**So that** I don't re-enter common configurations for recurring project types.

| Acceptance Criteria |
|---|
| User can save current requirement as a named template |
| User can load a saved template and edit it before submission |
| User can delete templates they no longer need |
| Templates are stored per-user (or globally for POC) |

---

#### US-16: Bulk Requirement Submission (P2)
**As** Aisha (CDWC member),
**I want** to submit multiple project requirements in a single batch,
**So that** I can get recommendations for several open positions at once during a committee session.

| Acceptance Criteria |
|---|
| Accept a JSON array of requirements via API or file upload |
| Each requirement is processed independently and returns its own ranked list |
| Results are grouped by requirement and returned as a single response |
| Each sub-request gets its own request_id in the audit log |

---

### Epic 2: Candidate Matching & Ranking

#### US-03: Top-K Ranked Candidates (P0)
**As** Aisha (CDWC member),
**I want** to receive a ranked list of the top 3–5 candidates for my project requirement,
**So that** I can make an informed staffing decision with a manageable shortlist.

| Acceptance Criteria |
|---|
| System returns top K candidates ranked by composite similarity score (descending) |
| K is configurable (default 5, range 1–20) |
| Results returned in < 5 seconds for a talent pool of up to 10,000 profiles |
| Response includes total candidates evaluated and total after hard filters |
| Ties are broken deterministically (data completeness, then employee_id) |

---

#### US-04: Similarity Scores (P0)
**As** Aisha (CDWC member),
**I want** to see a similarity score for each recommended candidate,
**So that** I can understand how well they match the requirement at a glance.

| Acceptance Criteria |
|---|
| Each candidate displays a composite score (0–100, normalized) |
| Individual dimension scores are visible (skill match, competency, experience, availability, certification) |
| Scores are consistent — identical inputs always produce identical scores |

---

#### US-05: Explainable Score Breakdown (P0)
**As** Aisha (CDWC member),
**I want** to see a detailed breakdown of each candidate's score,
**So that** I can understand exactly why they were ranked in that position and challenge it if needed.

| Acceptance Criteria |
|---|
| Breakdown shows per-dimension: raw score, weight applied, contribution to composite |
| Hard filter status is visible (passed / flagged) |
| Data completeness indicator is included |
| Breakdown uses human-readable labels (not internal variable names) |

---

#### US-06: Pre-Filters (P1)
**As** Aisha (CDWC member),
**I want** to filter candidates by department, location, or role before running the match,
**So that** I can narrow the search space to relevant candidates.

| Acceptance Criteria |
|---|
| Pre-filters are optional — omitting them searches the full pool |
| Filtered candidates are excluded before similarity computation (not after) |
| Response indicates how many candidates were excluded by each filter |

---

#### US-17: Side-by-Side Candidate Comparison (P2)
**As** Aisha (CDWC member),
**I want** to compare two or more recommended candidates side by side,
**So that** I can see their relative strengths across each scoring dimension.

| Acceptance Criteria |
|---|
| User selects 2–5 candidates from the recommendation list |
| System displays a comparison table: rows = dimensions, columns = candidates |
| Highlights which candidate scores highest per dimension |

---

### Epic 3: Validation, Feedback & Audit

#### US-07: Suitability Feedback (P0)
**As** Raj (HR SME),
**I want** to mark each recommended candidate as "suitable" or "not suitable" for the requirement,
**So that** we can measure system accuracy using Precision@K.

| Acceptance Criteria |
|---|
| Binary feedback (suitable / not suitable) captured per candidate per request |
| Feedback is linked to the original request_id |
| Feedback is persisted and available for Precision@K calculation |
| Optional free-text notes field per candidate |

**Technical Notes:** Maps to `POST /feedback` API.

---

#### US-08: Missed Candidate Reporting (P1)
**As** Raj (HR SME),
**I want** to suggest a candidate the system missed,
**So that** we can identify coverage gaps and improve the matching logic.

| Acceptance Criteria |
|---|
| SME can submit an employee_id that was not in the top-K but should have been |
| Submission includes a reason/note explaining why the candidate is suitable |
| System logs the miss linked to the original request_id |
| Missed candidates are available for gap analysis reporting |

---

#### US-09: Request History (P2)
**As** Aisha (CDWC member),
**I want** to see a history of past recommendation requests and their outcomes,
**So that** I can track decisions over time and reference previous searches.

| Acceptance Criteria |
|---|
| History shows: date, requirement summary, top candidates, SME feedback (if provided), final decision |
| Entries are sorted newest-first with pagination |
| Single-entry lookup by request_id is supported |
| History is searchable by date range and skills |

**Technical Notes:** Maps to `GET /history` and `GET /history/{request_id}` APIs.

---

#### US-19: Export Results (P2)
**As** Aisha (CDWC member),
**I want** to export recommendation results to CSV or PDF,
**So that** I can share them with committee members who don't have system access.

| Acceptance Criteria |
|---|
| Export includes: requirement summary, ranked candidates, scores, breakdowns |
| Supported formats: CSV (data), PDF (formatted report) |
| Export is triggered from the results view or via API |

---

#### US-20: Decision Recording (P2)
**As** Aisha (CDWC member),
**I want** to record which candidate was ultimately selected for the project,
**So that** we have a complete audit trail from recommendation to decision.

| Acceptance Criteria |
|---|
| User can mark one candidate as "selected" per request |
| Selection is linked to the request_id in the audit log |
| Selection data is available for Hit Rate@K backtesting |

---

### Epic 4: Weight Configuration

#### US-10: Adjust Scoring Weights (P1)
**As** Raj (HR SME),
**I want** to adjust the weights assigned to each scoring dimension,
**So that** the system reflects our current priorities (e.g., prioritize skills over experience).

| Acceptance Criteria |
|---|
| Weights are configurable per dimension: skill_match, competency, experience, availability, certification |
| Weights must sum to 1.0 — system rejects invalid configurations with a clear error |
| Changes take effect immediately on the next query |
| Current weights are always visible (GET /config/weights) |
| Default weights are documented and restorable |

**Technical Notes:** Maps to `PUT /config/weights` and `GET /config/weights` APIs.

---

#### US-11: What-If Weight Comparison (P2)
**As** Raj (HR SME),
**I want** to adjust weights and re-run the same requirement to see how rankings change,
**So that** I can calibrate weights effectively before committing them.

| Acceptance Criteria |
|---|
| User selects a past request from history |
| User modifies weights in a sandbox (does not affect production weights) |
| System re-runs the same requirement with new weights |
| Results are displayed side-by-side: original ranking vs. new ranking |
| Differences are highlighted (candidates that moved up/down/in/out of top-K) |

---

#### US-18: Weight Presets (P2)
**As** Raj (HR SME),
**I want** to save and load named weight presets (e.g., "Skills-Heavy", "Experience-Heavy"),
**So that** I can quickly switch between calibration profiles for different project types.

| Acceptance Criteria |
|---|
| User can save current weights as a named preset |
| User can load a preset to apply those weights |
| System ships with 2–3 default presets |
| Presets are stored as reference data (JSON or DB) |

---

### Epic 5: Conversational Interface

#### US-12: Natural Language Query (P1)
**As** Aisha (CDWC member),
**I want** to ask for talent recommendations using natural language,
**So that** I don't need to manually fill structured input fields.

| Acceptance Criteria |
|---|
| Chat interface accepts free-text queries (e.g., "I need a senior Python developer with ML experience, 5+ years") |
| System extracts: required_skills, competency_level, min_experience, role_level, availability |
| Extracted fields are passed to the `/recommend` API |
| Common aliases are mapped to canonical skills (ML → machine_learning, JS → javascript) |
| Works via both Streamlit web chat and CLI |

---

#### US-13: Automatic Interpretation & Results (P1)
**As** Aisha (CDWC member),
**I want** the system to interpret my query and return ranked candidates in a single conversational step,
**So that** I get results without navigating multiple screens.

| Acceptance Criteria |
|---|
| System returns top-K candidates with a natural language summary |
| Response includes candidate names, departments, scores, and score breakdowns |
| All data originates from the recommendation engine — no hallucinated attributes |
| Response is formatted for readability (not raw JSON) |

---

#### US-14: Extraction Transparency (P1)
**As** Aisha (CDWC member),
**I want** to review the structured query the chatbot extracted from my input,
**So that** I can verify it understood my intent correctly before results are generated.

| Acceptance Criteria |
|---|
| Before calling the API, the chat displays: "Understood: skills=[...], competency≥X, experience≥Y yrs, role=Z, available=yes/any" |
| User can confirm, edit the extracted fields, or re-phrase their query |
| If user edits, the corrected fields are used for the API call |

---

#### US-15: Clarification on Ambiguity (P2)
**As** Aisha (CDWC member),
**I want** the chatbot to ask clarifying questions when my query is ambiguous,
**So that** the system doesn't make incorrect assumptions about what I need.

| Acceptance Criteria |
|---|
| If required fields (especially skills) cannot be confidently extracted, the chat prompts for clarification |
| System never fabricates or assumes values for required fields |
| Clarification questions are specific (e.g., "What skills are you looking for?" not "Can you be more specific?") |

---

#### US-25: Conversation History (P2)
**As** Aisha (CDWC member),
**I want** to see my past chat conversations and their results,
**So that** I can reference previous searches without re-typing queries.

| Acceptance Criteria |
|---|
| Chat session history is preserved within the current session |
| User can scroll back to see previous queries and results |
| Past queries can be re-run with a single click/command |

---

#### US-26: Fallback to Structured Form (P1)
**As** Aisha (CDWC member),
**I want** to switch from chat to a structured form when the chatbot can't understand my request,
**So that** I always have a reliable way to submit requirements.

| Acceptance Criteria |
|---|
| A "Switch to form" option is always visible in the chat interface |
| If the chat fails to extract fields after 2 attempts, it proactively suggests the form |
| Form pre-fills any fields the chat did successfully extract |

---

### Epic 6: Data Management & Administration

#### US-21: Data Quality Dashboard (P1)
**As** Lena (HR Data Admin),
**I want** to see a dashboard showing talent data completeness and quality metrics,
**So that** I can identify and fix data gaps before they affect recommendations.

| Acceptance Criteria |
|---|
| Dashboard shows: total profiles, % with all required fields, % by completeness tier (>90%, 70–90%, <70%) |
| Drill-down to see which fields are most commonly missing |
| Filterable by department |

---

#### US-22: Vocabulary Management (P1)
**As** Lena (HR Data Admin),
**I want** to add, edit, or deprecate entries in the controlled skill and certification vocabularies,
**So that** the system stays current as the organization's skill landscape evolves.

| Acceptance Criteria |
|---|
| Admin can add new skills/certifications to the vocabulary |
| Admin can mark entries as deprecated (hidden from new inputs but preserved in historical data) |
| Changes take effect on the next recommendation query |
| Vocabulary changes are logged in the audit trail |

---

#### US-23: Profile Completeness Alerts (P2)
**As** Lena (HR Data Admin),
**I want** to receive alerts when employee profiles fall below the minimum completeness threshold,
**So that** I can proactively update them before they're excluded from recommendations.

| Acceptance Criteria |
|---|
| System flags profiles below 80% completeness |
| Alert includes: employee_id, name, department, list of missing fields |
| Alerts are available via dashboard or periodic report |

---

#### US-24: Bulk Data Import (P1)
**As** Lena (HR Data Admin),
**I want** to import updated talent data from CSV/Excel exports,
**So that** the system reflects the latest HR data without manual entry.

| Acceptance Criteria |
|---|
| Accept CSV or Excel file matching the talent profile schema |
| Validate all rows against schema; report errors per row |
| New profiles are added; existing profiles are updated (matched by employee_id) |
| Import summary: X added, Y updated, Z errors |
| Import is logged in the audit trail |

---

## 4. Priority Summary

| Priority | Stories | Description |
|---|---|---|
| **P0** | US-01, US-03, US-04, US-05, US-07 | Core pipeline: input → match → rank → explain → feedback. Must work for POC to be viable. |
| **P1** | US-06, US-08, US-10, US-12, US-13, US-14, US-21, US-22, US-24, US-26 | Key usability: pre-filters, chat interface, weight config, data management. Required for a usable POC. |
| **P2** | US-02, US-09, US-11, US-15, US-16, US-17, US-18, US-19, US-20, US-23, US-25 | Nice-to-have: templates, what-if, export, comparison, conversation history. Deferred if time-constrained. |

---

## 5. Sprint Mapping

| Sprint | Stories |
|---|---|
| **Sprint 1** (Data & Feature Engineering) | US-24 (bulk import), US-21 (data quality), US-22 (vocabulary mgmt) |
| **Sprint 2** (Similarity Engine) | US-03 (ranking), US-04 (scores), US-05 (breakdown), US-01 (structured input) |
| **Sprint 3** (API, UI & Chat) | US-06 (filters), US-07 (feedback), US-10 (weights), US-12 (NL query), US-13 (auto-interpret), US-14 (extraction review), US-26 (fallback form) |
| **Sprint 4** (Evaluation & Demo) | US-08 (missed candidate), US-09 (history), US-11 (what-if), US-15 (clarification), US-20 (decision recording) |

---

## 6. Dependency Map

```
US-24 (Bulk Import) ──→ US-21 (Data Quality) ──→ US-22 (Vocabulary)
                                                        │
US-01 (Structured Input) ──→ US-03 (Ranking) ──→ US-04 (Scores) ──→ US-05 (Breakdown)
                                    │
                                    ├──→ US-06 (Pre-filters)
                                    ├──→ US-07 (Feedback) ──→ US-08 (Missed Candidate)
                                    ├──→ US-09 (History) ──→ US-20 (Decision Recording)
                                    └──→ US-10 (Weights) ──→ US-11 (What-if) ──→ US-18 (Presets)
                                    
US-12 (NL Query) ──→ US-14 (Extraction Review) ──→ US-13 (Auto-interpret)
                                                        │
                                                        ├──→ US-15 (Clarification)
                                                        ├──→ US-25 (Conversation History)
                                                        └──→ US-26 (Fallback to Form)

US-03 (Ranking) ──→ US-17 (Compare Candidates)
US-03 (Ranking) ──→ US-19 (Export Results)
US-01 (Structured Input) ──→ US-02 (Templates) ──→ US-16 (Bulk Requirements)
```

---

**Document Prepared For:** Product Team, Engineering Team, HR Stakeholders
**Source Documents:** CDWC Agent PRD v1.1, CDWC Agent Steering Document v1.1
