# Changelog

All notable changes to Universal Learning Engine are documented here.

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
