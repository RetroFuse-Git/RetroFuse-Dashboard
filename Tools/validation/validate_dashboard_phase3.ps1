<#
.SYNOPSIS
  Dashboard Phase 3 validation — frontend template hardening checks.
.DESCRIPTION
  Validates that:
  - Python backend compiles
  - No tracked runtime junk in git
  - templates/index.html exists and contains required UI anchors
  - server.py does not contain stale duplicate full-page INDEX_HTML
  - All required API route strings are present in server.py
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

Write-Host "=== Dashboard Phase 3 Validation ===" -ForegroundColor Cyan
Write-Host ""

# 1. Python compile checks
Write-Host "[Python Compile]" -ForegroundColor Yellow
try {
    python -m py_compile "$root\server.py" 2>&1 | Out-Null
    Check "server.py compiles" $true
} catch { Check "server.py compiles" $false }

try {
    python -m py_compile "$root\app\model_dashboard.py" 2>&1 | Out-Null
    Check "model_dashboard.py compiles" $true
} catch { Check "model_dashboard.py compiles" $false }

# 2. Git tracked file hygiene
Write-Host "[Git Hygiene]" -ForegroundColor Yellow
$tracked = git -C $root ls-files
Check "No _Work files tracked" ($tracked -notmatch '_Work')
Check "No Watchdog logs tracked" ($tracked -notmatch 'Watchdog.log')
Check "No __pycache__ tracked" ($tracked -notmatch '__pycache__')
Check "No .pyc tracked" ($tracked -notmatch '\.pyc$')

# 3. Template file exists
Write-Host "[Template Source of Truth]" -ForegroundColor Yellow
$templatePath = "$root\templates\index.html"
Check "templates/index.html exists" (Test-Path $templatePath)

if (Test-Path $templatePath) {
    $template = Get-Content $templatePath -Raw
    Check "templates/index.html contains wrapper registry UI anchor" ($template -match 'models-wrappers-card')
    Check "templates/index.html contains effective settings UI anchor" ($template -match 'models-settings-intelligence-card')
    Check "templates/index.html contains gear drawer UI anchor" ($template -match 'settings-drawer')
    Check "templates/index.html contains model lanes UI anchor" ($template -match 'models-lanes-card')
    Check "templates/index.html contains fleet health UI anchor" ($template -match 'fleet-health-bar')
    Check "templates/index.html contains mode switch" ($template -match 'mode-switch')
    Check "templates/index.html contains wrapper chips JS" ($template -match 'wrapper-chips' -or $template -match 'row.wrappers')
    Check "templates/index.html contains settings intelligence JS" ($template -match 'renderSettingsIntelligence')
    Check "templates/index.html contains wrapper registry JS" ($template -match 'renderWrapperRegistry')
}

# 4. server.py does not contain stale duplicate full-page INDEX_HTML
Write-Host "[server.py Template Debt]" -ForegroundColor Yellow
$serverPy = Get-Content "$root\server.py" -Raw
# Check that the old INDEX_HTML constant is gone (the massive embedded one)
$hasOldIndexHtml = $serverPy -match 'INDEX_HTML = r"""<!DOCTYPE html>'
Check "server.py does not contain stale embedded full-page INDEX_HTML" (-not $hasOldIndexHtml)
# Check that the new template reader function exists
Check "server.py contains _read_template_fallback()" ($serverPy -match '_read_template_fallback')
# Check that index() uses the template reader
Check "server.py index() uses _read_template_fallback" ($serverPy -match 'return HTMLResponse\(_read_template_fallback')

# 5. Required API route strings
Write-Host "[API Routes]" -ForegroundColor Yellow
$routes = @(
    '/api/models/dashboard',
    '/api/models/edit-receipts',
    '/api/models/assets',
    '/api/models/routing-eligibility',
    '/api/models/wrappers',
    '/api/models/settings-intelligence',
    '/api/latest',
    '/api/orchestrator',
    '/api/bolt',
    '/api/apps/dailybundle',
    '/api/smc/wrc-live-status'
)
foreach ($route in $routes) {
    Check "server.py contains route $route" ($serverPy -match [regex]::Escape($route))
}

# 6. No forbidden endpoints
Write-Host "[Forbidden Endpoints]" -ForegroundColor Yellow
Check "No launch endpoint" ($serverPy -notmatch 'api/models/launch')
Check "No settings mutation endpoint" ($serverPy -notmatch 'api/models/settings-mutate')

Write-Host ""
Write-Host "=== Results ===" -ForegroundColor Cyan
Write-Host "Passed: $passed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
if ($failed -eq 0) { Write-Host "ALL CHECKS PASSED" -ForegroundColor Green }
else { Write-Host "SOME CHECKS FAILED" -ForegroundColor Red }
