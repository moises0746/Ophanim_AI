param(
    [int]$CorePort = 8080
)

$ErrorActionPreference = "Stop"
$desktopRoot = Split-Path -Parent $PSScriptRoot
$projectRoot = Split-Path -Parent (Split-Path -Parent $desktopRoot)
$coreRoot = Join-Path $projectRoot "services\ophanim-core"

if (-not $env:OPHANIM_RUNTIME_TENANT_ID) {
    $env:OPHANIM_RUNTIME_TENANT_ID = [guid]::NewGuid().ToString()
}
if (-not $env:OPHANIM_RUNTIME_WORKSPACE_ID) {
    $env:OPHANIM_RUNTIME_WORKSPACE_ID = [guid]::NewGuid().ToString()
}
if (-not $env:OPHANIM_DESKTOP_API_TOKEN) {
    $tokenBytes = New-Object byte[] 32
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $generator.GetBytes($tokenBytes)
    }
    finally {
        $generator.Dispose()
    }
    $env:OPHANIM_DESKTOP_API_TOKEN = [Convert]::ToBase64String($tokenBytes).
        TrimEnd("=").
        Replace("+", "-").
        Replace("/", "_")
}

$env:OPHANIM_CORE_BASE_URL = "http://127.0.0.1:$CorePort"
$coreProcess = $null

try {
    $coreArgs = @(
        "-m", "uvicorn", "ophanim.main:app",
        "--host", "127.0.0.1",
        "--port", $CorePort.ToString()
    )
    $coreProcess = Start-Process -FilePath "python.exe" -ArgumentList $coreArgs -WorkingDirectory $coreRoot -WindowStyle Hidden -PassThru

    $healthy = $false
    for ($attempt = 0; $attempt -lt 40; $attempt++) {
        if ($coreProcess.HasExited) {
            throw "Ophanim Core exited before becoming healthy."
        }
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri "$env:OPHANIM_CORE_BASE_URL/health" -TimeoutSec 1
            if ($response.StatusCode -eq 200) {
                $healthy = $true
                break
            }
        }
        catch {
            Start-Sleep -Milliseconds 250
        }
    }
    if (-not $healthy) {
        throw "Ophanim Core did not become healthy within 10 seconds."
    }

    Push-Location $desktopRoot
    try {
        & npm.cmd run tauri dev
        if ($LASTEXITCODE -ne 0) {
            throw "Tauri development runtime exited with code $LASTEXITCODE."
        }
    }
    finally {
        Pop-Location
    }
}
finally {
    if ($coreProcess -and -not $coreProcess.HasExited) {
        Stop-Process -Id $coreProcess.Id
        $coreProcess.WaitForExit()
    }
}
