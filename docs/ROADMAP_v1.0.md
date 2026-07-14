# Universal Learning Engine v1.0 Stable Roadmap

## Status

This document is the approved implementation contract for the first Stable
release. v1.0 is a production-quality completion release, not a feature
expansion release.

## Preserved baseline

v1.0 preserves the complete v0.9 learning, session, adaptive, analytics,
Expansion Platform, Pack Runtime, error, and security contracts. The Expansion
interface version remains `0.7` and lifecycle-only v0.7 Packs remain compatible.

## Approved scope

- Official ULE Signal Grid dark interface
- Dashboard as the session Home screen
- Dashboard, Learning, and Review navigation
- Compact result metrics and collapsed detailed review content
- Session-safe navigation metadata and queued view transitions
- Static trusted styling with responsive, focus, and reduced-motion rules
- Presentation-layer extraction without domain or Expansion rewrites
- Tested direct dependency constraints for the Stable release line
- Developer, security, public API, and release documentation
- Complete regression, compilation, health, UI, performance, and security review

## Dashboard contract

The Dashboard presents Today's Learning, Current Topic, Recommended Next Step,
Accuracy, Recovery Priority, Recent Round, Weakness Summary, Learning Progress,
and Recent Activity. It reads existing session evidence and never mutates the
adaptive or analytics source records.

Dashboard navigation does not clear learning data. The preserved Home reset
continues to clear the lesson, completed evidence, derived analytics, and widget
state. Dashboard data is not durable and never claims cross-session history.

## Recommendation contract

The primary recommendation is derived from existing deterministic adaptive
evidence. It is labeled as evidence-based session guidance and is never
presented as an AI Decision Engine. Applying a recommended difficulty still
requires explicit learner action.

## Public API contract

`ExpansionAPI` is the recommended public facade. Existing exports, methods,
signatures, immutable status types, structured exception types, exact-version
behavior, and interface version `0.7` remain compatible. Registry, Loader,
Manager, and Runtime remain available as advanced low-level APIs.

## Explicit exclusions

- Persistence, accounts, durable history, timeline, or retention models
- New adaptive or analytics thresholds
- AI Decision Engine, Weakness Score, or autonomous learning actions
- New OpenAI request types or lesson schema changes
- Remote Packs, dependency resolution, marketplace, or concrete Living OS work
- Network, IPC, subprocess, command, background, or asynchronous Pack execution
- Authentication sandbox for untrusted Packs
- PDF, OCR, voice, image, 3D, or frontend-framework migration

## Acceptance criteria

1. Existing v0.9 behavior and tests remain compatible.
2. Dashboard is the initial Home screen and is session-only.
3. Navigation cannot accidentally clear learning evidence.
4. Home and Retry retain their clearing contracts.
5. Official UI is dark, responsive, keyboard-visible, and restrained.
6. Detailed results remain available without dominating the default page.
7. Expansion public API and interface version remain compatible.
8. Python 3.10 and 3.13 CI, branch coverage, and health checks pass.
9. Security and release reviews find no secret or private-payload regression.
10. Version, documentation, release notes, and checklist agree on `v1.0.0`.
