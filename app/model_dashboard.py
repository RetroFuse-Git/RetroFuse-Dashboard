"""Unity Model Dashboard - governed settings visibility and edit design.

Reads Bolt_ModelAliases.json and the continuation packet to produce a
structured model/lane dashboard with effective settings, default/explicit
differentiation, and governed edit support.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BOLT_ROOT = Path(r"D:\\PORTTORETRO_ARCHIVE\\PROJECTS\\Bolt")
MODEL_ALIASES_PATH = BOLT_ROOT / "Tools" / "Bolt_ModelAliases.json"
CONTINUATION_PACKET_PATH = BOLT_ROOT / "Tools" / "maintenance" / "UNITY_MODEL_DASHBOARD_CONTINUATION_v0.1.json"
EDIT_RECEIPTS_DIR = BOLT_ROOT / "Reports" / "Diagnostics" / "model_settings_edits"

OLLAMA_DEFAULTS = {
    "num_ctx": 2048,
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "repeat_penalty": 1.1,
    "num_predict": -1,
    "timeout_seconds": 300,
}

KNOWN_EXPLICIT_SETTINGS = {
    "gemma4:12b-gov64k": {
        "num_ctx": 65536, "temperature": 0.3, "top_p": 0.85, "top_k": 20,
        "repeat_penalty": 1.15, "num_predict": 4096, "timeout_seconds": 120, "output_ceiling": 4096,
    },
    "gemma4:12b": {
        "num_ctx": 65536, "temperature": 0.3, "top_p": 0.85, "top_k": 20,
        "repeat_penalty": 1.15, "num_predict": 4096, "timeout_seconds": 120, "output_ceiling": 4096,
    },
    "deepseek-v4-flash": {
        "num_ctx": 65536, "temperature": 0.5, "top_p": 0.9, "timeout_seconds": 120,
    },
    "deepseek-pro": {
        "num_ctx": 131072, "temperature": 0.3, "top_p": 0.85, "timeout_seconds": 300,
    },
    "gpt-oss:20b-cloud": {
        "num_ctx": 32768, "temperature": 0.5, "timeout_seconds": 120,
    },
    "gpt-oss:120b-cloud": {
        "num_ctx": 65536, "temperature": 0.5, "timeout_seconds": 180,
    },
    "llama3.1:8b": {
        "num_ctx": 8192, "temperature": 0.6, "top_p": 0.9, "timeout_seconds": 60,
    },
    "granite4.1:3b": {
        "num_ctx": 4096, "temperature": 0.6, "timeout_seconds": 60,
    },
    "lfm2.5:latest": {
        "num_ctx": 32768, "temperature": 0.5, "timeout_seconds": 120,
    },
    "lfm2.5:thinking": {
        "num_ctx": 65536, "temperature": 0.3, "top_p": 0.85, "timeout_seconds": 180,
    },
    "lfm2.5:gov": {
        "num_ctx": 65536, "temperature": 0.3, "top_p": 0.85, "timeout_seconds": 180, "output_ceiling": 4096,
    },
}

ADAPTER_LANES = [
    {"name": "ollama", "label": "Ollama (Direct)", "provider": "http://127.0.0.1:11434"},
    {"name": "codex", "label": "Codex", "provider": "ollama-launch"},
    {"name": "claude", "label": "Claude", "provider": "ollama-launch (proxy)"},
    {"name": "openclaw", "label": "OpenClaw", "provider": "ollama-launch"},
    {"name": "copilot", "label": "Copilot", "provider": "github-servers"},
    {"name": "cursor", "label": "Cursor", "provider": "agent.cmd"},
]

# ============================================================
# Wrapper Registry — Phase 1
# ============================================================

WRAPPER_REGISTRY = {
    "ollama_direct": {
        "wrapper_id": "ollama_direct",
        "label": "Ollama Direct",
        "short_label": "Ollama",
        "icon_key": "Ol",
        "class": "PREFERRED",
        "operator_preferred": True,
        "enabled": True,
        "detected": True,
        "configured": True,
        "operator_pinned": True,
        "main_board_visible": True,
        "catalog_visible": True,
        "launcher_path": None,
        "shortcut_prefix": None,
        "supports_read": True,
        "supports_write": False,
        "supports_execute": False,
        "supports_model_selection": True,
        "supports_ollama": True,
        "supports_cloud": True,
        "supports_local": True,
        "requires_admin": False,
        "evidence_status": "CONFIGURED",
        "last_validated": "2026-06-23T00:00:00Z",
        "notes": "Local Ollama server at http://127.0.0.1:11434.",
    },
    "codex": {
        "wrapper_id": "codex",
        "label": "Codex",
        "short_label": "Codex",
        "icon_key": "Cx",
        "class": "PREFERRED",
        "operator_preferred": True,
        "enabled": True,
        "detected": True,
        "configured": True,
        "operator_pinned": True,
        "main_board_visible": True,
        "catalog_visible": True,
        "launcher_path": "D:\\PORTTORETRO_ARCHIVE\\PROJECTS\\Bolt\\Tools\\bolt-codex.ps1",
        "shortcut_prefix": "bc",
        "supports_read": True,
        "supports_write": True,
        "supports_execute": False,
        "supports_model_selection": True,
        "supports_ollama": True,
        "supports_cloud": True,
        "supports_local": True,
        "requires_admin": False,
        "evidence_status": "CONFIGURED",
        "last_validated": "2026-06-23T00:00:00Z",
        "notes": "Codex native provider. ollama-launch profile.",
    },
    "claude_code": {
        "wrapper_id": "claude_code",
        "label": "Claude Code",
        "short_label": "Claude",
        "icon_key": "Cl",
        "class": "PREFERRED",
        "operator_preferred": True,
        "enabled": True,
        "detected": True,
        "configured": True,
        "operator_pinned": True,
        "main_board_visible": True,
        "catalog_visible": True,
        "launcher_path": "D:\\PORTTORETRO_ARCHIVE\\PROJECTS\\Bolt\\Tools\\bolt-claude.ps1",
        "shortcut_prefix": "bcl",
        "supports_read": True,
        "supports_write": True,
        "supports_execute": False,
        "supports_model_selection": True,
        "supports_ollama": True,
        "supports_cloud": True,
        "supports_local": True,
        "requires_admin": False,
        "evidence_status": "CONFIGURED",
        "last_validated": "2026-06-23T00:00:00Z",
        "notes": "Claude supervisor lane. ollama-launch proxy :3456.",
    },
    "openclaw": {
        "wrapper_id": "openclaw",
        "label": "OpenClaw",
        "short_label": "OpenClaw",
        "icon_key": "OC",
        "class": "SUPPORTED",
        "operator_preferred": True,
        "enabled": True,
        "detected": False,
        "configured": False,
        "operator_pinned": True,
        "main_board_visible": True,
        "catalog_visible": True,
        "launcher_path": "D:\\PORTTORETRO_ARCHIVE\\PROJECTS\\Bolt\\Tools\\bolt-openclaw.ps1",
        "shortcut_prefix": "bo",
        "supports_read": True,
        "supports_write": True,
        "supports_execute": False,
        "supports_model_selection": True,
        "supports_ollama": True,
        "supports_cloud": True,
        "supports_local": True,
        "requires_admin": False,
        "evidence_status": "UNKNOWN",
        "last_validated": None,
        "notes": "ollama-launch. Evidence UNKNOWN — do not infer.",
    },
    "copilot": {
        "wrapper_id": "copilot",
        "label": "Copilot",
        "short_label": "Copilot",
        "icon_key": "CP",
        "class": "SUPPORTED",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "UNKNOWN",
        "notes": "GitHub Copilot lane. github-servers.",
    },
    "gemini": {
        "wrapper_id": "gemini",
        "label": "Gemini",
        "short_label": "Gemini",
        "icon_key": "Gm",
        "class": "SUPPORTED",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "DEFERRED_MODEL_SELECTION",
        "notes": "Gemini model selection deferred.",
    },
    "opencode": {
        "wrapper_id": "opencode",
        "label": "OpenCode",
        "short_label": "OpenCode",
        "icon_key": "OCd",
        "class": "OPTIONAL",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "NOT_CONFIGURED",
        "notes": "Ecosystem completeness, not operator preference.",
    },
    "aider": {
        "wrapper_id": "aider",
        "label": "Aider",
        "short_label": "Aider",
        "icon_key": "Ai",
        "class": "OPTIONAL",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "NOT_CONFIGURED",
        "notes": "Ecosystem wrapper.",
    },
    "continue": {
        "wrapper_id": "continue",
        "label": "Continue",
        "short_label": "Continue",
        "icon_key": "Ct",
        "class": "OPTIONAL",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "NOT_CONFIGURED",
        "notes": "Ecosystem wrapper.",
    },
    "cursor": {
        "wrapper_id": "cursor",
        "label": "Cursor",
        "short_label": "Cursor",
        "icon_key": "Cu",
        "class": "OPTIONAL",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "NOT_CONFIGURED",
        "notes": "agent.cmd.",
    },
    "cline_roo": {
        "wrapper_id": "cline_roo",
        "label": "Cline / Roo",
        "short_label": "Cline/Roo",
        "icon_key": "CR",
        "class": "OPTIONAL",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "NOT_CONFIGURED",
        "notes": "Ecosystem wrapper.",
    },
    "goose": {
        "wrapper_id": "goose",
        "label": "Goose",
        "short_label": "Goose",
        "icon_key": "Gs",
        "class": "OPTIONAL",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "NOT_CONFIGURED",
        "notes": "Ecosystem wrapper.",
    },
    "custom_wrapper": {
        "wrapper_id": "custom_wrapper",
        "label": "Custom Wrapper",
        "short_label": "Custom",
        "icon_key": "+",
        "class": "CUSTOM",
        "operator_preferred": False,
        "enabled": False,
        "configured": False,
        "main_board_visible": False,
        "catalog_visible": True,
        "evidence_status": "PLACEHOLDER",
        "notes": "Placeholder for user-defined custom wrapper.",
    },
}

WRAPPER_CLASSES = {
    "PREFERRED": "Operator-preferred wrapper. Shown on main board and catalog.",
    "SUPPORTED": "Product-supported wrapper. May be configured or unconfigured.",
    "AVAILABLE": "Available but not yet classified.",
    "OPTIONAL": "Ecosystem wrapper. Catalog-only by default.",
    "EXPERIMENTAL": "Experimental wrapper. Not yet stable.",
    "UNKNOWN": "Classification not yet determined.",
    "DISLIKED_BY_OPERATOR": "Operator has explicitly indicated non-preference.",
    "BLOCKED": "Blocked by policy or technical constraint.",
    "CUSTOM": "User-defined custom wrapper.",
}

EVIDENCE_STATUSES = {
    "CONFIGURED": "Wrapper is configured and operational.",
    "VALIDATED": "Wrapper has been validated against a known-good state.",
    "UNKNOWN": "No evidence available. Do not infer.",
    "NOT_CONFIGURED": "Wrapper is not configured.",
    "DEFERRED_MODEL_SELECTION": "Model selection is deferred.",
    "FAILED": "Wrapper validation failed.",
    "NOT_SUPPORTED": "Wrapper does not support this model.",
    "PLACEHOLDER": "Placeholder entry for future configuration.",
}


def build_wrapper_registry() -> Dict[str, Any]:
    """Build the wrapper registry response with active and catalog-only wrappers."""
    active = []
    catalog_only = []
    for wid, w in WRAPPER_REGISTRY.items():
        if w.get("main_board_visible", False):
            active.append(dict(w))
        else:
            catalog_only.append(dict(w))

    by_class: Dict[str, int] = {}
    by_evidence: Dict[str, int] = {}
    for w in WRAPPER_REGISTRY.values():
        cls = w.get("class", "UNKNOWN")
        by_class[cls] = by_class.get(cls, 0) + 1
        ev = w.get("evidence_status", "UNKNOWN")
        by_evidence[ev] = by_evidence.get(ev, 0) + 1

    return {
        "registry_version": "v0.1",
        "generated_at": _iso_now_local(),
        "active_wrappers": active,
        "catalog_wrappers": catalog_only,
        "wrapper_classes": WRAPPER_CLASSES,
        "evidence_statuses": EVIDENCE_STATUSES,
        "summary": {
            "total_wrappers": len(WRAPPER_REGISTRY),
            "active_wrappers": len(active),
            "catalog_only_wrappers": len(catalog_only),
            "by_class": by_class,
            "by_evidence_status": by_evidence,
            "configured": sum(1 for w in WRAPPER_REGISTRY.values() if w.get("configured")),
            "detected": sum(1 for w in WRAPPER_REGISTRY.values() if w.get("detected")),
            "enabled": sum(1 for w in WRAPPER_REGISTRY.values() if w.get("enabled")),
            "unknown_evidence": sum(1 for w in WRAPPER_REGISTRY.values() if w.get("evidence_status") == "UNKNOWN"),
            "main_board_visible": len(active),
            "catalog_visible": sum(1 for w in WRAPPER_REGISTRY.values() if w.get("catalog_visible")),
        },
    }


# ============================================================
# Effective Settings Intelligence — Phase 2
# ============================================================

SETTINGS_GROUPS = [
    {
        "group": "core",
        "label": "Core Parameters",
        "home_visible": True,
        "settings": [
            {"setting_id": "num_ctx", "label": "Context Window", "default": 2048, "unit": "tokens", "risk_threshold": 2048, "ollama_param": "num_ctx"},
            {"setting_id": "temperature", "label": "Temperature", "default": 0.7, "unit": "", "risk_threshold": 0.7, "ollama_param": "temperature"},
            {"setting_id": "num_predict", "label": "Max Output Tokens", "default": -1, "unit": "tokens", "risk_threshold": -1, "ollama_param": "num_predict"},
            {"setting_id": "timeout_seconds", "label": "Timeout", "default": 300, "unit": "s", "risk_threshold": 300, "ollama_param": None},
        ],
    },
    {
        "group": "sampling",
        "label": "Sampling Parameters",
        "home_visible": False,
        "settings": [
            {"setting_id": "top_p", "label": "Top P", "default": 0.9, "unit": "", "risk_threshold": None, "ollama_param": "top_p"},
            {"setting_id": "top_k", "label": "Top K", "default": 40, "unit": "", "risk_threshold": None, "ollama_param": "top_k"},
            {"setting_id": "min_p", "label": "Min P", "default": 0.0, "unit": "", "risk_threshold": None, "ollama_param": "min_p"},
            {"setting_id": "repeat_penalty", "label": "Repeat Penalty", "default": 1.1, "unit": "", "risk_threshold": None, "ollama_param": "repeat_penalty"},
            {"setting_id": "seed", "label": "Seed", "default": 0, "unit": "", "risk_threshold": None, "ollama_param": "seed"},
        ],
    },
    {
        "group": "prompt_session",
        "label": "Prompt & Session",
        "home_visible": False,
        "settings": [
            {"setting_id": "system_prompt", "label": "System Prompt", "default": "", "unit": "", "risk_threshold": None, "ollama_param": "system"},
            {"setting_id": "stop_tokens", "label": "Stop Tokens", "default": [], "unit": "", "risk_threshold": None, "ollama_param": "stop"},
            {"setting_id": "session_context_state", "label": "Session Context", "default": "ephemeral", "unit": "", "risk_threshold": None, "ollama_param": None},
        ],
    },
    {
        "group": "ollama_server",
        "label": "Ollama Server",
        "home_visible": False,
        "settings": [
            {"setting_id": "ollama_host", "label": "Ollama Host", "default": "http://127.0.0.1:11434", "unit": "", "risk_threshold": None, "ollama_param": None},
            {"setting_id": "ollama_models_path", "label": "Models Path", "default": "~/.ollama/models", "unit": "", "risk_threshold": None, "ollama_param": None},
            {"setting_id": "serve_mode", "label": "Serve Mode", "default": "single-user", "unit": "", "risk_threshold": None, "ollama_param": None},
        ],
    },
    {
        "group": "persistence",
        "label": "Persistence & Profiles",
        "home_visible": False,
        "settings": [
            {"setting_id": "runtime_only", "label": "Runtime Only", "default": True, "unit": "", "risk_threshold": None, "ollama_param": None},
            {"setting_id": "modelfile_profile", "label": "Modelfile Profile", "default": "none", "unit": "", "risk_threshold": None, "ollama_param": None},
            {"setting_id": "wrapper_profile", "label": "Wrapper Profile", "default": "none", "unit": "", "risk_threshold": None, "ollama_param": None},
            {"setting_id": "known_good_profile", "label": "Known Good Profile", "default": "none", "unit": "", "risk_threshold": None, "ollama_param": None},
        ],
    },
]

OLLAMA_PARAMETER_INTELLIGENCE = {
    "runtime_examples": [
        {"command": "ollama run <model> --temperature <value> --num-ctx <value>", "description": "Set temperature and context at runtime"},
        {"command": "/set parameter seed <value>", "description": "Set random seed for reproducibility"},
        {"command": "/set parameter num_predict <value>", "description": "Limit max output tokens"},
        {"command": "/set parameter top_k <value>", "description": "Top-K sampling"},
        {"command": "/set parameter top_p <value>", "description": "Nucleus sampling threshold"},
        {"command": "/set parameter min_p <value>", "description": "Minimum probability threshold"},
        {"command": "/set parameter num_ctx <value>", "description": "Context window size"},
        {"command": "/set parameter temperature <value>", "description": "Model temperature"},
        {"command": "/set parameter stop <tokens>", "description": "Stop tokens"},
        {"command": "/show parameters", "description": "Show current effective parameters"},
    ],
    "persistent_examples": [
        {"command": "Modelfile FROM <base>", "description": "Base model for Modelfile"},
        {"command": "PARAMETER temperature <value>", "description": "Persistent temperature override"},
        {"command": "PARAMETER top_p <value>", "description": "Persistent top-p override"},
        {"command": "PARAMETER num_ctx <value>", "description": "Persistent context window"},
        {"command": "SYSTEM <prompt>", "description": "Persistent system prompt"},
    ],
    "server_examples": [
        {"command": "OLLAMA_HOST", "description": "Environment variable for Ollama server host"},
        {"command": "OLLAMA_MODELS", "description": "Environment variable for models path"},
        {"command": "ollama serve", "description": "Start Ollama server"},
    ],
    "rule": "Display as capability/setting knowledge only. Do not execute ollama commands and do not create Modelfiles in this phase.",
}

HAZARD_PROFILES = {
    "gemini*flash*ollama*": {
        "model_pattern": "gemini*flash*ollama*",
        "home_mode_recommended": False,
        "business_mode_allowed": True,
        "requires_guard_profile": True,
        "cost_sensitive": True,
        "settings_sensitive": True,
        "default_behavior_risk": True,
        "known_good_profile": "guarded_gemini_flash",
        "default_risk_reason": "Cost-sensitive cloud model. Default settings may incur unexpected charges. Use only with known-good guarded profile.",
        "recommended_action": "Configure guarded profile before use. Not recommended for casual Home Mode.",
        "profile_status": "NOT_CONFIGURED",
    },
}

DEFAULT_HAZARD_PROFILE = {
    "model_pattern": "*",
    "home_mode_recommended": True,
    "business_mode_allowed": True,
    "requires_guard_profile": False,
    "cost_sensitive": False,
    "settings_sensitive": False,
    "default_behavior_risk": False,
    "known_good_profile": None,
    "default_risk_reason": None,
    "recommended_action": None,
    "profile_status": "UNKNOWN",
}


def _resolve_hazard_profile(alias_name: str, model_name: str) -> Dict[str, Any]:
    """Resolve hazard profile for a model by pattern matching."""
    import fnmatch
    for pattern, profile in HAZARD_PROFILES.items():
        if fnmatch.fnmatch(alias_name, pattern) or fnmatch.fnmatch(model_name, pattern):
            return dict(profile)
    return dict(DEFAULT_HAZARD_PROFILE)


def _build_effective_settings_for_model(
    alias_name: str,
    alias_config: Dict[str, Any],
    explicit: Dict[str, Any],
    defaults: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build effective settings with source stack for a single model."""
    result = []
    for group in SETTINGS_GROUPS:
        for sdef in group["settings"]:
            sid = sdef["setting_id"]
            default_val = sdef["default"]
            effective = default_val
            source = "factory_default"
            source_stack = []

            # Check explicit overrides
            if sid in explicit:
                effective = explicit[sid]
                source = "explicit"
                source_stack.append("explicit")

            # Check alias config
            if sid in alias_config and alias_config[sid] is not None:
                effective = alias_config[sid]
                source = "config"
                source_stack.append("config")

            # Check Ollama defaults
            if sid in defaults:
                if source == "factory_default":
                    effective = defaults[sid]
                    source = "ollama_default"
                    source_stack.append("ollama_default")

            # If still factory default, use the default value
            if not source_stack:
                source_stack.append("factory_default")

            # Determine risk
            risk_level = "safe"
            risk_reason = None
            threshold = sdef.get("risk_threshold")
            if threshold is not None and effective == threshold:
                risk_level = "defaulted"
                risk_reason = f"At factory default ({threshold})"
            if threshold is not None and sid == "num_ctx" and effective == 2048:
                risk_level = "risky"
                risk_reason = "Default 2048 context may be too small for governed lanes"
            if sid == "num_predict" and effective == -1:
                risk_level = "risky"
                risk_reason = "Unlimited output tokens (-1) may cause unbounded generation"
            if sid == "timeout_seconds" and effective == 300:
                risk_level = "risky"
                risk_reason = "Default 300s timeout may cause hung requests"

            result.append({
                "setting_id": sid,
                "label": sdef["label"],
                "group": group["group"],
                "group_label": group["label"],
                "home_visible": group["home_visible"],
                "effective_value": effective,
                "source": source,
                "source_stack": source_stack,
                "default_value": default_val,
                "configured_value": alias_config.get(sid, None),
                "runtime_override": None,
                "wrapper_override": None,
                "modelfile_value": None,
                "risk_level": risk_level,
                "risk_reason": risk_reason,
                "home_visibility": "visible" if group["home_visible"] else "hidden",
                "business_visibility": "visible",
                "editable_future": True,
                "notes": None,
                "ollama_param": sdef.get("ollama_param"),
            })
    return result


def build_settings_intelligence() -> Dict[str, Any]:
    """Build the settings intelligence response with per-model effective settings and hazard profiles."""
    aliases_data = _load_model_aliases()
    continuation = _load_continuation_packet()
    aliases = aliases_data.get("aliases", {})
    continuation_rows = continuation.get("dashboard_rows", [])

    per_model = []
    summary_risks = {"defaulted": 0, "risky": 0, "safe": 0, "unknown": 0}
    summary_hazards = {"cost_sensitive": 0, "settings_sensitive": 0, "needs_profile": 0}

    for alias_name, alias_config in aliases.items():
        if not isinstance(alias_config, dict):
            continue

        model_name = alias_config.get("model", alias_name)
        explicit = KNOWN_EXPLICIT_SETTINGS.get(alias_name, {})
        defaults = OLLAMA_DEFAULTS.copy()

        effective_settings = _build_effective_settings_for_model(alias_name, alias_config, explicit, defaults)
        hazard = _resolve_hazard_profile(alias_name, model_name)

        # Count risks
        for s in effective_settings:
            rl = s["risk_level"]
            summary_risks[rl] = summary_risks.get(rl, 0) + 1

        if hazard.get("cost_sensitive"):
            summary_hazards["cost_sensitive"] += 1
        if hazard.get("settings_sensitive"):
            summary_hazards["settings_sensitive"] += 1
        if hazard.get("requires_guard_profile"):
            summary_hazards["needs_profile"] += 1

        per_model.append({
            "alias": alias_name,
            "model": model_name,
            "route_tier": alias_config.get("route_tier", ""),
            "usage_tier": alias_config.get("usage_tier", 0),
            "status": alias_config.get("status", "active"),
            "effective_settings": effective_settings,
            "hazard_profile": hazard,
        })

    def _sort_key(m):
        tier_order = {"local": 0, "cloud": 1}
        return (tier_order.get(m["route_tier"], 99), m.get("usage_tier", 99), m["alias"])

    per_model.sort(key=_sort_key)

    return {
        "intelligence_version": "v0.1",
        "generated_at": _iso_now_local(),
        "settings_groups": SETTINGS_GROUPS,
        "ollama_parameter_intelligence": OLLAMA_PARAMETER_INTELLIGENCE,
        "hazard_profiles": HAZARD_PROFILES,
        "per_model": per_model,
        "summary": {
            "total_models": len(per_model),
            "risk_counts": summary_risks,
            "hazard_counts": summary_hazards,
        },
    }

def _read_json(path: Path) -> Optional[Any]:
    try:
        if not path.exists():
            return None
        raw = path.read_bytes()
        for encoding in ("utf-8", "utf-8-sig", "utf-16", "utf-16-le"):
            try:
                return json.loads(raw.decode(encoding))
            except Exception:
                continue
    except Exception:
        return None
    return None


def _iso_now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _safe_stat_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except Exception:
        return 0.0


def _load_model_aliases() -> Dict[str, Any]:
    data = _read_json(MODEL_ALIASES_PATH)
    return data if isinstance(data, dict) else {}


def _load_continuation_packet() -> Dict[str, Any]:
    data = _read_json(CONTINUATION_PACKET_PATH)
    return data if isinstance(data, dict) else {}


def _build_model_settings_row(
    alias_name: str,
    alias_config: Dict[str, Any],
    continuation_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    explicit = KNOWN_EXPLICIT_SETTINGS.get(alias_name, {})
    defaults = OLLAMA_DEFAULTS.copy()
    cont_row = None
    for row in continuation_rows:
        row_model = (row.get("model", "") or "")
        if row_model == alias_name or row_model == alias_config.get("model", "") or alias_name.startswith(row_model.split("(")[0].strip()):
            cont_row = row
            break

    def _effective(key: str, default_val: Any = None):
        if key in explicit:
            return explicit[key], "explicit"
        if key in alias_config and alias_config[key] is not None:
            return alias_config[key], "config"
        if default_val is not None:
            return default_val, "default"
        return defaults.get(key, None), "default"

    ctx, ctx_src = _effective("context_window_tokens", alias_config.get("context_window_tokens"))
    if ctx is None:
        ctx, ctx_src = _effective("num_ctx")
    temp, temp_src = _effective("temperature")
    top_p, top_p_src = _effective("top_p")
    top_k, top_k_src = _effective("top_k")
    rp, rp_src = _effective("repeat_penalty")
    num_pred, np_src = _effective("num_predict")
    timeout, to_src = _effective("timeout_seconds")
    output_ceil, oc_src = _effective("output_ceiling")

    status = cont_row.get("status", "") if cont_row else ""
    if not status:
        alias_status = alias_config.get("status", "active")
        if alias_status == "candidate":
            status = "CANDIDATE"
        elif alias_status == "active":
            status = "ACTIVE"
        else:
            status = alias_status.upper()

    confidence = cont_row.get("confidence", "") if cont_row else ""
    if not confidence:
        confidence = "MEDIUM" if alias_config.get("tested_with_claude_cloud") else "LOW"

    role_class = cont_row.get("role_class", "") if cont_row else ""
    if not role_class:
        route_tier = alias_config.get("route_tier", "")
        role_class = "local" if route_tier == "local" else "cloud"

    evidence_packet = cont_row.get("evidence_packet", "") if cont_row else ""
    known_failures = cont_row.get("known_failure_signatures", []) if cont_row else []
    next_action = cont_row.get("next_action", "") if cont_row else ""
    promotion_eligible = cont_row.get("promotion_eligible", False) if cont_row else False

    settings_fields = [
        {"key": "num_ctx", "label": "Context Window", "value": ctx, "source": ctx_src,
         "is_default": ctx_src == "default", "is_unsafe": ctx_src == "default" and ctx == 2048},
        {"key": "temperature", "label": "Temperature", "value": temp, "source": temp_src,
         "is_default": temp_src == "default", "is_unsafe": temp_src == "default"},
        {"key": "top_p", "label": "Top P", "value": top_p, "source": top_p_src,
         "is_default": top_p_src == "default"},
        {"key": "top_k", "label": "Top K", "value": top_k, "source": top_k_src,
         "is_default": top_k_src == "default"},
        {"key": "repeat_penalty", "label": "Repeat Penalty", "value": rp, "source": rp_src,
         "is_default": rp_src == "default"},
        {"key": "num_predict", "label": "Max Output Tokens", "value": num_pred, "source": np_src,
         "is_default": np_src == "default", "is_unsafe": np_src == "default" and num_pred == -1},
        {"key": "output_ceiling", "label": "Output Ceiling", "value": output_ceil, "source": oc_src,
         "is_default": oc_src == "default"},
        {"key": "timeout_seconds", "label": "Timeout (s)", "value": timeout, "source": to_src,
         "is_default": to_src == "default", "is_unsafe": to_src == "default" and timeout == 300},
    ]

    adapter_statuses = []
    for lane in ADAPTER_LANES:
        lane_name = lane["name"]
        cont_adapter = (cont_row.get("adapter", "") or "") if cont_row else ""
        if cont_row and (cont_adapter == lane_name or cont_adapter.startswith(lane_name)):
            lane_status = cont_row.get("status", "UNKNOWN")
            lane_confidence = cont_row.get("confidence", "NONE")
        else:
            lane_status = "UNKNOWN_NOT_PROVEN"
            lane_confidence = "NONE"
        adapter_statuses.append({
            "adapter": lane_name,
            "label": lane["label"],
            "provider": lane["provider"],
            "status": lane_status,
            "confidence": lane_confidence,
        })

    # Wrapper chips for this model (active/main-board wrappers only)
    model_wrappers = []
    for wid, wdef in WRAPPER_REGISTRY.items():
        if not wdef.get("main_board_visible", False):
            continue
        model_wrappers.append({
            "wrapper_id": wid,
            "label": wdef.get("short_label", wid),
            "icon_key": wdef.get("icon_key", ""),
            "class": wdef.get("class", "UNKNOWN"),
            "evidence_status": wdef.get("evidence_status", "UNKNOWN"),
            "configured": wdef.get("configured", False),
            "supports_read": wdef.get("supports_read", False),
            "supports_write": wdef.get("supports_write", False),
            "supports_local": wdef.get("supports_local", False),
            "supports_cloud": wdef.get("supports_cloud", False),
        })

    # Effective settings intelligence for this model
    effective_settings = _build_effective_settings_for_model(alias_name, alias_config, explicit, defaults)
    hazard_profile = _resolve_hazard_profile(alias_name, alias_config.get("model", alias_name))

    return {
        "alias": alias_name,
        "model": alias_config.get("model", alias_name),
        "claude_model": alias_config.get("claude_model", ""),
        "description": alias_config.get("description", ""),
        "route_tier": alias_config.get("route_tier", ""),
        "usage_tier": alias_config.get("usage_tier", 0),
        "usage_cost": alias_config.get("usage_cost", ""),
        "default_allowed": alias_config.get("default_allowed", False),
        "write_allowed": alias_config.get("write_allowed", False),
        "provider_base_url": alias_config.get("provider_base_url", ""),
        "codex_profile": alias_config.get("codex_profile", ""),
        "status": status,
        "confidence": confidence,
        "role_class": role_class,
        "evidence_packet": evidence_packet,
        "known_failure_signatures": known_failures,
        "next_action": next_action,
        "promotion_eligible": promotion_eligible,
        "settings": settings_fields,
        "adapter_statuses": adapter_statuses,
        "wrappers": model_wrappers,
        "effective_settings": effective_settings,
        "hazard_profile": hazard_profile,
        "last_validated": _iso_now_local(),
    }


def build_model_dashboard() -> Dict[str, Any]:
    aliases_data = _load_model_aliases()
    continuation = _load_continuation_packet()
    aliases = aliases_data.get("aliases", {})
    continuation_rows = continuation.get("dashboard_rows", [])

    rows = []
    for alias_name, alias_config in aliases.items():
        if not isinstance(alias_config, dict):
            continue
        row = _build_model_settings_row(alias_name, alias_config, continuation_rows)
        rows.append(row)

    def _sort_key(row):
        tier_order = {"local": 0, "cloud": 1}
        return (tier_order.get(row["route_tier"], 99), row.get("usage_tier", 99), row["alias"])

    rows.sort(key=_sort_key)

    total = len(rows)
    local_count = sum(1 for r in rows if r["route_tier"] == "local")
    cloud_count = sum(1 for r in rows if r["route_tier"] == "cloud")
    default_risk_count = sum(1 for r in rows for s in r["settings"] if s.get("is_unsafe"))
    explicit_count = sum(1 for r in rows for s in r["settings"] if s["source"] == "explicit")
    default_count = sum(1 for r in rows for s in r["settings"] if s["source"] == "default")

    return {
        "dashboard_version": "v0.2",
        "generated_at": _iso_now_local(),
        "source_aliases": str(MODEL_ALIASES_PATH),
        "source_continuation": str(CONTINUATION_PACKET_PATH),
        "summary": {
            "total_models": total,
            "local_models": local_count,
            "cloud_models": cloud_count,
            "settings_with_default_risk": default_risk_count,
            "settings_explicitly_configured": explicit_count,
            "settings_at_default": default_count,
        },
        "rows": rows,
        "defaults": OLLAMA_DEFAULTS,
        "known_explicit_overrides": {k: v for k, v in KNOWN_EXPLICIT_SETTINGS.items()},
    }


def build_edit_receipt(
    model_alias: str,
    field: str,
    old_value: Any,
    new_value: Any,
    operator: str = "dashboard",
) -> Dict[str, Any]:
    receipt = {
        "receipt_type": "model_settings_edit",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model_alias": model_alias,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "operator": operator,
        "rollback": {
            "action": f"Set {field} back to {old_value} for {model_alias}",
            "previous_value": old_value,
        },
        "diff": f"{field}: {old_value} -> {new_value}",
        "status": "pending_apply",
    }
    return receipt


def save_edit_receipt(receipt: Dict[str, Any]) -> Optional[str]:
    if not EDIT_RECEIPTS_DIR.exists():
        try:
            EDIT_RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
        except Exception:
            return None
    ts = receipt.get("timestamp_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    safe_ts = ts.replace(":", "-").replace("+", "_").replace(".", "-")
    model = receipt.get("model_alias", "unknown")
    safe_model = model.replace(":", "_").replace("/", "_").replace("\\", "_")
    filename = f"edit_{safe_model}_{safe_ts}.json"
    path = EDIT_RECEIPTS_DIR / filename
    try:
        path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        return str(path)
    except Exception:
        return None


def list_edit_receipts(limit: int = 20) -> List[Dict[str, Any]]:
    if not EDIT_RECEIPTS_DIR.exists():
        return []
    try:
        files = sorted(
            [p for p in EDIT_RECEIPTS_DIR.glob("edit_*.json") if p.is_file()],
            key=_safe_stat_mtime,
            reverse=True,
        )[:limit]
    except Exception:
        return []
    receipts = []
    for p in files:
        data = _read_json(p)
        if isinstance(data, dict):
            data["_path"] = str(p)
            data["_mtime"] = datetime.fromtimestamp(_safe_stat_mtime(p)).astimezone().isoformat(timespec="seconds")
            receipts.append(data)
    return receipts


# ============================================================
# Asset Inventory & Provider Policy Guardrails
# ============================================================

ASSET_INVENTORY = {
    "ollama_local": {
        "provider": "Ollama",
        "surface": "local",
        "access_enabled": True,
        "access_level": "LOCAL_INCLUDED",
        "cost_class": "free",
        "quota_class": "unlimited",
        "license_scope": "PERSONAL",
        "allowed_use": "PERSONAL",
        "verification_source": "configured",
        "last_verified": "2026-06-23T00:00:00Z",
        "confidence": "CONFIGURED",
        "notes": "Local Ollama server at http://127.0.0.1:11434. No external API calls.",
    },
    "ollama_cloud_proxy": {
        "provider": "Ollama Cloud Proxy",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "FREE_TIER_REPORTED",
        "cost_class": "light",
        "quota_class": "bounded",
        "license_scope": "PERSONAL",
        "allowed_use": "PERSONAL",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "Ollama-compatible cloud proxy. Free tier reported by operator.",
    },
    "deepseek_api": {
        "provider": "DeepSeek",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "METERED_API",
        "cost_class": "medium",
        "quota_class": "metered",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "DeepSeek V4 Flash (Tier 1) and DeepSeek V4 Pro (Tier 3). Metered API.",
    },
    "qwen_api": {
        "provider": "Qwen (Alibaba Cloud)",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "METERED_API",
        "cost_class": "medium",
        "quota_class": "metered",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "Qwen 3.5 (Tier 1), Qwen3-Coder-Next (Tier 2), Qwen3-Coder 480B (Tier 2).",
    },
    "gemma_cloud": {
        "provider": "Gemma (Google)",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "FREE_TIER_REPORTED",
        "cost_class": "medium",
        "quota_class": "bounded",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "Gemma 4 31B Cloud (Tier 1 candidate). Free tier reported.",
    },
    "gpt_oss_api": {
        "provider": "GPT-OSS",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "FREE_TIER_REPORTED",
        "cost_class": "light",
        "quota_class": "bounded",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "GPT-OSS 20B (Tier 0) and 120B (Tier 1). Free tier reported.",
    },
    "nemotron_api": {
        "provider": "NVIDIA Nemotron",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "FREE_TIER_REPORTED",
        "cost_class": "light",
        "quota_class": "bounded",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "Nemotron 3 Nano 30B (Tier 0), Super 120B (Tier 1), Ultra (Tier 3 candidate).",
    },
    "minimax_api": {
        "provider": "MiniMax",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "METERED_API",
        "cost_class": "medium",
        "quota_class": "metered",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "MiniMax M2.5 (Tier 1), M2.7 (Tier 1), M3 (Tier 2). Metered API.",
    },
    "glm_api": {
        "provider": "GLM (Zhipu AI)",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "METERED_API",
        "cost_class": "heavy",
        "quota_class": "metered",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "GLM 5.1 (Tier 2), 5.2 (Tier 2), GLM-5 (Tier 3). 744B MoE.",
    },
    "kimi_api": {
        "provider": "Kimi (Moonshot AI)",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "METERED_API",
        "cost_class": "heavy",
        "quota_class": "metered",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "Kimi K2.5 (Tier 2), K2.6 (Tier 2), K2.7 Code (Tier 2 candidate).",
    },
    "devstral_api": {
        "provider": "Devstral",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "FREE_TIER_REPORTED",
        "cost_class": "medium",
        "quota_class": "bounded",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "Devstral Small 2 24B (Tier 1), Devstral 2 123B (Tier 2).",
    },
    "gemini_api": {
        "provider": "Gemini (Google)",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "FREE_TIER_REPORTED",
        "cost_class": "heavy",
        "quota_class": "scarce",
        "license_scope": "BUSINESS",
        "allowed_use": "BUSINESS",
        "verification_source": "operator_reported",
        "last_verified": "2026-06-16T00:00:00Z",
        "confidence": "OPERATOR_REPORTED",
        "notes": "Gemini 3 Flash Preview (Tier 3, Claude only). Scarce quota.",
    },
    "claude_supervisor": {
        "provider": "Claude (Anthropic)",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "USER_SUBSCRIPTION",
        "cost_class": "heavy",
        "quota_class": "metered",
        "license_scope": "PERSONAL",
        "allowed_use": "PERSONAL",
        "verification_source": "configured",
        "last_verified": "2026-06-23T00:00:00Z",
        "confidence": "CONFIGURED",
        "notes": "Claude supervisor lane. User subscription.",
    },
    "codex_native": {
        "provider": "Codex (OpenAI)",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "USER_SUBSCRIPTION",
        "cost_class": "medium",
        "quota_class": "metered",
        "license_scope": "PERSONAL",
        "allowed_use": "PERSONAL",
        "verification_source": "configured",
        "last_verified": "2026-06-23T00:00:00Z",
        "confidence": "CONFIGURED",
        "notes": "Codex native provider. User subscription.",
    },
    "github_copilot": {
        "provider": "GitHub Copilot",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "USER_SUBSCRIPTION",
        "cost_class": "medium",
        "quota_class": "metered",
        "license_scope": "PERSONAL",
        "allowed_use": "PERSONAL",
        "verification_source": "configured",
        "last_verified": "2026-06-23T00:00:00Z",
        "confidence": "CONFIGURED",
        "notes": "GitHub Copilot lane. User subscription.",
    },
    "cursor_agent": {
        "provider": "Cursor Agent",
        "surface": "cloud",
        "access_enabled": True,
        "access_level": "USER_SUBSCRIPTION",
        "cost_class": "medium",
        "quota_class": "metered",
        "license_scope": "PERSONAL",
        "allowed_use": "PERSONAL",
        "verification_source": "configured",
        "last_verified": "2026-06-23T00:00:00Z",
        "confidence": "CONFIGURED",
        "notes": "Cursor agent lane. User subscription.",
    },
}

HOME_MODE_POLICY = {
    "mode": "home",
    "label": "Home Mode (Personal)",
    "description": "Default personal-use policy. Conservative defaults. No sensitive data exposure.",
    "default_access_level": "PERSONAL",
    "allowed_surfaces": ["local", "cloud"],
    "max_cost_class": "medium",
    "blocked_providers": [],
    "restricted_providers": [],
    "sensitive_data_allowed": "BLOCKED",
    "write_allowed": True,
    "default_allowed_tiers": [0, 1],
    "require_explicit_route_reason_for_tiers": [2, 3],
    "audit_logging": "minimal",
    "policy_version": "v0.1",
    "last_updated": "2026-06-23T00:00:00Z",
}

BUSINESS_MODE_POLICY = {
    "mode": "business",
    "label": "Business Mode (Admin Policy)",
    "description": "Admin-configured business policy. Stricter access controls. Can allow sensitive data.",
    "default_access_level": "BUSINESS",
    "allowed_surfaces": ["local", "cloud"],
    "max_cost_class": "heavy",
    "blocked_providers": [],
    "restricted_providers": ["gemini_api"],
    "sensitive_data_allowed": "POLICY_CONTROLLED",
    "write_allowed": True,
    "default_allowed_tiers": [0, 1, 2],
    "require_explicit_route_reason_for_tiers": [3],
    "audit_logging": "full",
    "policy_version": "v0.1",
    "last_updated": "2026-06-23T00:00:00Z",
}


def build_asset_inventory() -> Dict[str, Any]:
    assets = []
    for asset_id, asset in ASSET_INVENTORY.items():
        entry = dict(asset)
        entry["asset_id"] = asset_id
        assets.append(entry)

    def _sort_key(a):
        surface_order = {"local": 0, "cloud": 1}
        return (surface_order.get(a["surface"], 99), a["provider"])

    assets.sort(key=_sort_key)

    return {
        "inventory_version": "v0.1",
        "generated_at": _iso_now_local(),
        "total_assets": len(assets),
        "assets": assets,
        "home_mode": HOME_MODE_POLICY,
        "business_mode": BUSINESS_MODE_POLICY,
    }


def _resolve_authoritative_tier(
    alias_name: str,
    alias_config: Dict[str, Any],
    model_tiers: Dict[str, int],
) -> Tuple[int, str]:
    """Resolve the authoritative tier for a model alias.
    
    Uses routing_policy tiers as source of truth, with usage_tier as fallback.
    Returns (tier, source) where source is 'routing_policy' or 'usage_tier'.
    """
    model_name = alias_config.get("model", alias_name)
    if model_name in model_tiers:
        return model_tiers[model_name], "routing_policy"
    # Fallback: check alias_name directly
    if alias_name in model_tiers:
        return model_tiers[alias_name], "routing_policy"
    # Fallback: use usage_tier from alias config
    usage_tier = alias_config.get("usage_tier")
    if usage_tier is not None:
        return usage_tier, "usage_tier"
    return 99, "unknown"


def build_routing_eligibility() -> Dict[str, Any]:
    aliases_data = _load_model_aliases()
    aliases = aliases_data.get("aliases", {})
    policy = aliases_data.get("routing_policy", {})
    tiers = policy.get("tiers", [])

    tier_defs = []
    for t in tiers:
        tier_defs.append({
            "tier": t.get("tier"),
            "name": t.get("name"),
            "default_allowed": t.get("default_allowed", False),
            "write_allowed": t.get("write_allowed", False),
            "use_cases": t.get("use_cases", ""),
        })

    model_tiers = {}
    for t in tiers:
        for model_name in t.get("models", []):
            model_tiers[model_name] = t.get("tier")

    eligibility = []
    for alias_name, alias_config in aliases.items():
        if not isinstance(alias_config, dict):
            continue
        tier, tier_source = _resolve_authoritative_tier(alias_name, alias_config, model_tiers)
        route_tier = alias_config.get("route_tier", "")
        default_allowed = alias_config.get("default_allowed", False)
        write_allowed = alias_config.get("write_allowed", False)
        status = alias_config.get("status", "")

        home_eligible = default_allowed and tier <= 1
        biz_eligible = default_allowed or (tier <= 2 and status == "active")

        eligibility.append({
            "alias": alias_name,
            "model": model_name,
            "tier": tier,
            "tier_source": tier_source,
            "route_tier": route_tier,
            "status": status,
            "default_allowed": default_allowed,
            "write_allowed": write_allowed,
            "home_mode_eligible": home_eligible,
            "business_mode_eligible": biz_eligible,
            "requires_explicit_route_reason": tier >= 2,
        })

    def _sort_key(e):
        return (e["tier"], e["alias"])

    eligibility.sort(key=_sort_key)

    return {
        "routing_version": "v0.1",
        "generated_at": _iso_now_local(),
        "tier_definitions": tier_defs,
        "total_models": len(eligibility),
        "home_eligible_count": sum(1 for e in eligibility if e["home_mode_eligible"]),
        "business_eligible_count": sum(1 for e in eligibility if e["business_mode_eligible"]),
        "requires_reason_count": sum(1 for e in eligibility if e["requires_explicit_route_reason"]),
        "eligibility": eligibility,
    }

def build_mode_aware_dashboard(mode: str = "home") -> Dict[str, Any]:
    """Build a mode-aware dashboard with visual layer data."""
    dashboard = build_model_dashboard()
    inventory = build_asset_inventory()
    routing = build_routing_eligibility()

    mode = mode.lower()
    if mode not in ("home", "business"):
        mode = "home"

    policy = inventory.get("home_mode", {}) if mode == "home" else inventory.get("business_mode", {})

    # Build model_tiers lookup from routing policy
    aliases_data_local = _load_model_aliases()
    policy_local = aliases_data_local.get("routing_policy", {})
    tiers_local = policy_local.get("tiers", [])
    model_tiers = {}
    for t in tiers_local:
        for model_name in t.get("models", []):
            model_tiers[model_name] = t.get("tier")

    # Build visual layer data
    visual = {
        "mode": mode,
        "mode_label": "Home Mode (Personal)" if mode == "home" else "Business Mode (Admin Policy)",
        "policy": policy,
        "lane_cards": [],
        "risk_summary": {"total": 0, "ctx_risk": 0, "temp_risk": 0, "output_risk": 0, "timeout_risk": 0, "profile_risk": 0, "route_risk": 0},
        "route_flow": [],
        "asset_badges": [],
    }

    # Build lane cards
    for row in dashboard.get("rows", []):
        alias = row.get("alias", "")
        status = row.get("status", "UNKNOWN")
        confidence = row.get("confidence", "LOW")
        route_tier = row.get("route_tier", "")
        usage_tier = row.get("usage_tier", 99)
        default_allowed = row.get("default_allowed", False)

        # Determine lane card state
        unsafe_count = sum(1 for s in row.get("settings", []) if s.get("is_unsafe"))
        if status in ("WORKING_CONTROL", "FUNCTIONAL_AFTER_REPAIR", "VALIDATED") and unsafe_count == 0:
            lane_state = "READY"
        elif unsafe_count > 0:
            lane_state = "DEFAULT_RISK"
        elif status in ("CAPPED", "ROUTE_ENFORCED_ONLY"):
            lane_state = "STALE"
        elif status in ("UNUSABLE", "BLOCKED_WITH_SIGNATURE", "PICKER_COVERAGE_GAP"):
            lane_state = "BLOCKED"
        elif status in ("CANDIDATE", "DOWNLOADED_ONLY", "UNKNOWN_NOT_PROVEN"):
            lane_state = "UNKNOWN"
        else:
            lane_state = "VALIDATED" if confidence == "HIGH" else "UNKNOWN"

        # Determine home/business eligibility using canonical tier
        authoritative_tier, tier_source = _resolve_authoritative_tier(alias, row, model_tiers)
        if mode == "home":
            eligible = default_allowed and authoritative_tier <= 1
        else:
            eligible = default_allowed or (authoritative_tier <= 2 and status.lower() == 'active')

        # Build risk heat badges
        risk_badges = []
        for s in row.get("settings", []):
            if s.get("is_unsafe"):
                key = s.get("key", "")
                if key == "num_ctx":
                    risk_badges.append("CTX")
                    visual["risk_summary"]["ctx_risk"] += 1
                elif key == "temperature":
                    risk_badges.append("TEMP")
                    visual["risk_summary"]["temp_risk"] += 1
                elif key in ("num_predict", "output_ceiling"):
                    risk_badges.append("OUTPUT")
                    visual["risk_summary"]["output_risk"] += 1
                elif key == "timeout_seconds":
                    risk_badges.append("TIMEOUT")
                    visual["risk_summary"]["timeout_risk"] += 1

        if not row.get("codex_profile"):
            risk_badges.append("PROFILE")
            visual["risk_summary"]["profile_risk"] += 1
        if not default_allowed:
            risk_badges.append("ROUTE")
            visual["risk_summary"]["route_risk"] += 1

        visual["risk_summary"]["total"] += len(risk_badges)

        # Build route flow
        route_flow_state = "IDLE"
        if lane_state == "READY":
            route_flow_state = "VERIFIED"
        elif lane_state == "DEFAULT_RISK":
            route_flow_state = "RECOMMENDED"
        elif not default_allowed:
            route_flow_state = "REQUIRES_REASON"
        elif lane_state == "BLOCKED":
            route_flow_state = "BLOCKED"

        lane_card = {
            "alias": alias,
            "model": row.get("model", ""),
            "description": row.get("description", ""),
            "route_tier": route_tier,
            "usage_tier": usage_tier,
            "status": status,
            "confidence": confidence,
            "lane_state": lane_state,
            "eligible": eligible,
            "risk_badges": risk_badges,
            "unsafe_count": unsafe_count,
            "route_flow_state": route_flow_state,
            "default_allowed": default_allowed,
            "write_allowed": row.get("write_allowed", False),
            "provider_base_url": row.get("provider_base_url", ""),
            "codex_profile": row.get("codex_profile", ""),
        }
        visual["lane_cards"].append(lane_card)

    # Build route flow summary
    flow_states = {}
    for card in visual["lane_cards"]:
        state = card["route_flow_state"]
        flow_states[state] = flow_states.get(state, 0) + 1
    visual["route_flow"] = [
        {"state": "VERIFIED", "count": flow_states.get("VERIFIED", 0), "label": "Verified routes"},
        {"state": "RECOMMENDED", "count": flow_states.get("RECOMMENDED", 0), "label": "Needs tuning"},
        {"state": "REQUIRES_REASON", "count": flow_states.get("REQUIRES_REASON", 0), "label": "Requires reason"},
        {"state": "BLOCKED", "count": flow_states.get("BLOCKED", 0), "label": "Blocked"},
        {"state": "IDLE", "count": flow_states.get("IDLE", 0), "label": "Idle / unknown"},
    ]

    # Build asset confidence badges
    for asset in inventory.get("assets", []):
        visual["asset_badges"].append({
            "provider": asset.get("provider", ""),
            "asset_id": asset.get("asset_id", ""),
            "confidence": asset.get("confidence", "UNKNOWN"),
            "access_level": asset.get("access_level", "UNKNOWN"),
            "surface": asset.get("surface", ""),
            "cost_class": asset.get("cost_class", ""),
        })

    return {
        "dashboard_version": dashboard.get("dashboard_version", "v0.2"),
        "visual_version": "v0.1",
        "generated_at": _iso_now_local(),
        "mode": mode,
        "mode_label": visual["mode_label"],
        "policy": policy,
        "summary": dashboard.get("summary", {}),
        "visual": visual,
        "rows": dashboard.get("rows", []),
        "defaults": dashboard.get("defaults", {}),
    }

