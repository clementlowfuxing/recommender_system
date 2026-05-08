# Requirements Document

## Introduction

This feature redesigns the CDWC recommendation engine from a project-matching
system into a **team talent-diagnostic engine**. The existing engine
(`app/recommender.py`, `app/features.py`) assumes fields that do not exist in
the real data (`skills` lists, `years_experience`, `role_level`,
`availability`) and cannot answer the questions HODs and GMs actually ask
("How healthy is my team?", "Who is promotable?", "Which competency gaps are
structural vs people-driven?", "What actions should we take next?").

The redesigned engine consumes two sample data sources
(`data/DUMMY_SMA_HRIS_sample.json` and `data/DUMMY_TPCP_Assessment_sample.json`)
joined on `dummy_id`, applies an org-scope filter, computes six per-person
health scores, runs three parallel analyses (team rollup, competency gap matrix,
individual drill-down), and emits a rule-based action triage. The engine layer
never formats prose — it always emits structured JSON that the conversation
layer converts into narrative.

This spec covers the **engine layer only** (ingestion, scoring, analysis,
insight, JSON contract). The conversation layer, API endpoint wiring, and UI
are out of scope and tracked separately.

Architectural decisions captured in
`presentation_ppt/CDWC_Redesign_Proposal.pptx` and
`presentation_ppt/CDWC_Architecture_Scoring_Flow.pptx` are treated as fixed
inputs and translated into acceptance criteria below.

## Glossary

- **Engine**: The redesigned talent diagnostic engine module.
- **HRIS_Loader**: Component that ingests `DUMMY_SMA_HRIS_sample.json`.
- **TPCP_Loader**: Component that ingests `DUMMY_TPCP_Assessment_sample.json`.
- **Joiner**: Component that left-joins HRIS and TPCP records on `dummy_id`
  into a Unified_Employee_Record.
- **Unified_Employee_Record**: A single employee record that carries identity,
  org hierarchy, HRIS CBS fields, TPCP rolled-up fields, and TPCP competency
  cells after the join.
- **Scope_Filter**: Component that restricts the employee pool by
  `business`, `opu`, and `division` values supplied in the query.
- **Scorer**: Component that computes six 0–1 health scores per employee.
- **TPCP_Health**: Score derived from `cti_met_pct`, `base_pct`, `key_pct`,
  `pacing_pct`, `emerging_pct`, and `passed_tpcp`.
- **CBS_Health**: Score derived from `technical_cbs_pct`, `overall_cbs_pct`,
  and `leadership_cbs_pct`.
- **Combined_Competency**: Weighted blend of TPCP_Health and CBS_Health.
- **Grade_Fit**: Score measuring alignment of `job_grade` with
  `assessment_level`.
- **Tenure_Readiness**: Score derived from `year_in_sg` and a grade-based
  tenure threshold.
- **Critical_Gap_Score**: 1 minus the fraction of TPCP competency cells that
  scored ≤ 1, across the four blocks B, K, P, E.
- **Competency_Cell**: A single TPCP assessment cell in the Base (b1..b25),
  Key (k1..k15), Pacing (p1..p10), or Emerging (e1..e10) block.
- **Team_Aggregate**: Rollup statistics across a scoped employee pool (pass
  rate, level distribution, averages, not-assessed count).
- **Gap_Matrix**: Per-competency-cell failure-rate analysis classifying each
  cell as Structural, Mixed, or People.
- **Individual_Drill_Down**: Per-employee flagging (low performer, promotable,
  personal gap list).
- **Insight_Engine**: Rule-based triage layer producing training, exposure,
  and hiring action recommendations.
- **Engine_Response**: The JSON document emitted by the Engine for a single
  query. It is the complete output contract.

## Requirements

### Requirement 1: Ingest HRIS Sample Data

**User Story:** As the Engine, I want to ingest the HRIS sample file, so that
I can use CBS scores, grade, tenure, and org identifiers for every employee.

#### Acceptance Criteria

1. WHEN the Engine starts a query, THE HRIS_Loader SHALL read
   `data/DUMMY_SMA_HRIS_sample.json` and return a list of records keyed by
   `dummy_id`.
2. THE HRIS_Loader SHALL preserve the following fields per record when
   present: `dummy_id`, `employee_name`, `superior_name`, `skill_group`,
   `job_grade`, `salary_grade`, `year_in_sg`, `sma_completion_status`,
   `overall_cbs_pct`, `technical_cbs_pct`, `leadership_cbs_pct`.
3. IF a CBS percentage field (`overall_cbs_pct`, `technical_cbs_pct`, or
   `leadership_cbs_pct`) is absent from a record, THEN THE HRIS_Loader SHALL
   mark that dimension as missing rather than substituting zero.
4. IF `dummy_id` is missing or not an integer for a record, THEN THE
   HRIS_Loader SHALL skip that record and record it in a load-error list.
5. IF the HRIS sample file cannot be read or parsed as JSON, THEN THE
   HRIS_Loader SHALL raise a descriptive data-load error that names the file
   and the underlying cause.

### Requirement 2: Ingest TPCP Assessment Sample Data

**User Story:** As the Engine, I want to ingest the TPCP sample file, so that
I can use assessment roll-ups, per-cell scores, and org hierarchy for every
assessed employee.

#### Acceptance Criteria

1. WHEN the Engine starts a query, THE TPCP_Loader SHALL read
   `data/DUMMY_TPCP_Assessment_sample.json` and return a list of records keyed
   by `dummy_id`.
2. THE TPCP_Loader SHALL preserve the following fields per record when
   present: `dummy_id`, `employee_name`, `business`, `opu`, `division`,
   `skill_group`, `discipline`, `sub_discipline`, `assessment_level`,
   `assessment_type`, `qualified_level`, `passed_tpcp`, `base_pct`, `key_pct`,
   `pacing_pct`, `emerging_pct`, `cti_met_pct`.
3. THE TPCP_Loader SHALL preserve every field whose key matches the regex
   `^[bkpe]\d+$` (first competency block) and `^[bkpe]\d+\d+$` (second
   competency block) as numeric `Competency_Cell` values.
4. WHERE the same `dummy_id` appears more than once in the TPCP sample, THE
   TPCP_Loader SHALL retain the record with the most recent
   `assessment_date` and mark the older records as superseded.
5. IF `dummy_id` is missing or not an integer for a record, THEN THE
   TPCP_Loader SHALL skip that record and record it in a load-error list.
6. IF the TPCP sample file cannot be read or parsed as JSON, THEN THE
   TPCP_Loader SHALL raise a descriptive data-load error that names the file
   and the underlying cause.

### Requirement 3: Join HRIS and TPCP Records

**User Story:** As the Engine, I want HRIS and TPCP records joined into a
single employee record, so that scoring can use fields from both sources.

#### Acceptance Criteria

1. THE Joiner SHALL perform a full outer join of HRIS and TPCP records on
   `dummy_id` and emit one Unified_Employee_Record per unique `dummy_id`.
2. WHERE an employee has both HRIS and TPCP records, THE Joiner SHALL set
   `has_hris = true` and `has_tpcp = true` on the Unified_Employee_Record.
3. WHERE an employee has only an HRIS record, THE Joiner SHALL set
   `has_hris = true`, `has_tpcp = false`, and leave all TPCP-sourced fields
   unset on the Unified_Employee_Record.
4. WHERE an employee has only a TPCP record, THE Joiner SHALL set
   `has_hris = false`, `has_tpcp = true`, and leave all HRIS-sourced fields
   unset on the Unified_Employee_Record.
5. IF the same field name exists in both sources (e.g., `employee_name`,
   `skill_group`), THEN THE Joiner SHALL prefer the HRIS value and record the
   TPCP value under a `tpcp_` prefix for audit.
6. THE Joiner SHALL produce a join-summary object reporting the count of
   both-sources, HRIS-only, and TPCP-only Unified_Employee_Records.

### Requirement 4: Apply Org Scope Filter

**User Story:** As an HOD, I want the Engine to restrict results to my team,
so that every downstream analysis is computed over my scope.

#### Acceptance Criteria

1. THE Scope_Filter SHALL accept a query containing `business`, `opu`, and
   `division` values.
2. WHEN all three scope values are supplied, THE Scope_Filter SHALL retain
   only Unified_Employee_Records whose TPCP-sourced `business`, `opu`, and
   `division` values match the query exactly.
3. WHERE a scope value is omitted from the query, THE Scope_Filter SHALL
   treat that dimension as unconstrained.
4. IF a Unified_Employee_Record has no TPCP-sourced org fields (HRIS-only
   case), THEN THE Scope_Filter SHALL exclude that record from scope-bound
   analyses and include it only in an `hris_only_unscoped` bucket.
5. THE Scope_Filter SHALL emit a scoped-pool object reporting the scope
   values used, the count of records retained, and the count of records
   excluded.

### Requirement 5: Compute TPCP Health Score Per Employee

**User Story:** As the Engine, I want to score each employee's TPCP
performance on a 0–1 scale, so that downstream analysis can rank and flag
employees on assessment health.

#### Acceptance Criteria

1. THE Scorer SHALL compute `tpcp_health` for every Unified_Employee_Record
   where `has_tpcp = true`.
2. THE Scorer SHALL compute `tpcp_health` as
   `0.6 × cti_met_pct + 0.4 × mean(base_pct, key_pct, pacing_pct, emerging_pct)`,
   plus `0.1` when `passed_tpcp = "Y"`, capped at `1.0`.
3. WHERE any of `base_pct`, `key_pct`, `pacing_pct`, `emerging_pct` is
   missing, THE Scorer SHALL compute the mean over the non-missing values
   only.
4. IF `has_tpcp = false` for an employee, THEN THE Scorer SHALL set
   `tpcp_health = 0` and mark `tpcp_health_source = "no_tpcp_record"`.

### Requirement 6: Compute CBS Health Score Per Employee

**User Story:** As the Engine, I want to score each employee's CBS
performance on a 0–1 scale, so that HRIS signal is reflected even when no
TPCP record exists.

#### Acceptance Criteria

1. THE Scorer SHALL compute `cbs_health` for every Unified_Employee_Record
   where `has_hris = true`.
2. WHEN all three CBS fields are present, THE Scorer SHALL compute
   `cbs_health = 0.5 × technical_cbs_pct + 0.3 × overall_cbs_pct + 0.2 × leadership_cbs_pct`.
3. WHERE one or more CBS dimensions are missing, THE Scorer SHALL
   rebalance the remaining weights to sum to 1.0 and compute `cbs_health`
   over the present dimensions.
4. IF `has_hris = false` for an employee, THEN THE Scorer SHALL set
   `cbs_health = 0` and mark `cbs_health_source = "no_hris_record"`.

### Requirement 7: Compute Combined Competency Score Per Employee

**User Story:** As the Engine, I want a single combined score per employee,
so that ranking and promotability rules can operate on one primary metric.

#### Acceptance Criteria

1. THE Scorer SHALL compute `combined_competency` for every
   Unified_Employee_Record.
2. WHEN both `tpcp_health > 0` and `cbs_health > 0`, THE Scorer SHALL
   compute `combined_competency = 0.55 × tpcp_health + 0.45 × cbs_health`.
3. WHERE `tpcp_health = 0` and `cbs_health > 0`, THE Scorer SHALL set
   `combined_competency = cbs_health`.
4. WHERE `cbs_health = 0` and `tpcp_health > 0`, THE Scorer SHALL set
   `combined_competency = tpcp_health`.
5. IF both `tpcp_health = 0` and `cbs_health = 0`, THEN THE Scorer SHALL set
   `combined_competency = 0` and mark `combined_competency_source = "no_signal"`.

### Requirement 8: Compute Grade Fit Score Per Employee

**User Story:** As the Engine, I want to measure alignment between job grade
and assessment level, so that the team dashboard can flag grade-level
misalignment.

#### Acceptance Criteria

1. THE Scorer SHALL map `job_grade` to an expected assessment level using
   the following bands: `P1..P3 → "Staff"`, `P4..P6 → "Principal"`,
   `P7..P12 → "Custodian"`.
2. WHEN the expected level equals the actual `assessment_level`, THE Scorer
   SHALL set `grade_fit = 1.0`.
3. WHEN the actual `assessment_level` is higher than the expected level
   (e.g., grade maps to Staff but `assessment_level = "Principal"`), THE
   Scorer SHALL set `grade_fit = 0.5`.
4. WHEN the actual `assessment_level` is lower than the expected level,
   THE Scorer SHALL set `grade_fit = 0.0`.
5. IF `job_grade` or `assessment_level` is missing for an employee, THEN
   THE Scorer SHALL set `grade_fit = null` and mark
   `grade_fit_source = "missing_input"`.

### Requirement 9: Compute Tenure Readiness Score Per Employee

**User Story:** As the Engine, I want a tenure-based readiness score, so
that promotability logic can require minimum time-in-grade.

#### Acceptance Criteria

1. THE Scorer SHALL map `job_grade` to a tenure threshold using:
   `P1..P3 → 3`, `P4..P6 → 4`, `P7..P12 → 5` years.
2. THE Scorer SHALL compute
   `tenure_readiness = min(year_in_sg / grade_tenure_threshold, 1.0)`.
3. IF `year_in_sg` or `job_grade` is missing, THEN THE Scorer SHALL set
   `tenure_readiness = null` and mark
   `tenure_readiness_source = "missing_input"`.

### Requirement 10: Compute Critical Gap Score Per Employee

**User Story:** As the Engine, I want a per-employee competency gap score,
so that individuals with many weak cells can be flagged.

#### Acceptance Criteria

1. THE Scorer SHALL enumerate all Competency_Cell values across the B, K, P,
   and E blocks present on the Unified_Employee_Record.
2. THE Scorer SHALL count `gap_count` as the number of Competency_Cell
   values that are less than or equal to `1`.
3. THE Scorer SHALL compute `critical_gap_score = 1 - (gap_count / total_cells)`
   where `total_cells` is the count of present Competency_Cell values.
4. THE Scorer SHALL emit `weakest_cells` as the list of cell names whose
   value is less than or equal to `1`, ordered by cell name.
5. IF `has_tpcp = false` for an employee, THEN THE Scorer SHALL set
   `critical_gap_score = null`, `gap_count = null`, and
   `weakest_cells = []`.

### Requirement 11: Produce Per-Employee Health Vector

**User Story:** As the Engine, I want a single structured per-employee
result, so that downstream analysis consumes a consistent contract.

#### Acceptance Criteria

1. THE Scorer SHALL emit one `employee_health` object per scoped
   Unified_Employee_Record containing `dummy_id`, `employee_name`,
   `job_grade`, `assessment_level`, `passed_tpcp`, `tpcp_health`,
   `cbs_health`, `combined_competency`, `grade_fit`, `tenure_readiness`,
   `critical_gap_score`, `gap_count`, and `weakest_cells`.
2. THE Scorer SHALL include source/flag fields (`tpcp_health_source`,
   `cbs_health_source`, `combined_competency_source`, `grade_fit_source`,
   `tenure_readiness_source`) whenever a score was computed with missing
   inputs or fallback logic.
3. THE Scorer SHALL emit the per-employee results in a deterministic order
   keyed by `dummy_id` ascending.

### Requirement 12: Produce Team Aggregate Rollup

**User Story:** As an HOD, I want headline team statistics, so that I can see
overall health for my scope at a glance.

#### Acceptance Criteria

1. THE Team_Aggregate SHALL report `team_size` equal to the count of scoped
   Unified_Employee_Records.
2. THE Team_Aggregate SHALL report `assessed_count` equal to the count of
   records with `has_tpcp = true` in the scoped pool.
3. THE Team_Aggregate SHALL report `not_assessed_count` equal to
   `team_size - assessed_count`.
4. THE Team_Aggregate SHALL report `pass_rate` equal to the fraction of
   assessed records with `passed_tpcp = "Y"`, rounded to four decimals.
5. THE Team_Aggregate SHALL report `level_distribution` as a map from each
   value of `qualified_level` (`"Staff"`, `"Principal"`, `"Custodian"`,
   `"Not TP"`) to its count in the assessed pool.
6. THE Team_Aggregate SHALL report `avg_combined_competency`,
   `avg_tpcp_health`, and `avg_cbs_health` as means over the scoped pool,
   excluding null values and rounded to four decimals.
7. THE Team_Aggregate SHALL report `weakest_dimension` as the TPCP dimension
   (`"base"`, `"key"`, `"pacing"`, or `"emerging"`) with the lowest mean
   percentage across the assessed pool.
8. WHERE the scoped pool is empty, THE Team_Aggregate SHALL emit
   `team_size = 0` and leave average/distribution fields null rather than
   raising an error.

### Requirement 13: Produce Competency Gap Matrix

**User Story:** As an HOD, I want each competency cell classified by team
failure rate, so that I can distinguish structural gaps from individual
performance issues.

#### Acceptance Criteria

1. THE Gap_Matrix SHALL compute, for each Competency_Cell observed in the
   scoped pool, a `fail_rate` equal to the count of assessed records where
   the cell value is less than or equal to `1` divided by the count of
   assessed records with that cell present.
2. WHEN `fail_rate ≥ 0.60`, THE Gap_Matrix SHALL classify the cell as
   `"structural"`.
3. WHEN `fail_rate < 0.60` and `fail_rate ≥ 0.20`, THE Gap_Matrix SHALL
   classify the cell as `"mixed"`.
4. WHEN `fail_rate < 0.20`, THE Gap_Matrix SHALL classify the cell as
   `"people"`.
5. THE Gap_Matrix SHALL emit a list of cell entries each containing `cell`,
   `block` (`"base"`, `"key"`, `"pacing"`, or `"emerging"`), `fail_rate`,
   `classification`, and `affected_count`.
6. THE Gap_Matrix SHALL emit a `repeat_gaps` list containing the top N cells
   ranked by `affected_count` descending (default N = 10, configurable).
7. WHERE the assessed pool is empty, THE Gap_Matrix SHALL emit an empty cell
   list and an empty `repeat_gaps` list without raising an error.

### Requirement 14: Produce Individual Drill-Down Flags

**User Story:** As an HOD, I want specific individuals flagged for attention,
so that I can act on promotable talent and close critical gaps.

#### Acceptance Criteria

1. THE Individual_Drill_Down SHALL emit a `low_performers` list containing
   every scoped employee whose `combined_competency < 0.50`, ordered by
   `combined_competency` ascending.
2. THE Individual_Drill_Down SHALL emit a `promotable` list containing every
   scoped employee for whom all of the following hold:
   `combined_competency ≥ 0.75`,
   `tenure_readiness ≥ 1.0`,
   `passed_tpcp = "Y"`,
   `gap_count ≤ 3`.
3. THE Individual_Drill_Down SHALL emit a `close_in_6m` list containing
   every scoped employee whose `combined_competency` is between `0.65`
   (inclusive) and `0.75` (exclusive) together with the list of their
   weakest cells valued at `2`.
4. THE Individual_Drill_Down SHALL emit a `not_assessed` list of scoped
   employees with `has_tpcp = false`, containing `dummy_id`, `employee_name`,
   `job_grade`, and `sma_completion_status`.
5. WHERE no employees qualify for a list, THE Individual_Drill_Down SHALL
   emit that list as an empty array rather than omitting it.

### Requirement 15: Produce Action Recommendations (Training, Exposure, Hiring)

**User Story:** As an HOD, I want the engine to recommend concrete actions,
so that I can turn the diagnosis into a plan.

#### Acceptance Criteria

1. THE Insight_Engine SHALL emit a `training` action for every Gap_Matrix
   cell classified as `"structural"` whose block is `"base"` or `"key"`,
   with fields `type = "training"`, `priority = "high"`, `cell`,
   `fail_rate`, `affects = affected_count`, and `horizon_months = 6`.
2. THE Insight_Engine SHALL emit an `exposure` action for every Gap_Matrix
   cell classified as `"mixed"` whose block is `"pacing"` or `"emerging"`,
   with fields `type = "exposure"`, `priority = "medium"`, `cell`,
   `fail_rate`, `affects = affected_count`, and `horizon_months = 9`.
3. WHEN the scoped `level_distribution` shows Principal-and-Custodian count
   less than `0.30 × team_size`, THE Insight_Engine SHALL emit a `hiring`
   action with `type = "hiring"`, `priority = "high"`, `reason =
   "insufficient_senior_coverage"`, and `horizon_months = 12`.
4. WHEN a Gap_Matrix cell has `fail_rate = 1.0` and every scoped assessed
   record scored `0` on that cell, THE Insight_Engine SHALL emit a `hiring`
   action with `type = "hiring"`, `priority = "medium"`, `cell`,
   `reason = "no_internal_exposure"`, and `horizon_months = 12`.
5. THE Insight_Engine SHALL sort the action list by `priority` descending
   (`"high"` before `"medium"`) and then by `affects` descending.
6. WHERE no actions are triggered, THE Insight_Engine SHALL emit an empty
   action list and a `summary` field with value `"no_actions_recommended"`.

### Requirement 16: Emit Structured JSON Engine Response

**User Story:** As a caller of the Engine, I want a single structured JSON
response, so that the conversation layer can render narrative without
re-parsing intermediate state.

#### Acceptance Criteria

1. THE Engine SHALL emit one `Engine_Response` JSON document per query
   containing the top-level fields `scope`, `join_summary`, `team_aggregate`,
   `gap_matrix`, `individual_drill_down`, `actions`, and `employee_health`.
2. THE `scope` field SHALL contain the `business`, `opu`, and `division`
   values from the query together with `team_size`.
3. THE `employee_health` field SHALL contain the list produced in
   Requirement 11.
4. THE Engine SHALL never emit natural-language prose, narrative sentences,
   or human-readable summaries inside any field of the Engine_Response.
5. THE Engine SHALL emit the Engine_Response as valid JSON that can be
   serialized by `json.dumps` without custom encoders.
6. FOR ALL Engine_Response objects, the round-trip
   `json.loads(json.dumps(response))` SHALL produce an equivalent object.

### Requirement 17: Support Edge Cases in the Employee Pool

**User Story:** As the Engine, I want to handle incomplete data without
failing, so that the response is always well-formed.

#### Acceptance Criteria

1. WHERE the scoped pool contains only HRIS-only records, THE Engine SHALL
   compute `cbs_health` and `combined_competency` for those records, set
   TPCP-dependent scores to `null` or their documented fallbacks, and emit a
   Gap_Matrix with an empty cell list.
2. WHERE the scoped pool contains only TPCP-only records, THE Engine SHALL
   compute `tpcp_health` and `combined_competency` for those records, set
   CBS-dependent scores to `null` or their documented fallbacks, and still
   emit a valid Team_Aggregate.
3. IF the scoped pool is empty after filtering, THEN THE Engine SHALL emit
   an Engine_Response with `scope.team_size = 0`, empty lists for
   `employee_health`, `gap_matrix.cells`, `gap_matrix.repeat_gaps`,
   `individual_drill_down.*`, and `actions`, and a `summary` of
   `"scope_empty"`.
4. IF any required file is missing at engine startup, THEN THE Engine SHALL
   raise a descriptive error naming the missing file and SHALL NOT emit a
   partial Engine_Response.

### Requirement 18: Produce Deterministic Results

**User Story:** As a caller, I want the Engine to be deterministic, so that
the same input always yields the same output for audit and testing.

#### Acceptance Criteria

1. WHEN invoked with the same query and the same sample data files, THE
   Engine SHALL produce byte-identical Engine_Response JSON across repeated
   invocations.
2. THE Engine SHALL not use random number generation, wall-clock time, or
   any non-deterministic data source inside scoring, analysis, or insight
   computation.
3. THE Engine SHALL sort every list it emits (employee_health, gap cells,
   repeat_gaps, individual drill-down lists, actions) using a documented,
   stable ordering.

### Requirement 19: Expose Configurable Weights and Thresholds

**User Story:** As a maintainer, I want scoring weights and thresholds to
live in configuration, so that they can be tuned without code changes.

#### Acceptance Criteria

1. THE Engine SHALL read the following values from a single configuration
   object: TPCP_Health weights (default `0.6` and `0.4`) and pass bonus
   (default `0.1`); CBS_Health weights (defaults `0.5`, `0.3`, `0.2`);
   Combined_Competency weights (defaults `0.55`, `0.45`); grade-to-level
   bands; tenure thresholds; Gap_Matrix classification thresholds
   (defaults `0.60` and `0.20`); promotability thresholds (defaults
   `0.75`, `1.0`, `"Y"`, `3`); low-performer threshold (default `0.50`);
   close-in-6m band (defaults `0.65` and `0.75`); senior-coverage floor
   (default `0.30`); repeat-gaps top-N (default `10`).
2. WHEN a configuration value is overridden, THE Engine SHALL use the
   overridden value in every place the default is referenced in this spec.
3. IF a configuration value is missing or out of its documented range,
   THEN THE Engine SHALL raise a descriptive configuration error at startup
   and SHALL NOT run scoring with a silent fallback.
