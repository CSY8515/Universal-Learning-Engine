# Module Specification

## Scope

This specification describes the implemented v0.8 Pack Runtime working tree on the preserved v0.7 baseline. Existing learning-runtime responsibilities remain in `app.py`; deterministic adaptive rules remain in `adaptive.py`, deterministic Learning Analytics remain in `analytics.py`, and all expansion responsibilities remain isolated in the `expansion` package.

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

## Core quality test module

File: `tests/test_app_quality.py`

The core quality tests cover:

- Three supported JSON response shapes
- Question-count truncation and notice creation
- Invalid answer-index rejection
- Duplicate-choice rejection
- Index-based scoring with repeated display text
- Retryable and non-retryable API error examples
- Required v0.3.1 Hard and Nightmare prompt phrases

The complete suite also covers adaptive rules, analytics, Streamlit v0.4/v0.5
regression behavior, v0.6 failure boundaries, answer immutability, and analytics
cache reuse. Release review additionally verifies the rendered landing UI and
browser console. It does not claim a paid live API call, persistence integration,
load benchmarking, or security penetration testing.

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
- Expose stable matched-rule names and quantitative fields without calculating a Weakness Score or making a learning decision.

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

## v0.6 reliability integration

Functions in `app.py`: `configure_logging`, `extract_text`,
`parse_json_response`, `normalize_choice_text`, `user_facing_error_message`,
`should_try_api_fallback`, `is_correct_answer`, and
`get_cached_learning_analytics`.

Responsibilities:

- Accept one plain, fenced, or lightly wrapped JSON lesson object.
- Reject ambiguous objects, boolean indices, and normalized duplicate choices.
- Lock submitted answer and confidence evidence during feedback.
- Bound API work with explicit timeout, no hidden SDK retry, and at most one
  approved compatibility fallback.
- Separate safe learner errors from operational failure metadata.
- Invalidate derived analytics cache data whenever completed evidence changes.
- Preserve all v0.5 module contracts and user-visible flow.

`tests/test_v06_quality.py` and the preserved suites cover the v0.6 reliability
contract. The complete local Python 3.13.14 suite contains 57 passing tests.
GitHub Actions is configured for Python 3.10 and 3.13.

## v0.7 common interface module

Files: `expansion/interfaces.py`, `expansion/errors.py`

Responsibilities:

- Define immutable `PackManifest` exact identity and interface compatibility.
- Define lifecycle-only `ExpansionPack` callbacks.
- Validate packs without executing lifecycle code.
- Provide stable Expansion Platform exception types.

## Pack Registry module

File: `expansion/registry.py`

Responsibilities:

- Store pack instances by exact `(pack_id, version)` in process.
- Reject duplicate exact identities and ambiguous version selection.
- Return immutable manifests and deterministic version listings.
- Add no database, discovery, or remote acquisition behavior.

## Pack Loader module

File: `expansion/loader.py`

Responsibilities:

- Load only registered, compatible pack instances.
- Invoke lifecycle callbacks once for valid state transitions.
- Preserve unloaded state after load failure and loaded state after unload failure.

## Pack Manager and Expansion API modules

Files: `expansion/manager.py`, `expansion/api.py`

Responsibilities:

- Coordinate install, remove, load, unload, lookup, and exact version listing.
- Unload a loaded pack successfully before unregistering it.
- Expose immutable `PackStatus` values through the Expansion API facade.
- Remain independent of Streamlit, OpenAI, adaptive rules, and analytics.

## Living OS Integration Interface module

File: `expansion/living_os.py`

Responsibilities:

- Define connect, disconnect, and connected-state members only.
- Accept an Expansion API binding without providing a concrete adapter.
- Perform no Living OS, network, command, authentication, or synchronization
  behavior.

## v0.7 test module

File: `tests/test_expansion_platform.py`

The tests cover manifests, common-interface validation, exact version identity,
Registry ambiguity, lifecycle transitions and failures, Manager removal,
Expansion API behavior, and the abstract Living OS boundary.

## v0.8 executable contract

File: `expansion/interfaces.py`

Responsibilities:

- Preserve `ExpansionPack` and interface version `0.7` unchanged.
- Define optional `ExecutableExpansionPack.execute(session)` and
  `terminate(session)` callbacks.
- Add no execution result schema, learning hook, UI hook, or external transport.

## Pack Runtime and Session module

File: `expansion/runtime.py`

Public classes: `PackRuntime`, `PackSession`, `PackSessionStatus`

Responsibilities:

- Start only an installed, loaded, executable exact pack version.
- Own at most one active session per exact identity.
- Generate opaque session ids and separate state dictionaries.
- Invoke execution and termination callbacks synchronously and once per valid
  transition.
- Publish no active session after execution failure.
- Preserve the active session after termination failure.
- Return immutable status values without exposing private session state.
- Return deterministic session listings.

## v0.8 Loader, Manager, and API integration

Files: `expansion/loader.py`, `expansion/manager.py`, `expansion/api.py`

Responsibilities:

- Reject reentrant pack-level lifecycle transitions.
- Require loaded state before runtime execution.
- Terminate an exact active session before unload or removal.
- Expose additive `start`, `stop`, `session`, and `sessions` methods.
- Preserve every v0.7 method and return type.
- Add no Streamlit, OpenAI, adaptive, analytics, network, IPC, filesystem,
  synchronization, command, Living OS, persistence, or background dependency.

## v0.8 test module

File: `tests/test_pack_runtime.py`

The tests cover legacy-pack compatibility, loaded-state requirements, immutable
status, start/stop identity, single-session enforcement, failure cleanup,
termination-state preservation, unload/remove order, exact-version and
cross-pack state separation, private-state non-exposure, and Loader reentrancy.
The complete suite contains 80 tests: 68 preserved tests and 12 v0.8 tests.
