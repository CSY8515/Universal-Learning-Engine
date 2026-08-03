# Universal Learning Engine Roadmap

## Roadmap rules

- The implemented v0.4 baseline, including all preserved v0.3.1 behavior, is preserved.
- A roadmap entry is not an implementation.
- Features may enter development only after their requirements and acceptance criteria are approved.
- Missing algorithms, thresholds, schemas, and UI behavior must not be invented.
- Features assigned to later versions must not be implemented early.
- The implemented working-tree version is v1.06; publishing
  remains separately controlled.

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

### v0.5 — Learning Analytics

The released v0.5 baseline is defined by the detailed implemented contract in `ROADMAP_v0.5.md` and is preserved by v0.6.

Implemented v0.5 scope:

- Latest-round analytics
- Current-topic session analytics
- Overall analytics across all records retained in the active Streamlit session
- Weighted accuracy and learning-result summaries
- Round, confidence, and learning-pattern analysis
- Evidence-qualified strength and weakness summaries
- A pure, reusable analytics foundation and additive completed-round UI

v0.5 consumes the session-only results already produced by v0.4. It does not add persistence, autonomous decisions, a Decision Engine, background scheduling, notifications, or Living OS integration. Existing v0.4 Home behavior continues to clear the source records and therefore all derived analytics.

Learning Timeline and Knowledge Retention are not assigned to v0.5 and are not implemented.

Weakness Score, Learning Decision Engine, new Recovery Priority behavior, autonomous actions, database, background scheduling, notifications, Living OS integration, and Expansion features remain unimplemented.

### v0.6 — Quality & Reliability

The implemented and verified v0.6 release strengthens the preserved v0.5
application without adding a new learning capability. It covers scoring
correctness, JSON validation, exception isolation, bounded API behavior,
automated testing, performance, backward-compatible UI fixes, operational
logging, and documentation.

The detailed contract is `ROADMAP_v0.6.md`. Decision Engine expansion, new
Recovery behavior, persistence, Living OS integration, Expansion Platform work,
and learning-flow changes remain excluded.

### v0.7 — Expansion Platform

- Expansion Pack
- Pack Loader
- Pack Registry
- Expansion API
- Living OS Integration

The approved detailed v0.7 implementation contract is `ROADMAP_v0.7.md`.
It also defines the Pack Manager and lifecycle-only common interface required to
coordinate these roadmap components. Actual Living OS functionality remains
excluded.

The v0.7 contract is implemented, verified, and committed on `main` as the
preserved v0.8 baseline. GitHub Release and deployment remain separately
controlled.

### v0.8 - Pack Runtime

- Executable Expansion Pack contract
- Pack Runtime management
- Isolated Pack Sessions
- Stable start and stop lifecycle
- Exact-version and cross-pack independence

The approved detailed v0.8 implementation contract is `ROADMAP_v0.8.md`.
It preserves the v0.7 interface version and management behavior while adding
only synchronous in-process execution. Living OS functionality, network, IPC,
file sharing, synchronization, command execution, persistence, new UI, and
v0.9-or-v1.0 features remain excluded.

### v0.9 — Final Stabilization

- Shared Runtime/Loader transition protection
- Runtime-aware direct-unload prevention
- Structured and sanitized failure context
- Streamlit session repair and atomic completed-round updates
- Bounded dependency ranges and branch-coverage evidence
- Complete compile, regression, and headless health automation
- Release checklist and explicit v1.0 design entry gate

The approved detailed contract is `ROADMAP_v0.9.md`. v0.9 adds no learning feature, persistent state, external integration, background work, new UI, or v1.0 capability. Public Expansion methods and interface version `0.7` remain unchanged.

### v1.0.0 — Stable

- Official ULE Signal Grid interface
- Dashboard Home, Learning, and Review workspaces
- Read-only session Dashboard and evidence-based next-step presentation
- Result readability and selective major-view rendering
- Presentation-layer separation and tested direct dependency constraints
- Developer, security, public API, compatibility, and release documentation
- Stable release verification and publication gates

The approved contract is `ROADMAP_v1.0.md`. v1.0 preserves all v0.9 learning,
session, adaptive, analytics, Expansion, Runtime, public API, and security
behavior. It adds no persistence, new learning algorithm, autonomous action,
external transport, remote Pack capability, or concrete Living OS behavior.

### v1.02 — World Integration

- Nine functional Worlds
- Normalized local World state
- Recovery Sessions, Challenge entry, AI actions, Planner, Library, Management,
  My Learning, and Report

The implemented contract is `ROADMAP_v1.02.md`.

### v1.03 — Learning Flow Integration

- Recovery records, history, duration, and Challenge recommendations
- Independent Challenge Sessions and Results
- Integrated Analytics supplied to AI
- AI Recommendation to Planner goal and Learning schedule
- Planner topic transfer into Learning
- Multi-source Library, integrated My Learning, and all-World Report
- Dashboard, Review, and legacy routing removal

The implemented contract is `ROADMAP_v1.03.md`. v1.03 adds no UI redesign,
background action, notification, autonomous learning, or concrete Living OS
behavior.

### v1.04 — AI Integration & BYOK

- Per-user API key registration, change, deletion, and connection testing
- Session-memory-only key isolation with no repository, backup, or logging path
- AI question, explanation, recommendation, and summary actions
- AI-only disablement when no key is registered
- AI output integration into Planner, Library, My Learning, and Report
- Sanitized, non-fatal AI error handling

The implemented contract is `ROADMAP_v1.04.md`. v1.04 preserves the existing UI
and v1.03 World structure. It adds no shared developer key, durable key storage,
background action, notification, autonomous learning, or concrete Living OS
behavior.

### v1.05 — End-to-End Validation

- Complete nine-World and Report data-flow validation
- Learner-visible button-flow verification
- Supported create/read/update/delete, backup, and restore verification
- BYOK and no-key path verification
- Learner-visible internal-output and unfinished-label inspection
- Full compile, regression, Streamlit, and localhost health verification

The implemented contract is `ROADMAP_v1.05.md`. v1.05 adds verification evidence
only and preserves the complete v1.04 runtime, UI, data schema, Expansion
Platform, and Living OS boundary.

### v1.06 — Localization & User Experience

- Korean learner-facing navigation, controls, guidance, reports, and errors
- Learner-oriented BYOK registration, replacement, confirmed deletion, and
  connection testing
- Selective, category, all-record, and full-reset data management
- Confirmation gates for every destructive data action
- Developer-output and unfinished-label non-exposure verification
- Existing-record compatibility without schema replacement

The implemented contract is `ROADMAP_v1.06.md`. v1.06 preserves the v1.05
learning behavior, World data flow, UI structure, visuals, state schema,
Expansion Platform, and Living OS boundary.

### v1.07 — Official UI / UX

- Central Learning World and nine functional orbital glass domes
- Dedicated World backgrounds and themes in the Living OS visual language
- World-map navigation, persistent interior navigation, Hover, animation,
  transition, and Glass polish
- Korean learner-facing functional surfaces with no developer-output exposure
- Static, repository-owned presentation assets with responsive and
  reduced-motion behavior

The implemented contract is `ROADMAP_v1.07.md`. v1.07 changes the presentation
layer only. The Learning Engine, World data, CRUD, API, BYOK, Analytics, Report,
and learning-flow contracts remain those of v1.06.1.

### v1.08 — Architecture Audit & Implementation Recovery

- Repository-based Database and Database Manager architecture audit
- Closed operational classification Registry and versioned SQLite Data Plane
- Append-only preservation of operational success, failure, recovery, rollback,
  validation, execution, invalid-data, decision, and unresolved evidence
- Database Manager validation, duplicate control, deterministic analysis,
  recommendations, Rule Candidates, Standard Candidates, and reporting
- OS Ecosystem Personal Secretary Core Capability report port and adapter
- Unchanged Streamlit, UI, World state, learner data, Learning Engine, API,
  BYOK, Analytics, Report, Expansion, and Living OS runtime

The implemented contract is `ROADMAP_v1.08.md`. The recovered package remains
independent and inert until explicitly instantiated by an authorized caller.
It adds no automatic event capture, background work, autonomous rule activation,
concrete Personal Secretary behavior, or learner-facing UI.

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
