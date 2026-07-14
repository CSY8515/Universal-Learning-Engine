# Universal Learning Engine v0.9 Final Stabilization Roadmap

## Document status

This document is the approved implementation contract for v0.9. It preserves the complete v0.8 learning application and Expansion Pack Runtime while establishing the final stability and release-evidence baseline required before v1.0 design approval.

## 1. Preserved v0.8 baseline

v0.9 preserves:

- The Streamlit learning UI, lesson schema, scoring, feedback, Retry, and Home flow
- Adaptive and analytics rules, thresholds, outputs, and session-only boundary
- Expansion interface version `0.7` and lifecycle-only v0.7 Pack compatibility
- Exact `(pack_id, version)` identity and existing Expansion API methods
- Synchronous in-process execution and one active session per exact identity
- No persistence, discovery, external transport, background work, or Living OS behavior

## 2. Approved v0.9 scope

v0.9 adds only:

- A shared internal cross-layer transition guard for Loader and Runtime
- Runtime-aware protection against direct Loader unload
- Reentrant lifecycle/runtime transition rejection
- Structured, sanitized lifecycle and execution error context
- Observable execute-cleanup failure state without exposing callback payloads
- Streamlit session metadata repair and atomic completed-round recording
- Complete CBT and confidence widget-state cleanup on Retry/Home transitions
- Bounded runtime and development dependency ranges
- Branch coverage reporting, complete Expansion compilation, and CI health checks
- Synchronized release documentation and an explicit v1.0 entry checklist

## 3. State-transition contract

Registry remains the installed-state authority, Loader remains the loaded-state authority, and Runtime remains the active-session authority. The shared internal coordinator owns no duplicate installed, loaded, or session state. It tracks only lifecycle transitions, runtime transitions, and active runtime identities so conflicting operations can be rejected.

For one exact identity:

- Lifecycle and runtime transitions cannot overlap.
- A running Pack cannot be unloaded directly through its Loader.
- Start cannot publish a session until `execute` succeeds.
- Stop removes a session only after `terminate` succeeds.
- Execute failure publishes no session and attempts cleanup once.
- Cleanup failure is recorded on the raised stable error and logged by exception type only.
- Termination failure preserves the session, loaded state, and installation.
- Different identities retain independent state.

## 4. Session-state contract

- Existing session keys retain their meanings.
- Invalid container, flag, index, revision, cache, and error-code values are repaired before use.
- Completed-round evidence, learning progress, analytics revision, and cache invalidation are prepared before source records are replaced.
- A failed adaptive build does not append a partial record or advance the revision.
- Internal exception messages are not retained in `adaptation_error`.
- Retry removes both CBT and confidence widget keys.
- Home continues to clear all adaptive and analytics source state.

## 5. Error contract

`PackLoadError` and `PackExecutionError` retain their existing types and constructor compatibility. They add stable operation, pack id, and version attributes. `PackExecutionError` also exposes a boolean `cleanup_failed` indicator. Public messages contain no callback exception text, Pack Session state, API keys, learner content, or other private payloads. Original exceptions remain available through Python exception chaining for controlled diagnostics.

## 6. Verification contract

- Preserve all 80 v0.8 tests.
- Add focused cross-layer and session-atomicity tests.
- Compile `app.py`, pure learning modules, `expansion/`, and tests.
- Run the full suite with branch coverage and maintain at least the recorded 84% project baseline.
- Run CI on Python 3.10 and 3.13.
- Start Streamlit headlessly and require a healthy `/_stcore/health` response.
- Verify no secrets, tokens, private learner records, or sensitive exception payloads are tracked.

## 7. Acceptance criteria

1. All 90 automated tests pass.
2. Python compilation passes for every runtime and test module.
3. Branch coverage is at least 84%, with the changed error module fully covered and focused Runtime/Loader transition scenarios present.
4. The Streamlit health endpoint returns HTTP 200 and `ok`.
5. Existing public Expansion API methods and interface version `0.7` remain unchanged.
6. The v0.8 learning UI and behavior regressions pass unchanged.
7. Documentation, version, dependency bounds, and release state agree.
8. Security review finds no tracked secret or sensitive runtime payload.
9. Commit, push, tag, GitHub Release, and deployment remain separately authorized.

## 8. Explicit exclusions

- Any v1.0 feature or early v1.0 implementation
- New learning behavior, adaptive thresholds, analytics rules, or UI redesign
- Persistent learner, Pack, Runtime, or Session state
- Database, scheduler, worker, automatic restart, or notification
- Pack discovery, marketplace, remote download, dependency resolution, update, or rollback
- Network, IPC, shared files, synchronization, commands, or cross-Pack messaging
- Concrete Living OS implementation
- Authentication, login, export, PDF, OCR, voice, image, or 3D learning
