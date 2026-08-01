# B10 Phase 2 integration contract

**Status:** s20 BACK IMPLEMENT contract note
**API namespace:** `/api`; `/api/v2` is reserved for breaking changes only.

## HTTP

- Reports and warnings use typed response models and stable operation IDs.
- OpenAPI is an exact additive inventory for the phase-2 REST surface.
- Error responses retain machine-readable `code` and `message` fields.

## Emulator seam

- Deterministic emulator-shaped samples and events feed report and warning services.
- Quarantined quality is exposed as `quarantine`; no synthetic fresh value is emitted.

## T7 rebrowse

- Added or changed valid mappings enter quarantine until acknowledgement.
- Removed, unknown, or stale mappings do not project as normal live data.
- State assertions use stable enum values rather than localized text.

## T10 WebSocket

- Endpoint remains `/api/stream`.
- Six simultaneous clients subscribe independently and receive published frames.
- Reconnect supplies a client-held per-channel cursor and receives replay plus ack.
- Expired cursors produce an explicit `CURSOR_EXPIRED` frame; replay is never silently empty.

## Exclusions

- The approved v1 runtime contains no shore forwarding, ML dependency, prediction, or AI wording.
- Source and generated OpenAPI exclusion scans are separate acceptance checks.
