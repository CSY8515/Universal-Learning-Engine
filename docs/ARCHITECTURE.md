# Architecture

## Current architecture

Universal Learning Engine v1.0 preserves the single-process Streamlit learning application and independent in-process Expansion Platform. `app.py` remains the composition, configuration, OpenAI, validation, session, and compatibility boundary. `ui/` owns the official theme, navigation, Dashboard, Review, and reusable presentation components. `adaptive.py` contains pure deterministic adaptive rules. `analytics.py` contains pure deterministic Learning Analytics. The `expansion` package preserves the common interface, Registry, Loader, Manager, API, connection-only Living OS boundary, execution layer, and shared transition guard.

```text
User
  │ topic, count, difficulty, answers
  ▼
Streamlit UI
  │ validated generation request
  ▼
Prompt builder ──► OpenAI API
                     │ JSON text
                     ▼
               Parser and validator
                     │ validated lesson
                     ▼
              Streamlit session state
                     │
                     ▼
             CBT, feedback, summary
```

After a round completes, validated answer evidence flows through `adaptive.py` to produce Round Status, pattern signals, difficulty advice, and recovery advice. There is no database, background worker, external analytics system, account system, or durable learner profile.

The retained completed summaries then flow read-only through `analytics.py`. It normalizes valid records independently and produces latest-round, current-topic, overall-session, topic, difficulty, confidence, pattern, and strength/weakness views. Analytics do not call OpenAI, modify adaptive records, select a learning action, or persist a second copy of state.

## Runtime boundaries

### Presentation boundary

Streamlit renders topic and configuration inputs, generated lesson sections, CBT controls, feedback, progress, and the round summary. UI rendering reads and updates session state but does not persist it outside the active session.

### Generation boundary

The application builds one text prompt from the topic, requested question count, and difficulty. The model is instructed to return only the defined JSON lesson structure and not to introduce recovery, analytics, dashboard, decision-engine, or expansion-pack content.

### External API boundary

The OpenAI client receives the resolved API key and model. The Responses interface is primary. A chat-completions call is a conditional compatibility fallback, not an unconditional retry.

### Validation boundary

All model output crosses a parser and lesson validator before it becomes session data. This boundary owns JSON extraction, required-field checks, question-count normalization, choice validation, duplicate detection, answer-index validation, and explanation validation.

### State boundary

Streamlit session state contains:

| Key | Purpose |
|---|---|
| `lesson` | Current validated generated lesson |
| `answers` | Selected choice index by question index |
| `current_question_index` | Current CBT position |
| `current_feedback` | Feedback for the active question |
| `round_finished` | Whether summary mode is active |
| `cbt_round_id` | Separates widget keys between retries |
| `is_generating` | Prevents repeated generation-button activation |
| `answer_confidence` | Optional reported confidence by question index |
| `adaptation_records` | Completed summaries grouped by session-local topic key |
| `latest_adaptive_summary` | Current advisory output rendered after the round result |
| `adaptation_error` | Non-fatal analysis failure state |
| `pending_recommended_difficulty` | Explicitly queued selector update |
| `analytics_cache` | Revision-bound derived v0.5 analytics output |
| `analytics_revision` | Invalidates derived analytics when source evidence changes |
| `active_view` | Current Dashboard, Learning, or Review workspace |
| `pending_view` | Queued view change applied before navigation widget creation |
| `navigation_explicit` | Distinguishes explicit Dashboard navigation from first lesson entry |

State normalization removes invalid answers, bounds the active index, repairs invalid flags, and clears malformed feedback.

## Configuration architecture

- `.env` may populate local environment variables.
- Existing environment variables are not overwritten by the fallback `.env` loader.
- Streamlit Secrets are consulted when an environment value is absent.
- `OPENAI_API_KEY` has no built-in default.
- `OPENAI_MODEL` defaults to `gpt-4.1-mini`.
- `.streamlit/config.toml` defines presentation theme only.

## Error behavior

- Missing API configuration and dependencies produce controlled runtime errors.
- Invalid model JSON and invalid lesson data produce user-facing validation errors.
- Authentication, permission, quota, billing, payment, and rate-limit failures do not trigger a second API call.
- Likely transient connection or service failures may trigger one fallback call.

## Security and privacy boundary

API secrets are excluded from tracked source through `.gitignore`. The repository includes examples containing placeholders only. The current application does not intentionally persist learner content, but topics and generated requests are sent to the configured OpenAI API.

## v0.4 adaptive boundary

Adaptive analysis occurs only after the existing scoring path and never bypasses input, output, or scoring validation. The pure adaptive module receives completed-round evidence and returns advisory dictionaries without Streamlit or API dependencies.

The interface applies a recommended difficulty through a queued state value before the selector widget is created. This avoids autonomous generation and preserves explicit learner control. Learning Timeline, Knowledge Retention, and Decision Engine capabilities remain outside this architecture.

## v0.5 analytics boundary

Analytics execute only after the existing v0.4 result and adaptive summary paths. `adaptation_records` remains the sole completed-round source of truth. Analytics outputs are derived during rendering and are not stored in a database. v0.6 may retain one revision-bound session cache of derived output; it is invalidated whenever a completed record is added or Home clears the source records.

The pure module owns:

- Required-field validation and independent invalid-record exclusion
- Versioned Round Analytics dictionaries
- Weighted accuracy, round-average accuracy, totals, ranges, and ordered same-topic comparisons
- Confidence coverage and correctness-confidence aggregation
- Topic, difficulty, current-topic, and overall retained-session summaries
- v0.4 signal frequency and recent same-topic repetition
- Evidence summaries with stable rule names and quantitative fields

Strength and weakness classification is limited to topic-and-difficulty groups with at least two rounds and ten answered questions. It does not calculate a Weakness Score or make a decision. The UI renders at most three concise strengths and weaknesses and keeps detailed evidence available.

Analytics failures are caught at the presentation boundary. The complete v0.4 result, adaptive guidance, Retry, Home, and recommendation controls remain available. Existing v0.4 Recovery Priority is preserved but not extended by v0.5.

Overall analytics cover only records still present in the active Streamlit session. Home clears `adaptation_records`, so all derived analytics also disappear. No timestamp, cross-session timeline, retention model, scheduler, notification, Living OS integration, or autonomous action exists.

## v0.6 reliability boundary

The lesson schema and UI flow remain unchanged. Model text must resolve to one
unambiguous JSON object, indices must be exact integers rather than booleans, and
submitted answer evidence is locked while feedback is active. The OpenAI client
uses an explicit timeout with SDK retries disabled so the application owns the
documented single compatibility fallback decision.

Operational logs contain event metadata and failure types only. They do not log
API keys, prompts, generated lesson text, answer text, or raw learner content.
Unexpected exceptions are logged by type and mapped to a stable learner-facing
message.

## v0.7 expansion boundary

The Expansion Platform is imported and used independently from `app.py`,
`adaptive.py`, and `analytics.py`.

```text
ExpansionAPI
  -> PackManager
       -> PackRegistry (installed exact versions, in process)
       -> PackLoader (loaded exact versions and lifecycle calls)

LivingOSIntegrationInterface
  -> connection contract to ExpansionAPI only
```

Pack identity is the exact `(pack_id, version)` pair. Multiple versions may be
installed, but an operation without a version is rejected when selection would
be ambiguous. Pack lifecycle callbacks add no learning hook and cannot bypass
lesson validation, scoring, adaptive rules, analytics, or the existing UI.

Registry and Loader state is process-local. There is no filesystem discovery,
database, remote repository, dependency resolution, automatic update, or
background worker. The Living OS boundary has no concrete implementation and
performs no communication or Living OS action.

## v0.8 Pack Runtime boundary

```text
ExpansionAPI
  -> PackManager
       -> PackRegistry (installed exact versions)
       -> PackLoader (pack-level loaded state)
       -> PackRuntime (execution state)
            -> PackSession (one private state object per exact identity)
            -> ExecutableExpansionPack.execute / terminate

LivingOSIntegrationInterface (unchanged abstract boundary only)
```

The existing interface version remains `0.7`. A lifecycle-only v0.7 pack keeps
all management behavior. An `ExecutableExpansionPack` adds synchronous
`execute(session)` and `terminate(session)` callbacks and may run only while its
exact version is installed and loaded.

One exact identity has at most one active session. Sessions have opaque ids,
immutable ownership fields, and separate private mutable state dictionaries.
Public status snapshots never expose this state. Runtime start/stop failures are
isolated by exact identity; a failed termination leaves that session active.
Unload and removal terminate an active session before pack-level unload.

The runtime passes no learning-engine, Manager, API, Living OS, or external
transport reference to callbacks. It is synchronous and in process: there are no
threads, workers, subprocesses, network calls, IPC, shared files,
synchronization, commands, persistence, discovery, or new UI. Reference
separation is not an operating-system security sandbox against malicious pack
code.

## v0.9 stability boundary

```text
PackManager
  -> PackRegistry (installed authority)
  -> PackLoader (loaded authority)
       -> shared internal transition guard
  -> PackRuntime (active-session authority)
       -> shared internal transition guard
```

The transition guard records only conflicting lifecycle/runtime transitions and active runtime identities. It does not duplicate Registry, Loader, or Runtime state. It prevents direct unload of a running Pack and rejects lifecycle/runtime reentrancy for the same exact identity. Different exact identities remain independent.

`PackLoadError` and `PackExecutionError` expose stable operation and exact-identity context. `PackExecutionError.cleanup_failed` records best-effort cleanup failure. Messages and logs do not expose callback exception text or session state.

Streamlit initialization repairs malformed session metadata before use. Completed-round evidence and derived analytics revision/cache changes are prepared before source replacement. Retry removes CBT and confidence widget state. Learning data remains session-only and Home retains its clearing behavior.

The v0.9 boundary adds no new UI, learning rule, persistence, external integration, transport, background execution, or v1.0 capability.

## v1.0 presentation boundary

```text
app.py composition root
  -> ui.theme (trusted static CSS only)
  -> ui.navigation (session-safe major view selection)
  -> ui.dashboard (read-only session evidence)
  -> existing Learning and Review renderers
  -> adaptive.py / analytics.py (unchanged policy authorities)
```

Dashboard is the initial Home view. Selecting Dashboard never clears source
evidence. Home reset queues a Dashboard transition and preserves the established
clear-all learning-data contract. Only the selected major view is rendered.

Static brand markup and `assets/ule.css` are repository-controlled. Topics,
generated content, answers, secrets, provider errors, and Pack state are not
interpolated into unsafe HTML. Dashboard makes no external request and stores no
second copy of analytics evidence.

The v1.0 boundary changes no lesson schema, scoring rule, adaptive threshold,
analytics classification, Expansion state authority, Pack callback, public API,
or interface version.
