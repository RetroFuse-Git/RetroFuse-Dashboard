# RetroFuse Dashboard Worksurface Blueprint Template v0.1

## Worksurface Identity

- Worksurface name: Dashboard
- Worksurface path: `D:\RETROFUSE_OPS\Dashboard`
- Folder owner: RetroFuse Operations
- Audience: Dashboard Runtime Workers / Local Workers
- Applies to: Web app server, watchdog, status API, and UI operations.

## Authority Boundary

- This blueprint defines local floor doctrine for the Dashboard worksurface.
- **Non-Git Environment:** All persistent source changes must be receipt-sealed as external artifacts.
- Authority_effect defaults to `NONE`.
- Ready_for_production defaults to `false`.
- External verifier owns PASS.

## Read Roots / Write Roots

- Read roots:
  - `D:\RETROFUSE_OPS`
  - `D:\PORTTORETRO_ARCHIVE`
- Write roots:
  - `D:\RETROFUSE_OPS\Dashboard`
  - `D:\RETROFUSE_OPS\_CI_ReviewStaging\templates`
  - `D:\RETROFUSE_OPS\_CI_ReviewStaging\receipts`
  - `D:\RETROFUSE_OPS\_CI_ReviewStaging\handoff`
- Path rule:
  - Copy operator-provided paths exactly.
  - Do not normalize, reconstruct, or silently repair underscores or root prefixes.

## Model Route

Every task packet must include:

- Preferred
- Allowed fallback
- Blocked
- Reason
- Write authority

If `MODEL ROUTE` is missing, return `BLOCKED_MODEL_ROUTE_MISSING`.

## Runtime & Server Lifecycle

- **Server:** `server.py` (Flask/Python).
- **Binding:** Use machine-agnostic local binding (e.g., `0.0.0.0` or env-driven).
- **Machine-Agnosticism:** Do not hardcode machine-specific paths, IP addresses, or hostnames. Use environment variables for local configuration.
- **Restart Policy:** Do not restart the server or watchdog unless explicitly authorized in the task packet.        

## Watchdog Integrity

- **Watchdog:** `Run_RetroFuse_OPS_Dashboard_Watchdog.ps1`.
- **Reporting:** Distinguish clearly between "stale data" and "active error".
- **UNKNOWN > False Green:** If status is ambiguous or timestamp is stale, report `UNKNOWN`. Never claim `READY` or `PASS` without verified fresh evidence.
- **Process Scans:** Bounded scans only. Enumerate only Dashboard-related Python and PowerShell PIDs. No broad system process scans.

## API & Schema Data (`api_*.json`)

- API data files are treated as transient runtime artifacts.
- Do not mutate API JSON schemas freehand; use deterministic emitters if available.
- Verify file presence and freshness before aggregating status reports.

## Artifact Retention & Backup Policy

- **Non-Git Tracking:** High-volume backups (`*.bak_*`) are preserved as historical evidence.
- **Cleanup:** Do not delete or rotate historical backups unless specifically targeted.
- **Source Edits:** Every edit to `server.py` or scripts must result in a receipt-sealed external artifact record in CI ReviewStaging.

## Allowed Actions

- Read application source, logs, and `api_*.json` status files.
- Apply bounded hotfixes to server or watchdog logic (receipt-sealed).
- Aggregate and summarize dashboard status reports.
- Produce concise JSON-first receipts.
- Verify machine-agnosticism in configuration changes.

## Forbidden Actions

- No broad system process scans.
- No passive focus stealing (web app context).
- No production readiness claims.
- No deletion of historical artifacts.
- No hardcoding of machine-local paths.

## JSON-First Receipt + Human Summary

Worker final output must be JSON first.

Required receipt fields:

- `model_primary_requested`
- `model_primary_used`
- `model_backup_allowed`
- `model_backup_used`
- `model_escalation_allowed`
- `model_escalation_used`
- `model_reason`
- `authority_effect`
- `ready_for_production`
- `human_summary`

Human summary rule:

- Brief, operator-readable, and limited to 13 lines.
- No introduction of facts absent from the JSON receipt.

## Verification Rules

- Verify machine-agnosticism for all configuration changes.
- Confirm server/watchdog PIDs before reporting runtime status.
- External verifier owns PASS.
- Identify verification steps before acting.

## Standard Handoff Format

- Status
- Scope
- Files changed
- Validation
- Machine-agnosticism check
- Remaining risks
- Next recommended action

## Floor Reminder

Model strength does not replace local doctrine.
Machine-agnostic design and receipt-sealed external artifacts govern the Dashboard worksurface.