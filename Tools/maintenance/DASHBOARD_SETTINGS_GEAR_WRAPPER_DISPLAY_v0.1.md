# Dashboard Settings Gear — Wrapper Display Controls v0.1

## Summary
Added a settings gear icon in the dashboard header that opens a slide-out drawer with Displayed Wrappers controls. This is a UI shell only — no persistence, no launch, no settings mutation.

## Changes

### templates/index.html (and server.py INDEX_HTML)
1. **Gear icon** — Small ⚙ button in the .meta-bar next to the Refresh button
2. **Settings drawer** — 420px slide-out panel from the right with backdrop overlay
3. **Displayed Wrappers section** — 13 wrapper rows with:
   - Checkbox toggle (UI-only for this phase)
   - Icon badge (2-letter initial, color-coded by class)
   - Name + meta description
   - Status chip (CONFIGURED / UNKNOWN / DEFERRED / NOT CONFIGURED / PLACEHOLDER)
4. **Future sections** — 6 placeholder sections (Appearance, Profiles, Wrapper Catalog, Provider Assets, Model Settings Baselines, Launch Profiles)
5. **Note** — Clear disclaimer: "Persistence and launch are future features"

### Wrapper Display Model
| Class | Wrappers | Default State |
|---|---|---|
| PREFERRED | Ollama Direct, Codex, Claude Code | Checked (enabled) |
| SUPPORTED | OpenClaw, Copilot, Gemini | OpenClaw checked, others unchecked |
| OPTIONAL | OpenCode, Aider, Continue, Cursor, Cline/Roo, Goose | Unchecked (catalog-only) |
| CUSTOM | Custom Wrapper | Unchecked (placeholder) |

### Validation
- [x] Server compiles (Python syntax check passed)
- [x] /api/models/dashboard?mode=home — OK (78009 bytes)
- [x] /api/models/dashboard?mode=business — OK (78094 bytes)
- [x] /api/models/assets — OK (7646 bytes)
- [x] /api/models/routing-eligibility — OK
- [x] No settings mutation enabled
- [x] No one-click launch implemented
- [x] No SAFEPOINT/continuity changes
- [x] Main Models board remains clean (optional wrappers not added)
