# Unity Model Dashboard — Wrapper Registry Phase 1 Applied v0.1

**Status:** APPLIED AND COMMITTED (no push)
**Date:** 2026-06-23
**Mode:** DASHBOARD_WRAPPER_VISIBILITY_PHASE1_APPLY_AND_COMMIT_NO_PUSH

---

## Files Changed

| File | Change |
|------|--------|
| `app/model_dashboard.py` | Added `WRAPPER_REGISTRY` (13 wrappers), `WRAPPER_CLASSES`, `EVIDENCE_STATUSES`, `build_wrapper_registry()`, wrapper chips in model row output |
| `server.py` | Added `build_wrapper_registry` import, `/api/models/wrappers` endpoint, wrapper chips in embedded `INDEX_HTML`, Wrapper Registry section card, JS rendering |
| `templates/index.html` | Added wrapper chips to model cards, Wrapper Registry section card, JS rendering functions with auto-refresh |

## Registry Shape

| Metric | Value |
|--------|-------|
| Total wrappers | 13 |
| Active (main board) | 4 — Ollama Direct, Codex, Claude Code, OpenClaw |
| Catalog-only | 9 — Copilot, Gemini, OpenCode, Aider, Continue, Cursor, Cline/Roo, Goose, Custom |
| Configured | 3 |
| Detected | 3 |
| Enabled | 4 |
| Unknown evidence preserved | 2 (OpenClaw, Copilot) |

## Validation Results

| Check | Result |
|-------|--------|
| `python -m py_compile model_dashboard.py` | ✅ PASS |
| `python -m py_compile server.py` | ✅ PASS |
| `GET /api/models/wrappers` | ✅ 200 — 13 total, 4 active, 9 catalog |
| `GET /api/models/dashboard?mode=home` | ✅ 200 |
| `GET /api/models/dashboard?mode=business` | ✅ 200 |
| `GET /api/models/edit-receipts` | ✅ 200 |
| `GET /api/models/assets` | ✅ 200 |
| `GET /api/models/routing-eligibility` | ✅ 200 |
| No launch endpoint | ✅ Confirmed |
| No settings mutation | ✅ Confirmed |
| No SAFEPOINT/continuity changes | ✅ Confirmed |

## Forbidden Items — Confirmed Not Violated

- ❌ No one-click launch
- ❌ No settings mutation
- ❌ No wrapper selection persistence
- ❌ No catalog-only wrappers on main model cards
- ❌ No SAFEPOINT/continuity changes
- ❌ No hardcoded pricing/quota promises

## Commit

- **SHA:** (see git log)
- **Push:** Not performed
- **Message:** "Apply dashboard wrapper registry phase 1"
