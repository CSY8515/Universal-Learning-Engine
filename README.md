# Universal Learning Engine v0.3.1

![Version](https://img.shields.io/badge/version-v0.3.1-blue)
![Python](https://img.shields.io/badge/python-3.10%2B-green)
![Streamlit](https://img.shields.io/badge/streamlit-ready-red)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

Universal Learning Engine is a Streamlit-based learning MVP that generates a simple learning flow for any topic:

Topic → Tutorial → Example → Practice → CBT → Scoring → Result

v0.3.1 is a **Difficulty Quality Hotfix** on top of the v0.3 Quality & Reliability Update. It does not add new engines. It improves Hard / Nightmare question quality, duplicate-choice validation, and difficulty prompt strength.

## Web Demo

Coming soon.

## GitHub Release

See [RELEASE_NOTES_v0.3.1.md](./RELEASE_NOTES_v0.3.1.md).

## Main Features

- Topic input
- Input validation
- Question count selection
  - 5
  - 10
  - 15
  - 20
- Difficulty selection
  - Easy
  - Normal
  - Hard
  - Nightmare
- OpenAI-powered learning content generation
- Tutorial
- Example
- Direct writing / implementation task
- Practice task
- One-question-at-a-time CBT
- Index-based CBT scoring
- Explanation display
- Round summary
- Retry / Home reset flow

## v0.3 Quality & Reliability Update

- CBT scoring now uses selected choice index instead of choice text
- Duplicate choice text no longer causes misgrading
- OpenAI API fallback is blocked for non-retryable errors
- JSON parsing handles plain JSON, fenced JSON, and lightly wrapped JSON
- Lesson structure is validated before rendering
- Hard / Nightmare difficulty prompts discourage simple definition-only questions
- Minimum test suite added with `unittest`

## v0.3.1 Difficulty Quality Hotfix

- Hard now emphasizes application, comparison, case-based reasoning, and plausible distractors
- Hard questions must connect at least 2 concepts
- Nightmare now emphasizes complex scenario, multi-step reasoning, trap choices, real-world judgment, and competing trade-offs
- Nightmare questions must connect at least 3 concepts
- Nightmare prompts require scenario-based questions
- Explanations are instructed to cover why the correct answer is best and why other choices are wrong
- Duplicate choices are rejected during JSON validation

## Not Included in v0.3

The following features are intentionally not implemented in v0.3:

- Recovery Engine
- Learning Analytics
- Dashboard
- Expansion Pack
- PDF
- Login
- OCR
- Voice
- Image
- Learning history storage
- Review scheduling

## Installation

```bash
pip install -r requirements.txt
```

## Run Locally

```bash
streamlit run app.py
```

## Run Tests

```bash
python -m unittest discover
```

`pytest` is not required for v0.3.

## OpenAI API Key Setup

Do not hardcode your API key in source code.

The app reads the API key in this order:

1. Local `.env`
2. Environment variable `OPENAI_API_KEY`
3. Streamlit Cloud Secrets

### Local `.env`

Copy `.env.example` to `.env`.

```bash
copy .env.example .env
```

Then edit `.env`.

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4.1-mini
```

`.env` is ignored by Git.

### Streamlit Cloud Secrets

In Streamlit Cloud, add this under App Settings → Secrets:

```toml
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-4.1-mini"
```

## Streamlit Cloud Deployment

Main file path:

```text
app.py
```

## Project Structure

```text
Universal_Learning_Engine/
├─ app.py
├─ requirements.txt
├─ README.md
├─ CHANGELOG.md
├─ RELEASE_NOTES_v0.3.0.md
├─ VERSION
├─ LICENSE
├─ .env.example
├─ .gitignore
├─ tests/
│  ├─ __init__.py
│  └─ test_app_quality.py
└─ .streamlit/
   ├─ config.toml
   └─ secrets.toml.example
```

## Release Note

See [RELEASE_NOTES_v0.3.1.md](./RELEASE_NOTES_v0.3.1.md).

## Changelog

See [CHANGELOG.md](./CHANGELOG.md).

## Known Issues

- Real OpenAI generation quality depends on model behavior and prompt interpretation.
- Streamlit Cloud requires `OPENAI_API_KEY` in Secrets.
- Final deployed API generation should be manually verified after deployment.

## Roadmap: v0.4 Candidates

- Recovery Engine
- Learning Analytics
- Dashboard
- Expansion Pack structure
- Learning history storage
- Review scheduling

## License

MIT License. See [LICENSE](./LICENSE).
