# Rule-Based Heuristic Approach for the CDWC Talent Recommendation Engine

## 1. Overview

The CDWC Talent Recommendation Engine is a **rule-based heuristic system** that matches employees to project requirements using deterministic scoring algorithms. It does not use machine learning model training, gradient descent, or learned parameters. All decision logic is hand-crafted by domain experts and encoded as mathematical formulas and conditional rules.

This document explains the technical rationale behind the rule-based approach, how it compares to machine learning alternatives, and how it is evaluated for POC sign-off.

---

## 2. What Is a Rule-Based Heuristic System?

A **heuristic** is a practical shortcut or rule of thumb that produces a "good enough" answer without guaranteeing the mathematically optimal one. It trades optimality for speed, simplicity, and interpretability.

A **rule-based system** encodes human domain knowledge as explicit if-then rules and mathematical formulas. The logic is written by developers and domain experts, not learned from data.

Key characteristics:
- **No learned parameters** — every threshold, weight, and formula is hand-defined
- **No training step** — there is no `.fit()`, no gradient descent, no optimization loop
- **No labeled data required** — the system operates purely on its coded logic
- **Fully deterministic** — same input always produces the same output

---

## 3. Is It Still AI?

Yes. Rule-based systems are the **original form of artificial intelligence**, dating back to the 1950s–1980s (the Expert Systems era). AI is defined by the capability — performing tasks that require human intelligence — not by the internal mechanism.

```
Artificial Intelligence
├── Symbolic AI (rule-based, knowledge-driven)
│   ├── Expert systems
│   ├── Heuristic search
│   └── CDWC Recommendation Engine  ← this system
│
└── Statistical AI (data-driven, learned)
    ├── Machine Learning (supervised, unsupervised, reinforcement)
    └── Deep Learning (CNNs, Transformers, LLMs)
```

All machine learning is AI, but not all AI is machine learning. This system is AI without being ML.

---

## 4. Data Inputs for Feature Engineering

The system ingests two categories of data fields:

### From the Candidate (Employee Data)
| Field | Type | Description |
|-------|------|-------------|
| `skills` | list of strings | e.g., `["python", "sql", "docker"]` |
| `competency_score` | float (0–5) | Overall competency rating |
| `years_experience` | int | Total years of professional experience |
| `role_level` | string | One of: junior, mid, senior, lead, principal |
| `availability` | boolean | Whether the employee is currently available |

### From the Project Requirement (Query)
| Field | Type | Description |
|-------|------|-------------|
| `required_skills` | list of strings | Skills the project needs |
| `required_competency_level` | float (0–5) | Minimum competency expected |
| `min_experience` | int | Minimum years of experience |
| `role_level` | string | Required seniority level |
| `availability_required` | boolean | Whether availability is mandatory |

---

## 5. How the Recommendation Pipeline Works

The engine follows a three-stage pipeline:

### Stage 1: Hard Filtering
Removes candidates who fail mandatory constraints:
- If availability is required and the candidate is unavailable → **rejected**
- If the candidate's role level is below the required level → **rejected**

### Stage 2: Feature Scoring (Heuristic Functions)
Four scoring functions compute 0.0–1.0 similarity scores:

| Function | Formula | What It Measures |
|----------|---------|------------------|
| `skill_overlap_score` | Jaccard-style: \|intersection\| / \|required\| | How many required skills the candidate has |
| `competency_similarity` | 1 − (\|candidate − required\| / 5.0) | How close the competency score is to the requirement |
| `experience_similarity` | Linear ratio if below requirement, 1.0 if meets/exceeds | Whether experience meets the minimum |
| `role_match_score` | 1.0 (exact), 0.5 (overqualified), 0.0 (underqualified) | Seniority alignment |

Each of these is a **heuristic** — a reasonable approximation based on domain knowledge, not a mathematically proven optimal formula.

### Stage 3: Weighted Aggregation and Ranking
Feature scores are combined using configurable weights:

```
Total Score = 0.35 × skill_overlap
            + 0.25 × competency
            + 0.20 × experience
            + 0.20 × role_match
```

Candidates are ranked by total score descending, and the top-K (default 5) are returned.

---

## 6. Why Rule-Based Over Machine Learning?

The decision to use a rule-based approach is driven by practical constraints:

| Factor | Rule-Based | Machine Learning |
|--------|-----------|-----------------|
| Labeled data required? | No | Yes (typically thousands of examples) |
| Training infrastructure? | None | Requires training pipeline, compute |
| Explainability | Full — every score can be traced to a formula | Varies — tree models are interpretable, neural nets are not |
| Time to build | Fast — encode domain knowledge directly | Slower — data collection, labeling, training, tuning |
| Maintenance | Update rules as business logic changes | Retrain on new data, monitor for drift |

**When labeled data is not available, rule-based is the recommended approach.** It serves as both a working system and a baseline for future ML if labeled data becomes available later.

---

## 7. Path to Machine Learning (If Labels Become Available)

If labeled outcome data becomes available in the future, the system can evolve:

### Target Variable Options

**Option A — Binary Classification (`match_success`)**
- Label: 1 if the employee was a good fit, 0 if not
- Source: manager ratings, project outcomes, reassignment history
- Algorithm: Gradient Boosted Trees (XGBoost/LightGBM), Logistic Regression

**Option B — Relevance Score (0–5)**
- Label: graded score indicating degree of match quality
- Source: expert panel scoring, composite formula from multiple outcome signals
- Algorithm: Gradient Boosted Regression, Learning to Rank (LambdaMART)

### Hybrid Approach (Recommended)
Keep the existing rule-based features as engineered input signals, and use ML to learn optimal weights for combining them — replacing the hand-tuned 0.35/0.25/0.20/0.20 weights with data-driven ones.

### Labeling Strategies
- **Expert panel scoring** — domain experts rate historical assignments (most reliable, most expensive)
- **Composite formula** — combine measurable signals (manager rating, on-time delivery, retention) into a score (most scalable)
- **Pairwise comparison** — "who was the better fit?" between two candidates (better quality labels, but O(n²) cost)

---

## 8. Evaluating the Rule-Based System for POC Sign-Off

Evaluation is required even without ML. The system's heuristics are hypotheses that must be validated.

### Evaluation Methods Implemented

The system includes a full evaluation pipeline (`evaluation/`) with the following:

#### 8.1 Ground Truth Generation
Since no labeled data exists, ground truth is constructed synthetically:
- **Rule-based oracle** — deterministic "ideal" relevance labels using stricter thresholds (≥50% skill overlap, competency within 1.0, experience met, role level met)
- **Simulated expert panel** — oracle labels with configurable noise (10% flip rate), majority-vote across 3 simulated experts

#### 8.2 Metrics Computed

| Metric | What It Measures | Formula |
|--------|-----------------|---------|
| Precision@K | Of the top K recommendations, how many are relevant? | \|relevant in top K\| / K |
| Recall@K | Of all relevant candidates, how many appear in top K? | \|relevant in top K\| / \|all relevant\| |
| NDCG@K | Are relevant candidates ranked higher? (position-aware) | DCG@K / IDCG@K |
| Diversity | Are recommendations from varied departments? | \|unique departments\| / K |
| Fairness | Does department representation reflect the eligible pool? | 1 − (1/D) × Σ\|deviation\| |
| Ranking Stability | Do rankings hold under small weight perturbations? | Average Kendall's τ across perturbations |

#### 8.3 Stability Testing
Weights are perturbed by ±5% across 10 iterations. Kendall's Tau measures how much the ranking changes. High stability (τ close to 1.0) means the system is robust and not overly sensitive to exact weight values.

### POC Sign-Off Criteria (Recommended)

```
Quantitative:
  ☐ Precision@5 ≥ 70% on expert-reviewed scenarios (minimum 25 scenarios)
  ☐ Hit Rate@5 ≥ 60% on historical assignment data (if available)
  ☐ System outperforms random baseline by ≥ 2x on Precision@5
  ☐ Ranking Stability (Kendall's τ) ≥ 0.8

Qualitative:
  ☐ Domain experts agree rankings "make sense" for ≥ 80% of test cases
  ☐ Passes all edge case scenarios without nonsensical results
  ☐ Response time < 2 seconds for recommendation generation

Operational:
  ☐ System handles full employee dataset without errors
  ☐ Results are fully reproducible (deterministic)
```

---

## 9. Summary

| Aspect | This System |
|--------|-------------|
| AI category | Symbolic AI / Rule-based heuristic system |
| Machine learning? | No — no training, no learned parameters |
| Deterministic? | Yes — same input always produces same output |
| Labeled data required? | No (for operation); optional (for evaluation) |
| Evaluation approach | Expert judgment + synthetic ground truth + stability testing |
| Future ML path | Keep features, add ML for weight optimization when labels are available |

The rule-based approach is the pragmatic and appropriate choice for this use case given the absence of labeled data. It delivers an interpretable, auditable, and deterministic recommendation system that can be rigorously evaluated and serves as a strong foundation for future ML enhancement.
