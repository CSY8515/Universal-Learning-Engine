# Universal Learning Engine v0.5 Learning Analytics Roadmap

## Document status

This document is the approved and implemented v0.5 Learning Analytics contract. Implementation and automated verification are complete in the working tree. `VERSION`, release notes, commit, push, tag, GitHub Release, and deployment remain pending separate approval.

The v0.5 implementation is additive. It expands the Learning Analytics layer using results already produced and retained by v0.4. It does not change lesson generation, CBT scoring, adaptive recommendation rules, recovery guidance, reset behavior, persistence, or learner control.

## 1. Current v0.4 baseline

Universal Learning Engine v0.4 is a single-process Streamlit application with two runtime modules:

- `app.py` owns configuration, prompt construction, OpenAI integration, response parsing and validation, session integration, scoring, and UI rendering.
- `adaptive.py` owns pure deterministic confidence categories, Round Status, learning-pattern signals, bounded difficulty advice, and recovery advice.

The implemented behavior includes:

- Validated universal topic input
- Question counts of 5, 10, 15, or 20
- Easy, Normal, Hard, and Nightmare difficulty levels
- Generated tutorial, example, direct task, practice, and CBT content
- Defensive JSON parsing and lesson validation
- One-question-at-a-time CBT interaction
- Index-based scoring, immediate feedback, explanations, and completed-round summary
- Retry and Home behavior
- Restricted fallback for retryable OpenAI API failures
- Optional self-reported confidence per submitted answer
- Session-only Round Status and same-topic Learning Progress
- Deterministic per-round learning-pattern signals
- Bounded, advisory next-difficulty and recovery recommendations
- Explicit learner action before a recommended difficulty is applied

v0.4 stores completed adaptive summaries in `adaptation_records`, grouped by normalized topic key. These records exist only in the active Streamlit session. Home clears them. There is no database, learner account, durable history, background worker, scheduler, or notification system.

Every v0.4 feature and its current behavior is a v0.5 compatibility requirement.

## 2. Exact v0.5 scope

v0.5 adds a read-only, deterministic Learning Analytics layer over retained v0.4 completed-round summaries:

1. **Latest-round analytics** with accuracy, answer-pattern, and reported-confidence measures.
2. **Current-topic session analytics** across all retained completed rounds for the active normalized topic.
3. **Overall learning analytics** across all topic groups currently retained in `adaptation_records`.
4. **Accuracy statistics** based on total correct answers and total questions, plus clearly labeled round averages and ranges.
5. **Learning-result summaries** that explain totals, changes, distributions, and evidence coverage.
6. **Round-level analytics** presented as ordered summaries of completed rounds.
7. **Confidence-data analysis** using the v0.4 confidence counts and correctness-confidence categories.
8. **Learning-pattern analysis** using v0.4 signals, signal frequency, recent repetition, accuracy direction, and difficulty breakdowns.
9. **Strength and weakness summaries** for topic-and-difficulty groups that meet an evidence minimum.
10. **Reusable analytics foundations** implemented as pure, Streamlit-independent functions with versioned output dictionaries.
11. **Additive UI panels** in the completed-round view; no separate application, account view, or persistent dashboard.

“Overall” in v0.5 means all completed-round records still retained in the current Streamlit session. It does not mean lifetime, cross-device, cross-session, or account-level analytics.

v0.5 analytics describe observed results. They must not select learning actions, alter difficulty, generate content, schedule work, or make autonomous decisions.

## 3. Analytics responsibilities

### Analytics domain layer

The proposed `analytics.py` module will:

- Accept v0.4 completed adaptive summaries as input.
- Validate and normalize analytics input without mutating source records.
- Calculate weighted accuracy from summed correct answers and question counts.
- Calculate round-average accuracy only as a separately labeled statistic.
- Aggregate reported-confidence and correctness-confidence categories.
- Summarize per-round, per-topic, per-difficulty, current-topic, and overall retained-session results.
- Describe observed pattern frequency, recent repetition, and accuracy direction.
- Produce evidence-qualified strength and weakness summaries.
- Return stable dictionaries that do not depend on Streamlit, OpenAI, storage, scheduling, or notifications.
- Return validation issues for unusable records while allowing valid records to remain analyzable.

### Session integration layer

`app.py` will:

- Read the existing `adaptation_records` structure after a round completes.
- Pass existing records to pure analytics functions.
- Select the current normalized topic for current-topic analytics.
- Render analytics after the complete v0.4 round result and adaptive guidance.
- Treat analytics failure as non-fatal and leave all v0.4 results visible and usable.
- Preserve the current Home clearing policy and Retry behavior.

### Presentation layer

The UI will:

- Clearly label the scope as “current session only.”
- Distinguish latest-round, current-topic, and overall retained-session results.
- Distinguish weighted accuracy from mean round accuracy.
- Show evidence counts with every strength or weakness statement.
- Use “reported confidence,” “signal,” and “observed result” language rather than diagnostic or psychological claims.
- Show an insufficient-evidence message instead of inventing a strength, weakness, or trend.

## 4. Required input data

v0.5 uses only data already produced by v0.4.

### Required completed-round fields

| Field | Type | Current source | Analytics use |
|---|---|---|---|
| `round_status.round_id` | integer | v0.4 session round | Stable session-local round identity |
| `round_status.topic_key` | string | `normalize_topic_key` | Current-topic and overall grouping |
| `round_status.difficulty` | supported difficulty | Validated lesson metadata | Difficulty breakdown |
| `round_status.question_count` | positive integer | Completed CBT | Denominators and evidence size |
| `round_status.correct_count` | integer | Index-based scoring | Weighted accuracy |
| `round_status.wrong_count` | integer | v0.4 Round Status | Result totals |
| `round_status.accuracy` | number from 0 to 100 | v0.4 Round Status | Round display and consistency checks |
| `round_status.confidence_counts` | mapping | Optional reported confidence | Confidence distribution and coverage |
| `round_status.answer_patterns` | mapping | v0.4 confidence categories | Confidence/correctness analysis |
| `learning_patterns` | list of signal dictionaries | v0.4 deterministic rules | Pattern frequency and repetition |

The existing record order inside each topic list is the only approved round sequence. v0.5 will not infer wall-clock time because v0.4 records have no timestamp.

### Explicitly unavailable inputs

The following are not present in v0.4 completed-round summaries and will not be fabricated:

- Concept tags or curriculum objectives
- Question text and selected-choice text in analytics records
- Response time or time-on-task
- Timestamps or elapsed time between rounds
- Cross-session learner identity or history
- Probabilistic confidence scores
- Generated-content quality scores
- Long-term retention or forgetting evidence

Because concept tags are unavailable, v0.5 strengths and weaknesses are limited to topic, difficulty, accuracy, confidence, and observed v0.4 pattern evidence. They cannot claim that a learner is strong or weak in a particular sub-concept.

## 5. Session-level analytics

Current-topic session analytics use all valid retained records under the active normalized topic key.

The summary will include:

- Completed-round count
- Total questions, correct answers, and wrong answers
- Weighted accuracy: `sum(correct_count) / sum(question_count) * 100`
- Mean round accuracy: `sum(round accuracy) / completed-round count`, labeled as unweighted
- Latest, previous, best, and lowest round accuracy
- Latest-versus-previous and first-versus-latest percentage-point changes
- Accuracy direction: `improved`, `declined`, `steady`, or `not_available`
- Round accuracy range: highest minus lowest
- Difficulty distribution and per-difficulty result summaries
- Aggregated reported-confidence counts and reporting rate
- Aggregated correctness-confidence categories
- v0.4 learning-signal frequencies
- Signals repeated in the two most recent rounds
- Evidence-qualified strengths and weaknesses for the current topic

One round is sufficient for descriptive totals but not for a longitudinal trend. A trend requiring comparison must return `not_available` until at least two rounds exist.

The word “session” refers to the active Streamlit session and the records that remain after applying existing v0.4 reset behavior.

## 6. Round-level analytics

Each valid completed round will produce a `RoundAnalytics` summary containing:

- Round identifier and sequence position within its topic group
- Normalized topic key
- Difficulty
- Question, correct, and wrong counts
- Accuracy
- Reported-confidence counts and reporting rate
- Correctness-confidence category counts and rates
- Supported-success count and rate: `secure_success + developing_success`
- Uncertain-success count and rate
- Confident-error count and rate
- Confidence-unknown count and rate
- v0.4 learning-pattern signal names and reasons
- v0.4 difficulty and recovery recommendations as descriptive source context only
- Validation issues, if optional source fields are absent or inconsistent

Round analytics must not recalculate or override v0.4 adaptive recommendations. They summarize the source recommendation so later analytics consumers can reuse one consistent record.

Round ordering is deterministic: topic groups retain insertion order, and records within each topic retain their existing list order. `round_id` is displayed as an identifier, not treated as a timestamp.

## 7. Overall analytics

Overall analytics aggregate every valid completed-round record across every topic key still present in `adaptation_records`.

The summary will include:

- Retained topic count
- Completed-round count
- Total questions, correct answers, and wrong answers
- Weighted accuracy and separately labeled mean round accuracy
- Best and lowest round accuracy
- Aggregated confidence distribution and reporting rate
- Aggregated correctness-confidence categories
- Learning-signal frequencies
- Per-topic summaries
- Per-difficulty summaries
- Eligible strength and weakness summaries across topic-and-difficulty groups
- Count of skipped invalid records and a non-sensitive issue summary

Per-topic and per-difficulty tables will use weighted accuracy. Sorting will be stable and deterministic:

1. Evidence-qualified groups before insufficient-evidence groups.
2. Higher weighted accuracy first for strengths.
3. Lower weighted accuracy first for weaknesses.
4. More questions first as the next tie-breaker.
5. Topic key and supported difficulty order as final tie-breakers.

An empty record set returns an explicit empty analytics result. It is not an error and must not hide the v0.4 UI.

## 8. Confidence analysis

v0.5 reuses the v0.4 confidence meanings and categories without changing them.

### Reported-confidence measures

- `reported_count = low + medium + high`
- `unset_count = unset`
- `reporting_rate = reported_count / question_count * 100`
- Low, medium, high, and unset counts and percentages

### Correctness-confidence measures

- `supported_success = secure_success + developing_success`
- `uncertain_success = uncertain_success`
- `confident_error = confident_error`
- `developing_gap = developing_gap`
- `recognized_gap = recognized_gap`
- `confidence_unknown = confidence_unknown`

Each category will expose a count and a percentage of all answers in the selected scope.

### Interpretation boundary

v0.5 will describe alignment between correctness and reported confidence. It will not calculate a calibration score, diagnose overconfidence, infer motivation, or convert low/medium/high values into invented probabilities. The existing v0.4 `overconfidence_risk` name may be displayed only as the existing deterministic signal with its evidence and cautionary wording.

Unset confidence remains unset. It is included in coverage statistics and must never be silently treated as low confidence.

## 9. Learning-pattern analysis

Learning-pattern analysis will combine observed sequences with the already approved v0.4 signals.

For each current-topic and overall scope it will report:

- Frequency of each v0.4 signal
- Percentage of rounds containing each signal
- Signals appearing in both of the two most recent comparable rounds
- Latest-versus-previous accuracy direction
- First-versus-latest accuracy direction
- Accuracy range across rounds
- Per-difficulty accuracy and confidence breakdowns
- Changes in reported-confidence coverage from the first to latest comparable round
- Changes in confident-error and supported-success rates from the first to latest comparable round

No regression line, prediction, causal statement, retention claim, or semantic learner label is included in v0.5. Different difficulty levels are shown explicitly so a change in accuracy is not presented as pure improvement when the difficulty also changed.

Overall cross-topic analytics will aggregate signal frequency and difficulty results, but it will not compute a single cross-topic chronological trend because v0.4 has no global timestamped order.

## 10. Strength and weakness summaries

Strength and weakness summaries are deterministic evidence statements, not learner diagnoses.

### Evaluation groups

Candidates are evaluated by normalized topic and difficulty. A candidate is eligible only when it contains:

- At least 2 completed rounds, and
- At least 10 total answered questions.

Groups below either minimum are listed as insufficient evidence and are not labeled as a strength or weakness.

### Strength rule

A group is a strength candidate when:

- Weighted accuracy is at least 85%, and
- Supported successes (`secure_success + developing_success`) are at least 60% of all answers.

The statement includes topic, difficulty, round count, question count, weighted accuracy, supported-success rate, and applicable v0.4 signal frequency.

### Weakness rule

A group is a weakness candidate when either:

- Weighted accuracy is below 60%, or
- Confident errors are at least 20% of all answers.

The statement identifies which condition matched and includes topic, difficulty, round count, question count, weighted accuracy, confident-error rate, and applicable v0.4 signal frequency.

### Conflict and display policy

- If more than one weakness condition matches, one candidate contains both reasons.
- A candidate that somehow satisfies both strength and weakness rules is shown as mixed evidence, not in both ranked lists.
- At most three strongest and three weakest eligible groups are shown in the concise summary; the full breakdown remains available in the detail table.
- When no eligible candidates match, the UI says that no clear strength or weakness is established from the retained evidence.
- Topic keys may be displayed using the current lesson topic when available; grouping remains based on the existing normalized key.

The approved implementation uses the 2-round/10-answer evidence minimum and the 85%/60%/20% thresholds.

## 11. UI changes

All v0.4 screens, controls, summary content, retry behavior, Home behavior, and recommendation controls remain available.

After the v0.4 adaptive summary, v0.5 will add a **Learning Analytics** section with:

1. A caption stating that analytics use only retained records from the current session.
2. **Latest Round** metrics for accuracy, reported-confidence coverage, supported success, and confident errors.
3. **Current Topic** metrics for rounds, questions, weighted accuracy, latest change, and evidence coverage.
4. **Overall Session** metrics for retained topics, rounds, questions, weighted accuracy, and confidence coverage.
5. **Strengths and Weaknesses** summaries with evidence counts or an insufficient-evidence message.
6. Expandable round, topic, difficulty, confidence, and pattern detail tables.

The concise view will prioritize text and Streamlit-native metrics/tables. No charting dependency is proposed. Any later chart proposal must use the same analytics outputs and receive separate review if it changes dependencies or interaction behavior.

The analytics section is informational. It adds no button that applies a learning action, changes difficulty, starts a round, sends a request, schedules a review, or creates a notification.

If analytics cannot be calculated, the UI displays a non-fatal analytics warning after the preserved v0.4 result. The existing result, adaptive summary, Retry, Home, and recommendation action remain usable.

## 12. Data structures

The structures below are contracts by field meaning. Implementation may use typed dictionaries or equivalent plain dictionaries without adding a dependency.

### `RoundAnalytics`

```text
schema_version: "0.5"
round_id: integer
sequence: positive integer within topic records
topic_key: string
difficulty: Easy | Normal | Hard | Nightmare
question_count: positive integer
correct_count: integer
wrong_count: integer
accuracy: number 0..100
confidence:
  counts: {low, medium, high, unset}
  percentages: {low, medium, high, unset}
  reported_count: integer
  reporting_rate: number 0..100
answer_patterns:
  counts: mapping of v0.4 category to integer
  percentages: mapping of v0.4 category to number 0..100
  supported_success_count: integer
  supported_success_rate: number 0..100
  confident_error_count: integer
  confident_error_rate: number 0..100
learning_patterns: list of {name, reason}
difficulty_recommendation: copied descriptive mapping or null
recovery_recommendation: copied descriptive mapping or null
issues: list of validation issue codes
```

### `AggregateAnalytics`

```text
schema_version: "0.5"
scope: current_topic | overall_session | topic | difficulty | topic_difficulty
scope_key: string or null
topic_count: integer
round_count: integer
question_count: integer
correct_count: integer
wrong_count: integer
weighted_accuracy: number or null
mean_round_accuracy: number or null
latest_accuracy: number or null
previous_accuracy: number or null
best_round_accuracy: number or null
lowest_round_accuracy: number or null
latest_change: number or null
first_to_latest_change: number or null
accuracy_direction: improved | declined | steady | not_available
accuracy_range: number or null
confidence: aggregated confidence mapping
answer_patterns: aggregated category mapping
learning_pattern_frequencies: mapping of signal name to round count
repeated_recent_signals: list of signal names
difficulty_summaries: list of AggregateAnalytics
topic_summaries: list of AggregateAnalytics
rounds: list of RoundAnalytics
strengths: list of EvidenceSummary
weaknesses: list of EvidenceSummary
insufficient_evidence: list of EvidenceSummary
skipped_record_count: integer
issues: list of validation issue codes
```

### `EvidenceSummary`

```text
classification: strength | weakness | mixed | insufficient_evidence
topic_key: string
difficulty: supported difficulty
round_count: integer
question_count: integer
weighted_accuracy: number or null
supported_success_rate: number or null
confident_error_rate: number or null
matched_rules: list of stable rule names
evidence_text: non-empty string
```

### State policy

Analytics outputs are derived views, not a second source of truth. v0.5 should calculate them from `adaptation_records` when rendering and should not change the v0.4 completed-round schema. No new persistent state key is required unless profiling demonstrates a verified need and a later design review approves caching semantics.

## 13. Expected file changes

### Documentation-only design stage (this task)

- `docs/ROADMAP_v0.5.md` — add the complete proposed v0.5 contract.
- `docs/ROADMAP.md` — replace the previous v0.5 longitudinal placeholder with the Learning Analytics proposal and move the unapproved timeline/retention concepts back to the unassigned future backlog.

No application, test, version, changelog, release-note, dependency, configuration, or deployment file changes are part of this task.

### Implemented runtime and test files

- `analytics.py` — new pure validation, round analytics, aggregation, pattern, and evidence-summary functions.
- `app.py` — additive analytics integration and completed-round UI rendering only.
- `tests/test_analytics.py` — new pure analytics unit and boundary tests.
- `tests/test_streamlit_v05.py` — new Streamlit analytics and v0.4 compatibility tests.

Existing v0.4 tests remain in place. `adaptive.py` is not expected to change because v0.5 consumes its current outputs rather than changing its rules. `requirements.txt` is not expected to change.

### Canonical documentation alignment

- `README.md` — describe implemented v0.5 analytics and current limitations.
- `CHANGELOG.md` — record completed v0.5 behavior while preserving history.
- `VERSION` — update to `v0.5` only during approved release preparation.
- `docs/ARCHITECTURE.md` — document the implemented analytics boundary and flow.
- `docs/MASTER_DESIGN.md` — add the approved and implemented v0.5 design.
- `docs/MODULE_SPEC.md` — add implemented analytics module contracts.
- `docs/ROADMAP.md` — mark v0.5 implementation status accurately.
- `docs/ROADMAP_v0.5.md` — replace proposal language with implemented status only after verification.
- `RELEASE_NOTES_v0.5.md` — create only during approved release preparation.

No commit, push, tag, GitHub Release, deployment, or publication is implied by any stage.

## 14. Backward-compatibility plan

- Preserve the v0.4 lesson JSON contract and every validation rule.
- Preserve topic validation, question-count options, difficulty options, generation, CBT, scoring, feedback, explanations, round summary, Retry, and Home.
- Preserve index-based scoring and duplicate-choice rejection.
- Preserve optional confidence and the meaning of unset confidence.
- Preserve all v0.4 adaptive thresholds, signals, difficulty recommendations, recovery guidance, and explicit learner control.
- Preserve `adaptation_records` as the completed-round source of truth and do not migrate or rewrite existing records.
- Preserve normalized-topic grouping.
- Preserve Home clearing all adaptive records; analytics disappear because their source records disappear.
- Preserve session-only behavior and make no configuration or dependency change.
- Keep prompt construction, OpenAI calls, model selection, API fallback, and generated lesson behavior unchanged.
- Calculate analytics only after existing scoring and adaptive recording succeed.
- If analytics input is partially invalid, analyze valid records, report skipped-record counts, and avoid changing source data.
- If analytics integration fails, render the entire v0.4 result and controls and show only a non-fatal analytics warning.
- Keep all existing v0.4 tests passing without weakening assertions.

## 15. Test plan

### Baseline regression

- Run `python -m unittest discover` before implementation.
- Run the complete suite after every implementation milestone.
- Preserve all v0.4 parsing, validation, scoring, fallback, adaptive-rule, session, and Streamlit assertions.

### Pure analytics unit tests

- Empty record set returns a valid empty result.
- One valid round produces exact round analytics.
- Weighted accuracy uses total correct divided by total questions and differs correctly from mean round accuracy when round sizes differ.
- Counts, percentages, and totals reconcile exactly.
- Percentage helpers handle zero denominators without division errors.
- Confidence reporting rate excludes unset from the numerator but retains unset in totals.
- Missing confidence remains unset.
- All v0.4 correctness-confidence categories aggregate correctly.
- Supported-success and confident-error measures use the documented categories.
- Topic, difficulty, and topic-difficulty grouping is correct.
- Current-topic analytics never include another topic.
- Overall analytics include every valid retained topic group exactly once.
- Latest/previous and first/latest comparisons follow record list order.
- One round returns `not_available` for comparison-dependent trends.
- Accuracy direction handles positive, negative, and zero changes.
- Overall analytics do not invent a cross-topic chronological trend.
- Signal frequencies and two-most-recent repetition are correct.
- Difficulty changes remain visible in trend evidence.
- Strength evidence boundaries cover 1/2 rounds and 9/10 questions.
- Strength thresholds cover just below/at 85% accuracy and 60% supported success.
- Weakness thresholds cover just below/at 60% accuracy and just below/at 20% confident errors.
- Mixed-evidence conflict handling is deterministic.
- Strength and weakness ordering and three-item concise limits are deterministic.
- Invalid records are skipped with stable issue codes while valid records remain included.
- Duplicate round identities in one topic group are handled according to the approved validation policy.
- Source dictionaries and nested lists are not mutated.
- Output contains `schema_version: "0.5"`.

### Application integration tests

- A completed round still renders the full v0.4 result before analytics.
- v0.4 adaptive guidance remains unchanged.
- Latest-round analytics use the just-recorded round once, without duplicate counting on Streamlit reruns.
- Current-topic analytics use only the current normalized topic.
- Overall analytics use all currently retained topic groups.
- Retry adds one completed record only after the retried round finishes.
- Home clears source records and therefore clears analytics, preserving v0.4 behavior.
- Leaving confidence unset does not block completion or analytics.
- Applying a v0.4 difficulty recommendation remains explicit and does not trigger generation.
- Analytics add no autonomous action, API call, scheduler, notification, or persistence.
- Analytics exceptions do not hide result, adaptive summary, Retry, Home, or recommendation controls.

### Streamlit/manual verification

- Start the app locally and verify it becomes ready without startup errors.
- Verify all v0.4 landing controls, question counts, difficulties, and generation behavior.
- Complete controlled correct, mixed, and incorrect rounds with high, medium, low, and unset confidence.
- Complete rounds of different sizes and confirm weighted versus mean round accuracy labels.
- Complete repeated rounds at the same and different difficulties and verify trend wording.
- Generate or inject controlled records for more than one topic and verify current-topic versus overall separation.
- Verify strength, weakness, mixed, and insufficient-evidence wording.
- Verify narrow layout readability and expand/collapse behavior.
- Verify Home and Retry behavior.
- Verify no network request is made by analytics rendering.

Live OpenAI generation remains a separate manual regression check requiring configured credentials. Deterministic analytics tests must not require credentials or network access.

## 16. Acceptance criteria

v0.5 implementation will be acceptable only when:

1. Every existing v0.4 automated test passes without weakened behavior assertions.
2. All existing v0.4 user-visible features and controls remain usable and semantically unchanged.
3. Analytics use only existing retained v0.4 learning results.
4. Latest-round analytics reconcile with the v0.4 Round Status exactly.
5. Current-topic analytics exclude all other topic keys.
6. Overall analytics include all and only valid records currently retained in `adaptation_records`.
7. Weighted accuracy is calculated from summed counts and is clearly distinguished from mean round accuracy.
8. Round, topic, difficulty, confidence, and pattern totals reconcile with their source records.
9. Unset confidence remains unset and is reflected in coverage statistics.
10. Learning-pattern summaries use observed v0.4 signals and record order without AI classification or prediction.
11. Strength and weakness labels appear only when the approved evidence minimum and thresholds are met.
12. Every strength or weakness statement displays topic, difficulty, sample size, and matched quantitative evidence.
13. Insufficient evidence produces an explicit neutral message rather than a forced label.
14. No concept-level strength or weakness is claimed without concept-level source data.
15. Analytics outputs are deterministic, versioned, Streamlit-independent, and do not mutate inputs.
16. Invalid analytics records cannot corrupt or hide valid v0.4 results.
17. Analytics failure is non-fatal and leaves the entire v0.4 result and navigation controls available.
18. Home continues to clear adaptive records and all derived analytics.
19. No analytics function calls OpenAI or changes generation, scoring, adaptive recommendations, or recovery rules.
20. No database, durable history, scheduler, notification, autonomous decision, or Living OS integration is introduced.
21. No new dependency is added unless separately reviewed and approved.
22. Automated regression, pure analytics, integration, Streamlit startup, and manual controlled-data checks pass.
23. Canonical documentation matches implemented behavior before any release preparation.
24. Version, release notes, Git operations, tags, deployment, and publication remain untouched until separately authorized.

## 17. Explicit out-of-scope items

- Learning Decision Engine
- Automatic selection or application of learning actions
- Autonomous difficulty changes or next-round generation
- AI-generated analytics interpretation or learner classification
- Changes to v0.4 adaptive thresholds or recovery rules
- Recovery-content generation
- Background jobs, scheduling, reminders, or notifications
- Database or any other durable storage
- Cross-session, cross-device, or account-level history
- Login, learner accounts, identity matching, or profiles
- Persistent Learning Timeline
- Knowledge Retention or forgetting/decay modeling
- Timestamp, duration, response-time, or time-on-task analytics
- Predictive analytics, forecasting, regression, or causal claims
- Concept-level mastery without new concept-tagged evidence
- Semantic topic merging
- External analytics services or telemetry
- Data export, PDF reports, or sharing
- Separate dashboard application or navigation redesign
- Living OS integration
- Expansion Backlog features
- PDF, OCR, voice, image, or Expansion Pack features
- Dependency upgrades unrelated to the approved analytics implementation
- Commit, push, tag, GitHub Release, deployment, or publication

## 18. Risks and rollback plan

### Risks

- **Small samples:** five-question rounds produce 20-percentage-point steps and can overstate a pattern.
- **Unequal round sizes:** averaging round percentages can disagree with the true combined accuracy.
- **Confidence subjectivity:** low, medium, and high are self-reported and not calibrated probabilities.
- **Missing confidence:** high unset rates limit confidence-based interpretation.
- **Difficulty confounding:** accuracy can change because difficulty changed, not because learning improved or declined.
- **Topic-key limits:** text normalization does not identify semantically equivalent topics.
- **No timestamps:** cross-topic chronological trends and time-aware claims are impossible.
- **Record-shape coupling:** analytics depend on the v0.4 completed-summary structure.
- **UI density:** several analytical scopes can overwhelm the completed-round view.
- **Overinterpretation:** strength, weakness, and pattern language may be read as a diagnosis.
- **Rerun duplication:** Streamlit reruns could double-count a round if integration bypasses the existing idempotent recorder.
- **Partial invalid data:** one malformed session record could otherwise prevent all analytics rendering.

### Mitigations

- Use weighted accuracy as the primary aggregate and label mean round accuracy separately.
- Require at least 2 rounds and 10 answers before strength or weakness labels.
- Always display round count, answer count, difficulty, and confidence coverage with conclusions.
- Keep difficulty-specific breakdowns adjacent to trend summaries.
- Use neutral evidence language and explicit current-session limitations.
- Derive analytics from the existing idempotent v0.4 record store.
- Validate records independently, skip unusable records, and report issue counts.
- Implement analytics as pure functions with no side effects.
- Keep concise metrics visible and place detailed tables in expanders.
- Fail open to the full v0.4 result when analytics is unavailable.

### Rollback plan

Implementation milestones must remain separable and uncommitted unless separately authorized.

- If pure analytics logic fails, remove or revert only `analytics.py` and `tests/test_analytics.py`; v0.4 runtime remains untouched.
- If session integration fails, remove the additive analytics call and v0.5 UI from `app.py`; existing `adaptation_records` remain unchanged.
- If presentation fails, disable only analytics rendering and retain pure analytics tests for correction.
- If documentation and runtime disagree, do not release; restore canonical documents to accurately describe the v0.4 baseline or the verified partial state.
- No schema migration, database rollback, or data conversion is required because v0.5 adds no persistence and does not rewrite v0.4 records.
- After any rollback, run the complete v0.4 regression suite and Streamlit startup check.

## 19. Proposed implementation milestones

### Milestone 0 — Design review and explicit approval (complete)

- Review this roadmap.
- Approve or revise the analytics scopes, evidence minimum, thresholds, conflict policy, invalid-record policy, and UI placement.
- Make no application changes until approval is explicit.

### Milestone 1 — Pure input validation and round analytics (complete)

- Add `analytics.py` with source-record validation, percentage helpers, and `RoundAnalytics` construction.
- Add exact unit tests for empty, valid, partial, malformed, and non-mutating input behavior.
- Do not change Streamlit or v0.4 adaptive rules.

### Milestone 2 — Aggregate accuracy and confidence analytics (complete)

- Add current-topic, overall-session, per-topic, per-difficulty, and topic-difficulty aggregation.
- Implement weighted accuracy, mean round accuracy, ranges, comparisons, confidence coverage, and category aggregation.
- Add grouping, calculation, ordering, and boundary tests.

### Milestone 3 — Pattern, strength, and weakness summaries (complete)

- Add v0.4 signal frequency, recent-signal repetition, accuracy direction, and difficulty-aware evidence.
- Add evidence minimums, strength/weakness rules, mixed conflict handling, stable ordering, and insufficient-evidence results.
- Add threshold and conflict tests.

### Milestone 4 — Non-fatal session integration (complete)

- Integrate pure analytics with existing `adaptation_records` after v0.4 round recording.
- Preserve idempotent round recording, Retry, Home, and explicit recommendation application.
- Add integration tests proving topic isolation, overall aggregation, rerun safety, reset behavior, and fail-open behavior.

### Milestone 5 — Additive Learning Analytics UI (complete)

- Add latest-round, current-topic, overall-session, strength/weakness, and expandable detail sections.
- Add Streamlit tests for rendering, labels, insufficient evidence, and preserved v0.4 controls.
- Confirm analytics adds no action-producing controls.

### Milestone 6 — Full verification and canonical documentation alignment (complete)

- Run the complete automated suite.
- Verify Streamlit startup and controlled manual flows.
- Verify no out-of-scope behavior, dependency, storage, or network use was introduced.
- Update README, changelog, versioned roadmap, architecture, master design, and module specification to match verified implementation.
- Prepare version and release notes only with separate release-preparation approval.
- Do not commit, push, tag, release, or deploy.

## Approved design decisions

Implementation approval accepted these roadmap defaults:

1. Approve or revise the minimum of 2 rounds and 10 answered questions for a topic-and-difficulty strength or weakness label.
2. Approve reuse of the v0.4 thresholds: 85% accuracy and 60% supported success for strengths; below 60% accuracy or at least 20% confident errors for weaknesses.
3. Approve the proposed mixed-evidence policy instead of giving weakness automatic precedence.
4. Approve skipping individually invalid analytics records with issue counts, rather than failing the entire analytics view.
5. Approve showing at most three strengths and three weaknesses in the concise view while retaining full detail tables.
6. Confirm that “overall” means all records currently retained in the active Streamlit session and that v0.4 Home clearing behavior remains unchanged.
7. Confirm that the first v0.5 UI remains embedded after the completed-round summary rather than becoming a separate dashboard page.

These decisions are implemented as deterministic analytics policy. Any later change requires a new design review because it can change learner-facing classifications.
