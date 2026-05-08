# CDWC Diagnostic Engine — High-Level Architecture

Two views: the engine in context (who calls it, what data it reads, what
it returns) and the engine internals (five-score pipeline with two
parallel analyses). Authoritative source: `.kiro/specs/recommendation-engine-redesign/design.md`.

## Context view

```mermaid
flowchart TB
    classDef inScope fill:#D1FAE5,stroke:#059669,color:#111827
    classDef outScope fill:#FEE2E2,stroke:#DC2626,color:#111827,stroke-dasharray:5 3
    classDef data fill:#DBEAFE,stroke:#2563EB,color:#111827
    classDef caller fill:#F3E8FF,stroke:#7C3AED,color:#111827
    classDef response fill:#1E293B,stroke:#1E293B,color:#FFFFFF
    classDef config fill:#FEF9C3,stroke:#CA8A04,color:#111827

    HOD["HOD / GM<br/><i>asks a team-diagnostic<br/>question</i>"]:::caller

    subgraph FUTURE["FUTURE LAYERS (out of scope)"]
        UI["Chat UI / Dashboard"]:::outScope
        CONV["Conversation Layer<br/><i>NL parser + narrative<br/>formatter</i>"]:::outScope
        API["API Layer<br/><i>FastAPI endpoints</i>"]:::outScope
        ACT["Action Triage Layer<br/><i>training · exposure · hiring</i>"]:::outScope
    end

    subgraph ENGINE_BOX["CDWC DIAGNOSTIC ENGINE (app/engine/)"]
        ENGINE["engine.run(query, config)<br/><i>pure function · deterministic ·<br/>JSON-only output</i>"]:::inScope
    end

    subgraph DATA["Data Layer"]
        HRIS[("DUMMY_SMA_HRIS_sample.json<br/><i>9,455 rows</i>")]:::data
        TPCP[("DUMMY_TPCP_Assessment_sample.json<br/><i>1,018 rows</i>")]:::data
    end

    CFG[/"EngineConfig<br/><i>weights, thresholds, bands</i>"/]:::config

    RESP["Engine_Response<br/><i>JSON document</i><br/>scope · join_summary ·<br/>team_aggregate ·<br/>individual_drill_down ·<br/>employee_health"]:::response

    HOD --> UI
    UI --> CONV
    CONV --> API
    API -->|"query:<br/>business, opu,<br/>division"| ENGINE
    CFG --> ENGINE
    HRIS --> ENGINE
    TPCP --> ENGINE
    ENGINE --> RESP
    RESP --> CONV
    RESP -.->|"future consumer"| ACT
```

## Container view

```mermaid
flowchart LR
    classDef ingest fill:#CCFBF1,stroke:#0D9488,color:#111827
    classDef transform fill:#FEE2E2,stroke:#DC2626,color:#111827
    classDef score fill:#DBEAFE,stroke:#2563EB,color:#111827
    classDef analyze fill:#FEF9C3,stroke:#CA8A04,color:#111827
    classDef assemble fill:#D1FAE5,stroke:#059669,color:#111827
    classDef io fill:#1E293B,stroke:#1E293B,color:#FFFFFF

    IN_HRIS[("HRIS<br/>JSON")]:::io
    IN_TPCP[("TPCP<br/>JSON")]:::io
    IN_Q[/"query<br/>business/opu/division"/]:::io
    IN_CFG[/"EngineConfig"/]:::io

    subgraph STAGE1["① Load & Join"]
        L1["load_hris()"]:::ingest
        L2["load_tpcp()"]:::ingest
        JN["join_records()<br/><i>full outer join<br/>on dummy_id</i>"]:::ingest
    end

    subgraph STAGE2["② Scope"]
        SC["apply_scope()<br/><i>mandatory<br/>business/opu/division</i>"]:::transform
    end

    subgraph STAGE3["③ Per-Person Scoring (5 scores)"]
        SR["score_all()"]:::score
        S1["tpcp_health<br/><i>0.6·cti_met +<br/>0.4·avg(rollups)<br/>+ 0.1·passed</i>"]:::score
        S2["cbs_health<br/><i>0.5·tech + 0.3·overall<br/>+ 0.2·leadership</i>"]:::score
        S3["combined_competency<br/><i>0.55·tpcp +<br/>0.45·cbs</i>"]:::score
        S4["grade_fit<br/><i>grade ↔ level<br/>alignment</i>"]:::score
        S5["tenure_readiness<br/><i>year_in_sg /<br/>grade_threshold</i>"]:::score
        SR --> S1 & S2 & S3 & S4 & S5
    end

    subgraph STAGE4["④ Analysis (2 parallel)"]
        AG["team_aggregate()<br/><i>pass_rate,<br/>level_distribution,<br/>avg scores,<br/>weakest_dimension</i>"]:::analyze
        DD["individual_drill_down()<br/><i>low_performers,<br/>promotable,<br/>close_in_6m,<br/>not_assessed</i>"]:::analyze
    end

    AS["assemble_response()<br/><i>+ JSON-native validation</i>"]:::assemble
    OUT[(Engine_Response JSON)]:::io

    IN_HRIS --> L1 --> JN
    IN_TPCP --> L2 --> JN
    IN_Q --> SC
    IN_CFG -.-> SR
    IN_CFG -.-> AG
    IN_CFG -.-> DD
    JN --> SC --> SR --> AG & DD
    AG --> AS
    DD --> AS
    SR --> AS
    SC --> AS
    JN --> AS
    AS --> OUT
```

## Scope boundary

| In scope (this engine) | Out of scope (other layers or deferred) |
|---|---|
| HRIS + TPCP ingestion | Free-text chat parsing, intent extraction |
| Full outer join on `dummy_id` | Any persistence layer (no DB, no cache) |
| Mandatory org-scope filtering | Authentication, authorisation, multi-tenant |
| 5 health scores per employee | `critical_gap_score` (dropped with per-cell fields) |
| Team aggregate rollup | Gap matrix / structural-vs-people classification |
| Individual drill-down (4 lists) | Action recommendations (training / exposure / hiring) |
| Structured JSON response | Natural-language narrative, dashboards, reports |
| Deterministic, config-driven formulas | Learned models, A/B testing, feature stores |
