# Universal Learning Engine v0.9 Final Stabilization

![Version](https://img.shields.io/badge/version-v0.9-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Streamlit](https://img.shields.io/badge/streamlit-ready-red)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Universal Learning Engine is a Streamlit learning MVP that generates a consistent learning flow for any topic:

Topic → Tutorial → Example → Direct Task → Practice → CBT → Scoring → Result

The repository is prepared as the **v0.9 Final Stabilization** baseline on the preserved v0.8 Pack Runtime. The repository version is `v0.9`; commit, push, tag, GitHub Release, and deployment remain separately controlled.

## Current features

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

1. [MASTER_DESIGN.md](./docs/MASTER_DESIGN.md) — canonical design through v0.9
2. [ARCHITECTURE.md](./docs/ARCHITECTURE.md) — current components, state, data flow, and boundaries
3. [MODULE_SPEC.md](./docs/MODULE_SPEC.md) — current logical module contracts
4. [ROADMAP_v0.4.md](./docs/ROADMAP_v0.4.md) — implemented v0.4 contract and acceptance plan
5. [ROADMAP_v0.5.md](./docs/ROADMAP_v0.5.md) — implemented v0.5 analytics contract
6. [ROADMAP_v0.6.md](./docs/ROADMAP_v0.6.md) — approved v0.6 reliability contract
7. [ROADMAP_v0.7.md](./docs/ROADMAP_v0.7.md) — approved v0.7 expansion contract
8. [ROADMAP_v0.8.md](./docs/ROADMAP_v0.8.md) — approved v0.8 Pack Runtime contract
9. [ROADMAP_v0.9.md](./docs/ROADMAP_v0.9.md) — approved v0.9 final-stabilization contract
10. [RELEASE_CHECKLIST.md](./docs/RELEASE_CHECKLIST.md) — release evidence and remaining publication gates
11. [ROADMAP.md](./docs/ROADMAP.md) — overall version boundaries
12. [CHANGELOG.md](./CHANGELOG.md) and release notes — historical change records

## Installation

```bash
pip install -r requirements.txt
```

Python 3.10 or newer is expected.

## Configuration

Do not hardcode an API key. The app resolves configuration in this order:

1. Local `.env` values loaded into the environment
2. Existing environment variables
3. Streamlit Cloud Secrets
4. `gpt-4.1-mini` as the model default when no model is configured

Create a local `.env` from `.env.example`:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

For Streamlit Cloud, use the equivalent keys shown in `.streamlit/secrets.toml.example`.

## Run locally

```bash
streamlit run app.py
```

## Run tests

```bash
python -m unittest discover
```

The 90-test suite preserves all 80 v0.8 tests and adds ten v0.9 stability tests for cross-layer transitions, structured errors, session repair, atomic recording, and widget cleanup. GitHub Actions runs complete compilation, branch coverage with an 84% floor, regression checks, and a headless health check on Python 3.10 and 3.13.

## Explicit exclusions

The following are not implemented or expanded in v0.9:

- Learning Decision Engine or Weakness Score
- New Recovery Priority behavior or recovery content-generation engine
- Learning history persistence or review scheduling
- Database, background scheduler, or notifications
- Autonomous learning actions
- Concrete Living OS functionality
- Separate persistent analytics dashboard
- Remote pack acquisition, durable pack persistence, dependency resolution, or automatic updates
- Network, IPC, shared files, synchronization, command execution, background pack work, or cross-pack messaging
- v1.0 functionality or any unapproved post-v0.9 capability
- Login, PDF, OCR, voice, or image features

See [ROADMAP.md](./docs/ROADMAP.md) for approved placement. Roadmap entries are documentation, not implemented functionality.

## Project structure

```text
Universal-Learning-Engine/
├─ expansion/                 # v0.9-stabilized Expansion Platform and Pack Runtime
├─ tests/test_v09_stability.py
├─ tests/test_pack_runtime.py
├─ tests/test_expansion_platform.py
├─ docs/ROADMAP_v0.9.md
├─ docs/RELEASE_CHECKLIST.md
├─ docs/ROADMAP_v0.8.md
├─ docs/ROADMAP_v0.7.md
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
├─ LICENSE
├─ .env.example
└─ .gitignore
```

## Release information

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
- Streamlit Cloud requires an `OPENAI_API_KEY` Secret.
- Adaptive state exists only in the current Streamlit session; Home clears it and there is no durable learner history.
- Confidence is self-reported and recommendations are deterministic guidance, not a diagnosis.
- Five-question rounds can produce volatile percentage changes.
- Overall analytics cover only records still retained in the active Streamlit session.
- Strength and weakness summaries are limited to topic/difficulty evidence because v0.4 records contain no concept tags or timestamps.
- Expansion Pack state is process-local, version selection is exact, and no concrete Living OS adapter is included.
- Direct Registry mutation is a low-level operation; coordinated lifecycle and Runtime changes must use Pack Manager or Expansion API.
- Pack Runtime execution is synchronous and in-process; session separation is not an operating-system security sandbox.
- GitHub Actions Python 3.10/3.13 release evidence becomes available only after an authorized push.

## License

MIT License. See [LICENSE](./LICENSE).
