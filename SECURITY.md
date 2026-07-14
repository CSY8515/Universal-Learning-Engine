# Security Policy

## Supported release line

Security fixes are accepted for the current v1.0 Stable line. Historical v0.x
releases are maintained as compatibility records rather than active security
release lines.

## Reporting

Do not publish API keys, learner content, generated private content, Pack Session
state, or provider exception payloads in a public issue. Report the affected
version, reproduction steps using synthetic data, and the security boundary
involved through the repository owner's private security-reporting channel.

## Application boundaries

- Topics and generation prompts are sent to the configured OpenAI API.
- Learner records are retained only in the active Streamlit session.
- `.env` and `.streamlit/secrets.toml` must remain untracked.
- Model output is untrusted and must pass validation before normal rendering.
- Operational logs must not include prompts, generated lessons, answers, secrets,
  session state, or raw provider/callback exceptions.
- Official CSS is static repository content. Dynamic learner content must use
  normal Streamlit rendering rather than unsafe HTML.

## Expansion boundary

Expansion Packs execute trusted Python code synchronously in process. The Pack
Runtime is not an operating-system sandbox and cannot safely contain malicious
code. Remote acquisition and untrusted Pack execution are unsupported.

## Dependency policy

Runtime dependencies use bounded compatibility ranges and a tested direct
constraint set. Dependency changes require Python 3.10/3.13 regression, compile,
coverage, health, API compatibility, and static secret review before release.
