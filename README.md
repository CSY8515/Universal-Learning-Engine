# Universal Learning Engine v0.6 Quality & Reliability

![Version](https://img.shields.io/badge/version-v0.6-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Streamlit](https://img.shields.io/badge/streamlit-ready-red)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Universal Learning Engine is a Streamlit learning MVP that generates a consistent learning flow for any topic:

Topic → Tutorial → Example → Direct Task → Practice → CBT → Scoring → Result

The repository is prepared for the **v0.6 Quality & Reliability** release on the preserved v0.5 Learning Analytics baseline. The runtime version is `v0.6`; publishing operations remain separately controlled.

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

Hard questions emphasize application, comparison, cases, and plausible distractors while connecting at least two concepts. Nightmare questions require a concrete scenario, multi-step reasoning, competing trade-offs, plausible traps, at least three connected concepts, and explanations of both correct and incorrect choices.

## Documentation authority

The repository is the single source of truth. Use these documents in this order:

1. [MASTER_DESIGN.md](./docs/MASTER_DESIGN.md) — canonical design through v0.6
2. [ARCHITECTURE.md](./docs/ARCHITECTURE.md) — current components, state, data flow, and boundaries
3. [MODULE_SPEC.md](./docs/MODULE_SPEC.md) — current logical module contracts
4. [ROADMAP_v0.4.md](./docs/ROADMAP_v0.4.md) — implemented v0.4 contract and acceptance plan
5. [ROADMAP_v0.5.md](./docs/ROADMAP_v0.5.md) — implemented v0.5 analytics contract
6. [ROADMAP_v0.6.md](./docs/ROADMAP_v0.6.md) — approved v0.6 reliability contract
7. [ROADMAP.md](./docs/ROADMAP.md) — overall version boundaries
8. [CHANGELOG.md](./CHANGELOG.md) and release notes — historical change records

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

The 57-test suite verifies preserved v0.5 behavior, adaptive rule boundaries, analytics calculations, strict scoring and JSON boundaries, bounded API fallback, exception sanitization, answer immutability, failure isolation, and controlled Streamlit flows. GitHub Actions is configured to run compile and regression checks on Python 3.10 and 3.13.

## Explicit exclusions

The following are not implemented or expanded in v0.6:

- Learning Decision Engine or Weakness Score
- New Recovery Priority behavior or recovery content-generation engine
- Learning history persistence or review scheduling
- Database, background scheduler, or notifications
- Autonomous learning actions
- Living OS integration
- Separate persistent analytics dashboard
- Expansion Packs
- Login, PDF, OCR, voice, or image features

See [ROADMAP.md](./docs/ROADMAP.md) for approved placement. Roadmap entries are documentation, not implemented functionality.

## Project structure

```text
Universal-Learning-Engine/
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

## License

MIT License. See [LICENSE](./LICENSE).
