<#
.SYNOPSIS
  Dashboard Phase 4 validation — UX/profile intelligence polish checks.
.DESCRIPTION
  Extends Phase 3 validation with Phase 4 UI anchor checks.
#>

$ErrorActionPreference = "Stop"
$root = "D:\RETROFUSE_OPS\Dashboard"
$passed = 0
$failed = 0

function Check($name, $condition) {
    if ($condition) {
        Write-Host "  PASS: $name" -ForegroundColor Green
        $script:passed++
    } else {
        Write-Host "  FAIL: $name" -ForegroundColor Red
        $script:failed++
    }
}

Write-Host "=== Dashboard Phase 4 Validation ===" -ForegroundColor Cyan
Write-Host ""

# 1. Python compile
Write-Host "[Python Compile]" -ForegroundColor Yellow
try { python -m py_compile "$root\server.py" 2>&1 | Out-Null; Check "server.py compiles" $true }
catch { Check "server.py compiles" $false }
try { python -m py_compile "$root\app\model_dashboard.py" 2>&1 | Out-Null; Check "model_dashboard.py compiles" $true }
catch { Check "model_dashboard.py compiles" $false }

# 2. Git hygiene
Write-Host "[Git Hygiene]" -ForegroundColor Yellow
$tracked = git -C $root ls-files
Check "No _Work files tracked" ($tracked -notmatch '_Work')
Check "No Watchdog logs tracked" ($tracked -notmatch 'Watchdog.log')
Check "No __pycache__ tracked" ($tracked -notmatch '__pycache__')
Check "No .pyc tracked" ($tracked -notmatch '\.pyc$')

# 3. Template UI anchors
Write-Host "[Template UI Anchors]" -ForegroundColor Yellow
$template = Get-Content "$root\templates\index.html" -Raw
$anchors = @(
    'models-wrappers-card', 'models-settings-intelligence-card', 'settings-drawer',
    'models-lanes-card', 'fleet-health-bar', 'mode-switch',
    'profile-badge', 'settings-group-label', 'drawer-section-active',
    'drawer-section-catalog', 'explanation-text',
    'renderSettingsIntelligence', 'renderWrapperRegistry', 'renderWrappers',
    'onWrapperToggle', 'toggleSettings'
)
foreach ($a in $anchors) {
    Check "templates/index.html contains $a" ($template -match [regex]::Escape($a))
}

# 4. server.py template reader
Write-Host "[server.py Template Reader]" -ForegroundColor Yellow
$serverPy = Get-Content "$root\server.py" -Raw
Check "server.py contains _read_template_fallback" ($serverPy -match '_read_template_fallback')
Check "server.py index() uses _read_template_fallback" ($serverPy -match 'return HTMLResponse\(_read_template_fallback')
Check "No stale embedded INDEX_HTML" ($serverPy -notmatch 'INDEX_HTML = r"""<!DOCTYPE html>')

# 5. API routes
Write-Host "[API Routes]" -ForegroundColor Yellow
$routes = @(
    '/api/models/dashboard', '/api/models/edit-receipts', '/api/models/assets',
    '/api/models/routing-eligibility', '/api/models/wrappers', '/api/models/settings-intelligence',
    '/api/latest', '/api/orchestrator', '/api/bolt', '/api/apps/dailybundle', '/api/smc/wrc-live-status'
)
foreach ($route in $routes) {
    Check "server.py contains route $route" ($serverPy -match [regex]::Escape($route))
}

# 6. No forbidden endpoints
Write-Host "[Forbidden Endpoints]" -ForegroundColor Yellow
Check "No launch endpoint" ($serverPy -notmatch 'api/models/launch')
Check "No settings mutation endpoint" ($serverPy -notmatch 'api/models/settings-mutate')

# 7. Hazard profile display fields
Write-Host "[Data Model]" -ForegroundColor Yellow
$modelPy = Get-Content "$root\app\model_dashboard.py" -Raw
Check "Hazard profiles have readiness_label" ($modelPy -match 'readiness_label')
Check "Hazard profiles have badge_class" ($modelPy -match 'badge_class')
Check "Hazard profiles have explanation_short" ($modelPy -match 'explanation_short')
Check "Hazard profiles have explanation_long" ($modelPy -match 'explanation_long')

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
if ($failed -eq 0) { Write-Host "ALL CHECKS PASSED" -ForegroundColor Green }
else { Write-Host "SOME CHECKS FAILED" -ForegroundColor Red }
