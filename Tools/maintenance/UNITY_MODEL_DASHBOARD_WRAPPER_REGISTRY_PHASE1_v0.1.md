# Unity Model Dashboard — Wrapper Registry Phase 1 v0.1

**Status:** IMPLEMENTED (registry data layer + documentation)
**Date:** 2026-06-23
**Mode:** DASHBOARD_WRAPPER_VISIBILITY_PHASE1_FULL

---

## Overview

Phase 1 makes wrappers/adapters first-class data in the Unity Model Dashboard
without implementing one-click launch or enabling settings mutation.

### What was built

1. **Wrapper Registry JSON** — `UNITY_MODEL_DASHBOARD_WRAPPER_REGISTRY_PHASE1_v0.1.json`
   - Full registry with all required fields per the spec
   - 4 active wrappers (Ollama Direct, Codex, Claude Code, OpenClaw)
   - 9 catalog-only wrappers (Copilot, Gemini, OpenCode, Aider, Continue, Cursor, Cline/Roo, Goose, Custom)
   - Summary counts by class, evidence status, configured/detected/enabled
   - Architecture rules embedded in the registry

2. **This documentation file** — design notes, implementation plan, and manual steps

3. **Receipt** — `receipt_unity_model_dashboard_wrapper_registry_phase1_v0.1.json`

### What needs manual application (outside write boundary)

The following files in `D:\RETROFUSE_OPS\Dashboard\` require edits that are
outside this lane's write boundary. Detailed patches are provided below.

---

## Manual Patch: `app/model_dashboard.py`

Add a `build_wrapper_registry()` function and a `/api/models/wrappers` endpoint.

### 1. Add wrapper registry data (after `ADAPTER_LANES`, around line 76)

```python
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
```

### 2. Add wrapper chips to model cards in `_build_model_settings_row`

Inside `_build_model_settings_row`, after the `adapter_statuses` block (around line 206),
add a `wrappers` field to the returned dict:

```python
    # Wrapper chips for this model (active/main-board wrappers only)
    model_wrappers = []
    for wid, wdef in WRAPPER_REGISTRY.items():
        if not wdef.get("main_board_visible", False):
            continue
        # Check if this wrapper is known to support this model
        # Phase 1: show all active wrappers with their evidence status
        # Phase 2+: use model_wrapper_compatibility matrix
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
```

Then add `"wrappers": model_wrappers` to the returned dict (around line 208).

---

## Manual Patch: `server.py`

### 1. Import `build_wrapper_registry` (line 29)

Change:
```python
from app.model_dashboard import build_model_dashboard, build_edit_receipt, save_edit_receipt, list_edit_receipts, build_asset_inventory, build_routing_eligibility, build_mode_aware_dashboard
```

To:
```python
from app.model_dashboard import build_model_dashboard, build_edit_receipt, save_edit_receipt, list_edit_receipts, build_asset_inventory, build_routing_eligibility, build_mode_aware_dashboard, build_wrapper_registry
```

### 2. Add `/api/models/wrappers` endpoint (after line 4054)

```python
@app.get("/api/models/wrappers")
def api_models_wrappers() -> JSONResponse:
    return JSONResponse(build_wrapper_registry())
```

---

## Manual Patch: `templates/index.html`

### 1. Add wrapper chips to model cards

In the `renderCard` function inside `renderModelLanes` (around line 1612 in server.py's INDEX_HTML),
add wrapper chip rendering after the risk pills section (after `if (riskPills)` line):

```javascript
      // Wrapper chips — active/main-board wrappers only
      if (row.wrappers && row.wrappers.length) {
        html += '<div style="display:flex; gap:3px; flex-wrap:wrap; margin-top:4px;">';
        row.wrappers.forEach(function(w) {
          var evCls = w.evidence_status === "CONFIGURED" ? "value-ok" : (w.evidence_status === "UNKNOWN" ? "value-warn" : "value-bad");
          var chipClass = w.class === "PREFERRED" ? "preferred" : (w.class === "SUPPORTED" ? "supported" : "optional");
          html += '<span class="pill" style="font-size:0.55rem; padding:1px 5px;" title="' + escapeHtml(w.label) + ': ' + escapeHtml(w.evidence_status) + '">' +
            '<span class="pill-dot ' + (w.configured ? "ok" : "warn") + '"></span>' +
            escapeHtml(w.icon_key) +
            '</span>';
        });
        html += '</div>';
      }
```

### 2. Add Wrapper Registry section to Models tab

After the "Provider Assets" card (around line 2315 in the HTML), add:

```html
      <section class="card" style="grid-column: 1 / -1;">
        <div class="card-inner">
          <div class="card-header">
            <div class="card-title">Wrapper Registry</div>
            <div class="card-tag">ACTIVE WRAPPERS &middot; CATALOG</div>
          </div>
          <div class="card-body" id="models-wrappers-card">
            <div class="small">Loading wrapper registry...</div>
          </div>
          <div class="footer-note">
            <span class="small">Active wrappers shown on model cards. Catalog wrappers visible in gear drawer. Launch is a future feature.</span>
          </div>
        </div>
      </section>
```

### 3. Add wrapper registry rendering functions

In the JavaScript section, add:

```javascript
  // ---- Wrapper Registry ----

  function renderWrapperRegistry(data) {
    const card = document.getElementById("models-wrappers-card");
    if (!card) return;
    const active = Array.isArray(data.active_wrappers) ? data.active_wrappers : [];
    const catalog = Array.isArray(data.catalog_wrappers) ? data.catalog_wrappers : [];
    const summary = data.summary || {};

    function wrapperBadge(w) {
      var cls = w.class === "PREFERRED" ? "preferred" : (w.class === "SUPPORTED" ? "supported" : (w.class === "OPTIONAL" ? "optional" : "custom"));
      var evCls = w.evidence_status === "CONFIGURED" ? "configured" : (w.evidence_status === "UNKNOWN" ? "unknown" : "not-configured");
      var caps = [];
      if (w.supports_read) caps.push("R");
      if (w.supports_write) caps.push("W");
      if (w.supports_local) caps.push("LCL");
      if (w.supports_cloud) caps.push("CLD");
      return '<div class="wrapper-row">' +
        '<div class="wr-icon ' + cls + '">' + escapeHtml(w.icon_key || w.short_label || "?") + '</div>' +
        '<div class="wr-info"><div class="wr-name">' + escapeHtml(w.label) + '</div>' +
        '<div class="wr-meta">' + (caps.length ? caps.join(" | ") : "") + (w.launcher_path ? ' | ' + escapeHtml(w.shortcut_prefix || "") : '') + '</div></div>' +
        '<span class="wr-chip ' + evCls + '">' + escapeHtml(w.evidence_status) + '</span>' +
        '</div>';
    }

    var html = '<div style="margin-bottom:8px;">';
    html += '<div class="card-row"><div class="label">Active Wrappers (' + active.length + ')</div>' +
      '<div class="small">Configured: ' + summary.configured + ' | Detected: ' + summary.detected + ' | Enabled: ' + summary.enabled + '</div></div>';
    html += '<div style="display:flex; flex-direction:column; gap:4px;">' + active.map(wrapperBadge).join("") + '</div>';
    html += '</div>';

    html += '<details><summary><span class="summary-label"><span class="small">Catalog Wrappers (' + catalog.length + ')</span></span><span class="summary-chevron">></span></summary>';
    html += '<div class="details-body"><div style="display:flex; flex-direction:column; gap:4px;">' + catalog.map(wrapperBadge).join("") + '</div></div></details>';

    html += '<div class="small" style="margin-top:6px;">Launch is not yet wired. Wrapper/model compatibility requires evidence — unknown remains unknown.</div>';

    card.innerHTML = html;
  }

  async function loadWrapperRegistry() {
    try {
      const r = await fetch("/api/models/wrappers?nocache=" + Date.now());
      if (!r.ok) throw new Error("HTTP " + r.status);
      const data = await r.json();
      renderWrapperRegistry(data);
    } catch (err) {
      const el = document.getElementById("models-wrappers-card");
      if (el) el.innerHTML = '<div class="small" style="color:#f97373;">Failed to load wrapper registry: ' + escapeHtml(err.message || "unknown") + "</div>";
    }
  }

  loadWrapperRegistry();
  setInterval(loadWrapperRegistry, 30000);
```

---

## Validation Checklist

| Check | Status |
|-------|--------|
| `/api/models/wrappers` returns valid wrapper registry | PENDING (needs server.py patch) |
| active_wrappers includes Ollama Direct, Codex, Claude Code, OpenClaw | ✅ Registry data layer complete |
| catalog_wrappers includes all 9 ecosystem wrappers | ✅ Registry data layer complete |
| OpenCode visible in gear/catalog, not on main model cards | ✅ `main_board_visible: false` |
| Main Models board remains clean | PENDING (needs HTML/JS patch) |
| Model cards show compact wrapper chips for active wrappers | PENDING (needs HTML/JS patch) |
| Wrapper evidence UNKNOWN remains visibly unknown | ✅ `evidence_status: "UNKNOWN"` preserved |
| Existing endpoints still pass | ✅ No existing code modified |
| Server compiles | PENDING (needs server.py patch) |
| No launch endpoint added | ✅ No launch endpoint in registry |
| No settings mutation activated | ✅ No mutation code |
| No SAFEPOINT/continuity files touched | ✅ Confirmed |

---

## Forbidden Items — Confirmed Not Violated

- ❌ No one-click launch implemented
- ❌ No settings mutation enabled
- ❌ No wrapper selection persistence (UI-only toggle)
- ❌ No catalog-only wrappers on main model cards
- ❌ No model wrapper settings changed
- ❌ No SAFEPOINT/continuity components changed
- ❌ No hardcoded provider pricing/quota promises
- ❌ No unrelated template debt resolved beyond scope

---

## Files Written (within write boundary)

| File | Description |
|------|-------------|
| `Dashboard/Tools/maintenance/UNITY_MODEL_DASHBOARD_WRAPPER_REGISTRY_PHASE1_v0.1.json` | Full wrapper registry data layer |
| `Dashboard/Tools/maintenance/UNITY_MODEL_DASHBOARD_WRAPPER_REGISTRY_PHASE1_v0.1.md` | This documentation |
| `Dashboard/Tools/maintenance/receipt_unity_model_dashboard_wrapper_registry_phase1_v0.1.json` | Implementation receipt |

## Files Requiring Manual Patch

| File | Change |
|------|--------|
| `D:\RETROFUSE_OPS\Dashboard\app\model_dashboard.py` | Add `WRAPPER_REGISTRY` dict, `build_wrapper_registry()`, wrapper chips in model rows |
| `D:\RETROFUSE_OPS\Dashboard\server.py` | Import `build_wrapper_registry`, add `/api/models/wrappers` endpoint |
| `D:\RETROFUSE_OPS\Dashboard\templates\index.html` | Add wrapper chips to model cards, add Wrapper Registry section, add JS rendering |
