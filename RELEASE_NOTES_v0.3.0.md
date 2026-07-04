# Universal Learning Engine v0.3.0

Universal Learning Engine v0.3.0 is a **Quality & Reliability Update** for the v0.2 Streamlit MVP.

This release does not add new engines. It focuses on safer CBT grading, stronger JSON validation, API cost protection, and clearer release documentation.

## v0.3 Changes

- CBT grading now uses selected choice index instead of choice text
- Duplicate choice text no longer causes misgrading
- OpenAI API fallback is limited to retry-worthy failures
- JSON parsing and validation are more defensive
- Difficulty prompts now support Easy / Normal / Hard / Nightmare
- Hard and Nightmare prompts discourage simple definition-only questions
- Minimum test suite added
- README, CHANGELOG, VERSION, and LICENSE prepared for release

## Quality & Reliability Update

### CBT Reliability

- Removed `choices.index(choice)` scoring risk
- Added index-based scoring helper
- Added duplicate-choice scoring test

### API Fallback Cost Protection

- No fallback retry for authentication errors
- No fallback retry for API key errors
- No fallback retry for quota, billing, permission, or payment errors
- Fallback is allowed only for retry-worthy connection or timeout style failures

### JSON Reliability

- Required lesson fields are validated
- CBT question count is checked and normalized
- Choice count must be exactly 4
- Answer index must be within `0..3`
- Explanation must be present
- Invalid JSON is handled with a user-facing error message

### Difficulty Reliability

- Easy: basic terms and simple concepts
- Normal: basic concepts plus simple application
- Hard: applied, case-based, comparison, and judgment questions
- Nightmare: harder multi-concept, case-based, and tricky judgment questions

## Fixed Bugs

- Fixed possible CBT misgrading when two choices have the same text
- Reduced unnecessary OpenAI API double-call risk
- Improved JSON extraction from fenced or lightly wrapped model responses

## Known Issues

- OpenAI output quality still depends on model behavior and prompt interpretation
- Streamlit Cloud deployment requires `OPENAI_API_KEY` in Secrets
- Real deployed API generation should be manually verified after deployment

## Next Version: v0.4 Candidates

- Recovery Engine
- Learning Analytics
- Dashboard
- Expansion Pack structure
- Learning history storage
- Review scheduling

## Release Status

Approved as v0.3.0 Release Candidate, pending final GitHub tag/release and Streamlit Cloud deployment verification.
