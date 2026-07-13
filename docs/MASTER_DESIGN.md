# Universal Learning Engine Master Design

## Status and purpose

This document defines the frozen v0.2 feature boundary and the implemented v0.3.1 Quality & Reliability baseline. It records what the repository does today; it does not authorize future functionality.

Current version: **v0.4**  
Runtime entry point: `app.py`  
Interface: Streamlit  
Persistence: Streamlit session state only

## Design principles

1. **Preserve released behavior.** Later work must not silently remove or redefine an implemented v0.3.1 feature.
2. **Keep version boundaries explicit.** Future capabilities remain unimplemented until their version scope and acceptance criteria are approved.
3. **Use one universal flow.** Topic-specific behavior is generated from the supplied topic rather than hardcoded into separate engines.
4. **Validate before rendering.** Model output is untrusted and must pass structural and value validation.
5. **Grade by stable identity.** CBT answers are compared by index, not display text.
6. **Protect API cost and failure clarity.** A second API call is attempted only for failures classified as retryable.
7. **Keep secrets outside source.** Credentials come from local environment configuration or Streamlit Secrets.
8. **Separate records from plans.** Release notes and changelog describe history; roadmap documents describe approved future direction.

## v0.2 feature freeze

The v0.2 product boundary is an interactive, session-based learning flow for a user-provided topic.

### Frozen user flow

1. Enter a topic.
2. Select 5, 10, 15, or 20 CBT questions.
3. Select a difficulty.
4. Generate a lesson containing tutorial, example, direct task, practice, and CBT questions.
5. Answer one CBT question at a time.
6. Receive correctness feedback and an explanation.
7. View a round summary.
8. Retry the round or return home.

### Frozen lesson contract

The generated lesson contains:

- `topic`: non-empty text
- `tutorial`: non-empty text
- `example`: non-empty text
- `direct_task`: non-empty text
- `practice`: non-empty text
- `cbt`: a non-empty list of question objects

Each CBT question contains:

- `question`: non-empty text
- `choices`: exactly four non-empty text values
- `answer_index`: integer from 0 through 3
- `explanation`: non-empty text

### Frozen exclusions

v0.2 does not include durable learning history, recovery, analytics, dashboard, review scheduling, login, document export, OCR, voice, image learning, or extension packs.

## v0.3 Quality & Reliability master design

v0.3 preserves the v0.2 product flow and strengthens correctness at system boundaries.

### Input reliability

- Topics are trimmed before use.
- Empty topics are rejected.
- Topics longer than 80 characters are rejected.
- Supported question counts are restricted to 5, 10, 15, and 20.
- Supported UI difficulties are Easy, Normal, Hard, and Nightmare.

### Model-output reliability

- Plain JSON is accepted.
- A complete fenced JSON block is unwrapped before parsing.
- Light surrounding text is tolerated by extracting the outermost JSON object.
- Invalid JSON produces a controlled data-format error.
- Required lesson fields and their non-empty text values are validated.
- CBT must be a non-empty list.
- Excess questions are truncated to the requested count with a notice.
- A short question list is retained with a notice instead of being fabricated.
- Choices, answer indices, and explanations are validated before rendering.

### Scoring reliability

- The selected choice index is stored.
- Correctness is determined by comparing the selected index with `answer_index`.
- Display text is never used to locate or infer the selected answer.
- v0.3.1 rejects duplicate choice text after trimming.

### API failure policy

The primary call uses the OpenAI Responses interface. A chat-completions fallback may be attempted only when the first failure appears transient, such as a connection, timeout, temporary service, server, or service-unavailable error.

Fallback is blocked for status codes 400, 401, 403, 404, and 429 and for messages indicating authentication, API-key, permission, quota, billing, payment, or rate-limit problems.

### Difficulty quality

- **Easy:** definitions, basic terms, and beginner concepts with simple distinct distractors.
- **Normal:** concept understanding, basic application, and simple comparison.
- **Hard:** application, comparison, case-based reasoning, at least two connected concepts, plausible distractors, and no simple definition-only questions.
- **Nightmare:** concrete scenarios, multi-step reasoning, at least three connected concepts, real-world judgment, competing trade-offs, tempting trap choices, and explanations covering why the best answer is correct and alternatives are wrong.

### Session behavior

The current lesson, answers, current question, feedback, round completion, round identifier, and generation flag are held in Streamlit session state. State is normalized before CBT rendering. Retry resets the round while retaining the lesson; home reset clears the lesson and the round.

## v0.3.1 acceptance baseline

The baseline is preserved when:

- The documented learning flow remains available.
- All four difficulties and all four question counts remain selectable.
- Invalid generated data cannot reach normal rendering unchecked.
- Answer scoring remains index-based.
- Duplicate choices remain invalid.
- Non-retryable API failures do not trigger fallback.
- Existing reset and summary behavior remains functional.
- The current unit tests continue to pass.

## Explicitly deferred

No adaptive rules, learner model, confidence calculation, learning pattern analysis, rule-candidate evaluation, timeline, retention calculation, durable storage, dashboard, or recovery behavior exists in v0.3.1. Their appearance in the roadmap must not be interpreted as implementation.

## v0.4 Adaptive Learning design

v0.4 adds a deterministic, session-only advisory layer while preserving the v0.3.1 generation and CBT flow.

- Confidence is optional and self-reported as low, medium, high, or unset.
- Completed answers produce Round Status metrics and evidence categories.
- Completed rounds are grouped by a normalized topic key for same-session Learning Progress.
- Learning Pattern signals are calculated with approved deterministic thresholds.
- Difficulty may be recommended one level higher or lower, bounded by Easy and Nightmare.
- A recommendation changes the next difficulty selector only after explicit user action.
- Recovery guidance consists of a priority, relative interval wording, evidence, and an explicit statement that nothing was scheduled.
- Home clears all adaptive state. No state survives the Streamlit session.
- Adaptive-analysis failure must not prevent the v0.3.1 round result from rendering.

The adaptive layer does not call an AI classifier and does not implement a Decision Engine, recovery-content engine, database, timeline, retention model, scheduler, notification, or autonomous action.
