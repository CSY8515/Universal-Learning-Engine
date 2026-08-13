# Architecture

## Current architecture

Universal Learning Engine v1.092 preserves the single-process Streamlit learning
application and independent in-process Expansion Platform. `app.py` remains the
composition, configuration, OpenAI, validation, session, and World presentation
boundary. `world_state.py` owns normalized persistent cross-World evidence and
all deterministic World connections. `ui/` owns the official theme,
nine-World navigation, and presentation-only Ultra Brain Theme Contract,
Design Tokens, registries, validated adapter, and Compatibility Layer.
`adaptive.py` and `analytics.py` preserve their pure
deterministic contracts. The `expansion` package preserves the common
interface, Registry, Loader, Manager, API, connection-only Living OS boundary,
execution layer, and shared transition guard.

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

After a round completes, validated answer evidence flows through `adaptive.py`
and into the normalized local World state. The application has durable local
single-user World history but no database server, background worker, external
analytics system, or account system.

The retained completed summaries then flow read-only through `analytics.py`. It normalizes valid records independently and produces latest-round, current-topic, overall-session, topic, difficulty, confidence, pattern, and strength/weakness views. Analytics do not call OpenAI, modify adaptive records, select a learning action, or persist a second copy of state.

## Runtime boundaries

### Presentation boundary

Streamlit renders topic and configuration inputs, generated lesson sections,
CBT controls, feedback, progress, World records, and the integrated report.
Explicit learner actions persist normalized state through `world_state.py`.

### Generation boundary

The application builds one text prompt from the topic, requested question count, and difficulty. The model is instructed to return only the defined JSON lesson structure and not to introduce recovery, analytics, dashboard, decision-engine, or expansion-pack content.

### External API boundary

The OpenAI client receives only the current user's session-memory BYOK value and
the resolved model. The Responses interface is primary. A chat-completions call
is a conditional compatibility fallback for validated lesson generation, not an
unconditional retry. Connection testing and AI World actions use Responses only.

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
| `active_view` | Current one of nine World workspaces |
| `pending_view` | Queued view change applied before navigation widget creation |
| `pending_learning_topic` | Planner-selected topic waiting to enter Learning |
| `pending_challenge` | Recovery recommendation waiting to enter Challenge |
| `active_challenge_source_recommendation_id` | Recovery source linked to the next Challenge Session |
| `world_data` | Active normalized v1.04 cross-World evidence; never contains an API key |
| `user_openai_api_key` | Current user's API key in session server memory only |
| `openai_connection_status` | Missing, registered, connected, or failed BYOK state |
| `openai_api_notice` | One-time sanitized BYOK lifecycle notice |

The internal World identifiers and state schema remain stable for compatibility.
The navigation formatter and presentation helpers translate those identifiers
into Korean at the learner boundary. Existing system-generated record labels
are localized during rendering rather than rewriting learner data.

State normalization removes invalid answers, bounds the active index, repairs invalid flags, and clears malformed feedback.

## Configuration architecture

- `.env` may populate non-secret local configuration.
- Existing environment variables are not overwritten by the fallback `.env` loader.
- Streamlit Secrets are consulted for model configuration when an environment value is absent.
- API keys are accepted only through Management and retained in the current
  Streamlit session's server memory.
- No developer-owned environment or Streamlit Secret key is used as a fallback.
- `OPENAI_MODEL` defaults to `gpt-4.1-mini`.
- `.streamlit/config.toml` defines presentation theme only.

## Error behavior

- Missing API configuration and dependencies disable only AI-dependent actions
  or produce controlled AI errors.
- Invalid model JSON and invalid lesson data produce user-facing validation errors.
- Authentication, permission, quota, billing, payment, and rate-limit failures do not trigger a second API call.
- Likely transient connection or service failures may trigger one fallback call.

## Security and privacy boundary

API secrets are accepted only through a password input and retained in
Streamlit session server memory. They are excluded from World evidence,
`.ule_data`, backup export, logs, tracked configuration, commits, and releases.
The deployed app does not use a shared developer key. World evidence is
persisted locally in `.ule_data` after explicit actions; topics and generated
requests are sent to OpenAI only through the explicitly registered user key.

## v1.06 data-management boundary

- Selective deletion accepts only tokens produced by the current normalized
  deletion catalog.
- Deleting a record also removes generated resources, activities, and explicit
  links whose sole source is that record.
- Category deletion uses the same validated selective-deletion path.
- All-record deletion preserves Management subjects and default settings.
- Full reset restores the durable World state to defaults and removes the
  session-only BYOK value.
- Every destructive UI action is disabled until its confirmation gate is met.

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

## v1.02 World integration boundary

```text
Learning / Challenge
  -> completed round
       -> Recovery queue and Recovery Sessions
       -> Analytics and Report
       -> Library learning resource
       -> Management subject list
       -> My Learning time, level, achievements, and statistics

AI <- current lesson and aggregate evidence
Planner -> explicit World navigation
Management -> Expansion status, settings, subjects, backup, and restore
```

`world_state.py` is the single authority for serializable cross-World evidence.
It writes a normalized local state file atomically after explicit learner
actions. Streamlit session state holds the active copy; backup export and restore
use the same validated schema. No World starts another action automatically.
Planner navigation and recommended actions remain learner controlled.

## v1.03 Learning flow integration boundary

```text
Learning
  -> Recovery Record and Recommendation
  -> Challenge Session and Result
  -> integrated Analytics
  -> AI Recommendation
  -> Planner goal and Learning schedule
  -> Learning topic transfer
  -> multi-World Library
  -> Management subjects
  -> My Learning
  -> integrated Report
```

Recovery completion owns the deterministic Challenge recommendation. Challenge
owns independent session and result identity. Integrated Analytics is derived
from the normalized World state and is the evidence supplied to AI. AI output is
stored in Library; an explicit connection creates one idempotent Planner goal
and Learning schedule. Opening that schedule transfers its retained topic into
Learning before the widget is rendered.

Library resources retain source World and source identity. Management subjects
are updated from connected topic evidence. My Learning and Report derive from
the same normalized World state and include all World record categories.

The removed Dashboard, Review, shared presentation helpers, explicit-navigation
metadata, and callback routing are not part of the v1.03 runtime. No background
action, notification, UI redesign, or autonomous learning start is added.

## v1.04 AI and BYOK boundary

Management owns explicit API registration, change, deletion, and connection
testing. The key remains outside normalized World state and all persistence
paths. Losing or deleting it disables lesson generation and AI World execution
without affecting Recovery, Challenge, Analytics, Planner, Library, Management,
My Learning, or Report.

AI owns four learner-triggered actions: question, explanation, recommendation,
and summary. Sanitized provider failures are contained at the AI boundary and do
not expose keys, raw response objects, JSON, stack traces, or internal state.
Successful AI output enters the existing AI history and Library path. An
explicit recommendation connection continues into Planner; Planner continues
into Learning; all resulting records continue into My Learning and Report.

v1.04 changes no theme, layout, World background, Hover, Animation, or Glass
behavior.

## v1.05 validation boundary

v1.05 adds no runtime component and changes no production data flow. Two
verification modules exercise the existing boundaries from the learner-facing
Streamlit controls down to normalized World state and integrated reports.

The pure-state end-to-end case carries one evidence set through Learning,
Recovery, Challenge, Analytics, AI, Planner, Library, Management, My Learning,
and Report. It also verifies the supported goal, schedule, note, subject,
settings, backup, and restore lifecycle.

The Streamlit end-to-end cases drive learner-visible buttons with an isolated
OpenAI-compatible test client, verify the no-key and provider-failure paths,
and inspect every World for prohibited internal output. Actual API-key
acceptance remains an explicit user action through Management and is never
automated from repository configuration.

## v1.06 localization and deletion boundary

The learner-facing layer maps compatible internal identifiers to Korean without
rewriting stored records. Generated system titles from earlier releases are
localized when displayed. Learner-authored content remains unchanged.

`deletion_catalog` exposes opaque UI tokens only to Streamlit controls and maps
them to current normalized records. `delete_selected_records` validates those
tokens against the live catalog before deleting selected records and dependent
generated evidence. Category deletion delegates to the same path. All-record
deletion preserves Management configuration; full reset restores defaults.
Every destructive control is gated in the presentation layer.

## v1.08 operational database boundary

The architecture audit distinguishes learner state from operational evidence:

```text
app.py / world_state.py
  -> existing learner runtime and World JSON (unchanged)

authorized operational producer
  -> DatabaseManager
       -> data validation
       -> explicit Registry classification
       -> non-destructive duplicate control
       -> OperationalDatabase
            -> OperationalRecordRegistry
            -> OperationalDataPlane contract
                 -> SQLiteOperationalDataPlane
                      -> record types
                      -> append-only operational records
                      -> retained report snapshots
       -> pattern and operational analysis
       -> advisory Recommendation
       -> inactive Rule Candidate
       -> inactive Standard Candidate
       -> Operational Report
            -> optional PersonalSecretaryIntegration
                 -> PersonalSecretaryCoreCapability port
```

### Database structure and authority

`OperationalRecordRegistry` is the only classification authority. It contains
the twelve v1.08 operational categories and their default severities. The
Data Plane persists a synchronized record-type table, schema metadata,
operational records, and operational report snapshots. `OperationalDatabase`
coordinates Registry and Data Plane access but performs no analysis.

Operational records are immutable after append. Failure, Error, Incident,
Validation Failure, Execution Failure, Invalid Data, Rejected Decision,
Unresolved Issue, Recovery, and Rollback evidence has no delete, truncate, or
reset contract. Exact duplicate observations remain stored with `duplicate_of`
pointing to the first canonical record. This preserves evidence while allowing
Database Manager to exclude duplicates from canonical counts.

### Database Manager structure and authority

`DatabaseManagerRegistry` declares the fixed v1.08 capabilities: validation,
classification, duplicate control, pattern analysis, operational analysis,
recommendation, rule candidate, standard candidate, and reporting. Database
Manager validates untrusted mappings, redacts values carried under known secret
keys, accepts only Registry categories, and appends through the Database facade.

Analysis is deterministic and bounded. A Recovery or Rollback with the same
correlation identifier resolves an earlier open operational record in report
analysis without mutating the source record. Recommendations and candidates are
advisory outputs only; candidates remain in `candidate` status and cannot
activate a rule or standard.

### Operational reporting and Personal Secretary boundary

Operational Reports aggregate category, severity, status, source, duplicate,
pattern, recommendation, candidate, and unresolved-identifier evidence. Raw
messages, payloads, metadata, API keys, and provider objects are not included.
Each generated report is retained by the Data Plane before optional delivery.

`PersonalSecretaryCoreCapability` is the explicit OS Ecosystem port.
`PersonalSecretaryIntegration` requires a connected implementation and sends a
versioned report envelope under capability id
`universal-learning-engine.operational-reporting`. The adapter adds no transport,
authentication, scheduling, discovery, or Personal Secretary behavior.

The package is not imported by `app.py`. Therefore v1.08 changes no Streamlit
runtime, learner data flow, UI, World state, Learning Engine, Database CRUD,
BYOK, Analytics, Report, Expansion, or Living OS presentation behavior.

## v1.09 UI compatibility boundary

`ui/contracts.py` defines immutable, versioned theme, token, component, and
module contracts. `ui/registry.py` owns exact-ID Theme and UI registries.
`ui/adapter.py` validates the closed host mapping and converts it to the fixed
CSS-variable vocabulary. `ui/interface.py` exposes the stable Ultra Brain host
port and coordinates the registries and adapter.

`ui/theme.py` continues to read the repository-owned stylesheet. Optional host
settings are validated and appended as declaration-only CSS overrides. With no
host settings, the official defaults are identical to v1.07. The adapter has
no dependency on Streamlit state, learner records, databases, APIs, secrets, or
business logic.

The UI Registry maps Dashboard, Learning, CBT, Recovery, Challenge, Analytics,
Reports, AI, Planner, Library, Management, and My Learning to shared background,
layout, header, navigation, card, button, widget, dialog, icon, typography, and
animation contracts. Ultra Brain owns customization and persistence; ULE owns
only payload validation and application. No transport, discovery, sync, or
second customization interface is implemented.

## v1.091 Theme World consumption boundary

`ui/theme.py` normalizes the existing `ultra-brain.ui/v1` query contract into a
presentation-only Theme World definition. Only approved theme ids, a bounded
source World id and revision, declared visual adjustments, and explicit
lock/override metadata cross this boundary. Invalid values fail closed.

The resolved context is passed to the existing navigation and World renderer.
Internal route and feature ids remain stable; separate Korean display labels
are used for learner-visible markup. No Theme World input enters learner state,
the Database, CRUD, API, BYOK, Analytics, Report, or operational storage.
