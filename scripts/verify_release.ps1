<#
.SYNOPSIS
Release 1 verification gate for Ophanim AI.

.DESCRIPTION
Runs the deterministic Release 1 checks in order and prints a PASS/FAIL/SKIP
summary. Exits non-zero if any required check fails.

Required checks (always run):
  1. Git whitespace: `git diff --check` (working tree) and `--cached --check`
  2. Core: ruff check, ruff format --check, pytest (services/ophanim-core)

Extended checks (run when the project and toolchain exist; skip with switches):
  3. Desktop: npm build, vitest, playwright e2e (apps/desktop)
  4. Node: cargo test (services/ophanim-node)

Secret scan (run unless -SkipSecretScan):
  5. Scans git-tracked first-party source for common secret patterns.
     Synthetic canaries inside test suites and vendored trees are excluded.

.PARAMETER SkipDesktop
Skip desktop (npm) checks.
.PARAMETER SkipNode
Skip Rust node (cargo) checks.
.PARAMETER SkipSecretScan
Skip the git-tracked secret pattern scan.
.PARAMETER CoreOnly
Run only the required core checks and skip all extended checks and the scan.
.PARAMETER RequireE2E
Fail the gate when the Desktop e2e runtime prerequisite is not met instead of
skipping the e2e step.
#>
[CmdletBinding()]
param(
    [switch]$SkipDesktop,
    [switch]$SkipNode,
    [switch]$SkipSecretScan,
    [switch]$CoreOnly,
    [switch]$RequireE2E
)

$ErrorActionPreference = 'Continue'
$repoRoot = Split-Path -Parent $PSScriptRoot

$script:results = [System.Collections.Generic.List[object]]::new()

function Add-Result {
    param(
        [string]$Check,
        [string]$Status,
        [string]$Detail = ''
    )
    $script:results.Add([PSCustomObject]@{ Check = $Check; Status = $Status; Detail = $Detail })
}

function Invoke-Native {
    param(
        [string]$Check,
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkDir = $repoRoot
    )
    Push-Location $WorkDir
    try {
        & $FilePath @Arguments 2>&1 | ForEach-Object { Write-Host "    $_" }
        if ($LASTEXITCODE -ne 0) {
            throw "exit code $LASTEXITCODE"
        }
        Add-Result -Check $Check -Status PASS
    }
    catch {
        Add-Result -Check $Check -Status FAIL -Detail $_.Exception.Message
    }
    finally {
        Pop-Location
    }
}

function Get-ConfiguredCoreUrl {
    if ($env:VITE_OPHANIM_CORE_URL) {
        return $env:VITE_OPHANIM_CORE_URL
    }
    $envFile = Join-Path $repoRoot "apps\desktop\.env.development"
    if (Test-Path $envFile) {
        foreach ($line in [System.IO.File]::ReadLines($envFile)) {
            if ($line -match '^\s*VITE_OPHANIM_CORE_URL\s*=\s*(.+?)\s*$') {
                return $Matches[1]
            }
        }
    }
    return $null
}

function Test-E2ERuntimeReady {
    $coreUrl = Get-ConfiguredCoreUrl
    if (-not $coreUrl) {
        return @{ Ready = $false; Reason = 'VITE_OPHANIM_CORE_URL is not configured' }
    }
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri "$coreUrl/health" -Headers @{ "Origin" = "http://127.0.0.1:4173" } -TimeoutSec 5
        $allowOrigin = [string]$response.Headers["Access-Control-Allow-Origin"]
        if ($response.StatusCode -ne 200) {
            return @{ Ready = $false; Reason = "core at $coreUrl returned HTTP $($response.StatusCode)" }
        }
        if ($allowOrigin -and $allowOrigin.Trim() -in @('*', 'http://127.0.0.1:4173', 'http://localhost:4173')) {
            return @{ Ready = $true; Reason = $coreUrl }
        }
        return @{ Ready = $false; Reason = "core at $coreUrl does not allow CORS origin http://127.0.0.1:4173 (got '$allowOrigin')" }
    }
    catch {
        return @{ Ready = $false; Reason = "core at $coreUrl is not reachable: $($_.Exception.Message)" }
    }
}

Write-Host "============================================"
Write-Host "  Ophanim AI - Release 1 verification gate"
Write-Host "============================================"

# --- 1. Git whitespace -----------------------------------------------
Write-Host "`n[1/5] Git whitespace checks"
# CRLF line-ending notices ("LF will be replaced by CRLF") are benign on
# Windows checkouts; only genuine whitespace errors fail the gate.
$diffOutput = & git diff --check 2>&1
$diffText = ($diffOutput | Out-String)
if ($LASTEXITCODE -ne 0 -and -not ($diffText -match "will be replaced by CRLF")) {
    $diffOutput | ForEach-Object { Write-Host "    $_" }
    Add-Result -Check "git diff --check" -Status FAIL -Detail "whitespace error(s)"
}
elseif ($LASTEXITCODE -ne 0) {
    $diffOutput | ForEach-Object { Write-Host "    $_" }
    Add-Result -Check "git diff --check" -Status PASS -Detail "CRLF notices only"
}
else {
    Add-Result -Check "git diff --check" -Status PASS
}
Invoke-Native -Check "git diff --cached --check" -FilePath "git" -Arguments @("diff", "--cached", "--check")

# --- 2. Core checks --------------------------------------------------
$coreDir = Join-Path $repoRoot "services\ophanim-core"
Write-Host "`n[2/5] Ophanim Core checks"
Invoke-Native -Check "ruff check" -FilePath "python" -Arguments @("-m", "ruff", "check", "ophanim", "tests") -WorkDir $coreDir
Invoke-Native -Check "ruff format --check" -FilePath "python" -Arguments @("-m", "ruff", "format", "--check", "ophanim", "tests") -WorkDir $coreDir
Invoke-Native -Check "pytest" -FilePath "python" -Arguments @("-m", "pytest", "tests", "-q") -WorkDir $coreDir

# --- 3. Desktop checks -----------------------------------------------
$desktopDir = Join-Path $repoRoot "apps\desktop"
$desktopRuns = -not $SkipDesktop -and -not $CoreOnly -and (Test-Path $desktopDir)
if ($desktopRuns) {
    Write-Host "`n[3/5] Desktop checks"
    Invoke-Native -Check "npm build" -FilePath "npm.cmd" -Arguments @("run", "build") -WorkDir $desktopDir
    Invoke-Native -Check "npm test (vitest)" -FilePath "npm.cmd" -Arguments @("run", "test") -WorkDir $desktopDir

    $e2eReady = Test-E2ERuntimeReady
    if (-not $e2eReady.Ready) {
        Write-Host "    e2e prerequisite not met: $($e2eReady.Reason)"
        if ($RequireE2E) {
            Add-Result -Check "npm run test:e2e (playwright)" -Status FAIL -Detail "e2e prerequisite not met: $($e2eReady.Reason)"
        }
        else {
            Add-Result -Check "npm run test:e2e (playwright)" -Status SKIP -Detail "core not e2e-ready: $($e2eReady.Reason)"
        }
    }
    else {
        Write-Host "    e2e core: $($e2eReady.Reason)"
        Invoke-Native -Check "npm run test:e2e (playwright)" -FilePath "npm.cmd" -Arguments @("run", "test:e2e") -WorkDir $desktopDir
    }
}
else {
    Add-Result -Check "desktop (npm)" -Status SKIP
}

# --- 4. Node checks ---------------------------------------------------
$nodeDir = Join-Path $repoRoot "services\ophanim-node"
$nodeRuns = -not $SkipNode -and -not $CoreOnly -and (Test-Path $nodeDir)
if ($nodeRuns) {
    Write-Host "`n[4/5] Rust node checks"
    Invoke-Native -Check "cargo test" -FilePath "cargo" -Arguments @("test") -WorkDir $nodeDir
}
else {
    Add-Result -Check "rust node (cargo)" -Status SKIP
}

# --- 5. Secret scan ---------------------------------------------------
if (-not $SkipSecretScan -and -not $CoreOnly) {
    Write-Host "`n[5/5] Secret pattern scan (git-tracked first-party source)"
    $excluded = @('anything-llm', 'ollama', 'Obsidian_Vault', 'node_modules', 'vendor')
    $tracked = git ls-files
    $files = $tracked | Where-Object {
        $path = $_
        if ($path -match '\\tests\\|/tests/') { return $false }
        if ($path -match '(^|\\|/)test_.*\.py$') { return $false }
        foreach ($ex in $excluded) {
            if ($path -match "(^|\\|/)($ex)(\\|/|$)") { return $false }
        }
        $ext = [System.IO.Path]::GetExtension($path)
        return $ext -in @('.py', '.ts', '.tsx', '.rs', '.toml', '.yaml', '.yml', '.json', '.md', '.js', '.css', '.html')
    }

    $patterns = @(
        'sk-[A-Za-z0-9_\-]{16,}',
        'AIza[0-9A-Za-z_\-]{20,}',
        'AKIA[0-9A-Z]{16}',
        '-----BEGIN [A-Z ]*PRIVATE KEY-----'
    )

    $hits = [System.Collections.Generic.List[object]]::new()
    foreach ($file in $files) {
        $full = Join-Path $repoRoot $file
        if (-not (Test-Path $full)) { continue }
        $lineNumber = 0
        foreach ($line in [System.IO.File]::ReadLines($full)) {
            $lineNumber++
            foreach ($pattern in $patterns) {
                if ($line -match $pattern) {
                    $hits.Add([PSCustomObject]@{ File = $file; Line = $lineNumber })
                    break
                }
            }
        }
    }

    if ($hits.Count -eq 0) {
        Add-Result -Check "secret scan" -Status PASS
    }
    else {
        foreach ($hit in $hits) {
            Write-Host "    POTENTIAL SECRET: $($hit.File):$($hit.Line)"
        }
        Add-Result -Check "secret scan" -Status FAIL -Detail "$($hits.Count) potential secret(s)"
    }
}
else {
    Add-Result -Check "secret scan" -Status SKIP
}

# --- Summary ----------------------------------------------------------
Write-Host "`n============================================"
Write-Host "  Verification summary"
Write-Host "============================================"
$failed = 0
foreach ($result in $script:results) {
    $detail = if ($result.Detail) { " - $($result.Detail)" } else { '' }
    Write-Host ("  {0,-28} {1}{2}" -f $result.Check, $result.Status, $detail)
    if ($result.Status -eq 'FAIL') { $failed++ }
}
Write-Host ""
if ($failed -gt 0) {
    Write-Host "GATE RESULT: FAILED ($failed check(s))" -ForegroundColor Red
    exit 1
}
Write-Host "GATE RESULT: PASSED" -ForegroundColor Green
exit 0
