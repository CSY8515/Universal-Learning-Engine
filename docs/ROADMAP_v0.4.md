# Universal Learning Engine v0.4 Adaptive Learning Implementation Roadmap

## Document status

This document is the implemented contract for v0.4. The repository version and release documentation are prepared; commit, push, tag, GitHub Release, and deployment remain pending explicit approval.

## 1. Current baseline

Universal Learning Engine v0.3.1 is a single-process Streamlit application with session-only state. It provides:

- Universal topic input with validation
- Question-count selection: 5, 10, 15, or 20
- Difficulty selection: Easy, Normal, Hard, or Nightmare
- OpenAI-generated tutorial, example, direct task, practice, and CBT content
- Defensive JSON extraction and lesson validation
- One-question-at-a-time CBT interaction
- Index-based scoring, immediate feedback, explanations, and round summary
- Retry and home-reset behavior
- Restricted API fallback for retryable failures
- Unit coverage for core parsing, validation, scoring, fallback, and prompt rules

The current lesson and round exist only in Streamlit session state. There is no database, learner account, background worker, durable history, recovery scheduler, or adaptive behavior.

v0.4 must preserve the complete v0.3.1 flow. Adaptation is additive and session-level only.

## 2. Exact v0.4 feature scope

v0.4 adds:

1. **Round Status** — a deterministic summary of the completed round.
2. **Learning Progress** — session-level comparison of completed rounds for the current topic.
3. **Confidence-based learning data** — optional self-reported confidence attached to each submitted answer.
4. **Learning Pattern analysis** — deterministic classification from answer correctness and confidence.
5. **Adaptive Difficulty** — a recommendation for the next round's difficulty based on completed-round evidence.
6. **Difficulty adjustment based on learning results** — an explicit user action applies the recommendation; the system does not autonomously start a round.
7. **Recovery priority and interval recommendation** — deterministic, advisory guidance derived from current-session evidence.
8. **Session-level adaptation** — evidence is retained only for the active Streamlit session and current topic.
9. **Recommendation explanations** — every difficulty and recovery recommendation includes human-readable reasons and supporting metrics.

The current manually selected difficulty remains available. Recommendations do not remove user control.

## 3. Data required for adaptation

### Per-answer record

Each submitted answer requires:

| Field | Type | Source | Purpose |
|---|---|---|---|
| `question_index` | integer | Current round | Stable question identity within the round |
| `selected_index` | integer 0–3 | Existing answer input | Scoring |
| `answer_index` | integer 0–3 | Validated lesson | Scoring |
| `is_correct` | boolean | Index comparison | Pattern and round metrics |
| `confidence` | `low`, `medium`, or `high` | Optional user input | Confidence analysis |
| `difficulty` | supported difficulty | Lesson metadata | Recommendation context |

No response-time metric is included because the current application does not measure it and timing semantics are not approved.

### Completed-round record

| Field | Type | Description |
|---|---|---|
| `round_id` | integer | Session-local round identifier |
| `topic_key` | string | Trimmed, case-normalized topic for session grouping |
| `difficulty` | supported difficulty | Difficulty used for the completed round |
| `question_count` | integer | Actual validated CBT length |
| `correct_count` | integer | Correct answers |
| `accuracy` | number 0–100 | Correct percentage |
| `confidence_counts` | mapping | Low/medium/high/unset totals |
| `answer_patterns` | mapping | Deterministic correctness-confidence categories |
| `completed_at` | none in v0.4 | Wall-clock history is excluded pending approval |

The record must not contain API credentials, raw prompts, or hidden model data. Question text is not required for v0.4 recommendations.

### Session adaptation state

- Completed-round records grouped by current normalized topic
- Latest Round Status
- Latest Learning Progress summary
- Latest difficulty recommendation and explanation
- Latest recovery recommendation and explanation

Home reset clears the active lesson, round, and all session adaptation records. Starting another generated lesson without using Home retains same-topic session progress.

## 4. Adaptive difficulty rules

### Difficulty order

```text
Easy < Normal < Hard < Nightmare
```

A recommendation may move by at most one level per completed round. Easy cannot move lower; Nightmare cannot move higher.

### Proposed deterministic rule table

| Condition for completed round | Recommendation |
|---|---|
| Accuracy at least 85%, with at least 60% of answers reporting medium/high confidence | Increase one level |
| Accuracy from 60% through 84% | Keep current level |
| Accuracy below 60% | Decrease one level |
| Accuracy at least 85%, but more than 40% of answers have low or unset confidence | Keep current level and recommend confidence-building recovery |

Rules are evaluated top to bottom after the round is complete. Confidence never increases difficulty by itself. Unset confidence is treated conservatively only for recommendation gating; it is not rewritten as low confidence.

The recommendation must contain:

- Current difficulty
- Recommended difficulty
- Accuracy and confidence evidence used
- Rule that matched
- A statement that the learner remains in control

Applying a recommendation changes the difficulty selector for the next generation request only. It does not regenerate content, submit an API request, or start a new round automatically.

The implemented policy uses the approved 85%, 60%, and 40% thresholds.

## 5. Confidence handling

Confidence is optional and self-reported for each answer:

- **Low:** learner is unsure or guessed.
- **Medium:** learner has some basis but is not fully certain.
- **High:** learner is confident in the answer.
- **Unset:** learner chose not to report confidence.

Confidence is captured before or with answer submission and becomes immutable for that submitted question during the round, matching the current one-submit feedback flow.

Correctness-confidence categories:

| Correctness | Confidence | Category |
|---|---|---|
| Correct | High | `secure_success` |
| Correct | Medium | `developing_success` |
| Correct | Low | `uncertain_success` |
| Incorrect | High | `confident_error` |
| Incorrect | Medium | `developing_gap` |
| Incorrect | Low | `recognized_gap` |
| Either | Unset | `confidence_unknown` |

Confidence is evidence, not a psychological diagnosis. UI wording must say “reported confidence” and must not claim certainty about learner knowledge.

## 6. Learning-pattern analysis

Pattern analysis operates only after a round completes and uses counts and proportions from that round. Proposed classifications are:

| Pattern | Deterministic condition | Explanation focus |
|---|---|---|
| `strong_mastery_signal` | Accuracy ≥85% and secure/developing successes ≥60% of all answers | Consistent correct performance with stated confidence |
| `fragile_success_signal` | Accuracy ≥85% and uncertain successes plus confidence-unknown answers >40% | Correct results with limited confidence evidence |
| `overconfidence_risk` | Confident errors ≥20% of all answers | High confidence attached to incorrect answers |
| `developing_understanding` | Accuracy 60–84% and overconfidence condition not met | Mixed performance with room to consolidate |
| `foundational_gap_signal` | Accuracy <60% | Current difficulty may exceed demonstrated performance |

Multiple signals may be reported when logically compatible, except `strong_mastery_signal` and `fragile_success_signal`, which are mutually exclusive. `overconfidence_risk` may accompany any non-mastery result.

Patterns must be rendered as evidence summaries, not hidden learner labels. No model call is used to classify them.

The approved classification thresholds are implemented. Compatible signals may appear together; strong-mastery and fragile-success signals remain mutually exclusive.

## 7. Recovery recommendation logic

Recovery in v0.4 is advisory only. It does not generate a recovery lesson, schedule work, send notifications, or persist a future task.

### Priority

| Priority | Proposed condition |
|---|---|
| High | Accuracy <60%, or confident errors ≥20% |
| Medium | Accuracy 60–84%, or fragile-success signal |
| Low | Strong-mastery signal with no overconfidence risk |

If multiple conditions match, the highest priority wins.

### Interval recommendation

Intervals are relative guidance only and are not scheduled:

| Priority | Proposed wording |
|---|---|
| High | Review before the next round |
| Medium | Review later in the current session |
| Low | No immediate recovery needed |

The recommendation explanation includes matched evidence, priority, interval wording, and a statement that no reminder has been scheduled.

No day-based or date-based interval is proposed because background scheduling, persistent timelines, and long-term retention tracking are out of scope.

## 8. UI changes

Existing screens and controls remain available. Additive changes:

1. Add an optional reported-confidence selector to each CBT question before answer submission.
2. Keep current correctness feedback and explanations unchanged.
3. Extend the completed-round summary with:
   - Round Status
   - Confidence distribution
   - Learning Pattern evidence
   - Learning Progress for the current topic and session
   - Recommended next difficulty with reasons
   - Recovery priority and interval guidance with reasons
4. Add an explicit “Use recommended difficulty” action when a different difficulty is recommended.
5. Keep “Retry” and “Home” actions.
6. Clearly label recommendations as advisory and session-only.

No dashboard, timeline page, notification control, account view, or autonomous next-round action is added.

## 9. Expected file changes

### Existing files

- `app.py` — add session adaptation data structures, pure analysis functions, confidence UI, summary sections, and explicit recommendation application.
- `tests/test_app_quality.py` — preserve all existing tests and add deterministic v0.4 unit and regression tests.
- `README.md` — document implemented v0.4 behavior only after implementation passes acceptance.
- `CHANGELOG.md` — record the completed v0.4 Adaptive Learning release scope.
- `VERSION` — set to `v0.4` during final release preparation.
- `docs/MASTER_DESIGN.md` — add the approved v0.4 design after implementation approval.
- `docs/ARCHITECTURE.md` — document implemented session adaptation flow.
- `docs/MODULE_SPEC.md` — replace v0.4 reservations with approved contracts.
- `docs/ROADMAP.md` — link to this detailed roadmap and reflect approved status.

### Proposed new implementation file

- `adaptive.py` — pure, Streamlit-independent data normalization and deterministic recommendation logic.
- `tests/test_adaptive.py` — focused adaptive-rule, boundary, explanation, and compatibility tests.

Separating pure logic prevents additional complexity in the existing 692-line UI module and makes rule behavior directly testable. No new dependency is expected.

## 10. Backward compatibility plan

- Preserve existing lesson JSON fields and validation behavior.
- Do not require confidence in generated model JSON.
- Keep topic, count, difficulty, generation, CBT, scoring, feedback, summary, retry, and home flows.
- Keep answer correctness index-based.
- Keep all existing session keys functional; add new keys without changing their meaning.
- Treat missing confidence as `unset`, allowing the existing answer path to continue.
- Keep existing OpenAI prompt, API fallback, and model configuration behavior unless a separately approved change is required.
- Do not alter v0.3.1 difficulty prompt semantics as part of adaptive recommendation work.
- If adaptive analysis fails, render the existing v0.3.1 summary and a non-fatal advisory error rather than losing the round result.

## 11. Test plan

### Existing regression suite

Run `python -m unittest discover` after every milestone. All existing tests must remain passing.

### Pure adaptive-rule tests

- Difficulty ordering and one-level movement
- Upper and lower difficulty bounds
- Every accuracy threshold boundary: 59/60/84/85
- Confidence gate boundaries, including unset confidence
- Confidence category mapping for all correctness-confidence combinations
- Pattern classification and mutual exclusion
- Overconfidence-risk combinations
- Recovery priority precedence
- Recovery interval wording
- Explanation presence and evidence fields
- Empty and malformed evidence handling
- No mutation of input records

### Session and compatibility tests

- Existing answers without confidence remain valid
- Retry creates a distinct round and preserves intended session evidence
- Home reset follows the approved adaptation-state policy
- Topic normalization prevents accidental cross-topic aggregation
- A changed topic does not reuse another topic's recommendation
- Adaptive failure does not break existing round summary
- Applying a recommendation changes only the next selected difficulty

### Streamlit verification after each milestone

- Start the app locally and confirm it becomes ready without startup errors.
- Manually verify topic validation, generation controls, all difficulties, and all question-count choices.
- Use controlled lesson data to complete correct, mixed, and incorrect rounds.
- Verify confidence input, existing feedback, summary, retry, home, recommendation explanation, and explicit application.
- Verify no automatic API call, next round, notification, or persistence occurs.

Live OpenAI generation is a separate manual check requiring configured credentials and must not be required for deterministic unit tests.

## 12. Acceptance criteria

v0.4 is acceptable only when:

1. Every existing v0.3.1 test passes unchanged or with backward-compatible additions.
2. All existing v0.3.1 user features remain usable.
3. A completed round produces deterministic Round Status and Learning Progress.
4. Optional confidence is recorded without blocking learners who leave it unset.
5. Pattern output follows the approved rule table and shows supporting evidence.
6. Difficulty recommendations move no more than one level and respect Easy/Nightmare bounds.
7. Difficulty never changes without an explicit user action.
8. Recovery priority and interval guidance follow the approved rules and include reasons.
9. Recommendations are visibly advisory and session-only.
10. Data from different normalized topics is not mixed.
11. No adaptive classifier requires an AI call.
12. No database, durable learner history, scheduler, notification, or v0.5 feature is introduced.
13. Adaptive-analysis failure cannot prevent the existing round result from rendering.
14. Streamlit startup and manual regression verification pass.
15. Documentation matches the implemented behavior.

## 13. Explicit out-of-scope items

- v0.5 Decision Engine
- Autonomous AI decisions or model-selected difficulty
- Automatic generation or starting of the next round
- Background jobs, scheduling, reminders, or notifications
- Database, account, login, or cloud persistence infrastructure
- Persistent Learning Timeline
- Long-term Knowledge Retention tracking or decay modeling
- Cross-session learner profile
- Date-based recovery scheduling
- Dashboard or external analytics
- Recovery-content generation engine
- Expansion Packs
- PDF, OCR, voice, or image features
- Changes to Git history, repository identity, releases, tags, or deployment

## 14. Risks and rollback plan

### Risks

- **Unapproved thresholds:** proposed numeric rules may not match the intended pedagogy.
- **Self-report ambiguity:** confidence is subjective and may be unset or inconsistently interpreted.
- **Small-round volatility:** five-question rounds make each answer worth 20 percentage points.
- **State coupling:** adding adaptation to the current single-file Streamlit state can create reset or rerun regressions.
- **Topic grouping:** simple normalized text may treat near-equivalent topics as different or distinct topics as equivalent.
- **Recommendation overstatement:** deterministic signals could be mistaken for diagnoses without careful UI wording.
- **Testability:** full Streamlit interaction needs controlled data because live model responses are nondeterministic.

### Mitigations

- Require approval of thresholds before implementation.
- Use descriptive “signal” language and show evidence.
- Move deterministic rules into pure functions.
- Bound changes to one difficulty level.
- Keep recommendations advisory and explicitly applied.
- Fail open to the existing v0.3.1 summary when analysis is unavailable.

### Incremental rollback

Each implementation milestone must be separable. If a milestone fails verification, revert only that milestone's uncommitted changes while retaining the documented v0.3.1 baseline. Runtime integration must be guarded so the existing summary path works without adaptive output. No schema migration or data rollback is required because v0.4 stores no durable data.

## Proposed implementation stages

### Stage 0 — Policy approval (complete)

Approve or revise thresholds, confidence values, pattern coexistence, recovery wording, and home-reset behavior. Update canonical design documents before runtime work.

### Stage 1 — Pure adaptive domain logic (complete)

Add session-record structures and pure functions for confidence categories, Round Status, pattern analysis, difficulty recommendation, recovery recommendation, and explanations. Add boundary-focused unit tests. No UI changes.

### Stage 2 — Session integration and Learning Progress (complete)

Record completed rounds by normalized topic, calculate current-session progress, implement reset isolation, and add compatibility/error-fallback tests. Existing UI remains functionally unchanged.

### Stage 3 — Confidence UI and adaptive summary (complete)

Add optional confidence input and additive Round Status, pattern, progress, difficulty, and recovery summary sections. Preserve existing feedback and summary content.

### Stage 4 — Explicit recommendation application (complete)

Add the user-controlled action that applies a recommended difficulty to the next generation form. Verify it never triggers generation or starts a round automatically.

### Stage 5 — Full regression and documentation alignment (complete)

Run the entire automated suite, verify Streamlit startup and manual flows, confirm only approved scope exists, and align README, changelog, architecture, master design, module specification, and roadmap documentation. Do not version, commit, push, tag, release, or deploy without separate approval.
