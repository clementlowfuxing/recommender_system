# CDWC Agent — Steering Document

## Proof of Concept: Capability Development Working Committee Decision-Support System

**Version:** 1.1
**Date:** April 16, 2026
**Status:** Draft for Leadership Review
**Classification:** Internal — Confidential

---

## 1. Executive Summary

The Capability Development Working Committee (CDWC) currently relies on manual, experience-driven processes to identify and assign internal talent to projects. This approach is time-consuming, inconsistent, and difficult to audit. It creates bottlenecks in project staffing and limits the organization's ability to deploy the right people to the right work at the right time.

This document proposes a Proof of Concept (POC) for the **CDWC Agent** — a deterministic, similarity-based decision-support system that recommends and ranks internal candidates for project deployment using structured HR data. The core engine is transparent, explainable, and fully deterministic — designed to augment, not replace, human decision-making.

To improve usability, the system includes a **Conversational Interface Layer** — a chat-based front end that allows CDWC members to express project requirements in natural language. This chat layer translates user queries into structured inputs for the recommendation engine and formats the engine's structured outputs into human-readable responses. The chatbot does not perform ranking, scoring, or any decision logic — it serves strictly as an input parser and output formatter. All recommendations originate from the deterministic engine.

The POC targets a 4-sprint delivery cycle, after which the CDWC committee and HR SMEs will evaluate the system's accuracy, speed, and trustworthiness against current manual processes.

**Key outcomes of the POC:**
- Ranked candidate recommendations (top 3–5) for any structured project requirement
- Explainable similarity scores with per-dimension breakdowns
- Natural language access to talent search via conversational interface
- Measurable reduction in time-to-decision for talent deployment
- A foundation for future ML/AI evolution without current AI risk exposure

---

## 2. Problem Statement

The CDWC faces several systemic challenges in its current talent deployment process:

| Pain Point | Impact |
|---|---|
| **Manual candidate identification** | Committee members rely on personal knowledge and ad-hoc spreadsheet reviews to identify candidates. This is slow (days to weeks) and biased toward recently visible employees. |
| **Inconsistent evaluation criteria** | Different committee members weigh skills, experience, and availability differently. There is no standardized scoring framework, leading to inconsistent outcomes across sessions. |
| **Limited visibility into the talent pool** | No single view exists that maps employee capabilities against project requirements. Qualified candidates are routinely overlooked because their profiles are not top-of-mind. |
| **No audit trail** | Decisions are made in meetings with minimal documentation of why a particular candidate was selected or rejected. This creates compliance and fairness risks. |
| **Bottleneck at committee level** | The CDWC meets periodically. Urgent staffing needs wait for the next session, delaying project timelines. |
| **Underutilization of HR data** | The organization maintains structured HR data (skills inventories, competency ratings, tenure, certifications, availability status) that is not systematically leveraged for staffing decisions. |

These problems compound as the organization scales. Without a structured approach, talent deployment becomes a constraint on delivery capacity rather than an enabler.

---

## 3. Vision & Objective

### Vision

Transform the CDWC from a manual, opinion-driven staffing committee into a data-informed, transparent, and auditable talent deployment function — starting with a deterministic decision-support tool and evolving toward intelligent workforce optimization.

### Objectives for the POC

1. **Demonstrate feasibility** of similarity-based talent matching using existing structured HR data
2. **Deliver a working prototype** that accepts a structured project requirement and returns a ranked list of 3–5 candidates with explainable scores
3. **Validate accuracy** through SME review, measuring whether the system's recommendations align with expert judgment
4. **Establish trust** by proving the system is deterministic, auditable, and free from hallucination or opaque AI behavior
5. **Define the path forward** from rule-based matching to supervised/unsupervised ML enhancements

---

## 4. Scope of POC

### In Scope

- Ingestion and processing of structured talent data (skills, competency levels, experience years, certifications, role, department, availability status)
- Ingestion of structured project requirements (required skills, competency thresholds, experience range, role type, timeline)
- Feature encoding pipeline for categorical and numerical talent/project attributes
- Similarity computation engine (cosine similarity with configurable weighted scoring)
- Ranking engine that produces top K candidates with per-dimension score breakdowns
- Simple API layer for programmatic access
- Basic UI or dashboard for CDWC members to input requirements and view results (optional, stretch goal)
- Evaluation framework: SME validation sessions, Precision@K measurement
- Documentation of algorithm logic, feature weights, and decision rationale

### Out of Scope

- Natural language processing or text analysis of any kind
- Large Language Models (LLMs), Retrieval-Augmented Generation (RAG), or generative AI
- Predictive modeling (e.g., predicting project success or attrition)
- Integration with external HR systems (HRIS, ATS) — data will be provided as structured exports
- Automated decision-making — all recommendations require human validation
- Mobile application
- Multi-tenant or cross-organization deployment
- Real-time data synchronization

---

## 5. Key Design Principles

### 5.1 Deterministic — No Hallucination

The system produces identical outputs for identical inputs, every time. There are no probabilistic language models, no generated text, and no stochastic components. Every recommendation is traceable to specific data points and scoring rules.

**Why this matters:** Leadership and HR must trust that the system does not fabricate qualifications, invent scores, or produce inconsistent results. Determinism is the foundation of that trust.

### 5.2 Explainable

Every candidate recommendation includes a full breakdown of how the similarity score was computed — which dimensions contributed, what the individual scores were, and how weights were applied. A CDWC member can look at any recommendation and understand exactly why that candidate was ranked where they were.

**Why this matters:** Unexplainable systems cannot be audited, challenged, or improved. Explainability enables meaningful human oversight and continuous refinement of the matching logic.

### 5.3 Human-in-the-Loop

The system recommends. Humans decide. The CDWC Agent is a decision-support tool, not a decision-making tool. Every output is presented to committee members or HR SMEs for validation, override, or rejection. Feedback from these reviews feeds back into weight calibration and evaluation metrics.

**Why this matters:** Talent deployment decisions have career and organizational impact. Removing humans from the loop is neither appropriate nor desirable at this stage. The system's role is to make human decisions faster, more consistent, and better informed.

---

## 6. Solution Overview

### 6.1 Similarity-Based Talent Matching Engine

The core of the CDWC Agent is a matching engine that computes the similarity between a **project requirement vector** and each **talent profile vector** in the database. This engine is the sole source of all ranking and scoring decisions.

**How it works:**

1. **Project requirement** is encoded as a structured feature vector (required skills as binary/ordinal, competency thresholds as numerical, experience range, role type, availability window)
2. **Each talent profile** is encoded as a comparable feature vector using the same schema
3. **Similarity is computed** using a weighted combination of cosine similarity (for multi-dimensional skill vectors) and rule-based scoring (for hard constraints like availability and role match)
4. **Candidates are ranked** by composite score, and the top K are returned with full score breakdowns
5. **Hard filters** (e.g., unavailable candidates, wrong department) are applied before similarity computation to reduce noise

### 6.2 Conversational Interface Layer (NEW)

To reduce friction and improve usability for CDWC members, the system includes a **Chat Interface** that sits in front of the recommendation engine. This layer allows users to express project needs in natural language instead of filling structured forms.

**Architecture flow:**

```
User (natural language query)
  → Chat Interface (LLM / parser)
    → Structured query extraction (skills, experience, role, etc.)
      → Recommendation API (/recommend)
        → Structured results (top candidates + scores)
          → LLM formats response (natural language summary)
            → User sees answer
```

**Critical design boundaries:**

- The chat layer is ONLY an **input parser** (natural language → structured JSON) and a **response formatter** (structured JSON → natural language)
- The chat layer MUST NOT perform ranking, infer new facts, override scoring logic, or fabricate candidate attributes
- All recommendations are produced exclusively by the deterministic engine
- The LLM's responses are grounded entirely in the API's structured output — no external knowledge, no hallucinated data

**Example interaction:**

> **User:** "I need a senior Python developer with ML experience, at least 5 years, available now"
>
> **Chat Layer extracts:** `{ required_skills: ["python", "machine_learning"], required_competency_level: 4.0, min_experience: 5, role_level: "senior", availability_required: true }`
>
> **Engine returns:** Top 5 ranked candidates with score breakdowns
>
> **Chat Layer formats:** "Here are the top 3 matches for your request. Grace Okafor scored 0.99 — she matches all 3 required skills, has 7 years of experience, and is available. Her strongest dimension is skill overlap at 100%..."

```
┌─────────────────────┐     ┌──────────────────────┐
│  Project Requirement │     │   Talent Profiles     │
│  (Structured Input)  │     │   (Structured Data)   │
└────────┬────────────┘     └──────────┬───────────┘
         │                             │
         ▼                             ▼
┌─────────────────────┐     ┌──────────────────────┐
│  Feature Encoding    │     │  Feature Encoding     │
└────────┬────────────┘     └──────────┬───────────┘
         │                             │
         └──────────┬──────────────────┘
                    ▼
         ┌─────────────────────┐
         │  Hard Filter Layer   │
         │  (Availability, Role)│
         └────────┬────────────┘
                  ▼
         ┌─────────────────────┐
         │  Similarity Engine   │
         │  (Cosine + Weighted) │
         └────────┬────────────┘
                  ▼
         ┌─────────────────────┐
         │  Ranking Engine      │
         │  (Top K + Breakdown) │
         └────────┬────────────┘
                  ▼
         ┌─────────────────────┐
         │  CDWC / HR SME       │
         │  (Human Validation)  │
         └─────────────────────┘
```

---

## 7. Value Proposition

| Value Area | Current State | With CDWC Agent |
|---|---|---|
| **Speed of decision** | Days to weeks per staffing request | Minutes per request (system response < 5 seconds, human review adds deliberation time) |
| **Consistency** | Varies by committee composition and session | Standardized scoring framework applied uniformly to every request |
| **Transparency** | Decisions are opaque, rationale is verbal | Every recommendation has a documented, auditable score breakdown |
| **Coverage of talent pool** | Limited to committee members' awareness | Entire structured talent database is evaluated for every request |
| **Fairness** | Recency bias, visibility bias, affinity bias | Systematic evaluation reduces (does not eliminate) individual bias |
| **Auditability** | No structured record of decision rationale | Full log of inputs, scores, rankings, and human decisions |
| **Ease of access** | Requires knowledge of system fields and structured forms | Natural language queries via chat interface — ask in plain English, get ranked candidates |
| **Reduced friction** | Manual form-filling for every query | Conversational UX extracts requirements automatically from user intent |
| **Faster decision-making** | Multiple steps between need identification and candidate review | Single conversational flow from question to ranked answer |
| **Foundation for evolution** | No data infrastructure for talent analytics | Establishes data pipelines, feature schemas, and evaluation frameworks that enable future ML capabilities |

---

## 8. Architecture Overview (Layered)

The system is organized into four distinct layers, each with clear responsibilities and boundaries:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CDWC Agent — Layered Architecture           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Layer 1: Chat Interface (LLM)                            │  │
│  │  • Accepts natural language queries from users            │  │
│  │  • Extracts structured fields (skills, experience, etc.)  │  │
│  │  • Formats engine output into conversational responses    │  │
│  │  • DOES NOT rank, score, or infer new facts               │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │ structured JSON                    │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │  Layer 2: Orchestrator Layer                              │  │
│  │  • Validates extracted fields against schema              │  │
│  │  • Applies defaults for optional fields                   │  │
│  │  • Routes structured request to /recommend API            │  │
│  │  • Handles errors and fallback prompts                    │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │ API call                           │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │  Layer 3: Recommendation Engine (Existing Core)           │  │
│  │  • Hard filtering (availability, role eligibility)        │  │
│  │  • Feature engineering (skill overlap, competency, etc.)  │  │
│  │  • Weighted scoring with configurable weights             │  │
│  │  • Top-K ranking with full score breakdowns               │  │
│  │  • Deterministic — sole source of all recommendations     │  │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │ reads from                         │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │  Layer 4: Data Layer                                      │  │
│  │  • Talent profiles (employees.json / DB)                  │  │
│  │  • Reference data (vocabularies, weights)                 │  │
│  │  • Request/feedback audit logs                            │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Key architectural constraint:** Data flows downward (chat → orchestrator → engine → data), but all recommendation decisions flow upward exclusively from the engine. The chat layer never bypasses the engine.

---

## 9. Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Data quality issues** — Incomplete, outdated, or inconsistent talent profiles | High | High | Conduct data audit in Sprint 1. Define minimum data completeness thresholds. Flag profiles with missing data in output. Establish data hygiene process with HR. |
| **Algorithmic bias** — Systematic over- or under-representation of certain groups due to historical data patterns | Medium | High | Audit feature weights for proxy discrimination. Ensure protected attributes are not used as features. Conduct fairness review of top-K outputs with HR SMEs. Document bias mitigation approach. |
| **Incomplete profiles** — Key employees missing from the dataset or having sparse data | High | Medium | Report coverage metrics. Allow CDWC members to flag missing candidates. Treat incomplete profiles as a data quality issue, not a system failure. |
| **Stakeholder resistance** — Committee members distrust or resist system recommendations | Medium | Medium | Position as decision-support, not decision-making. Involve CDWC members in weight calibration. Demonstrate explainability early. Run parallel evaluation (system vs. manual) to build confidence. |
| **Overfitting to current weights** — Initial weight configuration may not generalize across project types | Medium | Low | Design weights to be configurable. Plan calibration sessions with SMEs. Track Precision@K across different project categories. |
| **Scope creep** — Pressure to add NLP, predictive features, or integrations during POC | Medium | Medium | Enforce scope boundaries defined in Section 4. Defer enhancements to post-POC roadmap. Maintain a backlog of future capabilities. |
| **LLM hallucination in chat layer** — Chat interface fabricates candidate attributes, scores, or qualifications not present in the engine's output | Medium | High | Chat layer is strictly grounded in API response data. System prompt enforces "only use data from the API response" rule. No external knowledge base or RAG. Output validation checks that all referenced employee IDs and scores exist in the engine response. |
| **Query misinterpretation** — Chat layer incorrectly extracts skills, experience, or role level from ambiguous natural language input | Medium | Medium | Orchestrator validates extracted fields against controlled vocabularies and schema constraints. Chat layer asks clarifying questions when extraction confidence is low. Users can review the extracted structured query before execution. Fallback to structured form input is always available. |

---

## 10. Success Metrics

| Metric | Definition | Target for POC |
|---|---|---|
| **Precision@K (SME-validated)** | Of the top K candidates recommended, what proportion do SMEs agree are suitable? | ≥ 70% agreement at K=5 |
| **Time-to-shortlist** | Time from project requirement submission to ranked candidate list | < 5 seconds (system) + human review time |
| **Talent pool coverage** | Percentage of eligible employees evaluated per request | 100% of profiles meeting hard filters |
| **Explainability satisfaction** | CDWC members rate the score breakdowns as understandable and useful (survey) | ≥ 4/5 average rating |
| **Consistency score** | Same input produces same output across runs | 100% (deterministic requirement) |
| **Data completeness** | Percentage of talent profiles with all required fields populated | Baseline measured in Sprint 1, improvement tracked |
| **Stakeholder trust** | CDWC members willing to use the system as a regular input to their process (survey) | ≥ 60% of committee members |

---

## 11. Roadmap

### Phase 1: POC (Current — 4 Sprints)

- Structured data ingestion and feature engineering
- Similarity-based matching engine with weighted scoring
- Ranking with explainable breakdowns
- API layer and optional basic UI
- SME validation and Precision@K evaluation
- Leadership demo and go/no-go decision

### Phase 2: Pilot (Post-POC, if approved)

- Integration with HRIS for automated data refresh
- Expanded feature set (project history, performance ratings, learning completions)
- Weight optimization through SME feedback loops
- Role-based access control and audit logging
- Deployment to a subset of CDWC use cases for live evaluation

### Phase 3: Scale & Evolve

- Supervised learning models trained on validated CDWC decisions (labeled data from Phase 2)
- Clustering for talent segmentation and bench strength analysis
- Demand forecasting integration (predict upcoming skill needs)
- Multi-criteria optimization (balance individual fit with team composition)
- Self-service portal for hiring managers (beyond CDWC)

### Phase 4: Intelligent Workforce Platform

- Graph-based skill ontology and career pathing
- Recommendation engine for learning and development
- Scenario modeling (what-if analysis for workforce planning)
- Continuous learning from deployment outcomes

```
Phase 1 (POC)          Phase 2 (Pilot)        Phase 3 (Scale)        Phase 4 (Platform)
─────────────────── → ─────────────────── → ─────────────────── → ───────────────────
Rule-based matching    HRIS integration       Supervised ML          Skill ontology
Cosine similarity      Weight optimization    Clustering             Career pathing
Explainable scores     RBAC + audit logs      Demand forecasting     Scenario modeling
SME validation         Live pilot             Team optimization      Continuous learning
```

---

**Document Prepared For:** CDWC Leadership, HR Leadership, Technology Leadership
**Next Step:** Leadership review and approval to proceed with POC Sprint 1
