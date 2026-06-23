# Dashboard Product Boundary

**Last updated:** 2026-06-23
**Phase:** DASHBOARD_REPO_BOUNDARY_CLEANUP_PHASE0

## Canonical Root

The canonical dashboard root is **`D:\RETROFUSE_OPS\Dashboard`**.

This directory is the single source of truth for all OPS Dashboard code,
templates, static assets, validation scripts, maintenance receipts, documentation,
and roadmap artifacts.

## What Dashboard Owns

| Area | Description |
|------|-------------|
| `app/` | Python application modules (model_dashboard.py, app_main.py) |
| `server.py` | FastAPI server with embedded INDEX_HTML fallback |
| `templates/` | HTML templates (index.html — canonical) |
| `static/` | Static assets |
| `Tools/maintenance/` | Maintenance receipts, registry data, phase documentation |
| `Tools/validation/` | Validation scripts (future) |
| `docs/` | Product documentation |
| `README.md`, `CHANGELOG.md`, `ROADMAP.md` | Product identity documents |
| `DASHBOARD_PRODUCT_BOUNDARY.md` | This boundary declaration |
| `.gitignore` | Git ignore rules |
| `requirements.txt` | Python dependencies |
| `BLUEPRINT.md`, `RUN_CONTRACT.json`, `WORKER_BRIEF.md` | Project governance |
| `Start_*.ps1`, `Run_*.ps1`, `Watch_*.ps1` | PowerShell startup/watchdog scripts |
| `_Archive/` | Historical dashboard index snapshots (preserved) |
| `_Forensic/` | Forensic backups of mangled states (preserved) |
| `_Work/` | Runtime work logs (gitignored, preserved in place) |

## What Dashboard Does NOT Own

| Area | Owner | Reason |
|------|-------|--------|
| Daily Bundle builder kit | OPS COO / Bolt | Not dashboard-owned unless separately promoted by explicit future phase |
| SAFEPOINT engine files | SAFEPOINT / Continuity | Dashboard displays SAFEPOINT state but does not own continuity machinery |
| Bolt RC2 browser/controller | Bolt RC2 | Dashboard displays Bolt status but does not own controller files |
| Bolt RC2 Chrome profile | Bolt RC2 | Browser profile is Bolt territory |
| Wrapper/CLI infrastructure | Bolt / Wrapper Registry | Dashboard displays wrapper state but does not own launcher scripts |
| OPS COO orchestrator | OPS COO | Dashboard displays orchestrator telemetry but does not own the orchestrator |
| SMC WRC observer | Symphony / SMC | Dashboard displays WRC status but does not own the observer |
| Provider pricing/quota data | Operator-reported | Dashboard displays but does not guarantee pricing/quota accuracy |

## Historical References (Noncanonical)

- **`D:\PORTTORETRO_ARCHIVE\PROJECTS\Dashboard`** — This is a Unity game project
  (UnityProject/, Branding/, CR/), not the OPS Dashboard. It is a noncanonical
  reference only.
- **`D:\PORTTORETRO_ARCHIVE\PROJECTS\Bolt\Dashboard`** — Does not exist as of
  Phase 0. No historical dashboard files under Bolt.

## Design Debt

1. **Dual-template architecture:** `server.py` embeds an `INDEX_HTML` string constant
   that serves as a fallback when `templates/index.html` is unavailable. The canonical
   template is `templates/index.html`. Both must be kept synchronized. This is
   acknowledged design debt to be resolved in a future phase (see ROADMAP.md).

2. **Backup file proliferation:** The root directory contains many `.bak` and historical
   `server.py` variants. These are preserved for forensic reference but are not part
   of the active product. The `.gitignore` excludes them from version control.

## Boundary Rules

- Dashboard may display OPS state but does not own OPS continuity machinery.
- Dashboard may reference Bolt paths for display purposes but does not own Bolt files.
- No Daily Bundle builder kit files shall be migrated into Dashboard unless
  separately promoted by an explicit future phase.
- No SAFEPOINT/continuity files shall be migrated into Dashboard.
- No Bolt RC2 browser/controller files shall be migrated into Dashboard.
- No generic wrapper/CLI infrastructure shall be migrated into Dashboard unless
  Dashboard directly owns it.
