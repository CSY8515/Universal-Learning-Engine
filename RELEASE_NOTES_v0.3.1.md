# Universal Learning Engine v0.3.1

v0.3.1 is a focused hotfix for CBT difficulty quality.

No new engine was added. This release only improves prompt quality and validation around Hard and Nightmare CBT generation.

## Changes

- Hard difficulty now strongly emphasizes:
  - application
  - comparison
  - case-based reasoning
  - plausible distractors
  - at least 2 connected concepts

- Nightmare difficulty now strongly emphasizes:
  - complex scenario
  - multi-step reasoning
  - trap choices
  - real-world judgment
  - competing trade-offs
  - at least 3 connected concepts
  - explanations that cover both correct and incorrect choices

## Fixed

- Hard questions could be too close to simple definition questions
- Nightmare could be insufficiently different from Hard
- Duplicate choice text is now rejected during lesson validation

## Known Issues

- Actual question quality still depends on OpenAI model behavior
- Final quality should be manually checked with real API calls for several topics

## Upgrade Notes

- VERSION updated to `v0.3.1`
- README and CHANGELOG updated
- No Streamlit deployment setting changes required
