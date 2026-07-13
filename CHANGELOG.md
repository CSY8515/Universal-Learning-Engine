# Changelog

All notable changes to Universal Learning Engine are documented here.

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
