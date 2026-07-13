# Universal Learning Engine v0.7 Expansion Platform Roadmap

## Document status

This document is the approved, implemented, and verified working-tree contract
for v0.7. It preserves the complete v0.6 runtime and adds only the Expansion
Platform assigned to v0.7 by `ROADMAP.md`. Publishing remains separately
controlled.

## 1. Preserved baseline

v0.7 must preserve without redefinition:

- The existing Streamlit learning flow and UI
- The lesson JSON contract, validation, and index-based CBT scoring
- The v0.4 adaptive rules and explicit learner control
- The v0.5 analytics calculations and presentation
- The v0.6 reliability, API fallback, logging, and cache behavior
- All existing public functions and session-state behavior

The Expansion Platform is an independent Python boundary. The existing
`app.py`, `adaptive.py`, and `analytics.py` modules do not depend on it.

## 2. Approved v0.7 scope

v0.7 contains only:

- Expansion Pack common interface
- Pack Registry
- Pack Loader
- Pack Manager
- Pack version identity and exact-version selection
- Expansion API
- Living OS Integration Interface

The Living OS work is limited to a connection interface. No Living OS service,
transport, command, workflow, or product behavior is implemented.

## 3. Common interface contract

Every pack exposes an immutable manifest containing `pack_id`, `name`,
`version`, and `interface_version`. All values are non-empty strings and v0.7
accepts only interface version `0.7`.

Version values are compared as exact strings. v0.7 does not add semantic version
ordering, dependency resolution, upgrade policy, or compatibility ranges.

Every pack implements `on_load()` and `on_unload()`. The common interface defines
lifecycle only. It does not add learning hooks, content types, tutor behavior,
rule execution, or UI extension points.

## 4. Registry contract

- Records are keyed by the exact pair `(pack_id, version)`.
- Multiple versions of one pack may be installed at the same time.
- Registering an existing exact key is rejected.
- Lookup without a version succeeds only when exactly one version exists.
- Registry state is in-process only; no database or durable history is added.
- Returned listings are deterministic and do not expose mutable registry state.

## 5. Loader contract

- Only a pack already present in the Registry can be loaded.
- The Loader validates the common interface and interface version before load.
- An exact pack version cannot be loaded twice.
- Failed `on_load()` calls do not mark a pack as loaded.
- Failed `on_unload()` calls leave the pack marked as loaded.
- Loader failures do not affect the existing learning engine.

## 6. Manager and version contract

- Install validates a pack and adds its exact identity to the Registry.
- Remove unloads the exact version first when necessary, then unregisters it.
- Remove never selects among multiple versions implicitly.
- List and lookup expose installed versions and whether each is loaded.
- No automatic update, remote download, dependency installation, discovery,
  rollback, marketplace, or package publishing is included.

## 7. Expansion API contract

The Expansion API is a facade over the Manager and provides install, remove,
load, unload, exact lookup, and deterministic listing. It does not expose or
modify lesson generation, scoring, adaptive rules, analytics, OpenAI
configuration, or Streamlit session state.

## 8. Living OS Integration Interface contract

The interface defines only `connect(expansion_api)`, `disconnect()`, and the
`connected` status. v0.7 provides no concrete Living OS adapter and performs no
network, process, message, command, authentication, or synchronization work.

## 9. Error and compatibility contract

- Contract, duplicate, missing-pack, ambiguous-version, load, and integration
  failures use stable Expansion Platform exception types.
- Failed operations must not partially report a successful state.
- Importing or using the platform must not initialize Streamlit, OpenAI,
  adaptive analysis, or analytics.

## 10. Acceptance criteria

1. Valid packs can be installed, listed, loaded, unloaded, and removed through
   the Expansion API.
2. Duplicate exact versions and incompatible interface versions are rejected.
3. Multiple installed versions require exact selection.
4. Lifecycle failures preserve consistent Registry and Loader state.
5. The Living OS boundary remains an interface with no concrete functionality.
6. Existing v0.6 tests remain passing without changing existing UI or APIs.
7. New tests cover every approved Expansion Platform component.
8. Version and canonical documentation describe the implemented v0.7 boundary.

## 11. Explicit exclusions

- Actual Living OS functionality
- New or redesigned UI
- AI Tutor, Voice, 3D Learning, Memory Curve, Knowledge Engine
- Rule Engine or Decision Engine expansion
- New learning flow, lesson fields, scoring, adaptive, or analytics behavior
- Database, durable persistence, remote pack repository, background work,
  notifications, automatic updates, or dependency resolution
- Any v0.8-or-later capability
