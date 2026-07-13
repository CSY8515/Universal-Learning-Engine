# Universal Learning Engine v0.4 Adaptive Learning

![Version](https://img.shields.io/badge/version-v0.4-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Streamlit](https://img.shields.io/badge/streamlit-ready-red)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Universal Learning Engine is a Streamlit learning MVP that generates a consistent learning flow for any topic:

Topic → Tutorial → Example → Direct Task → Practice → CBT → Scoring → Result

The current version is **v0.4 Adaptive Learning**, built on the preserved v0.3.1 Quality & Reliability baseline. The release files are prepared, but no commit, tag, GitHub Release, or deployment has been performed.

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

Hard questions emphasize application, comparison, cases, and plausible distractors while connecting at least two concepts. Nightmare questions require a concrete scenario, multi-step reasoning, competing trade-offs, plausible traps, at least three connected concepts, and explanations of both correct and incorrect choices.

## Documentation authority

The repository is the single source of truth. Use these documents in this order:

1. [MASTER_DESIGN.md](./docs/MASTER_DESIGN.md) — frozen v0.2 scope and implemented v0.3.1 baseline
2. [ARCHITECTURE.md](./docs/ARCHITECTURE.md) — current components, state, data flow, and boundaries
3. [MODULE_SPEC.md](./docs/MODULE_SPEC.md) — current logical module contracts
4. [ROADMAP_v0.4.md](./docs/ROADMAP_v0.4.md) — implemented v0.4 contract and acceptance plan
5. [ROADMAP.md](./docs/ROADMAP.md) — overall version boundaries
6. [CHANGELOG.md](./CHANGELOG.md) and release notes — historical change records

If a future proposal conflicts with the implemented baseline, the conflict must be resolved in the canonical documents before implementation.

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

The suite verifies the preserved v0.3.1 behavior, adaptive rule boundaries, confidence categories, topic-isolated progress, recovery precedence, and controlled Streamlit v0.4 flows.

## Explicit exclusions

The following are not implemented in v0.4:

- Recovery content-generation engine
- Learning Analytics or Dashboard
- Learning history persistence or review scheduling
- Expansion Packs
- Login, PDF, OCR, voice, or image features

See [ROADMAP.md](./docs/ROADMAP.md) for approved placement. Roadmap entries are documentation, not implemented functionality.

## Project structure

```text
Universal-Learning-Engine/
├─ app.py
├─ adaptive.py
├─ tests/
│  ├─ __init__.py
│  ├─ test_app_quality.py
│  ├─ test_adaptive.py
│  └─ test_streamlit_v04.py
├─ docs/
│  ├─ ROADMAP.md
│  ├─ ROADMAP_v0.4.md
│  ├─ MASTER_DESIGN.md
│  ├─ ARCHITECTURE.md
│  └─ MODULE_SPEC.md
├─ .streamlit/
│  ├─ config.toml
│  └─ secrets.toml.example
├─ README.md
├─ CHANGELOG.md
├─ RELEASE_NOTES_v0.3.0.md
├─ RELEASE_NOTES_v0.3.1.md
├─ RELEASE_NOTES_v0.4.md
├─ VERSION
├─ requirements.txt
├─ LICENSE
├─ .env.example
└─ .gitignore
```

## Release information

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

## License

MIT License. See [LICENSE](./LICENSE).
