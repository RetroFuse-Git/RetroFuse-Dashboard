# Dashboard Repo Boundary Cleanup — Phase 0 v0.1

**Status:** COMMITTED (no push)
**Date:** 2026-06-23
**Mode:** DASHBOARD_REPO_BOUNDARY_CLEANUP_PHASE0

---

## Summary

Phase 0 formalizes `D:\RETROFUSE_OPS\Dashboard` as a complete, standalone product
root with clear boundaries, product identity documents, and a clean `.gitignore`.

## What Was Done

### Inventory

| Source | Classification |
|--------|---------------|
| `D:\RETROFUSE_OPS\Dashboard` | **DASHBOARD_OWNED** — canonical root |
| `D:\PORTTORETRO_ARCHIVE\PROJECTS\Bolt\Dashboard` | **HISTORICAL_REFERENCE** — does not exist |
| `D:\PORTTORETRO_ARCHIVE\PROJECTS\Dashboard` | **HISTORICAL_REFERENCE** — Unity game project, unrelated |

### Files Created

| File | Purpose |
|------|---------|
| `README.md` | Product readme with quick start, structure, architecture notes |
| `CHANGELOG.md` | Version history from v1.0 through v1.7 |
| `ROADMAP.md` | Planned phases 0–5 and future work |
| `DASHBOARD_PRODUCT_BOUNDARY.md` | Boundary declaration — what Dashboard owns and does not own |
| `.gitignore` | Excludes `.venv/`, `__pycache__/`, `*.bak`, `_Work/`, `logs/`, API dumps, debug files |
| `docs/` | Documentation directory (placeholder for future) |
| `Tools/validation/` | Validation scripts directory (placeholder for future) |

### Exclusions Confirmed

- ❌ Daily Bundle builder kit — **not migrated**
- ❌ SAFEPOINT engine files — **not migrated**
- ❌ Bolt RC2 browser/controller files — **not migrated**
- ❌ Wrapper/CLI infrastructure — **not migrated**
- ❌ No files deleted outside `D:\RETROFUSE_OPS\Dashboard`
- ❌ No files deleted inside `D:\RETROFUSE_OPS\Dashboard` (backups preserved in place, gitignored)

### Design Debt Acknowledged

- Dual-template architecture (embedded `INDEX_HTML` vs `templates/index.html`) remains
  unresolved. Documented in `DASHBOARD_PRODUCT_BOUNDARY.md` and `ROADMAP.md`.

## Validation

| Check | Result |
|-------|--------|
| `python -m py_compile server.py` | ✅ PASS |
| `python -m py_compile app/model_dashboard.py` | ✅ PASS |
| No SAFEPOINT files changed | ✅ Confirmed |
| No Daily Bundle files moved | ✅ Confirmed |
| No Bolt RC2 files moved | ✅ Confirmed |
| No push performed | ✅ Confirmed |
