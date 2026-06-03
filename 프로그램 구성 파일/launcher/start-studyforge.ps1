$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$VenvDir = Join-Path $AppDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$Requirements = Join-Path $AppDir "requirements.txt"
$DistIndex = Join-Path $AppDir "dist\index.html"
$Sha1 = [System.Security.Cryptography.SHA1]::Create()
$InstanceId = -join ($Sha1.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($AppDir)) |
    ForEach-Object { $_.ToString("x2") })
$InstanceId = $InstanceId.Substring(0, 16)

function Write-Step {
    param([string] $Message)
    Write-Host ""
    Write-Host "== $Message"
}

function Get-PythonCommand {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return [pscustomobject]@{ File = "py"; Args = @("-3") }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        return [pscustomobject]@{ File = "python"; Args = @() }
    }
    throw "Python 3.11 or newer is required. Install Python, then run this launcher again."
}

function Invoke-Checked {
    param(
        [string] $File,
        [string[]] $Arguments
    )
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $File $($Arguments -join ' ')"
    }
}

function Test-PortOpen {
    param([int] $TargetPort)
    $connection = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    return $null -ne $connection
}

function Get-StudyForgeHealth {
    param([int] $TargetPort)
    try {
        $response = Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$TargetPort/api/health" -TimeoutSec 1
        return $response.Content | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

Set-Location $AppDir
Write-Host "Starting exam study app."
Write-Host "Keep this window open while using the app."

if (-not (Test-Path -LiteralPath $DistIndex)) {
    Write-Step "Building frontend"
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
        throw "Frontend build files are missing and npm is not installed. Re-download the repository or install Node.js LTS."
    }
    Invoke-Checked "npm" @("install")
    Invoke-Checked "npm" @("run", "build")
}

if (-not (Test-Path -LiteralPath $VenvPython)) {
    Write-Step "Preparing Python runtime"
    $python = Get-PythonCommand
    Invoke-Checked $python.File @($python.Args + @("-m", "venv", $VenvDir))
}

$DependencyMarker = Join-Path $VenvDir ".studyforge-deps-installed"
$ShouldInstall = -not (Test-Path -LiteralPath $DependencyMarker)
if (-not $ShouldInstall -and (Test-Path -LiteralPath $Requirements)) {
    $ShouldInstall = (Get-Item -LiteralPath $Requirements).LastWriteTimeUtc -gt
        (Get-Item -LiteralPath $DependencyMarker).LastWriteTimeUtc
}

if ($ShouldInstall) {
    Write-Step "Installing Python dependencies"
    Invoke-Checked $VenvPython @("-m", "pip", "install", "-r", $Requirements)
    Set-Content -LiteralPath $DependencyMarker -Value (Get-Date).ToString("o") -Encoding UTF8
}

$Port = $null
foreach ($CandidatePort in 8765..8785) {
    $health = Get-StudyForgeHealth $CandidatePort
    if ($health -and $health.instance_id -eq $InstanceId) {
        $Url = "http://127.0.0.1:$CandidatePort"
        Write-Step "Opening existing app server"
        Start-Process $Url
        Write-Host "Opened $Url"
        Read-Host "Press Enter to close this launcher"
        exit 0
    }
    if (-not (Test-PortOpen $CandidatePort)) {
        $Port = $CandidatePort
        break
    }
}

if (-not $Port) {
    throw "No available port found in 8765-8785. Close other local servers and try again."
}

$Url = "http://127.0.0.1:$Port"
if ($env:STUDYFORGE_NO_BROWSER -ne "1") {
    Write-Step "Opening browser"
    Start-Job -ScriptBlock {
        param([string] $TargetUrl)
        for ($index = 0; $index -lt 30; $index++) {
            try {
                Invoke-WebRequest -UseBasicParsing "$TargetUrl/api/health" -TimeoutSec 1 | Out-Null
                Start-Process $TargetUrl
                return
            }
            catch {
                Start-Sleep -Seconds 1
            }
        }
        Start-Process $TargetUrl
    } -ArgumentList $Url | Out-Null
}
else {
    Write-Step "Browser auto-open disabled"
}

Write-Step "Running app server"
Write-Host "The browser will open automatically. Manual URL: $Url"
Write-Host "Press Ctrl+C in this window to stop the server."
Invoke-Checked $VenvPython @((Join-Path $AppDir "scripts\run_api.py"), "--port", "$Port")
