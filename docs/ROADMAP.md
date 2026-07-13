# Universal Learning Engine Roadmap

## Roadmap rules

- The implemented v0.3.1 baseline is preserved.
- A roadmap entry is not an implementation.
- Features may enter development only after their requirements and acceptance criteria are approved.
- Missing algorithms, thresholds, schemas, and UI behavior must not be invented.
- Features assigned to later versions must not be implemented early.
- Versions v0.6 through v1.0 remain TBD until separately approved.

## Version sequence

### v0.1 — Initial MVP

Delivered the universal-topic Streamlit structure, generated tutorial and example content, direct and practice tasks, CBT generation, explanations, and OpenAI integration.

### v0.2 — Interactive CBT feature freeze

Delivered question-count and difficulty selection, one-question-at-a-time CBT, answer submission, feedback, summary, retry and reset, and safer response handling. The frozen scope is defined in `MASTER_DESIGN.md`.

### v0.3 and v0.3.1 — Quality & Reliability

Delivered index-based scoring, defensive parsing and validation, API fallback cost protection, tests, strengthened difficulty behavior, and duplicate-choice rejection. No adaptive engine was added.

### v0.4 — Adaptive Learning

Implementation and release documentation are complete in the working tree. Git operations, GitHub Release, and deployment remain pending explicit approval. The detailed contract is `ROADMAP_v0.4.md`.

Concepts assigned to v0.4:

- **Round Status:** a defined representation of the current learning round.
- **Learning Progress:** progress information suitable for adaptive decisions.
- **Confidence Analysis:** analysis derived from approved learner evidence.
- **Learning Pattern:** identification of approved within-learning patterns.
- **Learning Rule Candidates:** explicit candidate rules that can be evaluated before activation.

The implementation uses deterministic session-only data, documented thresholds, advisory recommendations, and explicit learner control. No persistent timeline, autonomous decision, or scheduled recovery behavior is included.

Recovery Engine, Learning Analytics, Dashboard, Expansion Pack structure, persistence, and review scheduling appeared previously as v0.4 candidates. They are not automatically part of the approved Adaptive Learning implementation; each requires explicit scope approval.

### v0.5 — Longitudinal learning candidates

Proposed placement, not implementation approval:

- **Learning Timeline:** ordered learning activity across rounds or sessions.
- **Knowledge Retention:** retention evidence across elapsed time and review activity.

These concepts are placed after v0.4 because they imply durable history, time-aware behavior, and likely review scheduling. Storage, privacy, retention policy, identity, and review requirements must be approved before development.

### v0.6 through v1.0 — TBD

No features are assigned. This range is reserved for future approved planning and must not be populated by assumption.

## v0.4 preparation gates — complete

Implementation may begin only after approval of:

1. Precise definitions for Round Status, Learning Progress, Confidence Analysis, Learning Pattern, and Learning Rule Candidates.
2. Inputs and outputs for each concept.
3. Whether adaptation is limited to the current round or crosses rounds.
4. Deterministic rule behavior, priority, conflict handling, and safety bounds.
5. User-visible behavior and explicit non-goals.
6. State lifecycle and any persistence decision.
7. Backward-compatibility requirements for the v0.3.1 lesson and CBT flow.
8. Unit, integration, regression, and manual acceptance criteria.

## Verification policy

Every version must retain relevant earlier regression tests, add tests for approved behavior, keep documentation synchronized with implementation, and verify that deferred features remain absent.
