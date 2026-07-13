# Universal Learning Engine v0.6 Quality & Reliability Roadmap

## Document status

This document is the approved, implemented, and verified v0.6 release contract.
v0.5 Learning Analytics is the preserved runtime baseline. v0.6 adds
no new learning capability; it strengthens correctness, failure isolation,
observability, performance, automated verification, and documentation.

## 1. Preserved baseline

v0.6 must preserve the complete v0.5 user-visible learning flow and all earlier
contracts:

- Topic, question-count, and difficulty selection
- Tutorial, example, direct task, practice, and CBT generation
- One-question-at-a-time CBT, index-based scoring, feedback, and explanations
- Retry and Home behavior
- Optional reported confidence
- v0.4 adaptive status, recovery guidance, and explicit recommendation control
- v0.5 latest-round, current-topic, and overall session analytics
- The existing lesson JSON field names and supported extra fields
- Session-only state and the existing Home clearing policy

Stricter rejection of malformed or ambiguous values is a reliability correction,
not a lesson-schema change. Existing valid lesson JSON remains valid.

## 2. Exact v0.6 scope

v0.6 may implement only:

1. Scoring correctness and submitted-answer immutability
2. Safer JSON extraction and lesson validation
3. Typed failure boundaries and safe user-facing errors
4. Explicit API timeout, retry, and fallback behavior
5. Operational logging without secrets or learner-content payloads
6. Removal of avoidable repeated analytics work
7. Backward-compatible UI reliability improvements
8. Automated unit, regression, Streamlit, compile, and startup verification
9. Documentation and release-readiness alignment

## 3. Reliability policies

### Scoring

- Selected and correct answers remain zero-based integer indices.
- Boolean values are not valid indices even though Python treats booleans as integers.
- A submitted answer and its reported confidence cannot be changed while feedback
  for that question is active.

### JSON validation

- Plain, fenced, and lightly wrapped single JSON objects remain supported.
- Multiple top-level JSON objects are rejected as ambiguous.
- The existing required fields, short-question notice, and excess-question
  truncation behavior remain unchanged.
- Duplicate choices are compared after whitespace, Unicode compatibility, and
  case normalization.

### API and exceptions

- The Responses API remains primary and chat completions remains a conditional
  compatibility fallback.
- Non-retryable authentication, permission, quota, billing, request, and rate-limit
  failures never cause the fallback call.
- Explicitly transient connection/service failures may cause at most one fallback.
- SDK retry and request timeout behavior must be explicit rather than implicit.
- User messages do not include raw provider exception text.

### Logging and privacy

- Operational logs may include event name, duration, model, difficulty, requested
  count, exception type, and status code.
- API keys, prompts, generated lesson text, answer text, and raw learner content
  must not be logged.

## 4. Expected file changes

- `app.py`: reliability boundaries, API policy, validation, logging, answer locking,
  and analytics cache integration
- `tests/`: boundary, failure, compatibility, regression, and Streamlit tests
- `.github/workflows/tests.yml`: automated compile and test execution
- `README.md`, `CHANGELOG.md`, and canonical documents: implemented v0.6 behavior
- `VERSION`: `v0.6`

## 5. Verification plan

- Complete pre-v0.6 regression suite: passed.
- Malformed/ambiguous JSON, strict index, normalized duplicate-choice, exception
  sanitization, transient status, and empty-response tests: passed.
- Streamlit answer immutability and preserved v0.4/v0.5 result-path tests: passed.
- Application and test module compilation: passed.
- Headless Streamlit startup and health endpoint: HTTP 200 `ok`.
- Final automated result: 57 tests passed with zero failures.
- Do not require a live paid API call for deterministic acceptance.

## 6. Acceptance criteria

v0.6 acceptance is complete because:

1. All existing v0.5 tests remain passing.
2. All new v0.6 tests pass.
3. Existing valid JSON and all existing UI controls remain compatible.
4. Boolean or out-of-range indices cannot reach scoring.
5. Submitted answers cannot be overwritten during feedback.
6. Ambiguous model output is rejected with a controlled error.
7. API fallback remains bounded and non-retryable failures do not trigger it.
8. Raw provider exception text is not displayed to the learner.
9. Adaptive or analytics failures cannot hide the base round result.
10. Operational logs contain no configured secret or lesson/answer payload.
11. Compile, automated regression, and Streamlit startup checks pass.
12. Documentation matches implementation.

## 7. Explicit exclusions

- New Decision Engine behavior
- New Recovery behavior or recovery-content generation
- Persistence, database, accounts, background workers, scheduling, or notifications
- Learning Timeline or Knowledge Retention
- Living OS integration
- Expansion Platform features
- New navigation, dashboard, or learning-flow structure
- Autonomous generation, difficulty changes, or learner actions

These features are not implemented in v0.6.

## 8. Implementation stages

1. Freeze the v0.5 baseline with regression and compile checks — complete.
2. Add the v0.6 design contract before runtime changes — complete.
3. Harden scoring, JSON parsing, validation, and submitted-answer behavior — complete.
4. Harden exception, API, logging, and analytics performance boundaries — complete.
5. Add CI and complete regression, compile, and Streamlit startup verification — complete.
6. Align documentation and report release readiness before any commit — complete.
