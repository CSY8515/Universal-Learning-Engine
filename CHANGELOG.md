# Changelog

All notable changes to Universal Learning Engine are documented here.

## v1.07 - Official UI / UX

### Added

- Official central Learning World with nine functional orbital World domes
- Dedicated cinematic background art for the World map and each of the nine
  functional Worlds
- Living OS glass surfaces, focused Hover glow, restrained entrance animation,
  World transition, and persistent World navigation dock
- Keyboard focus treatment, reduced-motion behavior, and responsive World-map
  presentation
- v1.07 presentation and nine-World entry regression tests

### Changed

- The presentation home is now the official Learning World map; My Learning
  remains an unchanged independent functional World
- Existing Streamlit function screens are presented as immersive World
  interiors without changing their actions or data flow

### Preserved

- Learning Engine, World-state schema, database behavior, CRUD, API, BYOK,
  Analytics, Report, and complete learning flow
- Existing user records and backward-compatible normalization
- Expansion Platform and Living OS integration boundary

## v1.06 - Localization & User Experience

### Added

- Korean learner-facing terminology across all nine Worlds, navigation,
  reports, controls, guidance, validation, and error states
- Selective record deletion with dependent generated-data cleanup
- Category-level record deletion, all-record deletion, and full user-data reset
- Explicit confirmation gates for destructive data and BYOK key deletion
- v1.06 localization, developer-marker, compatibility, and data-management tests

### Changed

- BYOK registration, replacement, deletion, and connection-test guidance now
  uses one learner-oriented Korean flow
- Backup files use the application-specific `.ule` extension while retaining
  backward-compatible restore parsing
- Existing English system-generated record labels are localized when rendered
- Invalid backup and generated-data details are kept behind sanitized Korean
  user messages

### Verified

- 145 automated compile, unit, integration, Streamlit, and regression tests
- Nine-World Korean display and developer-output non-exposure
- Existing user records normalize without deletion or reset
- Data cleanup preserves unrelated records and the documented settings boundary

### Preserved

- v1.05 end-to-end data flow and v1.04 BYOK security boundary
- Existing UI layout, backgrounds, Hover, Animation, and Glass behavior
- World-state schema version and backward-compatible normalization

## v1.05 - End-to-End Validation

### Added

- End-to-end validation of the Learning, Recovery, Challenge, Analytics, AI,
  Planner, Library, Management, My Learning, and Report data path
- Supported create, read, update, delete, backup, and restore verification
- Streamlit button-flow coverage for Learning, Challenge, AI, Planner, Library,
  and Management actions
- User-visible safety checks across all nine Worlds

### Verified

- 136 automated compile, unit, integration, Streamlit, and regression tests
- API-key-free operation keeps every non-AI World functional
- API success and isolated provider-failure paths
- User-confirmed live BYOK connection and AI response
- Session-only key handling outside World state and backup data
- Localhost health endpoint returns HTTP 200 and `ok`

### Preserved

- v1.04 BYOK and AI integration behavior
- v1.03 World data flow and Expansion runtime
- Existing UI, layout, backgrounds, Hover, Animation, and Glass behavior

## v1.04 - AI Integration & BYOK

### Added

- Per-user OpenAI API key registration, change, deletion, and connection testing
- Session-memory-only BYOK storage outside World data, backups, logs, and
  repository configuration
- Independent AI question, explanation, recommendation, and summary actions
- Focused BYOK lifecycle, sanitization, no-key isolation, and Streamlit tests

### Changed

- AI lesson generation and AI World actions use only the current user's
  registered key
- Missing or failed AI configuration disables only AI-dependent actions
- AI explanations join the existing AI history, Library, My Learning, and Report
  data flow

### Preserved

- v1.03 World structure and data flow
- Existing theme, layout, backgrounds, Hover, Animation, and Glass behavior
- Non-AI Worlds when no API key is registered

## v1.03 - Learning Flow Integration

### Added

- Recovery records, timing, history, and deterministic Challenge recommendations
- Independent Challenge Sessions, Results, and mode history
- Integrated cross-World Analytics supplied to AI
- Explicit AI Recommendation conversion into Planner goals and schedules
- Planner Learning-topic transfer
- Multi-source Library records from Learning, Recovery, Challenge, AI, and Planner
- Integrated My Learning statistics, achievements, and all-World Report
- v1.02 state migration and isolated Streamlit persistence tests

### Removed

- Unused Dashboard, Review, and shared legacy presentation modules
- Legacy explicit-navigation callback routing
- Obsolete topic input placeholder

### Preserved

- Existing UI theme and layout
- Validated lesson generation, CBT, adaptive, and analytics contracts
- Expansion Platform and Living OS interface boundaries

## v1.0.0 - Stable

### Added

- Official ULE Signal Grid dark interface
- Dashboard Home, Learning, and Review navigation
- Session-only Dashboard for current topic, recommendation, accuracy, recovery,
  recent results, weakness evidence, progress, and activity
- Responsive, keyboard-focus, and reduced-motion presentation rules
- Dedicated `ui` presentation package and trusted static stylesheet
- Stable Expansion public API compatibility tests and documentation
- Developer Guide, Security Policy, v1.0 roadmap, and release review
- Tested direct dependency constraints

### Changed

- Result metrics are prioritized while detailed mistakes and explanations are
  collapsed by default
- Major views render selectively to reduce unnecessary page work
- Navigation changes use queued session transitions compatible with Streamlit
  widget-state rules
- Documentation and release metadata now identify `v1.0.0` as the Stable line

### Removed

- Inactive legacy difficulty-rule function superseded by the preserved active
  v0.3.1 quality prompt rules

### Preserved

- Complete v0.9 learning, adaptive, recovery, analytics, session, Expansion,
  Runtime, error, security, and public API behavior
- Expansion interface version `0.7` and lifecycle-only v0.7 Pack compatibility

## v0.9 - Final Stabilization

### Added

- Shared internal Loader/Runtime transition guard
- Runtime-aware direct-unload protection
- Structured sanitized lifecycle and execution error context
- Session metadata repair and atomic completed-round updates
- Ten focused v0.9 stability tests
- Branch coverage and headless Streamlit health automation
- Release checklist and v1.0 design entry criteria

### Changed

- Dependency ranges now reject unapproved future major versions
- Retry clears both CBT and confidence widget state
- CI compiles the complete Expansion package and records branch coverage

### Preserved

- All public Expansion API operations and interface version `0.7`
- Complete v0.8 learning UI, Runtime, Loader, Session, adaptive, and analytics behavior

### Verification

- 90 automated tests passing locally on Python 3.13.14
- Full compilation passing
- 84% branch coverage baseline
- Headless Streamlit health endpoint returning HTTP 200 and `ok`
- Python 3.10/3.13 GitHub Actions matrix configured; remote result pending authorized push
## v0.8 - Pack Runtime

### Added

- Optional `ExecutableExpansionPack` execution and termination contract
- Synchronous in-process Pack Runtime
- Isolated per-identity Pack Sessions with private mutable state
- Immutable public Pack Session status snapshots
- Expansion API start, stop, session lookup, and session listing operations
- Runtime-aware unload and removal coordination
- Pack Runtime contract, independence, and failure-path tests

### Changed

- Pack Loader now rejects reentrant lifecycle transitions
- Manager unload and removal terminate an active exact-version session first

### Preserved

- Interface version `0.7` and all lifecycle-only v0.7 pack behavior
- Complete existing Runtime, UI, Streamlit session, API, adaptive, analytics,
  reliability, Registry, Loader, Manager, Expansion API, and Living OS boundary

### Excluded

- Concrete Living OS functionality, network, IPC, file sharing,
  synchronization, command execution, persistence, background work, new UI,
  cross-pack messaging, and v0.9-or-v1.0 features

### Verification

- 80 automated tests passing
- Python compilation and headless Streamlit startup passing

## v0.7 - Expansion Platform

### Added

- Lifecycle-only Expansion Pack common interface and immutable manifest
- In-process Pack Registry with exact multi-version identity
- Pack Loader with failure-safe lifecycle state
- Pack Manager for install, remove, load, unload, lookup, and version listing
- Expansion API facade independent of the existing learning runtime
- Connection-only Living OS Integration Interface
- Focused Expansion Platform contract and regression tests

### Preserved

- Complete v0.6 learning flow, public APIs, UI, adaptive behavior, analytics,
  reliability boundaries, and session-state behavior

### Excluded

- Concrete Living OS functionality, new UI, remote pack acquisition, durable
  pack persistence, dependency resolution, automatic updates, and v0.8 features

### Verification

- Expansion Platform contract tests passing
- Full v0.6 regression suite preserved

## v0.6 - Quality & Reliability

### Added

- Privacy-conscious operational event logging
- Explicit OpenAI timeout and application-owned fallback policy
- Revision-bound session analytics cache with evidence-change invalidation
- GitHub Actions compile and regression automation for Python 3.10 and 3.13
- Focused v0.6 JSON, scoring, exception, API, and UI reliability tests

### Changed

- Parse model output as one unambiguous plain, fenced, or lightly wrapped JSON object
- Normalize whitespace, Unicode compatibility forms, and case for duplicate-choice detection
- Sanitize unexpected and provider error messages shown to learners
- Lock submitted answer and confidence controls while feedback is active

### Fixed

- Boolean values can no longer pass as integer answer indices
- Transient 5xx failures can use the single approved compatibility fallback
- Billing and authentication indicators take precedence over transient status fallback
- Malformed completed records no longer break duplicate-round detection

### Preserved

- Complete v0.5 CBT, recovery, adaptive, analytics, recommendation, JSON field, UI, Retry, and Home behavior

### Verification

- 57 automated tests passing
- Python compile verification passing
- Streamlit headless startup and health endpoint verification passing

## v0.5 - Learning Analytics

### Added

- Independent, pure `analytics.py` domain module
- Latest-round, current-topic Session, and Overall Learning Analytics
- Weighted accuracy and separately labeled mean-round accuracy
- Learning-result summaries and round/topic/difficulty breakdowns
- Reported-confidence coverage and correctness-confidence aggregation
- v0.4 learning-pattern frequency and recent repetition analysis
- Evidence-qualified strength and weakness summaries
- Pure analytics and Streamlit v0.5 test suites

### Preserved

- Complete v0.4 generation, validation, CBT, scoring, feedback, adaptive guidance, Retry, Home, and explicit recommendation behavior
- Session-only storage and Home clearing policy
- Existing Recovery Priority behavior without v0.5 extension

### Excluded

- Weakness Score, Learning Decision Engine, autonomous actions, new Recovery Priority behavior, database, persistence, background scheduler, notifications, Living OS integration, and Expansion features

### Release status

- Released baseline for v0.6 Quality & Reliability.

## v0.4 - Adaptive Learning

### Added

- Optional per-answer reported confidence
- Session-only Round Status and same-topic Learning Progress
- Deterministic learning-pattern analysis
- Bounded adaptive difficulty recommendations with evidence
- Advisory recovery priority and interval recommendations
- Explicit user-controlled recommendation application
- Pure adaptive rule tests and Streamlit integration tests

### Changed

- Extended the completed-round summary with adaptive learning guidance
- Added explicit learner control for applying the recommended next difficulty
- Updated canonical architecture, module, master-design, and roadmap documentation
- Updated the repository version from `v0.3.1` to `v0.4`

### Preserved

- All v0.3.1 lesson generation, validation, CBT, scoring, feedback, summary, retry, reset, and API fallback behavior

### Excluded

- Persistent history, Decision Engine behavior, autonomous AI decisions, databases, background scheduling, and notifications

## v0.3.1 - Difficulty Quality Hotfix

### Changed

- Strengthened Hard difficulty prompt rules
- Strengthened Nightmare difficulty prompt rules
- Added stricter CBT quality instructions for plausible distractors
- Added explicit rule against duplicate choices
- Added explicit rule against obvious answer clues
- Added Nightmare requirement for concrete scenario-based questions
- Updated version from `v0.3.0` to `v0.3.1`

### Fixed

- Hard questions could feel too easy or definition-heavy
- Nightmare questions could feel too similar to Hard
- Duplicate choices are now rejected during JSON validation

### Tests

- Added duplicate-choice validation test
- Added v0.3.1 Hard / Nightmare prompt quality assertions

## v0.3.0 - Quality & Reliability Update

### Added

- Minimum test suite with `unittest`
- `VERSION` file
- MIT License
- Release note document for GitHub Releases

### Changed

- Improved CBT grading reliability by grading with selected choice index instead of choice text
- Improved duplicate-choice handling so repeated choice text does not cause misgrading
- Improved OpenAI API fallback behavior to avoid unnecessary second calls for non-retryable errors
- Strengthened difficulty prompt rules for Easy / Normal / Hard / Nightmare
- Updated README for Release Candidate readiness

### Fixed

- Removed the risk of incorrect scoring caused by `choices.index(choice)`
- Reduced unnecessary API fallback calls on authentication, quota, billing, and permission errors
- Improved JSON parsing for fenced or lightly wrapped JSON responses

### Known Issues

- Real OpenAI generation quality must be verified in the deployed Streamlit Cloud environment
- Streamlit Cloud requires `OPENAI_API_KEY` to be configured in Secrets
- License is now MIT, but package publishing metadata is not yet configured

## v0.2.0 - Interactive CBT Preview

### Added

- Question count selection: 5 / 10 / 15 / 20
- Difficulty selection
- One-question-at-a-time CBT flow
- Answer submission
- Correct / incorrect feedback
- Explanation display
- Round summary
- Retry and home reset flow
- JSON validation and safer response handling

## v0.1.0 - Initial MVP

### Added

- Universal topic input
- Tutorial generation
- Example generation
- Direct writing / implementation task
- Practice task
- CBT generation
- Wrong-answer note
- Explanation section
- Streamlit app structure
- OpenAI API integration
