# CDWC Agent — Microservices Architecture Overview

**Version:** 1.0
**Date:** April 16, 2026
**Status:** Architecture Proposal (does not modify existing documents)
**Context:** Describes how the current monolith would decompose into microservices

---

## 1. Current Monolith vs. Proposed Microservices

### What changes

| Aspect | Monolith (Current) | Microservices (Proposed) |
|---|---|---|
| Deployment | Single Python process | 6 independently deployable services |
| Communication | Direct function calls (`recommend()`, `load_employees()`) | HTTP/REST between services, async events via message broker |
| Data storage | Shared in-memory config + local JSON files | Each service owns its own database/store |
| Scaling | Scale the entire app | Scale individual services independently (e.g., scale recommendation engine without scaling chat) |
| Weight config | In-memory dict, lost on restart | Dedicated config service with persistent storage |
| Chat layer | Imports orchestrator and recommender directly | Separate service, calls recommendation service over HTTP |
| Audit logging | Appended to local JSON file | Dedicated audit service consuming events from all services |
| Failure isolation | One crash kills everything | Chat can be down while recommendations still work via API |
| Deployment complexity | `python app/main.py` | Container orchestration (Docker Compose / Kubernetes) |
| Development speed | Fast for small team | Slower initially, faster at scale with multiple teams |

### What stays the same

- The recommendation engine logic (filter → score → rank) is identical
- The API contract (`POST /recommend` request/response shape) is unchanged
- Determinism, explainability, and human-in-the-loop principles are preserved
- The chat layer remains strictly an input parser and output formatter
- All scoring decisions still originate from the recommendation engine only

---

## 2. Service Decomposition

The monolith's internal layers map to 6 services:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                        API Gateway / Load Balancer                       │
│                        (nginx / AWS ALB / Kong)                         │
│                                                                         │
└────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────────┘
     │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│  Chat   ││ Recom-  ││ Config  ││ Audit   ││ Data    ││Feedback │
│ Service ││ menda-  ││ Service ││ Service ││ Service ││ Service │
│         ││ tion    ││         ││         ││         ││         │
│ :8001   ││ Service ││ :8003   ││ :8004   ││ :8005   ││ :8006   │
│         ││ :8002   ││         ││         ││         ││         │
└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘└────┬────┘
     │          │          │          │          │          │
     │          │          │          │          │          │
     ▼          ▼          ▼          ▼          ▼          ▼
┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
│ (none)  ││ (none)  ││PostgreSQL││PostgreSQL││PostgreSQL││PostgreSQL│
│ state-  ││ state-  ││ config  ││  audit  ││ talent  ││ feedback│
│ less    ││ less    ││  store  ││   logs  ││profiles ││  store  │
└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

---

## 3. Service Definitions

### Service 1: Chat Service (port 8001)
**Responsibility:** Natural language interface — parse user queries, format engine responses.

| Aspect | Detail |
|---|---|
| Owns | Chat UI (Streamlit/CLI), LLM integration, NL parser, response formatter |
| Calls | Recommendation Service (HTTP), Config Service (to fetch skill vocabulary for alias mapping) |
| Database | None (stateless). Session history stored client-side or in Redis for ephemeral chat state |
| Endpoints | `POST /chat` (accepts NL query, returns formatted response) |
| Scaling | Scale independently when chat traffic is high; doesn't affect engine |
| Failure mode | If chat is down, users can still call Recommendation Service directly via API or form UI |

**Monolith equivalent:** `chat/orchestrator.py` + `chat/parser.py` + `chat/formatter.py`

---

### Service 2: Recommendation Service (port 8002)
**Responsibility:** The core engine — hard filtering, feature engineering, similarity scoring, ranking.

| Aspect | Detail |
|---|---|
| Owns | Hard filter module, feature encoder, similarity engine, ranking engine |
| Calls | Data Service (HTTP, to fetch talent profiles), Config Service (HTTP, to fetch current weights) |
| Database | None (stateless compute). All data fetched per-request from Data Service |
| Endpoints | `POST /recommend` (accepts structured requirement JSON, returns ranked candidates) |
| Scaling | Horizontally scalable — each instance is stateless. Scale up during committee sessions |
| Failure mode | If down, both chat and direct API users get errors. This is the critical path |

**Monolith equivalent:** `app/recommender.py` + `app/features.py`

**Key difference from monolith:** Instead of `from app.data_loader import load_employees` (direct import), this service calls `GET http://data-service:8005/employees` over HTTP. Instead of reading `config.WEIGHTS` from shared memory, it calls `GET http://config-service:8003/weights`.

---

### Service 3: Config Service (port 8003)
**Responsibility:** Manage scoring weights, K value, controlled vocabularies, and system settings.

| Aspect | Detail |
|---|---|
| Owns | Weight configurations, controlled vocabularies (skills, certifications, roles), weight presets |
| Calls | Nothing (leaf service) |
| Database | PostgreSQL — `config_store` (weights, vocabularies, presets, settings) |
| Endpoints | `GET /weights`, `PUT /weights`, `GET /vocabularies/{type}`, `PUT /vocabularies/{type}`, `GET /presets`, `POST /presets` |
| Scaling | Low traffic — single instance is fine |
| Failure mode | If down, Recommendation Service uses last-known cached weights. Chat Service can't validate skill aliases |

**Monolith equivalent:** `app/config.py` (in-memory dict)

**Key difference from monolith:** Weights survive restarts. Multiple instances of the Recommendation Service all read the same weights. Vocabulary changes are centralized.

---

### Service 4: Audit Service (port 8004)
**Responsibility:** Record every request, response, feedback action, and system event for compliance and evaluation.

| Aspect | Detail |
|---|---|
| Owns | Audit log storage, history queries |
| Calls | Nothing (receives events) |
| Database | PostgreSQL — `audit_logs` (request_id, timestamp, user_id, request_payload, response_payload, event_type) |
| Endpoints | `POST /log` (record an event), `GET /history` (paginated query), `GET /history/{request_id}` |
| Ingestion | Synchronous HTTP from other services, or async via message broker (preferred) |
| Scaling | Write-heavy — may need write replicas at scale |
| Failure mode | If down, other services continue operating but audit trail has gaps. Use message queue to buffer events |

**Monolith equivalent:** `app/history.py` (local JSON file)

**Key difference from monolith:** Centralized, persistent, queryable audit trail. All services emit events to one place. Supports compliance requirements at scale.

---

### Service 5: Data Service (port 8005)
**Responsibility:** Manage talent profiles — CRUD operations, data quality metrics, bulk import.

| Aspect | Detail |
|---|---|
| Owns | Talent profile storage, data quality computation, bulk import pipeline |
| Calls | Audit Service (to log data changes) |
| Database | PostgreSQL — `talent_profiles` (full schema from PRD §6.1) |
| Endpoints | `GET /employees` (all, with filters), `GET /employees/{id}`, `POST /employees` (create), `PUT /employees/{id}` (update), `POST /import` (bulk CSV/Excel), `GET /quality` (data completeness metrics) |
| Scaling | Read-heavy — add read replicas if needed |
| Failure mode | If down, Recommendation Service cannot function. Critical dependency |

**Monolith equivalent:** `app/data_loader.py` + `data/employees.json`

**Key difference from monolith:** Real database instead of a JSON file. Supports CRUD, bulk import, and data quality reporting. Single source of truth for all services.

---

### Service 6: Feedback Service (port 8006)
**Responsibility:** Capture SME feedback, missed candidate reports, and final decisions.

| Aspect | Detail |
|---|---|
| Owns | Feedback storage, Precision@K computation, gap analysis |
| Calls | Audit Service (to log feedback events) |
| Database | PostgreSQL — `feedback` (request_id, employee_id, suitable, notes, submitted_by, timestamp) |
| Endpoints | `POST /feedback` (suitability rating), `POST /missed` (missed candidate report), `POST /decision` (final selection), `GET /metrics` (Precision@K, Hit Rate@K) |
| Scaling | Low traffic — single instance |
| Failure mode | If down, recommendations still work. Feedback collection is delayed |

**Monolith equivalent:** Not yet implemented (specified in PRD §3 US-07, US-08, US-20)

---

## 4. Inter-Service Communication

### Synchronous (HTTP/REST)

These calls are on the critical path — the user is waiting for a response:

```
Chat Service ──POST /recommend──→ Recommendation Service
Recommendation Service ──GET /employees──→ Data Service
Recommendation Service ──GET /weights──→ Config Service
```

### Asynchronous (Message Broker — RabbitMQ or AWS SQS)

These are fire-and-forget events — no user is waiting:

```
Recommendation Service ──"recommendation.completed"──→ Audit Service
Chat Service ──"chat.query.processed"──→ Audit Service
Feedback Service ──"feedback.submitted"──→ Audit Service
Data Service ──"profile.updated"──→ Audit Service
Config Service ──"weights.changed"──→ Audit Service
```

### Request Flow: Chat Query (end-to-end)

```
User
 │
 ▼
API Gateway ──→ Chat Service (8001)
                    │
                    ├─ Parse NL → structured JSON
                    │
                    ├─ GET /vocabularies/skills ──→ Config Service (8003)
                    │                                    │
                    │                              (validate aliases)
                    │
                    ├─ POST /recommend ──→ Recommendation Service (8002)
                    │                          │
                    │                          ├─ GET /employees ──→ Data Service (8005)
                    │                          ├─ GET /weights ──→ Config Service (8003)
                    │                          │
                    │                          ├─ Filter → Score → Rank
                    │                          │
                    │                          ├─ emit "recommendation.completed" ──→ Audit (8004)
                    │                          │
                    │                          └─ Return ranked candidates
                    │
                    ├─ Format response (structured → NL)
                    │
                    ├─ emit "chat.query.processed" ──→ Audit (8004)
                    │
                    └─ Return formatted response
                         │
                         ▼
                       User
```

---

## 5. Data Ownership (Database-per-Service)

| Service | Database | Tables | Shared? |
|---|---|---|---|
| Config Service | `config_db` | weights, vocabularies, presets, settings | No — other services read via API |
| Audit Service | `audit_db` | audit_logs | No — write-only from other services |
| Data Service | `talent_db` | talent_profiles | No — other services read via API |
| Feedback Service | `feedback_db` | feedback, missed_candidates, decisions | No — other services read via API |
| Chat Service | (none) | — | Stateless |
| Recommendation Service | (none) | — | Stateless (compute only) |

No shared databases. Each service owns its data and exposes it through APIs. This is the core microservices principle that enables independent deployment and scaling.

---

## 6. Deployment Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Docker Compose / Kubernetes            │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ chat     │ │ recommend│ │ config   │ │ audit    │   │
│  │ :8001    │ │ :8002    │ │ :8003    │ │ :8004    │   │
│  │ 1 replica│ │ 3 replica│ │ 1 replica│ │ 1 replica│   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│                                                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│  │ data     │ │ feedback │ │ message  │                │
│  │ :8005    │ │ :8006    │ │ broker   │                │
│  │ 1 replica│ │ 1 replica│ │ (rabbit) │                │
│  └──────────┘ └──────────┘ └──────────┘                │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              PostgreSQL (4 databases)             │   │
│  │  config_db │ audit_db │ talent_db │ feedback_db  │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │              API Gateway (nginx / Kong)            │   │
│  │  /chat → :8001    /recommend → :8002              │   │
│  │  /config → :8003  /history → :8004                │   │
│  │  /employees → :8005  /feedback → :8006            │   │
│  └──────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
```

---

## 7. Key Trade-offs: Monolith vs. Microservices

| Dimension | Monolith wins | Microservices wins |
|---|---|---|
| **Time to first deploy** | ✅ `pip install && python main.py` | ❌ Need Docker, orchestration, service discovery |
| **Debugging** | ✅ Single process, single stack trace | ❌ Distributed tracing needed (Jaeger/Zipkin) |
| **Team size 1–3** | ✅ Less overhead, faster iteration | ❌ Overhead not justified |
| **Team size 5+** | ❌ Merge conflicts, coupled releases | ✅ Independent teams, independent deploys |
| **Scaling** | ❌ Scale everything or nothing | ✅ Scale recommendation engine independently during peak |
| **Fault isolation** | ❌ One bug crashes everything | ✅ Chat down ≠ recommendations down |
| **Data consistency** | ✅ Single DB, ACID transactions | ❌ Eventual consistency, distributed transactions |
| **Operational cost** | ✅ One server, one process | ❌ 6 services + DB + broker + gateway |
| **Latency** | ✅ In-process function calls (~μs) | ❌ Network hops add ~5–20ms per call |
| **Evolution** | ❌ Harder to replace components | ✅ Swap recommendation engine without touching chat |

---

## 8. Recommendation

For the current POC with a small team, the monolith is the right choice. The microservices architecture becomes justified when:

- Multiple teams need to deploy independently
- The recommendation engine needs to scale separately from the chat layer (e.g., 10x more API traffic than chat traffic)
- Fault isolation is critical (chat outage shouldn't block direct API users)
- The talent pool grows beyond 10K profiles and the data layer needs its own scaling strategy

The monolith's internal layering (chat → orchestrator → engine → data) already mirrors the microservices boundaries, making the migration path straightforward when the time comes.

---

**Document Prepared For:** Engineering Team, Architecture Review
**Source Documents:** CDWC Agent PRD v1.1, CDWC Agent Steering Document v1.1
**Note:** This document is a proposal only. No existing documents were modified.
