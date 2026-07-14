# Developer Guide

## Supported environment

- Python 3.10 and 3.13 are the release CI targets.
- Install with `python -m pip install -r requirements-dev.txt`.
- `requirements.txt` defines compatible ranges; `constraints.txt` records the
  tested direct dependency set for the Stable line.

## Configuration

Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. The optional
`OPENAI_MODEL` value defaults to `gpt-4.1-mini`. Never commit `.env` or
`.streamlit/secrets.toml`.

## Architecture

- `app.py`: composition, OpenAI boundary, validation, session coordination, and
  preserved learning renderers
- `ui/`: official theme, navigation, Dashboard, Review, and reusable components
- `adaptive.py`: pure deterministic learning recommendations
- `analytics.py`: pure deterministic session analytics
- `expansion/`: independent Expansion Platform and synchronous Pack Runtime
- `tests/`: unit, integration, Streamlit, compatibility, and stability tests

The UI package may read prepared dictionaries but must not redefine adaptive or
analytics policy. Expansion code must remain independent of Streamlit and the
learning engine.

## Common commands

```bash
python -m compileall -q app.py adaptive.py analytics.py expansion ui tests
python -m unittest discover -v
python -m coverage run -m unittest discover -v
python -m coverage report
streamlit run app.py
```

## Change policy

1. Review `MASTER_DESIGN.md`, `ARCHITECTURE.md`, and the active version roadmap.
2. Preserve released behavior unless a new approved contract explicitly changes it.
3. Add a focused test before structural or failure-path changes.
4. Keep learner content and provider exception payloads out of logs.
5. Run compilation, complete regression, coverage, and the health check.
6. Update canonical documentation in the same change.
7. Treat commit, push, tag, release, and deploy as separately authorized steps.

## UI development

`assets/ule.css` is trusted static source. Do not interpolate topics, generated
content, answers, secrets, Pack state, or exception text into HTML or CSS.
Use normal Streamlit text functions for dynamic content. Preserve visible focus,
mobile single-column behavior, and reduced-motion support.

## Dependency updates

Update compatible ranges and `constraints.txt` only after the complete Python
3.10/3.13 matrix succeeds. Review Streamlit DOM selectors, OpenAI Responses and
chat compatibility calls, startup health, and branch coverage after every update.
