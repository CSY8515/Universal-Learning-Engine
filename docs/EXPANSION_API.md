# Expansion Public API

## Supported facade

`ExpansionAPI` is the recommended integration surface. It exposes:

- `install(pack)` and `remove(pack_id, version=None)`
- `load(pack_id, version=None)` and `unload(pack_id, version=None)`
- `start(pack_id, version=None)` and `stop(session_id)`
- `session(session_id)` and `sessions()`
- `get(pack_id, version=None)`, `list()`, and `versions(pack_id)`

Pack identity is the exact `(pack_id, version)` pair. Versions are strings and
are not ranked or automatically resolved. Omitting a version is rejected when
more than one matching version is installed.

## Pack contracts

Every Pack implements `ExpansionPack` and returns an immutable `PackManifest`.
An executable Pack additionally implements `ExecutableExpansionPack.execute`
and `terminate`. The current interface version is `0.7`; lifecycle-only v0.7
Packs remain manageable but cannot be started.

## Status and errors

`PackStatus` and `PackSessionStatus` are immutable public snapshots. Session
status never exposes the private mutable `PackSession.state` dictionary.
Consumers should handle the exported `ExpansionError` subclasses rather than
matching human-readable message text.

## Advanced APIs

`PackRegistry`, `PackLoader`, `PackManager`, and `PackRuntime` remain exported for
advanced in-process integrations. Prefer Manager or ExpansionAPI coordination.
Direct Registry mutation is not Runtime-aware and can violate lifecycle
coordination assumptions.

## Security boundary

Packs are trusted Python objects executing synchronously in the application
process. Session separation is not a security sandbox. Do not install or run
untrusted Pack code. There is no network acquisition, signature verification,
dependency resolver, subprocess isolation, or permission model.
