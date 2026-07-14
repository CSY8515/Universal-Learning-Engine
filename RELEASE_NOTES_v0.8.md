# Universal Learning Engine v0.8 Pack Runtime

## Status

The v0.8 implementation is committed on `main` and present on `origin/main`. A v0.8 tag, GitHub Release, and deployment are not recorded in this repository and remain separately controlled.

## Added

- Optional executable contract layered on the v0.7 `ExpansionPack`
- Synchronous in-process Pack Runtime
- One isolated active Pack Session per exact pack identity
- Private per-session state and immutable public status snapshots
- Pack start, stop, session lookup, and deterministic session listing
- Runtime-aware unload and removal flow
- Execution, termination, lifecycle, compatibility, and independence tests

## Compatibility

The interface version remains `0.7`. Lifecycle-only v0.7 packs remain valid and
retain install, list, lookup, load, unload, and remove behavior. The complete
existing learning Runtime, UI, Streamlit session, lesson/API flow, adaptive
guidance, analytics, and reliability behavior remain unchanged.

## Lifecycle guarantees

- Only installed, loaded executable packs can start.
- One exact `(pack_id, version)` can own at most one active session.
- Execution failure publishes no active session and attempts local cleanup.
- Termination failure preserves running, loaded, and installed state.
- Unload and removal terminate the exact active session before pack unload.
- Reentrant Loader lifecycle transitions are rejected.
- Different packs and exact versions receive separate session and state objects.

## v0.8 boundary

- Execution is synchronous, in-process, and non-durable.
- Pack-state separation is not an operating-system security sandbox.
- No concrete Living OS adapter or behavior is included.
- No network, IPC, shared files, synchronization, or command execution exists.
- No discovery, remote repository, marketplace, dependency resolution,
  automatic update, rollback, worker, scheduler, or automatic restart exists.
- No new UI, learning hook, Streamlit integration, cross-pack messaging, v0.9,
  or v1.0 functionality is included.

## Verification

- All 80 automated tests pass: 68 preserved tests and 12 v0.8 Pack Runtime tests.
- Python compilation passes.
- Headless Streamlit startup and health endpoint pass.
- `app.py`, `adaptive.py`, and `analytics.py` remain byte-for-byte unchanged.
