# Module Specification

## Scope

This specification describes the implemented v0.5 working tree. Most runtime responsibilities remain in `app.py`; deterministic adaptive rules are separated into `adaptive.py`, and deterministic Learning Analytics are separated into `analytics.py`.

## Configuration module

Functions: `load_local_env`, `get_secret_value`, `get_api_key`, `get_model`

Responsibilities:

- Load local `.env` values without replacing existing environment variables.
- Read Streamlit Secrets without breaking local execution.
- Resolve the API key from environment then Streamlit Secrets.
- Resolve the model from environment, Streamlit Secrets, then the default.

The module must not hardcode credentials or expose them in rendered output.

## Difficulty and prompt module

Functions: `get_difficulty_rules`, `get_quality_difficulty_rules`, `build_prompt`

Responsibilities:

- Represent Easy, Normal, Hard, and Nightmare generation guidance.
- Apply the v0.3.1 quality distinctions.
- Insert the topic, question count, and selected difficulty into the prompt.
- Declare the JSON response contract and v0.3 exclusions.

`get_quality_difficulty_rules` is the active rule source used by `build_prompt`. The older difficulty-rule function remains implemented and must not be represented as active prompt behavior.

## API integration module

Functions: `extract_text`, `build_api_error_message`, `should_try_api_fallback`, `generate_lesson`

Responsibilities:

- Create the OpenAI client with resolved configuration.
- Make the primary Responses call.
- Classify the first failure before any fallback.
- Make at most one chat-completions fallback when classified as retryable.
- Extract response text across the supported response shapes.
- Parse and validate the lesson before returning it.
- Add selected difficulty and requested count metadata to valid lesson data.

## Parsing and validation module

Functions: `parse_json_response`, `build_response_data_error`, `validate_lesson`, `validate_topic_input`

Responsibilities:

- Parse plain, fenced, or lightly wrapped JSON.
- Reject missing or invalid lesson fields.
- Enforce supported question counts.
- Preserve short generated CBT lists with a notice.
- Truncate excess generated questions with a notice.
- Require exactly four non-empty, distinct choices per question.
- Require an integer answer index from 0 through 3.
- Require a non-empty explanation.
- Trim and constrain topic input.

The validator mutates lesson data only for question-count normalization and associated notices.

## Scoring module

Function: `is_correct_answer`

Contract:

```text
selected_index == answer_index → correct
selected_index != answer_index → incorrect
```

The scoring decision must never depend on choice text or its position found through a text search.

## Session-state module

Functions: `init_state`, `reset_round_state`, `reset_learning_state`, `normalize_round_state`

Responsibilities:

- Initialize all required state fields.
- Reset round answers, position, feedback, and completion state.
- Increment the round identifier so Streamlit widget keys are fresh.
- Clear the lesson during a home reset.
- Discard malformed or out-of-range state before rendering.

## Presentation module

Functions: `render_learning_status`, `render_lesson`, `render_cbt`, `render_current_feedback`, `render_round_summary`, `main`

Responsibilities:

- Render the generation form and configured learning flow.
- Disable generation while a request is in progress.
- Render validated lesson content.
- Present one CBT question at a time.
- Store a submitted answer by index and render feedback.
- Calculate and display correct count, wrong count, accuracy, wrong-answer details, and explanations.
- Provide retry and home actions.

## Current test module

File: `tests/test_app_quality.py`

The current tests cover:

- Three supported JSON response shapes
- Question-count truncation and notice creation
- Invalid answer-index rejection
- Duplicate-choice rejection
- Index-based scoring with repeated display text
- Retryable and non-retryable API error examples
- Required v0.3.1 Hard and Nightmare prompt phrases

The suite does not currently claim live API, full Streamlit UI, browser, persistence, performance, or security integration coverage.

## Adaptive rule module

File: `adaptive.py`

Responsibilities:

- Normalize optional confidence without converting missing data into low confidence.
- Classify correctness-confidence evidence.
- Build Round Status counts and percentages without mutating input records.
- Produce compatible Learning Pattern signals using approved thresholds.
- Recommend a bounded next difficulty without applying it.
- Recommend advisory recovery priority and relative interval wording.
- Include human-readable evidence and non-autonomy statements.

The module is pure Python and has no Streamlit, OpenAI, persistence, scheduling, or notification dependency.

## v0.4 session integration

Functions in `app.py`: `normalize_topic_key`, `confidence_input_to_value`, `calculate_learning_progress`, `record_completed_round`, `render_adaptive_summary`, `apply_pending_difficulty_recommendation`

Responsibilities:

- Group completed summaries by normalized topic within the active session.
- Compare the latest two same-topic round accuracies.
- Capture optional confidence without changing the lesson JSON contract.
- Render adaptive advice after the complete v0.3.1 result.
- Fail non-fatally when adaptive analysis cannot be produced.
- Queue and explicitly apply a recommended selector value without starting generation.
- Clear adaptive state on Home.

## Learning Analytics module

File: `analytics.py`

Public functions: `percentage`, `build_round_analytics`, `normalize_adaptation_records`, `build_aggregate`, `build_evidence_summaries`, `build_learning_analytics`

Responsibilities:

- Consume v0.4 completed adaptive summaries without mutating them.
- Validate required round fields and normalize optional analytics evidence.
- Skip duplicate or unusable records independently with stable issue codes.
- Produce versioned Round Analytics.
- Calculate weighted accuracy, mean round accuracy, totals, ranges, and ordered same-topic changes.
- Aggregate current-topic, overall-session, topic, difficulty, confidence, answer-pattern, and v0.4 signal evidence.
- Produce deterministic learning summaries.
- Produce evidence-qualified strength, weakness, mixed, and insufficient-evidence structures.
- Expose stable matched-rule names and quantitative fields for later extension without calculating a Weakness Score or making a learning decision.

The module has no Streamlit, OpenAI, database, persistence, scheduling, notification, Living OS, or autonomous-action dependency.

## v0.5 presentation integration

Functions in `app.py`: `_format_analytics_percentage`, `_analytics_round_rows`, `_analytics_aggregate_rows`, `render_learning_analytics`

Responsibilities:

- Render analytics only after the complete v0.4 result and adaptive guidance.
- Show latest-round, current-topic, overall-session, accuracy, confidence, pattern, and strength/weakness summaries.
- Label weighted accuracy separately from mean round accuracy.
- Keep detailed round/topic/difficulty evidence in expanders.
- Add no action-producing analytics control.
- Catch analytics errors and preserve every v0.4 result and navigation control.

## v0.5 test modules

- `tests/test_analytics.py` covers pure calculations, grouping, record order, confidence handling, evidence minimums, policy thresholds, duplicate/invalid records, non-mutation, and learning summaries.
- `tests/test_streamlit_v05.py` covers additive rendering, metric reconciliation, optional confidence, absence of analytics actions, Home compatibility, and non-fatal analytics failure.

## Future module reservation

Weakness Score, Learning Decision Engine behavior, new Recovery Priority behavior, Learning Timeline, Knowledge Retention, durable learner profiles, recovery-content generation, database, background scheduling, notifications, Living OS integration, and autonomous actions have no v0.5 module contract and must not be implemented without later approval.
