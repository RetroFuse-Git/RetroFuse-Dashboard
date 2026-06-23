param(
  [string]$DashRoot = 'D:\RETROFUSE_OPS\Dashboard',
  [int]$Port = 8101,
  [string]$TargetHost = '127.0.0.1',
  [int]$LoopIntervalSeconds = 15,
  [switch]$OneShot
)
$ErrorActionPreference = 'Stop'

$workDir = Join-Path $DashRoot '_Work'
$logPath = Join-Path $workDir 'OpsDashboard_Watchdog.log'
$supervisor = Join-Path $DashRoot 'Watch_RetroFuse_OpsDashboard.ps1'
$mutexName = 'Global\RetroFuse_OPS_Dashboard_Watchdog_Loop'
if (-not (Test-Path $workDir)) { New-Item -ItemType Directory -Path $workDir -Force | Out-Null }

function Write-Log {
  param([string]$Message, [string]$Level='INFO')
  $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
  Add-Content -Path $logPath -Value ('[' + $ts + '] [' + $Level + '] ' + $Message)
}

Write-Log ('Watchdog tick. DashRoot=' + $DashRoot + ' Port=' + $Port + ' TargetHost=' + $TargetHost)

if (-not (Test-Path -LiteralPath $supervisor)) {
  Write-Log ('Supervisor script missing: ' + $supervisor) 'ERROR'
  exit 1
}

function Invoke-SupervisorCycle {
  try {
    & $supervisor -DashRoot $DashRoot -Port $Port -TargetHost $TargetHost
    $code = if ($LASTEXITCODE -is [int]) { $LASTEXITCODE } else { 0 }
    if ($code -eq 0) {
      Write-Log 'Supervisor cycle completed successfully.'
    } else {
      Write-Log ('Supervisor returned non-zero exit code: ' + $code) 'WARN'
    }
    return $code
  } catch {
    Write-Log ('Watchdog tick failed: ' + $_.Exception.Message) 'ERROR'
    return 1
  }
}

if ($OneShot) {
  exit (Invoke-SupervisorCycle)
}

$mutex = New-Object System.Threading.Mutex($false, $mutexName)
$hasLock = $false
try {
  $hasLock = $mutex.WaitOne(0)
  if (-not $hasLock) {
    Write-Log 'Loop watchdog already running; exiting duplicate launcher.'
    exit 0
  }

  Write-Log ('Persistent watchdog loop started. Interval=' + $LoopIntervalSeconds + 's')
  while ($true) {
    [void](Invoke-SupervisorCycle)
    Start-Sleep -Seconds $LoopIntervalSeconds
  }
} finally {
  if ($hasLock) {
    try { $mutex.ReleaseMutex() | Out-Null } catch {}
  }
  $mutex.Dispose()
}

