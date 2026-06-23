# Roadmap

## Phase 0 — Repo Boundary Cleanup (current)
- [x] Inventory canonical dashboard root
- [x] Inventory historical dashboard artifacts
- [x] Create product boundary documents
- [x] Create .gitignore
- [x] Establish docs/, Tools/validation/ directories

## Phase 1 — Wrapper Registry (complete)
- [x] Wrapper registry data layer (13 wrappers)
- [x] /api/models/wrappers endpoint
- [x] Wrapper chips on model cards
- [x] Wrapper Registry section in Models tab
- [x] Gear drawer catalog display

## Phase 2 — Effective Settings Intelligence (complete)
- [x] Per-model effective settings with source stack
- [x] Settings groups: core, sampling, prompt/session, server, persistence
- [x] Hazard profiles (cost-sensitive, settings-sensitive, needs profile)
- [x] Ollama parameter intelligence documentation
- [x] GET /api/models/settings-intelligence endpoint
- [x] Effective Settings section in Models tab
- [x] Home Mode simplified core values; Business Mode full provenance
- [x] No mutation endpoint added

## Phase 3 — Wrapper/Model Compatibility
- [ ] Model-wrapper compatibility matrix
- [ ] Evidence-backed compatibility assertions
- [ ] Per-model wrapper chip filtering

## Phase 3 — Launch Profiles
- [ ] One-click wrapper launch
- [ ] Workspace mapping
- [ ] Authority levels

## Phase 4 — UX/Profile Intelligence Polish (complete)
- [x] Gear drawer active/catalog section distinction with visual borders
- [x] Profile readiness labels on model cards (Ready, Guarded, Needs tuning, Advanced only, Not recommended)
- [x] Settings grouped by Core/Sampling/Prompt/Session/Server/Persistence in Effective Settings section
- [x] Hazard profile explanation text in model card details
- [x] Display fields added to hazard profiles (readiness_label, badge_class, explanation_short, explanation_long)
- [x] Home Mode simplified view; Business Mode detailed provenance
- [x] No mutation enabled

## Phase 5 — Settings Mutation
- [ ] Governed edit apply
- [ ] Settings persistence
- [ ] Rollback support

## Phase 5 — Template Unification (complete)
- [x] Resolve dual-template architecture (embedded INDEX_HTML vs templates/index.html)
- [x] Single source of truth: templates/index.html
- [x] server.py reads template at runtime via _read_template_fallback()
- [x] Minimal error page fallback if template file is missing

## Future
- [ ] Wrapper selection persistence
- [ ] Provider asset management UI
- [ ] Profile switching (Home/Business/RetroFuse/Modular)
- [ ] Light/dark scheme toggle
- [ ] Reduced motion support
- [ ] Card density controls
