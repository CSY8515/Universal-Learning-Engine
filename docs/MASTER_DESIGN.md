# Universal Learning Engine Master Design

## Status and purpose

This document defines the frozen v0.2 feature boundary and records the implemented v0.3.1 through v1.0 behavior. It does not authorize future functionality.

- Implemented working-tree design: **v1.0 Stable**
- Release version file: **v1.0.0**

Runtime entry point: `app.py`  
Interface: Streamlit  
Persistence: Streamlit session state only

## Design principles

1. **Preserve released behavior.** Later work must not silently remove or redefine an implemented v0.3.1 feature.
2. **Keep version boundaries explicit.** Future capabilities remain unimplemented until their version scope and acceptance criteria are approved.
3. **Use one universal flow.** Topic-specific behavior is generated from the supplied topic rather than hardcoded into separate engines.
4. **Validate before rendering.** Model output is untrusted and must pass structural and value validation.
5. **Grade by stable identity.** CBT answers are compared by index, not display text.
6. **Protect API cost and failure clarity.** A second API call is attempted only for failures classified as retryable.
7. **Keep secrets outside source.** Credentials come from local environment configuration or Streamlit Secrets.
8. **Separate records from plans.** Release notes and changelog describe history; roadmap documents describe approved future direction.

## v0.2 feature freeze

The v0.2 product boundary is an interactive, session-based learning flow for a user-provided topic.

### Frozen user flow

1. Enter a topic.
2. Select 5, 10, 15, or 20 CBT questions.
3. Select a difficulty.
4. Generate a lesson containing tutorial, example, direct task, practice, and CBT questions.
5. Answer one CBT question at a time.
6. Receive correctness feedback and an explanation.
7. View a round summary.
8. Retry the round or return home.

### Frozen lesson contract

The generated lesson contains:

- `topic`: non-empty text
- `tutorial`: non-empty text
- `example`: non-empty text
- `direct_task`: non-empty text
- `practice`: non-empty text
- `cbt`: a non-empty list of question objects

Each CBT question contains:

- `question`: non-empty text
- `choices`: exactly four non-empty text values
- `answer_index`: integer from 0 through 3
- `explanation`: non-empty text

### Frozen exclusions

v0.2 does not include durable learning history, recovery, analytics, dashboard, review scheduling, login, document export, OCR, voice, image learning, or extension packs.

## v0.3 Quality & Reliability master design

v0.3 preserves the v0.2 product flow and strengthens correctness at system boundaries.

### Input reliability

- Topics are trimmed before use.
- Empty topics are rejected.
- Topics longer than 80 characters are rejected.
- Supported question counts are restricted to 5, 10, 15, and 20.
- Supported UI difficulties are Easy, Normal, Hard, and Nightmare.

### Model-output reliability

- Plain JSON is accepted.
- A complete fenced JSON block is unwrapped before parsing.
- Light surrounding text is tolerated by extracting the outermost JSON object.
- Invalid JSON produces a controlled data-format error.
- Required lesson fields and their non-empty text values are validated.
- CBT must be a non-empty list.
- Excess questions are truncated to the requested count with a notice.
- A short question list is retained with a notice instead of being fabricated.
- Choices, answer indices, and explanations are validated before rendering.

### Scoring reliability

- The selected choice index is stored.
- Correctness is determined by comparing the selected index with `answer_index`.
- Display text is never used to locate or infer the selected answer.
- v0.3.1 rejects duplicate choice text after trimming.

### API failure policy

The primary call uses the OpenAI Responses interface. A chat-completions fallback may be attempted only when the first failure appears transient, such as a connection, timeout, temporary service, server, or service-unavailable error.

Fallback is blocked for status codes 400, 401, 403, 404, and 429 and for messages indicating authentication, API-key, permission, quota, billing, payment, or rate-limit problems.

### Difficulty quality

- **Easy:** definitions, basic terms, and beginner concepts with simple distinct distractors.
- **Normal:** concept understanding, basic application, and simple comparison.
- **Hard:** application, comparison, case-based reasoning, at least two connected concepts, plausible distractors, and no simple definition-only questions.
- **Nightmare:** concrete scenarios, multi-step reasoning, at least three connected concepts, real-world judgment, competing trade-offs, tempting trap choices, and explanations covering why the best answer is correct and alternatives are wrong.

### Session behavior

The current lesson, answers, current question, feedback, round completion, round identifier, and generation flag are held in Streamlit session state. State is normalized before CBT rendering. Retry resets the round while retaining the lesson; home reset clears the lesson and the round.

## v0.3.1 acceptance baseline

The baseline is preserved when:

- The documented learning flow remains available.
- All four difficulties and all four question counts remain selectable.
- Invalid generated data cannot reach normal rendering unchecked.
- Answer scoring remains index-based.
- Duplicate choices remain invalid.
- Non-retryable API failures do not trigger fallback.
- Existing reset and summary behavior remains functional.
- The current unit tests continue to pass.

## Explicitly deferred

No adaptive rules, learner model, confidence calculation, learning pattern analysis, rule-candidate evaluation, timeline, retention calculation, durable storage, dashboard, or recovery behavior exists in v0.3.1. Their appearance in the roadmap must not be interpreted as implementation.

## v0.4 Adaptive Learning design

v0.4 adds a deterministic, session-only advisory layer while preserving the v0.3.1 generation and CBT flow.

- Confidence is optional and self-reported as low, medium, high, or unset.
- Completed answers produce Round Status metrics and evidence categories.
- Completed rounds are grouped by a normalized topic key for same-session Learning Progress.
- Learning Pattern signals are calculated with approved deterministic thresholds.
- Difficulty may be recommended one level higher or lower, bounded by Easy and Nightmare.
- A recommendation changes the next difficulty selector only after explicit user action.
- Recovery guidance consists of a priority, relative interval wording, evidence, and an explicit statement that nothing was scheduled.
- Home clears all adaptive state. No state survives the Streamlit session.
- Adaptive-analysis failure must not prevent the v0.3.1 round result from rendering.

The adaptive layer does not call an AI classifier and does not implement a Decision Engine, recovery-content engine, database, timeline, retention model, scheduler, notification, or autonomous action.

## v0.5 Learning Analytics design

v0.5 adds deterministic, read-only analytics over completed summaries already retained by v0.4.

- `analytics.py` is independent of Streamlit, OpenAI, persistence, scheduling, notifications, and adaptive action selection.
- Round Analytics reconcile counts, accuracy, reported-confidence coverage, correctness-confidence categories, and v0.4 signals.
- Session Analytics aggregate the active normalized topic in record order.
- Overall Learning Analytics aggregate all valid records still retained in the active Streamlit session.
- Weighted accuracy is primary; mean round accuracy is separately labeled.
- Topic and difficulty summaries expose exact counts and evidence sizes.
- Learning summaries describe observed totals, accuracy, confidence coverage, and available same-topic direction.
- Strengths require at least two rounds, ten answers, 85% weighted accuracy, and 60% supported success for the same topic and difficulty.
- Weaknesses require the same evidence minimum and either weighted accuracy below 60% or confident errors of at least 20%.
- Stable rule names and quantitative evidence are exposed without implementing a Weakness Score or Decision Engine.
- Invalid analytics records are excluded independently and reported without changing source records.
- Analytics failures cannot hide or replace the v0.4 result or adaptive UI.
- Home preserves its v0.4 behavior and clears all analytics source records.

The v0.5 layer does not add new Recovery Priority behavior, a Weakness Score, Learning Decision Engine, autonomous action, database, background scheduler, notification, Living OS integration, durable history, timeline, retention model, or Expansion feature.

## v0.6 Quality & Reliability design

v0.6 preserves the complete v0.5 learning flow and adds no new learning
capability. It strengthens system boundaries through strict index scoring, safer
single-object JSON extraction, normalized duplicate-choice detection, immutable
submitted answers during feedback, explicit API timeout and fallback behavior,
safe exception presentation, privacy-conscious operational logs, reduced repeated
analytics work, and automated regression and startup verification.

Existing valid lesson JSON, UI controls, session-state meaning, adaptive rules,
recovery guidance, recommendations, and analytics semantics remain unchanged.
Decision Engine expansion, new Recovery behavior, persistence, Living OS
integration, Expansion features, and a new UI or learning-flow structure remain
outside v0.6.

## v0.7 Expansion Platform design

v0.7 preserves the complete v0.6 learning runtime and adds an independent,
in-process Expansion Platform. The detailed approved contract is
`ROADMAP_v0.7.md`.

- An Expansion Pack exposes an immutable identity manifest and lifecycle-only
  common interface.
- Pack identity is the exact `(pack_id, version)` pair. Version strings are not
  ranked or resolved automatically.
- Pack Registry stores installed pack instances in process and supports exact,
  deterministic lookup without adding persistence.
- Pack Loader validates the interface contract and owns loaded state.
- Pack Manager coordinates install, remove, load, unload, listing, and exact
  version selection.
- Expansion API is a facade over those management operations and does not alter
  lesson generation, CBT, adaptive rules, analytics, or Streamlit state.
- Living OS integration is limited to a connect/disconnect interface bound to
  the Expansion API. No concrete Living OS behavior is included.
- Lifecycle failures are isolated from the existing learning engine and leave
  Registry and Loader state consistent.

v0.7 does not add a new UI, learning hook, content type, AI Tutor, Voice, 3D
Learning, Memory Curve, Knowledge Engine, Rule Engine expansion, durable
storage, remote pack acquisition, dependency resolution, background work, or
any v0.8 capability.

## v0.8 Pack Runtime design

v0.8 preserves the complete v0.7 Expansion Platform and adds an independent,
synchronous, in-process execution layer. The detailed contract is
`ROADMAP_v0.8.md`.

- The v0.7 `ExpansionPack`, manifest, exact identity, and interface version
  `0.7` remain valid and unchanged.
- `ExecutableExpansionPack` is an optional subtype with `execute(session)` and
  `terminate(session)` callbacks.
- Pack Runtime starts only installed and loaded executable exact versions.
- One exact identity owns at most one active Pack Session.
- Each session has immutable identity, an opaque id, and its own mutable state
  dictionary; public status does not expose state.
- Execution failure publishes no active session. Termination failure preserves
  active, loaded, and installed state.
- Unload and removal terminate the exact active session before pack unload.
- Loader and Runtime reject reentrant state transitions.
- Exact versions and separate packs have independent runtime/session state.

v0.8 adds no concrete Living OS behavior, network, IPC, shared-file behavior,
synchronization, command execution, durable state, discovery, remote packs,
dependency resolution, background work, automatic restart, new UI, learning
hook, cross-pack messaging, or v0.9-or-v1.0 capability. In-process reference
separation is not an operating-system security sandbox.

## v0.9 Final Stabilization design

v0.9 preserves the complete v0.8 product and adds no learning capability. It strengthens the release boundary before v1.0 through a shared internal Loader/Runtime transition guard, Runtime-aware unload protection, structured sanitized error context, repaired Streamlit session metadata, atomic completed-round updates, bounded dependency ranges, branch coverage, complete compilation, headless health verification, and synchronized release evidence.

Registry, Loader, and Runtime remain the sole authorities for installed, loaded, and active-session state respectively. The internal coordinator owns conflict information only and cannot become a second state source. Public Expansion methods, return types, interface version `0.7`, the v0.7 lifecycle contract, the v0.8 execution contract, and all existing learning behavior remain unchanged.

v0.9 adds no persistence, external transport, background work, discovery, Living OS behavior, cross-Pack messaging, new UI, new adaptive or analytics rule, or v1.0 feature.

## v1.0 Stable design

v1.0 preserves the complete v0.9 runtime and establishes the first official
production interface. The ULE Signal Grid presentation is dark, restrained,
responsive, and accessibility-aware. Dashboard is the initial Home view, while
Learning and Review provide explicit workspaces without changing the universal
lesson flow.

Dashboard reads only existing session evidence. Navigation is non-destructive;
the preserved Home reset remains the explicit action that clears lesson,
adaptive, analytics, and widget state. Recommended Next Step is deterministic
session guidance and is not represented as an AI Decision Engine.

Presentation responsibilities are separated into `ui/` and trusted static style
content in `assets/`. Dynamic learner and generated content continues through
normal Streamlit rendering and is never interpolated into unsafe HTML or CSS.

Expansion interface version `0.7`, all public facade operations and status types,
lifecycle-only v0.7 compatibility, synchronous Runtime behavior, and structured
errors remain unchanged. v1.0 adds no persistence, autonomous learning, external
transport, remote Packs, background work, concrete Living OS behavior, or new
learning algorithm.
