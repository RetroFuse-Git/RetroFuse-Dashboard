# RetroFuse OPS Dashboard server.py (v1.7_lineage_gate)
# - Snapshot & Overview: includes OPS Signals pills (4)
# - Browser Telemetry: collapsible RC1/RC2/RC3/Renderers/GPU (NO pills here)
# - Disks, SAFEPOINT, Alpha, Notes: restored
# - Bolt Lineage Gate: approved patch carried onto v1.7 baseline
#
# Design goals:
# - ASCII-only embedded HTML (avoid mojibake / unicodeescape issues)
# - Robust snapshot discovery in STATUS_DIR (doesn't assume a single filename)
# - RC1 detection: ungoogled-chromium on D:\ungoogled-chromium_*\chrome.exe

from __future__ import annotations

import json
import os
import re
import subprocess
import shutil
import time
import hashlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from app.model_dashboard import build_model_dashboard, build_edit_receipt, save_edit_receipt, list_edit_receipts, build_asset_inventory, build_routing_eligibility, build_mode_aware_dashboard, build_wrapper_registry, build_settings_intelligence

APP_VERSION = "v1.7_lineage_gate"
SAFEPOINT_PROOF_MAX_AGE_SECONDS = 24 * 60 * 60

OPS_ROOT = Path(r"D:\RETROFUSE_OPS")
STATUS_DIR = OPS_ROOT / "Status" / "RFCC"

# Ops signals JSON (produced by DailyCheck)
OPS_SIGNALS_JSON = STATUS_DIR / "ops_signals.json"

# Alpha capture location
ALPHA_RAW_DIR = OPS_ROOT / "Alpha" / "Raw"

# SAFEPOINT roots
ARCHIVE_ROOTS = [
    Path(r"D:\PORTTORETRO_ARCHIVE\SAFEPOINT_ENGINE\SAFEPOINTS"),
]

# RC2 root marker (for "not distinct yet" note)
RC2_ROOT_MARKER = Path(r"D:\PORTTORETRO_ARCHIVE\PROJECTS\Bolt\RC2")

# Bolt RC2 controller paths
BOLT_ROOT = Path(r"D:\PORTTORETRO_ARCHIVE\PROJECTS\Bolt")
BOLT_SAFEPOINTS_DIR = BOLT_ROOT / "Artifacts" / "SAFEPOINTS"
BOLT_SHELL_ROOT = BOLT_ROOT / "RC2" / "Shell" / "BoltShell"
BOLT_HEART_DIR = BOLT_ROOT / "_DailyBundles" / "HeartBundles"
BOLT_STATE = BOLT_SHELL_ROOT / "controller_state.json"
BOLT_CMDLOG = BOLT_SHELL_ROOT / "cmdlog.jsonl"
BOLT_LOCK = BOLT_SHELL_ROOT / "controller.lock"
BOLT_STARTUP_RECEIPT = BOLT_ROOT / "RC2" / "Logs" / "startup_receipt_latest.md"
BOLT_PROVENANCE = BOLT_ROOT / "RC2" / "Logs" / "startup_provenance.jsonl"
BOLT_SECRETARY_STATUS = BOLT_ROOT / "_DailyBundles" / "SecretaryState" / "secretary_status.json"
BOLT_WORKER_ARBITER = BOLT_ROOT / "_DailyBundles" / "SecretaryState" / "worker_arbiter.jsonl"
BOLT_WORKER_CONSUMED = BOLT_ROOT / "_DailyBundles" / "SecretaryState" / "worker_consumed.jsonl"
BOLT_AUTHORITY_PACKETS = BOLT_ROOT / "_DailyBundles" / "AuthorityState" / "authority_packets.jsonl"
BOLT_CLEANUP_RECEIPT = BOLT_ROOT / "_DailyBundles" / "cleanup_receipt.md"
BOLT_PROMPT_TRANSPORT_DIR = BOLT_ROOT / "_DailyBundles" / "SecretaryState" / "worker_prompt_transport"
BOLT_RETENTION_POLICY = BOLT_ROOT / "retention_policy.json"
BOLT_CHECKPOINTER_REPORT = BOLT_ROOT / "_DailyBundles" / "SecretaryState" / "checkpointer_validation" / "latest_report.json"
BOLT_SAFEPOINT_REPORT = BOLT_ROOT / "_DailyBundles" / "SecretaryState" / "safepoint_validation" / "latest_report.json"
BOLT_SAFEPOINT_VALIDATOR = BOLT_ROOT / "Tools" / "validate_bolt_safepoint.py"
BOLT_SESSION_BACKLOG_DIR = BOLT_ROOT / "_DailyBundles" / "_SessionBacklog"
BOLT_QUARANTINE_DIR = BOLT_ROOT / "_DailyBundles" / "_Quarantine"
# OPS COO orchestrator telemetry paths
ORCH_LOG_DIR = OPS_ROOT / "Logs" / "OPS_COO"
ORCH_LATEST = ORCH_LOG_DIR / "OpsCOO_Daily_Orchestrator_Latest.json"
ORCH_LOCK = ORCH_LOG_DIR / "OpsCOO_Daily_Orchestrator.lock"

# SMC WRC observation paths
SMC_DD_ROOT = Path(r"D:\PORTTORETRO_ARCHIVE\PROJECTS\Symphony\Projects\SMC_DDriveRecovery")
SMC_WRC_OBS_DIR = SMC_DD_ROOT / "_recovery" / "scan_state" / "wrc_observation"
SMC_WRC_CURRENT_STATUS = SMC_WRC_OBS_DIR / "WRC_CurrentStatus.json"

TEMPLATE_INDEX = OPS_ROOT / "Dashboard" / "templates" / "index.html"
PROJECT_BOARD_CACHE = OPS_ROOT / "Dashboard" / "api_debug_4b.json"
PLANES_REGISTRY_DIR = OPS_ROOT / "Registry" / "OPS_COO" / "Registration"
WORKER_EVENTS_DIR = OPS_ROOT / "Registry" / "OPS_COO" / "State" / "WorkerEvents"

# If you have a canonical DailyCheck snapshot name, you can set it here.
# Otherwise, the server will scan STATUS_DIR for the newest JSON file.
PREFERRED_SNAPSHOT_FILES = [
    "DailyCheck_latest.json",
    "DailyCheck_snapshot.json",
    "dailycheck_latest.json",
    "latest.json",
]


app = FastAPI(title="RetroFuse OPS Dashboard", version=APP_VERSION)


_BROWSER_PROCS_CACHE: Dict[str, Any] = {"expires_at": 0.0, "value": []}
_SAFEPOINT_CACHE: Dict[str, Any] = {"expires_at": 0.0, "value": []}
_SAFEPOINT_CANDIDATE_CACHE: Dict[str, Any] = {"expires_at": 0.0, "value": []}
_BOLT_AUX_CACHE: Dict[str, Any] = {
    "expires_at": 0.0,
    "backlog_count": 0,
    "quarantine_count": 0,
}


def _iso_now_local() -> str:
    # Keep offset in output
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _parse_utc_ts(value: str) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _read_json(path: Path) -> Optional[Any]:
    try:
        if not path.exists():
            return None
        raw = path.read_bytes()
        last_error: Optional[Exception] = None
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le"):
            try:
                return json.loads(raw.decode(encoding))
            except Exception as exc:
                last_error = exc
        if last_error:
            return None
    except Exception:
        return None


def _read_markdown_kv(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    out: Dict[str, str] = {}
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        for line in content.splitlines():
            m = re.match(r"^\-\s+([^:]+):\s*(.*)$", line)
            if m:
                out[m.group(1).strip()] = m.group(2).strip()
    except Exception:
        pass
    return out


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not path.exists():
        return rows
    try:
        for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                rows.append(row)
    except Exception:
        return []
    return rows


def _latest_cleanup_receipt() -> Dict[str, Any]:
    if not BOLT_CLEANUP_RECEIPT.exists():
        return {}
    try:
        lines = BOLT_CLEANUP_RECEIPT.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return {}

    blocks: List[List[str]] = []
    current: List[str] = []
    for raw in lines:
        line = raw.rstrip()
        if line.startswith("## Cleanup Receipt "):
            if current:
                blocks.append(current)
            current = [line]
            continue
        if current:
            current.append(line)
    if current:
        blocks.append(current)
    if not blocks:
        return {}

    latest = blocks[-1]
    out: Dict[str, Any] = {"header": latest[0]}
    m = re.match(r"^## Cleanup Receipt\s+(.+)$", latest[0])
    if m:
        out["receipt_utc"] = m.group(1).strip()
    for line in latest[1:]:
        if not line.startswith("- ") or ":" not in line:
            continue
        key, value = line[2:].split(":", 1)
        out[key.strip()] = value.strip()
    return out


def _load_retention_policy() -> Dict[str, Any]:
    data = _read_json(BOLT_RETENTION_POLICY)
    return data if isinstance(data, dict) else {}


def _safe_sha256(path: Path) -> str:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest().upper()
    except Exception:
        return ""


def _latest_safepoint_artifact() -> Dict[str, Any]:
    if not BOLT_SAFEPOINTS_DIR.exists():
        return {}
    try:
        zips = sorted(
            (p for p in BOLT_SAFEPOINTS_DIR.glob("*_FULL.zip") if p.is_file()),
            key=_safe_stat_mtime,
            reverse=True,
        )
    except Exception:
        return {}
    if not zips:
        return {}
    zip_path = zips[0]
    stem = zip_path.name.replace("_FULL.zip", "")
    receipt_path = BOLT_SAFEPOINTS_DIR / f"{stem}_RECEIPT.json"
    return {
        "zip_path": str(zip_path),
        "zip_name": zip_path.name,
        "zip_sha256": _safe_sha256(zip_path),
        "zip_mtime": datetime.fromtimestamp(zip_path.stat().st_mtime).astimezone().isoformat(timespec="seconds"),
        "receipt_path": str(receipt_path) if receipt_path.exists() else "",
        "receipt_name": receipt_path.name if receipt_path.exists() else "",
    }


def _run_bolt_safepoint_validator() -> Dict[str, Any]:
    if not BOLT_SAFEPOINT_VALIDATOR.exists():
        return {
            "ok": False,
            "error": f"Validator missing: {BOLT_SAFEPOINT_VALIDATOR}",
        }
    try:
        cp = subprocess.run(
            [sys.executable, str(BOLT_SAFEPOINT_VALIDATOR), "--json"],
            cwd=str(BOLT_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception as exc:
        return {"ok": False, "error": f"Validator execution failed: {exc}"}

    stdout = (cp.stdout or "").strip()
    stderr = (cp.stderr or "").strip()
    try:
        report = json.loads(stdout) if stdout else {}
    except Exception:
        report = {}
    ok = cp.returncode == 0 and isinstance(report, dict) and bool(report)
    return {
        "ok": ok,
        "returncode": cp.returncode,
        "report": report if isinstance(report, dict) else {},
        "stderr": stderr,
        "stdout": stdout[:4000],
    }


def _build_bolt_adjudication_snapshot(
    state: Dict[str, Any],
    receipt: Dict[str, str],
    secretary: Dict[str, Any],
    boot_status: str,
    boot_status_reason: str,
) -> Dict[str, Any]:
    conformance = _read_json(BOLT_CHECKPOINTER_REPORT)
    conformance = conformance if isinstance(conformance, dict) else {}
    safepoint = _read_json(BOLT_SAFEPOINT_REPORT)
    safepoint = safepoint if isinstance(safepoint, dict) else {}
    current_safepoint = _latest_safepoint_artifact()
    arbiter_rows = _read_jsonl(BOLT_WORKER_ARBITER)
    consumed_rows = _read_jsonl(BOLT_WORKER_CONSUMED)
    authority_rows = _read_jsonl(BOLT_AUTHORITY_PACKETS)
    retention_policy = _load_retention_policy()
    cleanup_receipt = _latest_cleanup_receipt()

    accepted_rows: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for row in arbiter_rows:
        if row.get("accepted") is not True:
            continue
        key = (str(row.get("task_id") or ""), str(row.get("result_utc") or ""))
        if not all(key):
            continue
        prev = accepted_rows.get(key)
        if prev is None or str(row.get("decided_utc") or "") >= str(prev.get("decided_utc") or ""):
            accepted_rows[key] = row

    consumed_keys = {
        (str(row.get("task_id") or ""), str(row.get("result_utc") or ""))
        for row in consumed_rows
        if row.get("task_id") and row.get("result_utc")
    }
    authority_keys = {
        (
            str(((row.get("metadata") or {}) if isinstance(row.get("metadata"), dict) else {}).get("task_id") or ""),
            str(((row.get("metadata") or {}) if isinstance(row.get("metadata"), dict) else {}).get("result_utc") or ""),
        )
        for row in authority_rows
        if isinstance(row, dict)
    }

    latest_accepted = None
    if accepted_rows:
        latest_accepted = max(
            accepted_rows.values(),
            key=lambda row: str(row.get("decided_utc") or ""),
        )

    stalled_imports: List[Dict[str, Any]] = []
    for key, row in accepted_rows.items():
        consumed = key in consumed_keys
        imported = key in authority_keys
        if not consumed or not imported:
            stalled_imports.append({
                "task_id": key[0],
                "result_utc": key[1],
                "reason": row.get("reason", ""),
                "consumed": consumed,
                "authority_imported": imported,
            })
    stalled_imports.sort(key=lambda row: (row["result_utc"], row["task_id"]))

    ttl_seconds = 0
    transient_classes = retention_policy.get("artifact_classes")
    if isinstance(transient_classes, dict):
        transient_cfg = transient_classes.get("transient_transport")
        if isinstance(transient_cfg, dict):
            try:
                ttl_seconds = int(transient_cfg.get("ttl_seconds") or 0)
            except Exception:
                ttl_seconds = 0

    cleanup_blocked: List[Dict[str, Any]] = []
    now_ts = time.time()
    if BOLT_PROMPT_TRANSPORT_DIR.exists():
        for path in sorted(BOLT_PROMPT_TRANSPORT_DIR.glob("*.prompt.txt")):
            task_id = path.name.split(".", 1)[0]
            age_seconds = max(0, int(now_ts - _safe_stat_mtime(path)))
            authority_imported = any(key[0] == task_id for key in authority_keys)
            if ttl_seconds and age_seconds >= ttl_seconds and not authority_imported:
                cleanup_blocked.append({
                    "task_id": task_id,
                    "path": str(path),
                    "age_seconds": age_seconds,
                    "authority_imported": authority_imported,
                })

    conformance_level = str(conformance.get("conformance_level") or "UNPROVEN")
    passed_all_base = bool(conformance.get("passed_all_base", False))
    safepoint_level = str(safepoint.get("conformance_level") or "UNPROVEN")
    safepoint_passed = bool(safepoint.get("passed_all_base", False))
    safepoint_validated_utc = str(safepoint.get("validated_utc") or "")
    safepoint_validated_dt = _parse_utc_ts(safepoint_validated_utc)
    safepoint_validation_age_seconds = (
        max(0, int((datetime.now(timezone.utc) - safepoint_validated_dt.astimezone(timezone.utc)).total_seconds()))
        if safepoint_validated_dt else None
    )
    safepoint_proof_fresh = (
        safepoint_validation_age_seconds is not None
        and safepoint_validation_age_seconds <= SAFEPOINT_PROOF_MAX_AGE_SECONDS
    )
    safepoint_results = safepoint.get("results") if isinstance(safepoint.get("results"), dict) else {}
    safepoint_select = safepoint_results.get("select_artifact") if isinstance(safepoint_results.get("select_artifact"), dict) else {}
    safepoint_receipt = safepoint_results.get("verify_receipt") if isinstance(safepoint_results.get("verify_receipt"), dict) else {}
    validated_zip_path = str(((safepoint_select.get("artifacts") or {}) if isinstance(safepoint_select.get("artifacts"), dict) else {}).get("zip_path") or "")
    validated_receipt_path = str(((safepoint_select.get("artifacts") or {}) if isinstance(safepoint_select.get("artifacts"), dict) else {}).get("receipt_path") or "")
    validated_zip_sha = str(((safepoint_receipt.get("artifacts") or {}) if isinstance(safepoint_receipt.get("artifacts"), dict) else {}).get("actual_zip_sha256") or "")
    safepoint_lineage_clear = bool(
        safepoint_passed
        and current_safepoint
        and current_safepoint.get("zip_path") == validated_zip_path
        and current_safepoint.get("zip_sha256") == validated_zip_sha
    )
    secretary_session = str(secretary.get("startup_session_id") or "")
    receipt_session = str(receipt.get("startup_session_id") or "")
    session_match = bool(receipt_session and secretary_session and receipt_session == secretary_session)
    replay_boundary_clear = boot_status == "READY" and session_match

    degraded_reasons: List[str] = []
    if not passed_all_base:
        degraded_reasons.append("Checkpointer conformance is not proven.")
    if not safepoint_passed:
        degraded_reasons.append("SAFEPOINT conformance is not proven.")
    if safepoint_passed and not safepoint_proof_fresh:
        degraded_reasons.append("SAFEPOINT proof is stale.")
    if safepoint_passed and not safepoint_lineage_clear:
        degraded_reasons.append("SAFEPOINT artifact drift detected after last validation.")
    if not replay_boundary_clear:
        degraded_reasons.append("Startup lineage and replay boundary are not strictly proven.")
    if stalled_imports:
        degraded_reasons.append(f"Authority import is stalled for {len(stalled_imports)} accepted worker result(s).")
    if cleanup_blocked:
        degraded_reasons.append(f"Cleanup is blocked for {len(cleanup_blocked)} stale prompt transport artifact(s).")
    degraded_highlights: List[str] = []
    if stalled_imports:
        stalled_ids = ", ".join(row["task_id"] for row in stalled_imports[:5])
        suffix = " ..." if len(stalled_imports) > 5 else ""
        degraded_highlights.append(f"Stalled authority import: {stalled_ids}{suffix}")
    if cleanup_blocked:
        cleanup_ids = ", ".join(row["task_id"] for row in cleanup_blocked[:5])
        suffix = " ..." if len(cleanup_blocked) > 5 else ""
        degraded_highlights.append(f"Cleanup blocked for: {cleanup_ids}{suffix}")
    if not passed_all_base:
        degraded_highlights.append("Conformance gate failed.")
    if not safepoint_passed:
        degraded_highlights.append("SAFEPOINT gate failed.")
    if safepoint_passed and not safepoint_proof_fresh:
        degraded_highlights.append(
            f"SAFEPOINT proof stale: {safepoint_validation_age_seconds or 0}s old exceeds {SAFEPOINT_PROOF_MAX_AGE_SECONDS}s."
        )
    if safepoint_passed and not safepoint_lineage_clear:
        degraded_highlights.append(f"SAFEPOINT drift: {current_safepoint.get('zip_name', 'unknown')} no longer matches validated proof.")
    if not replay_boundary_clear:
        degraded_highlights.append("Replay boundary proof is unclear.")

    truths = [
        {
            "label": "Startup lineage",
            "truth": "READY" if boot_status == "READY" else boot_status,
            "why": boot_status_reason,
        },
        {
            "label": "Checkpointer conformance",
            "truth": conformance_level,
            "why": f"Latest proof at {conformance.get('validated_utc', 'unavailable')} with passed_all_base={passed_all_base}.",
        },
        {
            "label": "SAFEPOINT conformance",
            "truth": safepoint_level,
            "why": f"Latest SAFEPOINT proof at {safepoint_validated_utc or 'unavailable'} with passed_all_base={safepoint_passed}.",
        },
        {
            "label": "SAFEPOINT proof freshness",
            "truth": "FRESH" if safepoint_proof_fresh else "STALE",
            "why": (
                f"Validation age is {safepoint_validation_age_seconds}s against a {SAFEPOINT_PROOF_MAX_AGE_SECONDS}s limit."
                if safepoint_validation_age_seconds is not None else "SAFEPOINT validation timestamp is unavailable."
            ),
        },
        {
            "label": "SAFEPOINT lineage",
            "truth": "MATCHED" if safepoint_lineage_clear else "DRIFTED",
            "why": (
                f"Validated ZIP {Path(validated_zip_path).name if validated_zip_path else 'n/a'} with SHA {validated_zip_sha or 'n/a'}."
                if safepoint_passed else "SAFEPOINT proof is not yet passing."
            ),
        },
        {
            "label": "Latest accepted worker boundary",
            "truth": (
                f"{latest_accepted.get('task_id')} accepted with {latest_accepted.get('reason')}"
                if latest_accepted else "No accepted worker result found."
            ),
            "why": (
                f"Latest accepted result decided at {latest_accepted.get('decided_utc')} by {latest_accepted.get('decided_by')}."
                if latest_accepted else "worker_arbiter.jsonl has no accepted rows."
            ),
        },
        {
            "label": "Cleanup law",
            "truth": "ACTIVE" if not cleanup_blocked else "BLOCKED",
            "why": (
                f"Latest cleanup receipt {cleanup_receipt.get('receipt_utc', 'unavailable')} removed {cleanup_receipt.get('removed_path', 'no recorded deletion')}."
                if cleanup_receipt else "No cleanup receipt found."
            ),
        },
    ]

    blocked = []
    for row in stalled_imports:
        blocked.append(
            f"Accepted result {row['task_id']} is blocked because consumed={row['consumed']} and authority_imported={row['authority_imported']}."
        )
    for row in cleanup_blocked:
        blocked.append(
            f"Prompt transport {row['task_id']} is retained because authority proof is missing after {row['age_seconds']}s."
        )
    if not passed_all_base:
        blocked.append("Checkpoint promotion proof is unavailable because base conformance is not passing.")
    if not safepoint_passed:
        blocked.append("SAFEPOINT promotion proof is unavailable because SAFEPOINT conformance is not passing.")
    if safepoint_passed and not safepoint_proof_fresh:
        blocked.append("SAFEPOINT proof is stale and requires revalidation before promotion or replay trust.")
    if safepoint_passed and not safepoint_lineage_clear:
        blocked.append("SAFEPOINT lineage is blocked because the latest ZIP on disk no longer matches the last validated artifact.")
    if not replay_boundary_clear:
        blocked.append("Replay boundary is unclear because startup lineage is not strictly aligned across controller, receipt, and secretary.")

    unlawful = []
    if not passed_all_base:
        unlawful.append("SAFEPOINT or checkpoint promotion cannot proceed lawfully until base conformance passes.")
    if not safepoint_passed:
        unlawful.append("SAFEPOINT-based replay or archival promotion cannot proceed lawfully until SAFEPOINT conformance passes.")
    if safepoint_passed and not safepoint_proof_fresh:
        unlawful.append("SAFEPOINT-based replay or archival promotion cannot proceed lawfully while SAFEPOINT proof is stale.")
    if safepoint_passed and not safepoint_lineage_clear:
        unlawful.append("SAFEPOINT-based replay or archival promotion cannot proceed lawfully while the validated SAFEPOINT artifact has drifted.")
    if stalled_imports:
        unlawful.append("Prompt cleanup and downstream archival cannot proceed lawfully for accepted worker results until authority import is committed.")
    if not replay_boundary_clear:
        unlawful.append("Replay or resume claims cannot proceed lawfully while startup lineage proof is unclear.")

    return {
        "status": "DEGRADED" if degraded_reasons else "CLEAN",
        "headline": "Degraded mode active." if degraded_reasons else "No degraded condition detected.",
        "degraded_reasons": degraded_reasons,
        "degraded_highlights": degraded_highlights,
        "truths": truths,
        "blocked": blocked,
        "unlawful": unlawful,
        "replay_boundary_clear": replay_boundary_clear,
        "latest_accepted": latest_accepted or {},
        "stalled_imports": stalled_imports,
        "cleanup_blocked": cleanup_blocked,
        "cleanup_receipt": cleanup_receipt,
        "conformance": {
            "path": str(BOLT_CHECKPOINTER_REPORT),
            "level": conformance_level,
            "validated_utc": conformance.get("validated_utc", ""),
            "passed_all_base": passed_all_base,
            "passed_all_detected": bool(conformance.get("passed_all_detected", False)),
        },
        "safepoint": {
            "path": str(BOLT_SAFEPOINT_REPORT),
            "level": safepoint_level,
            "validated_utc": safepoint.get("validated_utc", ""),
            "passed_all_base": safepoint_passed,
            "passed_all_detected": bool(safepoint.get("passed_all_detected", False)),
            "proof_max_age_seconds": SAFEPOINT_PROOF_MAX_AGE_SECONDS,
            "validation_age_seconds": safepoint_validation_age_seconds,
            "proof_fresh": safepoint_proof_fresh,
            "lineage_clear": safepoint_lineage_clear,
            "validated_zip_path": validated_zip_path,
            "validated_receipt_path": validated_receipt_path,
            "validated_zip_sha256": validated_zip_sha,
            "current": current_safepoint,
        },
    }


def _safe_stat_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except Exception:
        return 0.0


def _find_latest_status_snapshot() -> Tuple[Optional[Path], Dict[str, Any]]:
    """
    Look for a DailyCheck snapshot in STATUS_DIR. Prefer known filenames; otherwise
    pick the newest JSON file excluding ops_signals.json.
    """
    if not STATUS_DIR.exists():
        return None, {}

    # 1) Prefer known filenames
    for name in PREFERRED_SNAPSHOT_FILES:
        p = STATUS_DIR / name
        data = _read_json(p)
        if isinstance(data, dict):
            return p, data

    # 2) Scan newest *.json, excluding ops_signals
    candidates: List[Path] = []
    try:
        for p in STATUS_DIR.glob("*.json"):
            if p.name.lower() == OPS_SIGNALS_JSON.name.lower():
                continue
            candidates.append(p)
    except Exception:
        candidates = []

    if not candidates:
        return None, {}

    candidates.sort(key=_safe_stat_mtime, reverse=True)
    for p in candidates[:10]:
        data = _read_json(p)
        if isinstance(data, dict):
            return p, data

    return candidates[0], {}


def _ps_json(ps: str) -> Optional[Any]:
    """
    Run a powershell snippet that outputs JSON.
    """
    try:
        cp = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=12,
        )
        out = (cp.stdout or "").strip()
        if not out:
            return None
        return json.loads(out)
    except Exception:
        return None


def _ttl_cache_get(cache: Dict[str, Any]) -> Optional[Any]:
    if float(cache.get("expires_at", 0.0)) > time.time():
        return cache.get("value")
    return None


def _ttl_cache_set(cache: Dict[str, Any], value: Any, ttl_seconds: float) -> Any:
    cache["value"] = value
    cache["expires_at"] = time.time() + ttl_seconds
    return value


def _list_browser_procs() -> List[Dict[str, Any]]:
    """
    Return processes with Name in {chrome.exe, vivaldi.exe, msedgewebview2.exe}.
    Fields: pid, name, exe_path, cmd
    """
    cached = _ttl_cache_get(_BROWSER_PROCS_CACHE)
    if isinstance(cached, list):
        return cached

    ps = r"""
$candidates = @(Get-Process -Name chrome,vivaldi,msedgewebview2 -ErrorAction SilentlyContinue |
  Select-Object Id, ProcessName, Path)

if (-not $candidates -or $candidates.Count -eq 0) {
  @() | ConvertTo-Json -Depth 3
  exit
}

$idExpr = (($candidates | ForEach-Object { "ProcessId = $($_.Id)" }) -join " OR ")
$details = @{}
Get-CimInstance Win32_Process -Filter $idExpr -ErrorAction SilentlyContinue |
  ForEach-Object { $details[[int]$_.ProcessId] = $_ }

$rows = foreach ($p in $candidates) {
  $detail = $details[[int]$p.Id]
  [pscustomobject]@{
    ProcessId      = [int]$p.Id
    Name           = if ($p.ProcessName -match '\.exe$') { $p.ProcessName } else { "$($p.ProcessName).exe" }
    ExecutablePath = if ($detail -and $detail.ExecutablePath) { $detail.ExecutablePath } else { $p.Path }
    CommandLine    = if ($detail) { $detail.CommandLine } else { $null }
  }
}

$rows | ConvertTo-Json -Depth 3
""".strip()
    data = _ps_json(ps)
    if data is None:
        return []
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    out: List[Dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        out.append(
            {
                "pid": row.get("ProcessId"),
                "name": row.get("Name"),
                "exe_path": row.get("ExecutablePath"),
                "cmd": row.get("CommandLine"),
            }
        )
    return _ttl_cache_set(_BROWSER_PROCS_CACHE, out, ttl_seconds=5.0)


def _detect_rc1(procs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    RC1 is ungoogled-chromium installed under D:\\\\ungoogled-chromium_*\\\\chrome.exe
    """
    candidates: List[Dict[str, Any]] = []
    fallback: List[Dict[str, Any]] = []
    for pr in procs:
        exe = (pr.get("exe_path") or "")
        exe_l = exe.lower()
        if exe_l.startswith(r"d:\ungoogled-chromium_") and exe_l.endswith(r"\chrome.exe"):
            cmd_l = (pr.get("cmd") or "").lower()
            if "--type=" not in cmd_l:
                candidates.append(pr)
            else:
                fallback.append(pr)
    chosen = candidates[0] if candidates else (fallback[0] if fallback else None)
    if chosen:
        return {
            "status": "running",
            "process_id": chosen.get("pid"),
            "executable_path": chosen.get("exe_path") or "",
            "command_line": chosen.get("cmd") or "",
            "detected_by": "ungoogled_chromium_path",
        }
    return {"status": "not_running"}

def _detect_rc2(procs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Detects Bolt RC2: Any Chrome/Chromium process using the specific RC2 profile.
    """
    profile_marker = r"projects\bolt\rc2\chromeprofile"
    
    candidates: List[Dict[str, Any]] = []
    fallback: List[Dict[str, Any]] = []
    for pr in procs:
        exe_l = (pr.get("exe_path") or "").lower()
        cmd_l = (pr.get("cmd") or "").lower()
        
        # Identification by signature (profile) rather than installation path
        if ("chrome.exe" in exe_l or "chromium.exe" in exe_l) and profile_marker in cmd_l:
            if "--type=" not in cmd_l:
                candidates.append(pr)
            else:
                fallback.append(pr)
    chosen = candidates[0] if candidates else (fallback[0] if fallback else None)
    if chosen:
        return {
            "status": "running",
            "process_id": chosen.get("pid"),
            "executable_path": chosen.get("exe_path") or "",
            "command_line": chosen.get("cmd") or "",
            "detected_by": "rc2_profile_signature",
        }
    return {"status": "not_running"}


def _detect_vivaldi_rc3(procs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Conservative RC3 detection: require a profile or launch signature, otherwise
    prefer unknown over a false positive.
    """
    markers = [
        r"projects\bolt\rc3",
        r"--user-data-dir=d:\porttoretro_archive\projects\bolt\rc3",
        r"rc3profile",
    ]
    for pr in procs:
        name_l = (pr.get("name") or "").lower()
        exe_l = (pr.get("exe_path") or "").lower()
        cmd_l = (pr.get("cmd") or "").lower()
        if name_l == "vivaldi.exe" and any(marker in cmd_l or marker in exe_l for marker in markers):
            return {
                "status": "running",
                "process_id": pr.get("pid"),
                "executable_path": pr.get("exe_path") or "",
                "command_line": pr.get("cmd") or "",
                "detected_by": "rc3_signature",
            }
    return {"status": "unknown"}


def _renderer_summary(procs: List[Dict[str, Any]]) -> Dict[str, Any]:
    renderer_pids: List[int] = []
    for pr in procs:
        cmd = (pr.get("cmd") or "").lower()
        if "--type=renderer" in cmd:
            pid = pr.get("pid")
            if isinstance(pid, int):
                renderer_pids.append(pid)
    return {
        "renderer_count": len(renderer_pids),
        "renderer_pids": renderer_pids,
    }


def _gpu_pipeline_summary(procs: List[Dict[str, Any]]) -> Dict[str, Any]:
    gpu_pids: List[int] = []
    sample_cmd: Optional[str] = None
    for pr in procs:
        cmd = (pr.get("cmd") or "")
        if "--type=gpu-process" in cmd:
            pid = pr.get("pid")
            if isinstance(pid, int):
                gpu_pids.append(pid)
            if sample_cmd is None:
                sample_cmd = cmd
    return {
        "gpu_process_count": len(gpu_pids),
        "sample_gpu_cmd": sample_cmd,
    }


def _disk_list() -> List[Dict[str, Any]]:
    """
    Return bytes used/free/total for fixed drives we care about.
    """
    out: List[Dict[str, Any]] = []
    for letter in ["C", "D", "E", "Z"]:
        root = Path(f"{letter}:\\")
        if not root.exists():
            continue
        try:
            usage = shutil.disk_usage(str(root))
            total = int(usage.total)
            free = int(usage.free)
            used = total - free
            out.append({"name": letter, "total_bytes": total, "free_bytes": free, "used_bytes": used})
        except Exception:
            continue
    return out


def _latest_zip_under(root: Path) -> Optional[Dict[str, Any]]:
    if not root.exists():
        return None
    latest_path: Optional[Path] = None
    latest_m: float = 0.0
    try:
        for p in root.rglob("*.zip"):
            m = _safe_stat_mtime(p)
            if m > latest_m:
                latest_m = m
                latest_path = p
    except Exception:
        return None

    if latest_path is None:
        return None
    try:
        st = latest_path.stat()
        return {
            "name": latest_path.name,
            "full_path": str(latest_path),
            "size_bytes": int(st.st_size),
            "last_write": datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds"),
        }
    except Exception:
        return {"name": latest_path.name, "full_path": str(latest_path)}


def _safepoint_summaries() -> List[Dict[str, Any]]:
    cached = _ttl_cache_get(_SAFEPOINT_CACHE)
    if isinstance(cached, list):
        return cached

    out: List[Dict[str, Any]] = []
    for root in ARCHIVE_ROOTS:
        exists = root.exists()
        zip_count = 0
        if exists:
            try:
                zip_count = sum(1 for _ in root.rglob("*.zip"))
            except Exception:
                zip_count = 0
        out.append(
            {
                "root_path": str(root),
                "exists": bool(exists),
                "zip_count": zip_count,
                "latest_zip": _latest_zip_under(root),
            }
        )
    return _ttl_cache_set(_SAFEPOINT_CACHE, out, ttl_seconds=60.0)


def _safepoint_candidate_summaries() -> List[Dict[str, Any]]:
    cached = _ttl_cache_get(_SAFEPOINT_CANDIDATE_CACHE)
    if isinstance(cached, list):
        return cached

    root = OPS_ROOT / "_Capsules" / "SAFEPOINT_CANDIDATES"
    archive_root = OPS_ROOT / "_Capsules" / "_archive" / "SAFEPOINT_CANDIDATES"
    if not root.exists():
        return _ttl_cache_set(_SAFEPOINT_CANDIDATE_CACHE, [], ttl_seconds=60.0)

    out: List[Dict[str, Any]] = []
    try:
        candidate_dirs = [
            p for p in root.iterdir()
            if p.is_dir() and p.name.startswith("SAFEPOINT_CANDIDATE_")
        ]
    except Exception:
        candidate_dirs = []

    def _candidate_key(path: Path) -> float:
        return _safe_stat_mtime(path)

    for candidate_dir in sorted(candidate_dirs, key=_candidate_key, reverse=True):
        dashboard = _read_json(candidate_dir / "DASHBOARD.json")
        manifest = _read_json(candidate_dir / "rollup_manifest.json")
        receipt = _read_json(candidate_dir / "SAFEPOINT_CANDIDATE_RECEIPT.json")
        if not isinstance(dashboard, dict):
            dashboard = {}
        if not isinstance(manifest, dict):
            manifest = {}
        if not isinstance(receipt, dict):
            receipt = {}

        included_week_ranges = dashboard.get("included_week_ranges")
        if not isinstance(included_week_ranges, list):
            included_week_ranges = manifest.get("included_week_ranges") if isinstance(manifest.get("included_week_ranges"), list) else []
        created_utc = str(manifest.get("created_utc") or receipt.get("timestamp_utc") or "")
        created_dt = _parse_utc_ts(created_utc)
        age_days: Optional[float] = None
        if created_dt:
            age_days = round(max(0.0, (datetime.now(timezone.utc) - created_dt.astimezone(timezone.utc)).total_seconds() / 86400.0), 3)
        status = str(dashboard.get("dashboard_visibility") or manifest.get("dashboard_visibility") or "BLOCKED")
        out.append(
            {
                "candidate_path": str(candidate_dir),
                "candidate_name": candidate_dir.name,
                "candidate_status": status,
                "included_week_ranges": included_week_ranges,
                "latest_candidate_age_days": age_days,
                "runtime_authority": False,
                "production_authority": False,
                "safepoint_created": False,
                "authority_effect": "NONE",
                "dashboard_visibility": status,
                "receipt_path": str(candidate_dir / "SAFEPOINT_CANDIDATE_RECEIPT.json") if (candidate_dir / "SAFEPOINT_CANDIDATE_RECEIPT.json").exists() else "",
                "manifest_path": str(candidate_dir / "rollup_manifest.json") if (candidate_dir / "rollup_manifest.json").exists() else "",
                "sha256_path": str(candidate_dir / "SHA256SUMS.txt") if (candidate_dir / "SHA256SUMS.txt").exists() else "",
                "packet_root": str(candidate_dir),
                "archive_root": str(archive_root),
            }
        )
    return _ttl_cache_set(_SAFEPOINT_CANDIDATE_CACHE, out, ttl_seconds=60.0)


def _bolt_pid_running(pid: Any) -> bool:
    try:
        pid_i = int(pid)
    except Exception:
        return False
    ps = rf"""
$p = Get-CimInstance Win32_Process -Filter "ProcessId = {pid_i}" -ErrorAction SilentlyContinue
if ($null -eq $p) {{
  [pscustomobject]@{{ alive = $false }} | ConvertTo-Json -Compress
  exit
}}
$cmd = [string]$p.CommandLine
$isBolt = ($p.Name -match 'python(\.exe)?$') -and (
  $cmd -match 'Bolt_RC2_Controller\.py' -or
  $cmd -match 'PORTTORETRO_ARCHIVE\\PROJECTS\\Bolt'
)
[pscustomobject]@{{ alive = [bool]$isBolt }} | ConvertTo-Json -Compress
""".strip()
    data = _ps_json(ps)
    return bool(isinstance(data, dict) and data.get("alive"))


def _count_matching_files(root: Path, pattern: str, recursive: bool = False) -> int:
    if not root.exists():
        return 0
    try:
        it = root.rglob(pattern) if recursive else root.glob(pattern)
        return sum(1 for _ in it)
    except Exception:
        return 0


def _bolt_aux_counts() -> Tuple[int, int]:
    cached = _ttl_cache_get(_BOLT_AUX_CACHE)
    if cached is not None:
        return int(_BOLT_AUX_CACHE.get("backlog_count", 0)), int(_BOLT_AUX_CACHE.get("quarantine_count", 0))

    backlog_count = _count_matching_files(BOLT_SESSION_BACKLOG_DIR, "*.md", recursive=True)
    quarantine_count = _count_matching_files(BOLT_QUARANTINE_DIR, "*.md", recursive=True)
    _BOLT_AUX_CACHE["backlog_count"] = backlog_count
    _BOLT_AUX_CACHE["quarantine_count"] = quarantine_count
    _BOLT_AUX_CACHE["value"] = True
    _BOLT_AUX_CACHE["expires_at"] = time.time() + 30.0
    return backlog_count, quarantine_count


def _alpha_summary() -> Dict[str, Any]:
    if not ALPHA_RAW_DIR.exists():
        return {"path": str(ALPHA_RAW_DIR), "exists": False, "files_24h": 0, "latest_file": None}

    latest: Optional[Path] = None
    latest_m = 0.0
    files_24h = 0
    now = datetime.now().timestamp()
    try:
        for p in ALPHA_RAW_DIR.glob("*"):
            if not p.is_file():
                continue
            m = _safe_stat_mtime(p)
            if now - m <= 24 * 3600:
                files_24h += 1
            if m > latest_m:
                latest_m = m
                latest = p
    except Exception:
        pass

    latest_obj = None
    if latest is not None:
        try:
            st = latest.stat()
            latest_obj = {
                "name": latest.name,
                "full_path": str(latest),
                "size_bytes": int(st.st_size),
                "last_write": datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds"),
            }
        except Exception:
            latest_obj = {"name": latest.name, "full_path": str(latest)}

    return {
        "path": str(ALPHA_RAW_DIR),
        "exists": True,
        "files_24h": files_24h,
        "latest_file": latest_obj,
    }


def _bolt_controller_state() -> Dict[str, Any]:
    """Read controller_state.json and lock file for live Controller (Python) status."""
    state: Dict[str, Any] = {}

    raw = _read_json(BOLT_STATE)
    if isinstance(raw, dict):
        state.update(raw)

    lock = _read_json(BOLT_LOCK)
    if isinstance(lock, dict):
        state["lock"] = lock

    return state


def _derive_bolt_boot_status(state: Dict[str, Any]) -> str:
    """
    Derive high-level boot status from data timestamps only.
    Avoids process presence checks, controller health, or governor active flags.
    """
    if not state:
        return "AWAITING"

    last_seen_str = state.get("controller_last_seen_utc")
    last_heart_str = state.get("last_heartbeat_utc")

    last_seen = _parse_utc_ts(last_seen_str)
    last_heart = _parse_utc_ts(last_heart_str)

    now = datetime.now(timezone.utc)

    if not last_seen:
        return "OFFLINE"

    diff_seen = (now - last_seen.astimezone(timezone.utc)).total_seconds()

    if diff_seen > 300:  # 5 minutes
        return "OFFLINE"
    if diff_seen > 60:  # 1 minute
        return "STALE"

    # If seen recently, check heartbeats
    if not last_heart:
        return "BOOTING"

    diff_heart = (now - last_heart.astimezone(timezone.utc)).total_seconds()
    if diff_heart < 60:
        return "READY"

    return "RUNNING"


def _verify_bolt_lineage() -> Tuple[str, str]:
    """
    Verify RC2 startup lineage across controller state, startup receipt, and
    the latest provenance receipt record.
    """
    if not BOLT_STATE.exists() or not BOLT_STARTUP_RECEIPT.exists() or not BOLT_PROVENANCE.exists():
        return "UNKNOWN", "Missing required startup artifacts."

    state = _read_json(BOLT_STATE)
    if not isinstance(state, dict):
        return "UNKNOWN", "Controller state is missing or unreadable."

    c_pid = state.get("startup_controller_pid") or state.get("controller_pid")
    c_rv = state.get("startup_runtime_verified_utc") or state.get("runtime_verified_utc")
    c_tid = (
        state.get("startup_current_target_id")
        or state.get("current_target_id")
        or state.get("runtime_verified_target_id")
        or state.get("governor_target_id")
    )
    if not all([c_pid, c_rv, c_tid]):
        return "UNKNOWN", "Incomplete lineage fields in controller state."

    expected_lineage = state.get("startup_session_id") or f"{c_pid}|{c_rv}|{c_tid}"

    receipt_kv = _read_markdown_kv(BOLT_STARTUP_RECEIPT)
    receipt_session = receipt_kv.get("startup_session_id")
    if not receipt_session:
        return "UNKNOWN", "Missing startup_session_id in startup receipt."

    provenance_session = None
    try:
        lines = BOLT_PROVENANCE.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return "UNKNOWN", f"Unable to read startup provenance: {exc}"

    for raw_line in reversed(lines):
        line = raw_line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("phase") == "receipt" and entry.get("status") == "written":
            entry_session = entry.get("startup_session_id")
            if not entry_session:
                continue
            if entry_session == receipt_session:
                provenance_session = entry_session
                break
    if not provenance_session:
        return "UNKNOWN", "No written receipt entry found in startup provenance."

    if expected_lineage == receipt_session == provenance_session:
        return "READY", "Lineage verified across immutable startup state, receipt, and provenance."
    return "ARTIFACT_DRIFT", "Controller startup lineage, receipt, and provenance session mismatch."


def _bolt_recent_cmdlog(n: int = 20) -> List[Dict[str, Any]]:
    """Return the last n lines from cmdlog.jsonl."""
    if not BOLT_CMDLOG.exists():
        return []
    try:
        lines = BOLT_CMDLOG.read_text(encoding="utf-8", errors="replace").splitlines()
        recent = lines[-n:] if len(lines) > n else lines
        out: List[Dict[str, Any]] = []
        for line in reversed(recent):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
        return out
    except Exception:
        return []


def _bolt_recent_hearts(n: int = 5) -> List[Dict[str, Any]]:
    """Return metadata for the n most recent HeartBundle .md files."""
    if not BOLT_HEART_DIR.exists():
        return []
    try:
        files = sorted(
            (p for p in BOLT_HEART_DIR.glob("HEART_EXTRACT_*.md") if p.is_file()),
            key=_safe_stat_mtime,
            reverse=True,
        )[:n]
        out: List[Dict[str, Any]] = []
        for p in files:
            try:
                st = p.stat()
                # Peek first 400 chars for a preview
                preview = p.read_text(encoding="utf-8", errors="replace")[:400]
                out.append({
                    "name": p.name,
                    "size_bytes": int(st.st_size),
                    "mtime": datetime.fromtimestamp(st.st_mtime).astimezone().isoformat(timespec="seconds"),
                    "preview": preview,
                })
            except Exception:
                out.append({"name": p.name})
        return out
    except Exception:
        return []


def _build_bolt_snapshot() -> Dict[str, Any]:
    state = _bolt_controller_state()
    cmdlog = _bolt_recent_cmdlog(20)
    hearts = _bolt_recent_hearts(5)
    boot_status = _derive_bolt_boot_status(state)
    lineage_status, lineage_reason = _verify_bolt_lineage()

    # Controller status based on seen-ness
    last_seen = state.get("controller_last_seen_utc", None)
    
    # Simple staleness check for "controller status" field (distinct from boot status)
    controller_status = "offline"
    if last_seen:
        ls_dt = _parse_utc_ts(last_seen)
        if ls_dt:
            age = (datetime.now(timezone.utc) - ls_dt.astimezone(timezone.utc)).total_seconds()
            if age < 60:
                controller_status = "running"
            elif age < 300:
                controller_status = "stale"

    receipt = _read_markdown_kv(BOLT_STARTUP_RECEIPT)
    secretary = _read_json(BOLT_SECRETARY_STATUS)
    if not isinstance(secretary, dict):
        secretary = {}
    backlog_count, quarantine_count = _bolt_aux_counts()
    adjudication = _build_bolt_adjudication_snapshot(state, receipt, secretary, lineage_status, lineage_reason)

    return {
        "boot_status": boot_status,
        "lineage_status": lineage_status,
        "lineage_reason": lineage_reason,
        "adjudication": adjudication,
        "controller_status": controller_status,
        "last_seen_utc": last_seen,
        "last_heart_bundle": state.get("last_heart_bundle"),
        "last_heart_written_utc": state.get("last_heart_written_utc"),
        "inbox_index": state.get("inbox_index"),
        "startup_receipt_latest": str(BOLT_STARTUP_RECEIPT) if BOLT_STARTUP_RECEIPT.exists() else "",
        "startup_session_id": receipt.get("startup_session_id", ""),
        "startup_runtime_verified_utc": receipt.get("runtime_verified_utc", ""),
        "startup_receipt_generated_utc": receipt.get("receipt_generated_utc", ""),
        "secretary_status": secretary.get("secretary_health_status", ""),
        "secretary_startup_session_id": secretary.get("startup_session_id", ""),
        "secretary_backlog_count": backlog_count,
        "secretary_quarantine_count": quarantine_count,
        "cmdlog": cmdlog,
        "hearts": hearts,
        "raw_state": state,
    }



def _build_orchestrator_snapshot() -> Dict[str, Any]:
    latest = _read_json(ORCH_LATEST)
    lock = _read_json(ORCH_LOCK)

    if not isinstance(latest, dict):
        latest = {}
    if not isinstance(lock, dict):
        lock = {}

    steps = latest.get("steps") if isinstance(latest.get("steps"), list) else []
    failed_steps = [s for s in steps if isinstance(s, dict) and s.get("status") in ("failed", "missing") and s.get("required")]

    status = latest.get("status") if isinstance(latest.get("status"), str) else "unknown"
    strict = bool(latest.get("strictCRQualityGate", False))

    return {
        "status": status,
        "strict_cr_quality_gate": strict,
        "started": latest.get("started"),
        "finished": latest.get("finished"),
        "failed_step": latest.get("failedStep") or latest.get("error"),
        "ops_root": latest.get("opsRoot", str(OPS_ROOT)),
        "step_count": len(steps),
        "failed_required_count": len(failed_steps),
        "lock": lock,
        "steps": steps,
        "telemetry_path": str(ORCH_LATEST),
        "lock_path": str(ORCH_LOCK),
    }


def _extract_dailybundle_stdout_value(stdout: str, label: str) -> str:
    pattern = re.compile(r"^\s*" + re.escape(label) + r"\s*:?\s*(.+?)\s*$", re.IGNORECASE)
    for line in str(stdout or "").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return ""


def _build_dailybundle_app_snapshot() -> Dict[str, Any]:
    orchestrator = _build_orchestrator_snapshot()
    steps = orchestrator.get("steps") if isinstance(orchestrator.get("steps"), list) else []
    build_step = next(
        (s for s in steps if isinstance(s, dict) and s.get("name") == "OpsCOO_Build_DailyBundle_v1"),
        {},
    )
    scheduler_step = next(
        (s for s in steps if isinstance(s, dict) and s.get("name") == "OpsCOO_SchedulerIntegrityCheck"),
        {},
    )
    stdout = build_step.get("stdout_tail", "") if isinstance(build_step, dict) else ""

    return {
        "app": "daily_bundle",
        "label": "Daily Bundle",
        "status": build_step.get("status") if isinstance(build_step, dict) else "unknown",
        "orchestrator_status": orchestrator.get("status", "unknown"),
        "strict_cr_quality_gate": bool(orchestrator.get("strict_cr_quality_gate", False)),
        "started": orchestrator.get("started"),
        "finished": orchestrator.get("finished"),
        "failed_step": orchestrator.get("failed_step"),
        "artifact": {
            "zip": _extract_dailybundle_stdout_value(stdout, "CREATED"),
            "sha256": _extract_dailybundle_stdout_value(stdout, "ZIP_SHA256"),
            "manifest_sidecar": _extract_dailybundle_stdout_value(stdout, "MANIFEST (sidecar)"),
            "manifest_latest": _extract_dailybundle_stdout_value(stdout, "MANIFEST (latest)"),
            "bootstrap_latest_manifest": _extract_dailybundle_stdout_value(stdout, "BOOTSTRAP_LATEST (manifest)"),
        },
        "validation_gates": [
            {"name": "validate", "status": "todo", "note": "TODO: surface CLI validation evidence after preview install run."},
            {"name": "seal-check", "status": "todo", "note": "TODO: surface CLI seal-check evidence after preview install run."},
            {"name": "doctor", "status": "todo", "note": "TODO: surface binary doctor verdict after preview install run."},
            {"name": "run", "status": "todo", "note": "TODO: surface source-run/cold-machine run evidence."},
        ],
        "scheduler_integrity": {
            "status": scheduler_step.get("status", "not_reported") if isinstance(scheduler_step, dict) else "not_reported",
            "mode": "audit_only",
            "task_name": "RetroFuse_OPS_DailyBundle",
        },
        "topology": {
            "default_install_root": r"C:\RetroFuse",
            "config_path": r"C:\RetroFuse\Config\dailybundle.preview.json",
            "dailybundle_root": r"C:\RetroFuse\DailyBundle",
            "runtime_root": r"C:\RetroFuse\Runtime",
            "logs_root": r"C:\RetroFuse\Logs",
        },
        "install_lanes": [
            {"name": "daily_bundle", "status": "present", "surface": "continuity and governance evidence"},
            {"name": "future_app_lanes", "status": "reserved", "surface": "TODO: declare per-app install surface before release."},
        ],
        "source": {
            "orchestrator": str(ORCH_LATEST),
            "release_docs": str(BOLT_ROOT / "Docs" / "DAILY_BUNDLE_TOPOLOGY_SUMMARY_v0.9.md"),
        },
    }
def _build_smc_wrc_live_status() -> Dict[str, Any]:
    obs_dir = SMC_WRC_OBS_DIR
    current_status_path = SMC_WRC_CURRENT_STATUS

    def get_latest_file(pattern: str) -> Optional[Path]:
        if not obs_dir.exists():
            return None
        try:
            files = sorted(obs_dir.glob(pattern), key=_safe_stat_mtime, reverse=True)
            return files[0] if files else None
        except Exception:
            return None

    latest_checkpoint_file = get_latest_file("checkpoint_WRC_*.json")
    latest_session_file = get_latest_file("session_WRC_*.json")

    current_status = _read_json(current_status_path) or {}
    checkpoint = _read_json(latest_checkpoint_file) if latest_checkpoint_file else {}
    session = _read_json(latest_session_file) if latest_session_file else {}

    now = datetime.now(timezone.utc)
    in_window = False
    window_name = "NONE"
    window_range = "NONE"
    window_end_iso = None

    cw = current_status.get("current_window")
    if isinstance(cw, dict):
        in_window = True
        window_name = cw.get("label", "NONE")
        window_range = f"{cw.get('start_et', '??')}-{cw.get('end_et', '??')} ET"
        window_end_iso = cw.get("end_iso")

    checkpoint_age = None
    checkpoint_ts_str = checkpoint.get("checkpoint_timestamp")
    if checkpoint_ts_str:
        cp_dt = _parse_utc_ts(checkpoint_ts_str)
        if cp_dt:
            checkpoint_age = int((now - cp_dt.astimezone(timezone.utc)).total_seconds())

    observer_running = bool(current_status.get("observer_running"))
    if session.get("end_time"):
        observer_running = False

    sac = checkpoint.get("seed_aware_classifications", {})
    ccs = checkpoint.get("candidate_classification_summary", {})

    fast_suppressed = sac.get("KNOWN_FAST_SUPPRESSED", 0)
    ignore_non_media = sac.get("IGNORE_NON_MEDIA_NOISE", 0)
    player_config = ccs.get("PLAYER_CONFIG_CANDIDATE", 0)
    unknown_plausible = ccs.get("UNKNOWN_PLAUSIBLE_LINEAR_CANDIDATE", 0)
    seed_match_fresh = checkpoint.get("seed_aware_match_count", 0)

    resolver_state = current_status.get("resolver_state", "UNKNOWN")
    direct_source_found = bool(checkpoint.get("direct_source_found"))
    drm_detected = bool(checkpoint.get("drm_detected"))

    next_safe_action = current_status.get("next_action", "WAIT_FOR_WINDOW")

    # Status Color Logic
    # GREEN: running, fresh, no false escalation
    # YELLOW: no active window or only FAST suppressed
    # ORANGE: active window with stale checkpoint
    # RED: stopped early, missing session, active window without checkpoint
    status_color = "YELLOW"
    
    if in_window:
        if observer_running:
            if checkpoint_age is not None and checkpoint_age <= 300:
                status_color = "GREEN"
            elif checkpoint_age is not None and checkpoint_age > 600:
                status_color = "ORANGE"
                next_safe_action = "STALE_CHECKPOINT_RESTART_OBSERVER"
            else:
                status_color = "YELLOW"
        else:
            # Not running in window
            if direct_source_found:
                status_color = "GREEN" # Normal completion with result
            else:
                # Check for normal end
                is_normal_end = False
                if window_end_iso:
                    win_end_dt = _parse_utc_ts(window_end_iso)
                    sess_end_str = session.get("end_time")
                    if win_end_dt and sess_end_str:
                        sess_end_dt = _parse_utc_ts(sess_end_str)
                        if sess_end_dt and sess_end_dt >= win_end_dt.replace(second=0).astimezone(timezone.utc):
                             is_normal_end = True
                
                if is_normal_end:
                    status_color = "YELLOW"
                else:
                    status_color = "RED"
                    next_safe_action = "EARLY_EXIT_NO_CANDIDATE"
    else:
        status_color = "YELLOW"

    if not latest_checkpoint_file and in_window:
        status_color = "RED"

    return {
        "active_window": in_window,
        "session_id": checkpoint.get("session_id") or session.get("session_id", "NONE"),
        "window_name": window_name,
        "window_range": window_range,
        "observer_running": observer_running,
        "latest_checkpoint": latest_checkpoint_file.name if latest_checkpoint_file else "NONE",
        "checkpoint_age": checkpoint_age,
        "fast_suppressed_count": fast_suppressed,
        "ignore_non_media_count": ignore_non_media,
        "player_config_count": player_config,
        "unknown_plausible_linear_count": unknown_plausible,
        "seed_match_fresh_candidate_count": seed_match_fresh,
        "direct_source_found": direct_source_found,
        "drm_detected": drm_detected,
        "resolver_state": resolver_state,
        "production_mutation": False,
        "next_safe_action": next_safe_action,
        "status_color": status_color
    }


def _build_latest_snapshot() -> Dict[str, Any]:
    snap_path, snap = _find_latest_status_snapshot()
    if not isinstance(snap, dict):
        snap = {}

    # Attach ops_signals
    ops_signals = _read_json(OPS_SIGNALS_JSON)
    if isinstance(ops_signals, dict):
        snap["ops_signals"] = ops_signals
    else:
        snap.setdefault("ops_signals", {})

    # Core fields
    snap.setdefault("ops_root", str(OPS_ROOT))
    snap.setdefault("timestamp", _iso_now_local())

    # Server side telemetry assembly (authoritative)
    procs = _list_browser_procs()
    snap["rc1"] = _detect_rc1(procs)

    # Server-side RC2/RC3 detection is authoritative over stale snapshot content.
    snap["rc2"] = _detect_rc2(procs)

    if not isinstance(snap.get("rc3"), dict):
        snap["rc3"] = _detect_vivaldi_rc3(procs)
    else:
        snap["rc3"].setdefault("status", "unknown")

    snap["renderers"] = _renderer_summary(procs)
    snap["gpu_pipeline"] = _gpu_pipeline_summary(procs)

    # Disks, safepoints, alpha, notes
    snap["disks"] = _disk_list()
    snap["safepoints"] = _safepoint_summaries()
    snap["safepoint_candidates"] = _safepoint_candidate_summaries()
    snap["alpha"] = _alpha_summary()
    if not isinstance(snap.get("notes"), list):
        snap["notes"] = []

    snap["dashboard_loaded_at"] = datetime.now().isoformat(timespec="seconds")

    # Snapshot provenance (debug)
    if snap_path is not None:
        snap["snapshot_source"] = str(snap_path)

    # Derived Bolt status for main view
    bolt_state = _bolt_controller_state()
    snap["bolt_boot"] = _derive_bolt_boot_status(bolt_state)

    return snap


def _event_file_summary(path: Path) -> Dict[str, Any]:
    data = _read_json(path)
    if not isinstance(data, dict):
        data = {}
    data.setdefault("filename", path.name)
    data.setdefault("event_utc", datetime.fromtimestamp(_safe_stat_mtime(path), timezone.utc).isoformat())
    data.setdefault("event_type", path.stem)
    data.setdefault("task_id", "")
    data.setdefault("status", "")
    data.setdefault("blocker_code", "NONE")
    data.setdefault("summary", path.name)
    return data


def _latest_event_files(folder: Path, limit: int = 8) -> List[Path]:
    if not folder.exists():
        return []
    try:
        files = [p for p in folder.glob("*.json") if p.is_file()]
    except Exception:
        return []
    return sorted(files, key=_safe_stat_mtime, reverse=True)[:limit]


def _build_worker_events_summary() -> Dict[str, Any]:
    warnings: List[str] = []
    latest: Dict[str, List[Dict[str, Any]]] = {}
    counts: Dict[str, int] = {}
    for name in ("inbox", "processed", "invalid"):
        folder = WORKER_EVENTS_DIR / name
        if not folder.exists():
            warnings.append(f"Missing worker events folder: {folder}")
            counts[name] = 0
            latest[name] = []
            continue
        try:
            files = [p for p in folder.glob("*.json") if p.is_file()]
        except Exception as exc:
            warnings.append(f"Failed to scan {folder}: {exc}")
            files = []
        counts[name] = len(files)
        latest[name] = [_event_file_summary(p) for p in sorted(files, key=_safe_stat_mtime, reverse=True)[:8]]
    return {"ok": True, "counts": counts, "latest": latest, "warnings": warnings}


def _build_workers_status() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    latest_by_worker: Dict[str, Dict[str, Any]] = {}
    for folder_name in ("inbox", "processed", "invalid"):
        folder = WORKER_EVENTS_DIR / folder_name
        for path in _latest_event_files(folder, limit=100):
            event = _event_file_summary(path)
            worker_id = str(event.get("worker_id") or event.get("worker") or path.stem)
            previous = latest_by_worker.get(worker_id)
            previous_path = Path(str(previous.get("_path", ""))) if previous else None
            if previous_path and _safe_stat_mtime(previous_path) >= _safe_stat_mtime(path):
                continue
            event["_path"] = str(path)
            event["_folder"] = folder_name
            latest_by_worker[worker_id] = event

    workers: List[Dict[str, Any]] = []
    for worker_id, event in latest_by_worker.items():
        event_dt = _parse_utc_ts(str(event.get("event_utc") or ""))
        age_seconds: Optional[int] = None
        if event_dt:
            age_seconds = max(0, int((now - event_dt.astimezone(timezone.utc)).total_seconds()))
        status = str(event.get("status") or event.get("event_type") or "UNKNOWN")
        alive = status not in {"COMPLETED", "FAILED", "ERROR"} and (age_seconds is None or age_seconds < 6 * 60 * 60)
        blocker = str(event.get("blocker_code") or "NONE")
        workers.append(
            {
                "worker": worker_id,
                "pid": event.get("pid", ""),
                "state": "BLOCKED" if blocker != "NONE" else status,
                "alive": alive,
                "age_seconds": age_seconds,
                "timeout_risk": bool(age_seconds is not None and age_seconds > 60 * 60 and alive),
                "recommended_action": "Review blocker" if blocker != "NONE" else ("No action" if alive else "Review latest terminal event"),
                "profile": event.get("worker_type", event.get("profile", "")),
                "role": event.get("role", "Worker"),
                "task_id": event.get("task_id", ""),
                "stage": event.get("stage", ""),
                "current_operation": event.get("current_operation", event.get("summary", "")),
                "current_path": event.get("_path", ""),
                "blocker_code": blocker,
                "blocker_detail": event.get("blocker_detail", ""),
                "next_actor": event.get("next_actor", "worker"),
                "evidence_path": event.get("evidence_path", ""),
            }
        )
    workers.sort(key=lambda item: item.get("age_seconds") if item.get("age_seconds") is not None else 10**12)
    return workers


def _build_project_board() -> List[Dict[str, Any]]:
    data = _read_json(PROJECT_BOARD_CACHE)
    return data if isinstance(data, list) else []


def _build_planes_registry() -> Dict[str, Any]:
    warnings: List[str] = []
    planes: List[Dict[str, Any]] = []
    if not PLANES_REGISTRY_DIR.exists():
        warnings.append(f"Missing planes registry dir: {PLANES_REGISTRY_DIR}")
        return {"ok": False, "planes": planes, "warnings": warnings}
    try:
        files = sorted(PLANES_REGISTRY_DIR.rglob("registration_candidate.json"), key=_safe_stat_mtime, reverse=True)
    except Exception as exc:
        return {"ok": False, "planes": planes, "warnings": [f"Registry scan failed: {exc}"]}
    for path in files:
        data = _read_json(path)
        if not isinstance(data, dict):
            warnings.append(f"Malformed registration candidate: {path}")
            continue
        data.setdefault("source_path", str(path))
        planes.append(data)
    return {"ok": True, "planes": planes, "warnings": warnings}


def _read_template_fallback() -> str:
    """Read templates/index.html as the canonical frontend source.

    This replaces the previously embedded ~2500-line INDEX_HTML constant.
    templates/index.html is now the single source of truth for the dashboard UI.
    If the template file is missing, returns a minimal error page.
    """
    try:
        if TEMPLATE_INDEX.exists():
            return TEMPLATE_INDEX.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>RetroFuse OPS Dashboard</title></head>
<body style="background:#020617;color:#e5e7eb;font-family:system-ui;padding:40px;">
  <h1>RetroFuse OPS Dashboard</h1>
  <p>Template file not found at: {TEMPLATE_INDEX}</p>
  <p>The dashboard requires <code>templates/index.html</code> to render.</p>
  <p>API endpoints remain available at <code>/api/...</code></p>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse(_read_template_fallback())




@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "ops-dashboard", "version": APP_VERSION})
@app.get("/api/latest")
def api_latest() -> JSONResponse:
    snap = _build_latest_snapshot()
    return JSONResponse(snap)



@app.get("/api/orchestrator")
def api_orchestrator() -> JSONResponse:
    return JSONResponse(_build_orchestrator_snapshot())


@app.get("/api/planes/registry")
def api_planes_registry() -> JSONResponse:
    return JSONResponse(_build_planes_registry())


@app.get("/api/project-board")
def api_project_board() -> JSONResponse:
    return JSONResponse(_build_project_board())


@app.get("/api/workers/status")
def api_workers_status() -> JSONResponse:
    return JSONResponse(_build_workers_status())


@app.get("/api/worker-events/summary")
def api_worker_events_summary() -> JSONResponse:
    return JSONResponse(_build_worker_events_summary())


@app.get("/api/apps/dailybundle")
def api_apps_dailybundle() -> JSONResponse:
    return JSONResponse(_build_dailybundle_app_snapshot())


@app.get("/api/bolt")
def api_bolt() -> JSONResponse:
    return JSONResponse(_build_bolt_snapshot())


@app.get("/api/smc/wrc-live-status")
def api_smc_wrc_live_status():
    return JSONResponse(_build_smc_wrc_live_status())


@app.post("/api/bolt/revalidate-safepoint")
def api_bolt_revalidate_safepoint() -> JSONResponse:
    result = _run_bolt_safepoint_validator()
    status_code = 200 if result.get("ok") else 500
    return JSONResponse(result, status_code=status_code)

@app.get("/api/models/dashboard")
def api_models_dashboard(mode: str = "home") -> JSONResponse:
    return JSONResponse(build_mode_aware_dashboard(mode))


@app.get("/api/models/edit-receipts")
def api_models_edit_receipts() -> JSONResponse:
    return JSONResponse(list_edit_receipts())


@app.post("/api/models/edit-apply")
def api_models_edit_apply() -> JSONResponse:
    from fastapi import Request
    import asyncio
    async def _read():
        req = Request(scope={"type": "http"})
        body = await req.json()
        return body
    # For now, return a stub — governed edit apply will be implemented in v0.3
    return JSONResponse({
        "ok": False,
        "error": "Governed edit apply is not yet implemented. Use the dashboard for read-only visibility.",
        "note": "Edit receipts are generated for tracking. Apply requires explicit operator approval.",
    })

@app.get("/api/models/routing-eligibility")
def api_models_routing_eligibility() -> JSONResponse:
    return JSONResponse(build_routing_eligibility())


@app.get("/api/models/assets")
def api_models_assets() -> JSONResponse:
    return JSONResponse(build_asset_inventory())


@app.get("/api/models/wrappers")
def api_models_wrappers() -> JSONResponse:
    return JSONResponse(build_wrapper_registry())


@app.get("/api/models/settings-intelligence")
def api_models_settings_intelligence() -> JSONResponse:
    return JSONResponse(build_settings_intelligence())







