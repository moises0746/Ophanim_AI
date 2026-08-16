$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }
$coreDir = Join-Path $root 'services\ophanim-core'
$desktopDir = Join-Path $root 'apps\desktop'
$backendPidFile = Join-Path $root 'backend_pid.txt'
$frontendPidFile = Join-Path $root 'frontend_pid.txt'
$backendLog = Join-Path $coreDir 'backend.log'
$frontendLog = Join-Path $desktopDir 'frontend.log'

# Load core .env into the process environment so secret-reference adapters
# (which read process environment variables only) can resolve configured tokens.
$envFile = Join-Path $coreDir '.env'
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
}

Write-Host "Starting Ophanim AI Backend in background..."
$backend = Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList "-Command", "cd '$coreDir'; uvicorn ophanim.main:app --host 0.0.0.0 --port 8001 --reload *> '$backendLog'"
$backend.Id | Out-File -FilePath $backendPidFile

Write-Host "Starting Ophanim AI Frontend in background..."
$frontend = Start-Process powershell -WindowStyle Hidden -PassThru -ArgumentList "-Command", "cd '$desktopDir'; npm run dev *> '$frontendLog'"
$frontend.Id | Out-File -FilePath $frontendPidFile

Write-Host "All services started in the background!"
Write-Host "You can view their output in the following log files:"
Write-Host "  - $backendLog"
Write-Host "  - $frontendLog"
