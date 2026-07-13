# Universal Learning Engine v0.4

Universal Learning Engine v0.4 is the **Adaptive Learning** release. It adds deterministic, session-level learning guidance while preserving the complete v0.3.1 lesson generation, CBT, validation, scoring, feedback, explanation, summary, retry, reset, and API fallback behavior.

## Highlights

- Optional confidence reporting for each CBT answer
- Session-level Round Status and Learning Progress
- Deterministic Learning Pattern analysis
- Bounded Adaptive Difficulty recommendations
- Recovery priority and relative interval recommendations
- Clear evidence explaining each recommendation
- Explicit learner control before a recommended difficulty is applied

## Adaptive Difficulty

The next difficulty recommendation uses completed-round accuracy and reported confidence:

- High accuracy with sufficient medium/high confidence recommends one level higher.
- Developing accuracy keeps the current level.
- Low accuracy recommends one level lower.
- High accuracy with limited confidence evidence keeps the current level and emphasizes confidence-building recovery.

Recommendations move by at most one level and remain bounded between Easy and Nightmare. The application never starts a new lesson or changes difficulty autonomously. The learner must explicitly choose to apply a recommendation.

## Confidence and Learning Patterns

Confidence is optional and self-reported as low, medium, high, or unset. Correctness and confidence produce evidence categories used for these deterministic signals:

- Strong mastery signal
- Fragile success signal
- Developing understanding
- Foundational gap signal
- Overconfidence risk

Signals are evidence summaries, not diagnoses. No AI classifier is used.

## Round Status and Learning Progress

After a round finishes, v0.4 reports:

- Difficulty, correct count, question count, and accuracy
- Reported-confidence distribution
- Learning Pattern evidence
- Same-topic rounds completed in the current session
- Accuracy change from the previous same-topic round

Records are grouped by a normalized topic key and remain only in the active Streamlit session. Home clears the adaptive records.

## Recovery Guidance

Recovery guidance includes:

- High, medium, or low priority
- A relative interval such as before the next round or later in the current session
- The evidence that caused the recommendation
- An explicit statement that no reminder or background schedule was created

v0.4 does not generate a separate recovery lesson.

## Quality and Compatibility

- All v0.3.1 input and lesson validation remains in place.
- CBT scoring remains answer-index based.
- Duplicate choices remain invalid.
- Existing OpenAI API fallback cost protection remains unchanged.
- Adaptive analysis is isolated in pure deterministic functions.
- Adaptive failure does not prevent the existing round result from rendering.
- Confidence is not part of the generated lesson JSON contract and may be left unset.

## Tests

The v0.4 suite covers:

- Existing v0.3.1 parsing, validation, scoring, fallback, and difficulty-prompt behavior
- Confidence normalization and all correctness-confidence categories
- Accuracy and confidence threshold boundaries
- Difficulty bounds and one-level movement
- Pattern classification and recovery-priority precedence
- Topic-normalized session progress
- Preserved Streamlit landing controls
- Optional confidence UI
- Adaptive result rendering
- Explicit recommendation application
- Home cleanup of session adaptation data

## Explicitly Not Included

- v0.5 Decision Engine
- Autonomous AI decisions
- Automatic next-round generation
- Database or cross-session learner profile
- Persistent Learning Timeline
- Long-term Knowledge Retention tracking
- Background jobs, scheduling, reminders, or notifications
- Dashboard, external analytics, or recovery-content engine
- Login, PDF, OCR, voice, image, or Expansion Pack features

## Known Limitations

- Confidence is subjective and self-reported.
- Adaptive state is session-only.
- Five-question rounds produce coarse 20-percentage-point accuracy steps.
- Topic grouping normalizes text but does not perform semantic topic matching.
- Recovery intervals are advisory wording, not scheduled dates.
- Generated lesson quality still depends on the configured OpenAI model.

## Upgrade Notes

- `VERSION` is updated to `v0.4`.
- No new dependency is required.
- No database migration or configuration change is required.
- Existing `OPENAI_API_KEY` and optional `OPENAI_MODEL` configuration remain valid.

## Release Status

Implementation, documentation, automated tests, Streamlit startup, and real OpenAI learning-flow verification are complete. Commit, push, tag, GitHub Release, and deployment require separate approval.
