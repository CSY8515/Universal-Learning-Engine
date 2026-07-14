# Universal Learning Engine v0.8 Pack Runtime Roadmap

## Document status

This document is the approved implementation contract for v0.8. It preserves
the complete v0.7 Expansion Platform and adds the final in-process execution
structure required before v1.0. It does not authorize v0.9 or v1.0 features.

## 1. Preserved v0.7 baseline

v0.8 preserves without redefinition:

- The Streamlit runtime, UI, lesson contract, session-state keys, and API flow
- The adaptive and analytics modules and all existing public functions
- Exact `(pack_id, version)` identity and ambiguous-version rejection
- The `ExpansionPack`, `PackManifest`, Registry, Loader, Manager, Expansion API,
  and Living OS interface contracts
- Interface version `0.7`, so existing v0.7 packs remain installable, loadable,
  unloadable, removable, and listable without modification
- In-process, non-durable operation with no discovery or external integration

## 2. Approved v0.8 scope

v0.8 adds only:

- An optional executable-pack contract layered on `ExpansionPack`
- A Pack Runtime coordinating synchronous start and stop operations
- One isolated active Pack Session per exact installed pack identity
- Immutable public session-status snapshots
- Runtime-aware unload and removal behavior
- Failure-safe execution and termination state transitions
- Exact-version and cross-pack execution independence

## 3. Executable pack contract

`ExecutableExpansionPack` extends the existing lifecycle-only `ExpansionPack`.
It adds `execute(session)` and `terminate(session)` callbacks. Existing v0.7
packs are not required to implement these callbacks and remain valid management
packs; only executable packs may start a runtime session.

`execute` and `terminate` are synchronous in-process callbacks. v0.8 does not
create threads, workers, subprocesses, network connections, IPC channels, or
command runners. Callback return values do not define a result protocol and are
not exposed through the Expansion API.

## 4. Pack Session contract

- A session belongs to exactly one `(pack_id, version)` identity.
- A generated opaque `session_id` identifies one execution instance.
- Identity fields are immutable after construction.
- Each session owns a new mutable state dictionary passed only to its pack.
- Session state is not returned by public status or listing operations.
- Only one session may be active for one exact pack identity at a time.
- Different pack identities never receive the same session or state object.
- Session state is process-local and discarded after successful termination.

The in-process model provides ownership separation through runtime references; it
is not a security sandbox against malicious Python pack code.

## 5. Pack Runtime contract

- Start resolves an exact installed identity using the v0.7 Registry rules.
- Start requires the pack to be loaded and to implement the executable contract.
- Start creates an isolated session and invokes `execute` exactly once.
- Successful execution publishes one running session status.
- Failed execution attempts `terminate` for best-effort cleanup and publishes no
  active session.
- A second start for the same exact identity is rejected while it is running.
- Stop resolves an active `session_id` and invokes `terminate` exactly once.
- Successful termination removes and discards that session.
- Failed termination leaves the session active so state never reports a false
  successful stop.
- Session listings are immutable and deterministic.

## 6. Loader and lifecycle stability

The v0.7 Loader remains responsible only for pack-level load state. The v0.8
Runtime is responsible only for execution-session state. A pack must be loaded
before it can run, and it cannot remain running after a successful unload.

Manager unload and removal terminate the exact active session first. If
termination fails, unload/removal stops and both the pack and its session remain
active and installed. If termination succeeds but `on_unload` fails, the pack
remains loaded and installed while the already terminated session remains
stopped. No operation reports success for a transition that failed.

## 7. Manager and Expansion API additions

The existing methods and return types remain unchanged. The following additive
operations are exposed:

- `start(pack_id, version=None)`
- `stop(session_id)`
- `session(session_id)`
- `sessions()`

These operations expose immutable `PackSessionStatus` values. They do not expose
learning-runtime state, pack-owned session data, or Living OS behavior.

## 8. Independence contract

- Registry, Loader, and Runtime state remain owned by one Manager instance.
- Exact pack versions have independent load and runtime state.
- Starting, stopping, or failing one pack does not change another pack session.
- Pack callbacks receive no Manager, Registry, Loader, Expansion API, Streamlit,
  OpenAI, adaptive, analytics, or Living OS reference from the runtime.

Because execution is in-process, v0.8 guarantees platform state isolation and
reference separation, not operating-system-level isolation.

## 9. Acceptance criteria

1. Every v0.7 test passes unchanged.
2. A legacy lifecycle-only pack remains fully manageable.
3. A loaded executable pack can start and stop one isolated session.
4. Start is rejected for unloaded, legacy-only, or already running packs.
5. Execution failure leaves no active session.
6. Termination failure preserves active session, loaded state, and installation.
7. Unload and removal terminate a running session before pack-level unload.
8. Multiple packs and exact versions have separate session objects and state.
9. Runtime/API status values are immutable and deterministic.
10. Existing runtime modules and UI remain byte-for-byte unchanged.
11. Compilation, the complete regression suite, and headless startup pass.

## 10. Explicit exclusions

- Concrete Living OS integration or adapter
- Network communication, IPC, shared files, synchronization, or command execution
- Filesystem pack discovery, remote repository, marketplace, or download
- Durable pack, runtime, or session persistence
- Background threads, workers, schedulers, or automatic restart
- Dependency resolution, updates, rollback, or semantic version selection
- Cross-pack messaging, shared session state, or orchestration
- New UI, learning hooks, lesson changes, or Streamlit session integration
- v0.9 or v1.0 functionality
