# Architecture

## Current architecture

Universal Learning Engine v0.6 remains a single-process Streamlit application on the preserved v0.5 baseline. `app.py` contains configuration access, prompt construction, OpenAI integration, response parsing and validation, session integration, scoring, reliability logging, and UI rendering. `adaptive.py` contains pure deterministic v0.4 adaptive rules. `analytics.py` contains pure deterministic v0.5 Learning Analytics.

```text
User
  │ topic, count, difficulty, answers
  ▼
Streamlit UI
  │ validated generation request
  ▼
Prompt builder ──► OpenAI API
                     │ JSON text
                     ▼
               Parser and validator
                     │ validated lesson
                     ▼
              Streamlit session state
                     │
                     ▼
             CBT, feedback, summary
```

After a round completes, validated answer evidence flows through `adaptive.py` to produce Round Status, pattern signals, difficulty advice, and recovery advice. There is no database, background worker, external analytics system, account system, or durable learner profile.

The retained completed summaries then flow read-only through `analytics.py`. It normalizes valid records independently and produces latest-round, current-topic, overall-session, topic, difficulty, confidence, pattern, and strength/weakness views. Analytics do not call OpenAI, modify adaptive records, select a learning action, or persist a second copy of state.

## Runtime boundaries

### Presentation boundary

Streamlit renders topic and configuration inputs, generated lesson sections, CBT controls, feedback, progress, and the round summary. UI rendering reads and updates session state but does not persist it outside the active session.

### Generation boundary

The application builds one text prompt from the topic, requested question count, and difficulty. The model is instructed to return only the defined JSON lesson structure and not to introduce recovery, analytics, dashboard, decision-engine, or expansion-pack content.

### External API boundary

The OpenAI client receives the resolved API key and model. The Responses interface is primary. A chat-completions call is a conditional compatibility fallback, not an unconditional retry.

### Validation boundary

All model output crosses a parser and lesson validator before it becomes session data. This boundary owns JSON extraction, required-field checks, question-count normalization, choice validation, duplicate detection, answer-index validation, and explanation validation.

### State boundary

Streamlit session state contains:

| Key | Purpose |
|---|---|
| `lesson` | Current validated generated lesson |
| `answers` | Selected choice index by question index |
| `current_question_index` | Current CBT position |
| `current_feedback` | Feedback for the active question |
| `round_finished` | Whether summary mode is active |
| `cbt_round_id` | Separates widget keys between retries |
| `is_generating` | Prevents repeated generation-button activation |
| `answer_confidence` | Optional reported confidence by question index |
| `adaptation_records` | Completed summaries grouped by session-local topic key |
| `latest_adaptive_summary` | Current advisory output rendered after the round result |
| `adaptation_error` | Non-fatal analysis failure state |
| `pending_recommended_difficulty` | Explicitly queued selector update |
| `analytics_cache` | Revision-bound derived v0.5 analytics output |
| `analytics_revision` | Invalidates derived analytics when source evidence changes |

State normalization removes invalid answers, bounds the active index, repairs invalid flags, and clears malformed feedback.

## Configuration architecture

- `.env` may populate local environment variables.
- Existing environment variables are not overwritten by the fallback `.env` loader.
- Streamlit Secrets are consulted when an environment value is absent.
- `OPENAI_API_KEY` has no built-in default.
- `OPENAI_MODEL` defaults to `gpt-4.1-mini`.
- `.streamlit/config.toml` defines presentation theme only.

## Error behavior

- Missing API configuration and dependencies produce controlled runtime errors.
- Invalid model JSON and invalid lesson data produce user-facing validation errors.
- Authentication, permission, quota, billing, payment, and rate-limit failures do not trigger a second API call.
- Likely transient connection or service failures may trigger one fallback call.

## Security and privacy boundary

API secrets are excluded from tracked source through `.gitignore`. The repository includes examples containing placeholders only. The current application does not intentionally persist learner content, but topics and generated requests are sent to the configured OpenAI API.

## v0.4 adaptive boundary

Adaptive analysis occurs only after the existing scoring path and never bypasses input, output, or scoring validation. The pure adaptive module receives completed-round evidence and returns advisory dictionaries without Streamlit or API dependencies.

The interface applies a recommended difficulty through a queued state value before the selector widget is created. This avoids autonomous generation and preserves explicit learner control. Learning Timeline, Knowledge Retention, and Decision Engine capabilities remain outside this architecture.

## v0.5 analytics boundary

Analytics execute only after the existing v0.4 result and adaptive summary paths. `adaptation_records` remains the sole completed-round source of truth. Analytics outputs are derived during rendering and are not stored in a database. v0.6 may retain one revision-bound session cache of derived output; it is invalidated whenever a completed record is added or Home clears the source records.

The pure module owns:

- Required-field validation and independent invalid-record exclusion
- Versioned Round Analytics dictionaries
- Weighted accuracy, round-average accuracy, totals, ranges, and ordered same-topic comparisons
- Confidence coverage and correctness-confidence aggregation
- Topic, difficulty, current-topic, and overall retained-session summaries
- v0.4 signal frequency and recent same-topic repetition
- Evidence summaries with stable rule names and quantitative fields

Strength and weakness classification is limited to topic-and-difficulty groups with at least two rounds and ten answered questions. It does not calculate a Weakness Score or make a decision. The UI renders at most three concise strengths and weaknesses and keeps detailed evidence available.

Analytics failures are caught at the presentation boundary. The complete v0.4 result, adaptive guidance, Retry, Home, and recommendation controls remain available. Existing v0.4 Recovery Priority is preserved but not extended by v0.5.

Overall analytics cover only records still present in the active Streamlit session. Home clears `adaptation_records`, so all derived analytics also disappear. No timestamp, cross-session timeline, retention model, scheduler, notification, Living OS integration, or autonomous action exists.

## v0.6 reliability boundary

The lesson schema and UI flow remain unchanged. Model text must resolve to one
unambiguous JSON object, indices must be exact integers rather than booleans, and
submitted answer evidence is locked while feedback is active. The OpenAI client
uses an explicit timeout with SDK retries disabled so the application owns the
documented single compatibility fallback decision.

Operational logs contain event metadata and failure types only. They do not log
API keys, prompts, generated lesson text, answer text, or raw learner content.
Unexpected exceptions are logged by type and mapped to a stable learner-facing
message.
