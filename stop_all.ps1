Write-Host "Stopping Ophanim AI Services..."

$root = $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }
$backendPidFile = Join-Path $root 'backend_pid.txt'
$frontendPidFile = Join-Path $root 'frontend_pid.txt'

if (Test-Path $backendPidFile) {
    $procId = Get-Content $backendPidFile
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Remove-Item $backendPidFile -ErrorAction SilentlyContinue
}

if (Test-Path $frontendPidFile) {
    $procId = Get-Content $frontendPidFile
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Remove-Item $frontendPidFile -ErrorAction SilentlyContinue
}

# Kill any lingering processes still bound to the specific ports
$ports = @(8001, 1420)
foreach ($port in $ports) {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($conn in $connections) {
            $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "Killing lingering process $($proc.ProcessName) (PID: $($proc.Id)) on port $port"
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
}

Write-Host "All services stopped."
