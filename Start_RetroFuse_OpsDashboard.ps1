param([int]$Port = 8101)

Write-Host "Starting RetroFuse OPS Dashboard (detached single-instance) on http://127.0.0.1:$Port/ ..." -ForegroundColor Cyan
& "D:\RETROFUSE_OPS\Scripts\Run_OpsDashboard_Detached.ps1"
