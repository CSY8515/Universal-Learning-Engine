# Module Specification

## Scope

This specification describes the implemented v1.06 application on the preserved
v1.03 learning-flow and v0.9 Expansion runtime baselines. Learning-runtime and
BYOK coordination remain in `app.py`; presentation responsibilities are
separated into `ui/`; deterministic adaptive rules remain in `adaptive.py`,
deterministic Learning Analytics remain in `analytics.py`, and all expansion
responsibilities remain isolated in the `expansion` package.

## Configuration module

Functions: `load_local_env`, `get_secret_value`, `get_api_key`, `get_model`,
`normalize_api_key_input`, `register_api_key`, `delete_api_key`

Responsibilities:

- Load local `.env` values without replacing existing environment variables.
- Read Streamlit Secrets without breaking local execution.
- Accept API keys only through explicit user entry in Management.
- Retain the key only in current Streamlit session server memory.
- Register, replace, and delete the key without writing it to World state,
  backups, logs, repository configuration, commits, or releases.
- Resolve the model from environment, Streamlit Secrets, then the default.

The module must not hardcode credentials or expose them in rendered output.

## Localization and user-data management module

Functions in `world_state.py`: `world_label`, `difficulty_label`,
`challenge_mode_label`, `resource_kind_label`, `localized_record_text`,
`deletion_catalog`, `delete_selected_records`, `clear_record_category`,
`clear_all_records`, `reset_user_data`

Responsibilities:

- Keep persisted World, difficulty, and challenge identifiers compatible while
  presenting Korean learner terminology.
- Build deletion choices without displaying storage identifiers.
- Remove selected records and directly dependent generated evidence.
- Preserve Management subjects and settings for all-record deletion.
- Restore complete durable defaults for full reset.
- Never delete or initialize existing records during normal state
  normalization or localization.

Functions in `app.py`: `localize_system_text`,
`render_user_data_management`, `reset_transient_learning_state`

Responsibilities:

- Localize existing system-generated labels at render time.
- Keep destructive controls disabled until explicit confirmation.
- Clear obsolete session-only view state after durable records are removed.
- Present sanitized Korean errors without raw parser, provider, or storage
  details.

## Difficulty and prompt module

Functions: `get_quality_difficulty_rules`, `build_prompt`

Responsibilities:

- Represent Easy, Normal, Hard, and Nightmare generation guidance.
- Apply the v0.3.1 quality distinctions.
- Insert the topic, question count, and selected difficulty into the prompt.
- Declare the JSON response contract and v0.3 exclusions.

`get_quality_difficulty_rules` is the single active rule source used by `build_prompt`. The inactive pre-v0.3.1 duplicate was removed in v1.0 without changing generated prompt behavior.

## API integration module

Functions: `extract_text`, `build_api_error_message`, `should_try_api_fallback`,
`create_openai_client`, `test_openai_connection`, `generate_lesson`,
`generate_ai_world_text`

Responsibilities:

- Create the OpenAI client with resolved configuration.
- Test the user key with one bounded Responses request.
- Make the primary Responses call.
- Classify the first failure before any fallback.
- Make at most one chat-completions fallback when classified as retryable.
- Extract response text across the supported response shapes.
- Parse and validate the lesson before returning it.
- Add selected difficulty and requested count metadata to valid lesson data.
- Execute AI question, explanation, recommendation, and summary actions.
- Sanitize configuration and provider errors without exposing key material,
  raw payloads, stack traces, or internal state.

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

## v0.9 shared transition-state module

File: `expansion/_state.py`

Responsibilities:

- Reject same-identity overlap between Loader lifecycle and Runtime transitions.
- Track active runtime identities only for conflict validation.
- Own no installed, loaded, Pack Session, or learner state.
- Remain internal and add no public API.

## v0.9 Runtime, Loader, and error stabilization

Files: `expansion/runtime.py`, `expansion/loader.py`, `expansion/errors.py`

Responsibilities:

- Prevent direct unload of an active Runtime identity.
- Reject cross-layer reentrant start, stop, load, and unload operations.
- Preserve state after failed execution, cleanup, termination, load, or unload.
- Expose stable operation and exact-identity error attributes without callback payloads.
- Record best-effort execute cleanup failure using `cleanup_failed`.

## v0.9 session integration

File: `app.py`

Responsibilities:

- Repair invalid session containers, flags, revisions, cache values, and stable error codes.
- Prepare completed-round records and analytics invalidation before replacing source state.
- Avoid partial record creation when adaptive analysis fails.
- Remove both CBT and confidence widget keys during round reset.
- Preserve all v0.8 learning behavior and session-only boundaries.

## v0.9 verification module

Files: `tests/test_v09_stability.py`, `.coveragerc`, `.github/workflows/tests.yml`

The focused tests cover cross-layer reentrancy, direct Loader bypass prevention, structured cleanup failure, session repair, atomic recording, and widget cleanup. CI compiles the complete runtime, measures branch coverage, and verifies the headless Streamlit health endpoint on Python 3.10 and 3.13.

## Historical v1.0 presentation modules

Modules: `ui.theme`, `ui.navigation`, `ui.components`, `ui.dashboard`,
`ui.results`

`ui.components`, `ui.dashboard`, and `ui.results` were removed in v1.03 after
the nine-World runtime superseded their Dashboard and Review paths.

Responsibilities:

- Load repository-owned static CSS once without dynamic content interpolation.
- Render Dashboard, Learning, and Review navigation.
- Read current lesson, adaptive summary, and cached analytics without mutation.
- Present compact metrics, controlled empty states, and recent session evidence.
- Preserve explicit recommendation application and Home/Retry state contracts.
- Render responsive, focus-visible, and reduced-motion UI rules.

## v1.0 verification modules

`tests/test_streamlit_v10.py` covers Dashboard Home, navigation, session
preservation, evidence rendering, Review empty state, and metadata repair.
`tests/test_v10_ui_contract.py` covers official theme, static-style safety,
responsive rules, focus, and reduced motion. `tests/test_v10_public_api.py`
freezes the recommended Expansion facade operations and interface compatibility.

## v1.02 World state module

Module: `world_state.py`

Responsibilities:

- Normalize, load, atomically save, export, and restore versioned World state.
- Convert completed Learning and Challenge rounds into shared evidence.
- Produce and execute Recovery Sessions from retained wrong-answer evidence.
- Connect completed learning to Library resources and managed subjects.
- Store Planner goals and dated World schedules.
- Store Library notes and perform bounded resource/note search.
- Retain explicit AI question, recommendation, and summary history.
- Derive study time, level, achievements, long-term statistics, and reports.
- Keep persistence and internal identifiers out of learner-facing presentation.

## v1.02 presentation integration

`app.py` preserves the existing Streamlit primitives and static theme while
exposing the nine functional Worlds. No CSS, World background, Hover, Animation,
Glass, or visual redesign work is part of v1.02.

## v1.03 World flow state module

Module: `world_state.py`

Responsibilities:

- Upgrade v1.02 state into the normalized v1.03 schema without losing records.
- Store Recovery records, history, duration, and Challenge recommendations.
- Store independent Challenge Sessions and Results with source linkage.
- Build integrated World Analytics for AI, My Learning, and Report.
- Convert one AI Recommendation into one idempotent Planner goal and Learning
  schedule after explicit learner action.
- Store normalized Library resources with source World and source identity.
- Transfer connected topics into Management subjects.
- Derive all-World study time, points, level, achievements, and long-term
  counts.
- Generate the integrated Learning, Recovery, Challenge, Analytics, AI,
  Planner, Library, Management, and My Learning report.

## v1.03 application integration

Module: `app.py`

Responsibilities:

- Apply queued Recovery Challenge context before Challenge widgets render.
- Apply queued Planner topics before Learning widgets render.
- Start Challenge Sessions only after lesson generation succeeds.
- Render Recovery History, Recovery Recommendation, and Challenge History.
- Connect explicit AI Recommendation actions to Planner.
- Render generic multi-source Library records.
- Render integrated Analytics, My Learning, and Report evidence.
- Keep OpenAI calls learner triggered and preserve the existing error boundary.

## v1.03 presentation modules

Modules: `ui.theme`, `ui.navigation`

Responsibilities:

- Preserve the repository-owned static theme without modification.
- Render the existing nine-World navigation control.
- Add no Dashboard, Review, legacy callback routing, dynamic CSS, or new visual
  system.

## v1.03 verification modules

Files: `tests/test_world_integration_v103.py`,
`tests/test_streamlit_v103.py`, `tests/_streamlit_case.py`

The tests cover Recovery-to-Challenge transfer, independent Challenge results,
AI-to-Planner records, Planner-to-Learning topic transfer, multi-source Library
storage, integrated Analytics/My Learning/Report evidence, v1.02 state
normalization, and isolated Streamlit persistence.

## v1.04 BYOK and AI integration

Modules: `app.py`, `world_state.py`

Responsibilities:

- Render registration, change, deletion, and connection-test controls inside
  the existing Management World.
- Disable only AI-dependent controls when no user key exists.
- Store question, explanation, recommendation, and summary results through the
  existing AI history and Library path.
- Preserve explicit AI Recommendation to Planner conversion and downstream
  Learning, My Learning, and Report integration.
- Contain API failures inside the affected AI action.
- Keep the key outside all normalized and durable data.

## v1.04 verification modules

Files: `tests/test_byok_v104.py`, `tests/test_streamlit_v104.py`

The tests cover input normalization, registration/change/deletion, bounded
Responses connection testing, safe failure messages, no-key AI isolation,
explanation generation, Library integration, and the absence of key material
from normalized World state.

## v1.05 end-to-end verification modules

Files: `tests/test_e2e_v105.py`, `tests/test_streamlit_e2e_v105.py`

Responsibilities:

- Carry normalized evidence through all nine Worlds and the integrated Report.
- Verify supported create/read/update/delete, backup, and restore behavior.
- Exercise learner-visible Learning, Challenge, AI, Planner, Library, and
  Management controls through Streamlit's application test interface.
- Verify registered-key behavior with an isolated OpenAI-compatible client.
- Verify no-key operation and sanitized provider failures without disabling
  non-AI Worlds.
- Inspect all World screens for raw internal output or unfinished labels.

These modules add no production API, storage field, UI control, or runtime
dependency.

## v1.06 localization and user-data verification modules

File: `tests/test_localization_v106.py`

Responsibilities:

- Verify Korean display across all nine World entries.
- Reject learner-visible developer markers and unfinished labels.
- Verify existing system-title localization without rewriting user-authored
  content.
- Verify selective deletion cascades only to dependent generated evidence.
- Verify all-record deletion preserves subjects and settings.
- Verify full reset restores defaults.
- Verify BYOK and record deletion controls remain disabled before explicit
  confirmation.
