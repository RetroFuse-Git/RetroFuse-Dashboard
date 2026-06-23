# Unity Model Dashboard — P1 Visual Refinement v0.1

**Date:** 2026-06-23  
**Authority:** DASHBOARD_UI_REFINEMENT  
**Status:** REFINEMENT_COMPLETE  
**Success State:** UNITY_MODEL_DASHBOARD_P1_VISUAL_REFINEMENT_COMPLETE

---

## Changes Applied

### 1. Layout — Fleet Health Bar + Mode Strip
- Added **Fleet Health Bar** at the top of the Models tab — a horizontal segmented bar showing READY / DEFAULT_RISK / STALE / BLOCKED / UNKNOWN proportions
- Added **Mode Strip** below the bar showing: mode icon, mode name, eligible count, sensitive data status, max cost, allowed tiers
- Replaced two separate buttons with a **segmented control** for Home/Business mode switch
- Model cards grouped by **Local** and **Cloud** route tiers with group headers

### 2. Home Mode — Simplified Labels
- READY → **Available** (green pill)
- DEFAULT_RISK → **Needs tuning** (amber pill)
- STALE → **Needs attention** (amber pill)
- BLOCKED → **Not available** (red pill)
- UNKNOWN → **Unchecked** (gray pill)
- Settings provenance section **hidden** in Home Mode (shown only in Business Mode)
- Deep governance detail behind **expandable "Settings & evidence"** disclosure per card

### 3. Business Mode — Governance Details
- Settings Provenance section **visible** with explicit/config/default breakdown
- Lane state shown as raw taxonomy (READY, DEFAULT_RISK, etc.)
- Route reason requirements visible per card
- POLICY_CONTROLLED sensitive-data wording displayed

### 4. Risk Heat — Visual Grid
- Replaced text-only risk summary with a **7-column visual heat grid**: TOTAL / CTX / TEMP / OUTPUT / TIMEOUT / PROFILE / ROUTE
- Color intensity: **severe** (red) > **high** (orange) > **medium** (yellow) > **low** (blue) > **none** (green)
- Thresholds: severe >15, high >8, medium >0

### 5. Route Flow — Horizontal Pipeline
- Replaced vertical list with a **horizontal pipeline**: VERIFIED → RECOMMENDED → REASON → BLOCKED → IDLE
- Each stage shows count, percentage, and color-coded background
- Hover expands the stage proportionally
- Disclaimer: "Visual recommendation only. Does not imply live route execution."

### 6. Assets — Visual Badge Grid
- Replaced text list with a **responsive grid** of provider asset badges
- Each badge shows: provider name, confidence dot (animated), confidence level, surface, cost class, access level
- CONFIGURED confidence shown with green dot, OPERATOR_REPORTED with amber dot
- Disclaimer: "Pricing/quota are operator-reported, not product promises."

### 7. Motion — Subtle Animations
- **Health dots**: READY models pulse (2s), DEFAULT_RISK models blink (3s), BLOCKED models static
- **Card fade-in**: Staggered fade-in on load (30ms delay per card, up to 10 cards)
- **Hover effects**: Cards get border glow, fleet bar segments expand, route stages expand
- **Reduced motion**: prefers-reduced-motion media query disables animations

### 8. CSS Architecture
- All P1 styles added before </style> in the embedded INDEX_HTML
- Responsive breakpoints at 900px and 600px
- No external CSS dependencies

## Files Modified

| File | Action |
|------|--------|
| D:\RETROFUSE_OPS\Dashboard\server.py | Updated INDEX_HTML (CSS + HTML + JS) |
| D:\RETROFUSE_OPS\Dashboard\templates\index.html | Synced with updated INDEX_HTML |

## Verification

| Check | Status |
|-------|--------|
| Server compiles and starts | PASS |
| Root page returns HTML (not raw code) | PASS |
| Models tab button present | PASS |
| Fleet health bar present | PASS |
| Mode strip present | PASS |
| Segmented mode switch present | PASS |
| Model card grid present | PASS |
| Risk heat grid present | PASS |
| Route pipeline present | PASS |
| Asset badge grid present | PASS |
| Health dot animations (CSS) present | PASS |
| Card fade-in animations (CSS) present | PASS |
| Home Mode simplified labels (CSS) present | PASS |
| Home Mode hides settings section | PASS (JS logic) |
| Business Mode shows settings section | PASS (JS logic) |
| API: /api/models/dashboard?mode=home | PASS (28 cards, 12 eligible) |
| API: /api/models/dashboard?mode=business | PASS (28 cards, 23 eligible) |
| API: /api/models/routing-eligibility | PASS (28 models) |
| API: /api/models/assets | PASS (16 assets) |
| API: /api/models/edit-receipts | PASS (empty) |
| Settings mutation not activated | PASS (read-only) |
| SAFEPOINT/continuity not touched | PASS |

## Constraints Preserved
- All existing API behavior unchanged
- Home=12 and Business=23 eligibility consistency
- Home sensitive data = BLOCKED
- Business sensitive data = POLICY_CONTROLLED
- Settings provenance table visible (Business Mode)
- Edit receipts panel visible
- Route flow card visible
- Risk heat card visible
- Read-only/stubbed edit apply behavior
- No settings mutation enabled
- No SAFEPOINT/continuity components changed
- No provider pricing/quota hardcoded
