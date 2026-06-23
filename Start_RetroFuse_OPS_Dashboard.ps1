param(
    [string]$OpsRoot = "D:\RETROFUSE_OPS",
    [int]$Port = 8101
)

Write-Host "=== Start RetroFuse OPS Dashboard v1.0 ==="
$dashboardRoot = Join-Path $OpsRoot "Dashboard"
$reqFile = Join-Path $dashboardRoot "requirements.txt"
$venvPython = Join-Path $dashboardRoot ".venv\Scripts\python.exe"
$pythonExe = if (Test-Path -LiteralPath $venvPython -PathType Leaf) { $venvPython } else { "python" }

if (-not (Test-Path -Path $dashboardRoot -PathType Container)) {
    Write-Error "Dashboard root not found at $dashboardRoot"
    exit 1
}

if (-not (Test-Path -Path (Join-Path $dashboardRoot "server.py") -PathType Leaf)) {
    Write-Error "Dashboard server.py not found at $dashboardRoot"
    exit 1
}

if (-not (Test-Path -Path $reqFile -PathType Leaf)) {
    Write-Warning "requirements.txt not found at $reqFile"
} else {
    Write-Host "Ensuring Python deps from requirements.txt (first run may take a bit)..."
    & $pythonExe -m pip install -r $reqFile
}

Write-Host "Starting FastAPI dashboard on port $Port..."
Write-Host "URL: http://localhost:$Port/"
Write-Host ""
    # SMC_GOVERNED_START_BLOCK_BEGIN
    $smcPort = 8001
    $smcListener = Get-NetTCPConnection -LocalPort $smcPort -State Listen -ErrorAction SilentlyContinue
    if (-not $smcListener) {
        $smcLauncher = 'D:\PORTTORETRO_ARCHIVE\PROJECTS\Symphony\Tools\Start-SMC-Governed.ps1'
        if (Test-Path -LiteralPath $smcLauncher -PathType Leaf) {
            Write-Host "Starting governed SMC resolver on port $smcPort..."
            & $smcLauncher
        } else {
            Write-Warning "Governed SMC launcher not found at $smcLauncher"
        }
    }
    # SMC_GOVERNED_START_BLOCK_END
Set-Location $dashboardRoot
& $pythonExe -m uvicorn server:app --host 127.0.0.1 --port $Port
