# Universal Learning Engine v0.6 — Quality & Reliability

v0.6 is a reliability release over the preserved v0.5 Learning Analytics
baseline. It adds no new learning capability or learning-flow structure.

## Highlights

- Strict integer-only CBT scoring indices
- Immutable submitted answers and reported confidence during feedback
- Safer single-object JSON extraction and normalized duplicate-choice detection
- Explicit 60-second API timeout and application-owned single fallback decision
- Sanitized learner-facing exception messages
- Privacy-conscious operational event logs
- Reduced repeated analytics calculation within the active session
- GitHub Actions compile and regression matrix for Python 3.10 and 3.13

## Reliability improvements

- Boolean values can no longer pass as integer CBT answer indices.
- Submitted answers and reported confidence are locked while feedback is active.
- Plain, fenced, and lightly wrapped JSON remains accepted when it contains one
  unambiguous lesson object.
- Multiple top-level objects, non-object payloads, empty provider text, and
  normalized duplicate choices are rejected with controlled errors.
- The OpenAI client uses a 60-second timeout and disables hidden SDK retries.
- Authentication, permission, quota, billing, request, and rate-limit errors do
  not trigger a second API call; eligible transient failures may use one fallback.
- Provider exception details are not exposed to learners.
- Operational logs record event metadata without API keys, prompts, lessons, or
  answer content.
- Derived Learning Analytics are reused until completed-round evidence changes
  and are cleared with their source records by Home.

## Verification

- 57 automated tests passed with zero failures on local Python 3.13.14.
- Existing v0.5 unit and Streamlit regression tests remain passing.
- Python compilation passed for application and test modules.
- Streamlit started headlessly and returned HTTP 200 `ok` from its health endpoint.
- The rendered landing UI retained the v0.5 controls and produced no browser
  console warnings or errors during the release review.
- JSON validation, exception sanitization, API fallback bounds, submitted-answer
  immutability, analytics caching, and reset behavior have focused coverage.
- CI automation is configured for Python 3.10 and 3.13 and runs after repository push.

## Compatibility

The complete v0.5 CBT, recovery, adaptive learning, learning analytics,
recommendation, generated lesson JSON fields, UI controls, Retry, and Home flow
remain preserved.

## Exclusions

v0.6 adds no new learning capability, Decision Engine behavior, Recovery behavior,
persistence, Living OS integration, Expansion Platform feature, or new UI flow.

## Known limitations

- Generated content quality and live provider availability remain external model
  and service dependencies.
- Deterministic acceptance does not require a paid live OpenAI request.
- Learning records and derived analytics remain limited to the active Streamlit
  session and are cleared by Home.
- Dependency versions use compatible lower bounds rather than a lock file.
- The API timeout is a fixed 60-second application policy in v0.6.

## Next Version

v0.7 Expansion Platform

- Expansion Pack
- Pack Loader
- Pack Registry
- Expansion API
- Living OS Integration
