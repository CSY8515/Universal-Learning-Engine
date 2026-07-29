# Universal Learning Engine v1.04

## AI Integration & BYOK contract

v1.04 completes the learner-controlled OpenAI boundary on the released v1.03
World flow. It does not redesign the interface or change the existing World
structure.

## Implemented scope

### BYOK lifecycle

- Register a user's OpenAI API key in Management.
- Replace the current session key.
- Delete the current session key.
- Test the connection with one bounded Responses API request.
- Retain the key only in the current Streamlit session's server memory.
- Exclude the key from World state, `.ule_data`, backup export, logs, tracked
  configuration, commits, releases, and developer-owned deployment settings.

### AI behavior

- AI question
- AI explanation
- AI recommendation
- AI summary
- Controlled AI-only disablement when no key is registered
- Sanitized error handling that leaves the application and non-AI Worlds active

### Learning-flow integration

```text
Learning
  -> AI history
  -> Planner recommendation connection
  -> Library resources
  -> My Learning statistics
  -> Report
```

Successful AI results use the existing normalized AI history and Library
records. Recommendation conversion remains an explicit learner action and
creates idempotent Planner evidence. Planner-to-Learning, My Learning, and Report
continue to consume the retained v1.03 flow.

## Security boundary

The deployed application provides no shared developer OpenAI API key. The key
input is masked, cleared after submission, never rendered back, and never
included in provider error messages. Raw provider payloads, JSON, debug
information, internal state, and stack traces are not learner-facing.

## Explicit exclusions

- Durable API key storage
- Shared developer API keys
- UI redesign
- World background changes
- Hover, Animation, or Glass changes
- Background or autonomous AI actions
- Model migration
- New learning algorithms
- Concrete Living OS behavior

## Verification

- API key input validation
- Registration, replacement, deletion, and connection-state tests
- Bounded Responses API connection-test contract
- No-key AI-only disablement
- AI question, explanation, recommendation, and summary availability
- Sanitized failure behavior
- Key exclusion from normalized World state
- AI output to Library, Planner, My Learning, and Report regression coverage
- Complete compile, regression, localhost health, and rendered-World checks

## Official OpenAI references

- Responses API and Python SDK:
  https://developers.openai.com/api/docs/guides/text
- API error handling:
  https://developers.openai.com/api/docs/guides/error-codes
- API key safety:
  https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety
