# Changelog

## v1.9 — Frontend Template Hardening (2026-06-23)

- Replaced embedded ~2500-line INDEX_HTML with _read_template_fallback() template reader
- templates/index.html is now the single frontend source of truth
- server.py reduced by ~2500 lines (from 4274 to ~1770)
- Added Tools/validation/validate_dashboard_phase3.ps1 validation script
- Updated DASHBOARD_PRODUCT_BOUNDARY.md to reflect resolved template debt
- All existing UI features preserved: wrapper chips, Wrapper Registry, Effective Settings, gear drawer, model cards, Home/Business mode

## v1.8 — Effective Settings Intelligence (2026-06-23)

- Effective Settings Intelligence Phase 2 implemented
- Per-model effective settings with source stack (factory default, Modelfile, runtime, wrapper)
- 5 settings groups: core, sampling, prompt/session, server, persistence
- Hazard profiles: cost-sensitive, settings-sensitive, needs profile badges
- Ollama parameter intelligence documentation (runtime, persistent, server examples)
- GET /api/models/settings-intelligence endpoint
- Effective Settings section in Models tab with risk summary bar
- Home Mode shows simplified core values; Business Mode shows full provenance
- Hazard/profile badges on model cards
- Effective settings chips (ctx, temp, output, timeout) on model cards
- No mutation endpoint added

## v1.7 — Lineage Gate (2026-06-23)

- Wrapper Registry Phase 1 applied (13 wrappers, active/catalog separation, model card chips)
- CSS leak repair applied
- Settings gear drawer with Displayed Wrappers section
- UI integration repair
- P1 visual refinement (fleet bar, mode strip, risk heat, route flow)

## v1.6 — Model Dashboard (2026-06-16)

- Model dashboard with fleet health, model lanes, settings provenance, route flow, risk heat
- Mode-aware dashboard (Home/Business)
- Asset inventory with provider policy guardrails
- Routing eligibility with tier definitions
- Governed edit receipts

## v1.5 — SAFEPOINT & Orchestrator (2026-06-10)

- SAFEPOINT candidate review surface
- OPS COO orchestrator telemetry
- Bolt RC2 controller adjudication
- SAFEPOINT revalidation endpoint

## v1.4 — Bolt RC2 Integration (2026-06-04)

- Bolt controller state, cmdlog, heart bundles
- Startup lineage verification
- Secretary status, backlog, quarantine
- Worker arbiter and authority boundary proof

## v1.3 — SMC WRC Observer (2026-06-01)

- SMC WRC live observer status
- Window-aware checkpoint monitoring
- Seed-aware classification counts

## v1.2 — Browser Telemetry (2026-05-27)

- RC1/RC2/RC3 detection
- Renderer and GPU pipeline summary
- Live process scan via PowerShell

## v1.1 — Daily Bundle (2026-05-22)

- Daily Bundle install surface
- Validation gates
- Install lanes topology

## v1.0 — Initial OPS Dashboard (2026-05-15)

- Snapshot & Overview card
- OPS Signals pills
- Disks & Storage
- SAFEPOINT archive summary
- Alpha capture
- Ops Notes
