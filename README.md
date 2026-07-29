# Universal Learning Engine v1.04 AI Integration & BYOK

![Version](https://img.shields.io/badge/version-v1.04-35C8DD)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Streamlit](https://img.shields.io/badge/streamlit-ready-red)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Universal Learning Engine is a production-ready Streamlit learning application that generates a consistent learning flow for any topic:

Topic → Tutorial → Example → Direct Task → Practice → CBT → Scoring → Result

The repository contains the **v1.04 AI Integration & BYOK** implementation on
the preserved v1.03 learning-flow and Expansion runtime.

## Current features

- Official ULE Signal Grid dark interface
- Nine-World functional navigation with My Learning as the session home
- Independent Learning, Recovery, Challenge, Analytics, AI, Planner, Library,
  Management, and My Learning functional Worlds
- Completed Learning flow into Recovery recommendations and linked Challenge
  sessions
- Executable Recovery Sessions with retained records, history, timing, and
  Challenge recommendations
- Independent Exam, Hard, Nightmare, and mock-exam Challenge sessions, history,
  and results
- Per-user BYOK registration, change, deletion, and connection testing
- Session-memory-only API key handling outside World state, backups, logs, and
  tracked configuration
- AI question, explanation, recommendation, and summary actions using current
  learning context
- AI-only disablement when no user key is registered
- Sanitized, isolated AI failures that do not terminate the application
- Explicit AI Recommendation conversion into real Planner goals and schedules
- Planner Learning schedules that transfer their selected topic into Learning
- Automatic Library collection from Learning, Recovery, Challenge, AI, and
  Planner
- Integrated My Learning statistics and reports across all Worlds
- Goals, dated schedules, Today Learning actions, notes, search, settings,
  subject management, backup, and restore
- Mobile-first responsive presentation, visible focus, and reduced-motion support
- Topic input with empty-input and 80-character validation
- CBT question counts of 5, 10, 15, or 20
- Easy, Normal, Hard, and Nightmare difficulty levels
- OpenAI-generated tutorial, example, direct task, practice, and CBT content
- One-question-at-a-time CBT interaction
- Answer-index scoring and immediate feedback
- Explanation display and end-of-round summary
- Retry and home-reset flows
- Plain, fenced, and lightly wrapped JSON parsing
- Lesson schema, question-count, choice, answer-index, and explanation validation
- Duplicate-choice rejection
- Restricted fallback behavior for retryable OpenAI API failures
- Optional low, medium, high, or unset reported confidence per answer
- Session-only Round Status and same-topic Learning Progress
- Deterministic learning-pattern signals
- Bounded next-difficulty recommendations with explanations
- Advisory recovery priority and relative interval guidance
- Explicit user-controlled application of a recommended difficulty
- Latest-round Learning Analytics
- Current-topic Session Analytics
- Overall analytics across all completed records retained in the active session
- Weighted accuracy, mean-round accuracy, result totals, and learning summaries
- Reported-confidence coverage and correctness-confidence analytics
- Topic, difficulty, round, and learning-pattern breakdowns
- Evidence-qualified strength and weakness summaries
- Independent, deterministic analytics logic with non-fatal UI integration
- Strict integer-only scoring indices and immutable submitted answers
- Unambiguous single-object JSON extraction and normalized duplicate detection
- Explicit API timeout, bounded compatibility fallback, and sanitized errors
- Privacy-conscious operational event logging
- Revision-bound analytics reuse within the active session
- Automated compile and regression checks for Python 3.10 and 3.13
- Lifecycle-only Expansion Pack common interface
- In-process exact-version Pack Registry and failure-safe Pack Loader
- Pack Manager and Expansion API for install, remove, load, unload, and lookup
- Connection-only Living OS Integration Interface with no concrete adapter
- Optional executable-pack contract preserving lifecycle-only v0.7 packs
- Synchronous in-process Pack Runtime start and stop flow
- One isolated active Pack Session per exact pack identity
- Private per-session state and immutable public session status
- Runtime-aware unload/removal and failure-safe termination behavior
- Shared Loader/Runtime transition protection for exact Pack identities
- Runtime-aware prevention of direct unload while a Pack Session is active
- Structured sanitized lifecycle/execution errors and cleanup-failure status
- Session metadata repair and atomic completed-round analytics invalidation
- Branch coverage reporting and automated headless Streamlit health verification

Hard questions emphasize application, comparison, cases, and plausible distractors while connecting at least two concepts. Nightmare questions require a concrete scenario, multi-step reasoning, competing trade-offs, plausible traps, at least three connected concepts, and explanations of both correct and incorrect choices.

## Documentation authority

The repository is the single source of truth. Use these documents in this order:

1. [MASTER_DESIGN.md](./docs/MASTER_DESIGN.md) — canonical design through v1.04
2. [ARCHITECTURE.md](./docs/ARCHITECTURE.md) — current components, state, data flow, and boundaries
3. [MODULE_SPEC.md](./docs/MODULE_SPEC.md) — current logical module contracts
4. [ROADMAP_v0.4.md](./docs/ROADMAP_v0.4.md) — implemented v0.4 contract and acceptance plan
5. [ROADMAP_v0.5.md](./docs/ROADMAP_v0.5.md) — implemented v0.5 analytics contract
6. [ROADMAP_v0.6.md](./docs/ROADMAP_v0.6.md) — approved v0.6 reliability contract
7. [ROADMAP_v0.7.md](./docs/ROADMAP_v0.7.md) — approved v0.7 expansion contract
8. [ROADMAP_v0.8.md](./docs/ROADMAP_v0.8.md) — approved v0.8 Pack Runtime contract
9. [ROADMAP_v0.9.md](./docs/ROADMAP_v0.9.md) — approved v0.9 final-stabilization contract
10. [ROADMAP_v1.0.md](./docs/ROADMAP_v1.0.md) — approved v1.0 Stable contract
11. [ROADMAP_v1.02.md](./docs/ROADMAP_v1.02.md) — v1.02 World Integration contract
12. [ROADMAP_v1.03.md](./docs/ROADMAP_v1.03.md) — v1.03 Learning Flow Integration contract
13. [ROADMAP_v1.04.md](./docs/ROADMAP_v1.04.md) — v1.04 AI Integration & BYOK contract
14. [DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md) — development and verification workflow
15. [EXPANSION_API.md](./docs/EXPANSION_API.md) — supported Expansion API contract
16. [RELEASE_CHECKLIST.md](./docs/RELEASE_CHECKLIST.md) — release evidence and publication gates
17. [ROADMAP.md](./docs/ROADMAP.md) — overall version boundaries
18. [CHANGELOG.md](./CHANGELOG.md) and release notes — historical change records

## Installation

```bash
pip install -r requirements.txt
```

Python 3.10 or newer is expected.

## Configuration

Each user registers their own OpenAI API key in **Management → OpenAI API**.
The key is retained only in that browser session's server memory. It is never
written to World state, local backups, logs, tracked configuration, commits, or
releases. Register the key again after the Streamlit session ends.

Only the optional model setting is resolved from local `.env`, environment
variables, or Streamlit Secrets. It defaults to `gpt-4.1-mini`:

```env
OPENAI_MODEL=gpt-4.1-mini
```

When no user key is registered, the four AI actions and AI lesson generation
are disabled while every non-AI World remains available.

## Run locally

```bash
streamlit run app.py
```

## Run tests

```bash
python -m unittest discover
```

The regression suite covers the preserved learning and Expansion contracts,
v1.02 World behavior, v1.03 cross-World data flow, v1.04 BYOK lifecycle and AI
error isolation, isolated persistence, navigation context transfer, integrated
reports, and headless Streamlit behavior.
GitHub Actions runs complete compilation, branch coverage, regression checks,
and a headless health check on Python 3.10 and 3.13.

## Explicit exclusions

The following remain outside v1.04:

- Learning Decision Engine or Weakness Score
- Background scheduler or notifications
- Autonomous learning actions
- Concrete Living OS functionality
- Remote pack acquisition, durable pack persistence, dependency resolution, or automatic updates
- Network, IPC, shared files, synchronization, command execution, background pack work, or cross-pack messaging
- Login, PDF, OCR, voice, or image features

See [ROADMAP.md](./docs/ROADMAP.md) for approved placement. Roadmap entries are documentation, not implemented functionality.

## Project structure

```text
Universal-Learning-Engine/
├─ assets/                    # Official static ULE stylesheet
├─ ui/                        # Navigation and trusted static theme
├─ expansion/                 # Stable Expansion Platform and Pack Runtime
├─ tests/test_streamlit_v10.py
├─ tests/test_streamlit_v103.py
├─ tests/test_byok_v104.py
├─ tests/test_streamlit_v104.py
├─ tests/test_world_integration_v103.py
├─ tests/test_v10_ui_contract.py
├─ tests/test_v10_public_api.py
├─ tests/test_v09_stability.py
├─ tests/test_pack_runtime.py
├─ tests/test_expansion_platform.py
├─ docs/ROADMAP_v1.0.md
├─ docs/ROADMAP_v1.02.md
├─ docs/ROADMAP_v1.03.md
├─ docs/ROADMAP_v1.04.md
├─ docs/DEVELOPER_GUIDE.md
├─ docs/EXPANSION_API.md
├─ docs/RELEASE_REVIEW_v1.0.md
├─ docs/ROADMAP_v0.9.md
├─ docs/RELEASE_CHECKLIST.md
├─ docs/ROADMAP_v0.8.md
├─ docs/ROADMAP_v0.7.md
├─ RELEASE_NOTES_v1.0.md
├─ RELEASE_NOTES_v0.9.md
├─ RELEASE_NOTES_v0.8.md
├─ RELEASE_NOTES_v0.7.md
├─ app.py
├─ adaptive.py
├─ analytics.py
├─ tests/
│  ├─ __init__.py
│  ├─ test_app_quality.py
│  ├─ test_adaptive.py
│  ├─ test_streamlit_v04.py
│  ├─ test_analytics.py
│  ├─ test_streamlit_v05.py
│  └─ test_v06_quality.py
├─ docs/
│  ├─ ROADMAP.md
│  ├─ ROADMAP_v0.4.md
│  ├─ ROADMAP_v0.5.md
│  ├─ ROADMAP_v0.6.md
│  ├─ MASTER_DESIGN.md
│  ├─ ARCHITECTURE.md
│  └─ MODULE_SPEC.md
├─ .streamlit/
│  ├─ config.toml
│  └─ secrets.toml.example
├─ .github/workflows/tests.yml
├─ README.md
├─ CHANGELOG.md
├─ RELEASE_NOTES_v0.3.0.md
├─ RELEASE_NOTES_v0.3.1.md
├─ RELEASE_NOTES_v0.4.md
├─ RELEASE_NOTES_v0.5.md
├─ RELEASE_NOTES_v0.6.md
├─ VERSION
├─ requirements.txt
├─ constraints.txt
├─ SECURITY.md
├─ LICENSE
├─ .env.example
└─ .gitignore
```

## Release information

- [v1.0 Stable release notes](./RELEASE_NOTES_v1.0.md)
- [v1.0 release review](./docs/RELEASE_REVIEW_v1.0.md)
- [v0.9 release notes](./RELEASE_NOTES_v0.9.md)
- [v0.8 release notes](./RELEASE_NOTES_v0.8.md)
- [v0.7 release notes](./RELEASE_NOTES_v0.7.md)
- [v0.6 release notes](./RELEASE_NOTES_v0.6.md)
- [v0.5 release notes](./RELEASE_NOTES_v0.5.md)
- [v0.4 release notes](./RELEASE_NOTES_v0.4.md)
- [v0.3.1 release notes](./RELEASE_NOTES_v0.3.1.md)
- [v0.3.0 release notes](./RELEASE_NOTES_v0.3.0.md)
- [Changelog](./CHANGELOG.md)

## Known limitations

- Generated content quality depends on model behavior and prompt interpretation.
- Live API behavior and generated difficulty quality require manual verification.
- API keys are session-only and must be registered again after the browser
  session ends.
- Detailed adaptive evidence remains session-local, while normalized World
  history is stored locally.
- Confidence is self-reported and recommendations are deterministic guidance, not a diagnosis.
- Five-question rounds can produce volatile percentage changes.
- Detailed confidence and pattern analytics cover session-retained adaptive
  records; integrated World totals use durable World history.
- Strength and weakness summaries are limited to topic/difficulty evidence because v0.4 records contain no concept tags or timestamps.
- Expansion Pack state is process-local, version selection is exact, and no concrete Living OS adapter is included.
- Direct Registry mutation is a low-level operation; coordinated lifecycle and Runtime changes must use Pack Manager or Expansion API.
- Pack Runtime execution is synchronous and in-process; session separation is not an operating-system security sandbox.
- The official skin uses Streamlit DOM selectors that require review after Streamlit upgrades.
- Python 3.10/3.13 remote CI evidence remains a publication gate.

## License

MIT License. See [LICENSE](./LICENSE).
