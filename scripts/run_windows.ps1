<#
.SYNOPSIS
  Runs Redis (in WSL Ubuntu), OPA (Windows), Backend (Uvicorn), and Frontend (Next.js) without modifying env files.

.USAGE
  Run PowerShell (recommended as Administrator):
    powershell -ExecutionPolicy Bypass -File .\scripts\run_windows.ps1
#>

Param(
  [string]$WslDistro = "Ubuntu",
  [string]$OpaExe = "$env:USERPROFILE\opa.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LogDir = Join-Path $Root 'scripts\logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "[Windows Run] Starting Redis (WSL), OPA, Backend, Frontend in separate terminals..." -ForegroundColor Cyan

# 1) Ensure Redis is running in WSL (non-blocking, no systemd required)
Write-Host "[WSL:Redis] Ensuring redis-server is running in $WslDistro (no systemd)..."

# Quick-start: if redis isn't running, launch it daemonized
try {
  # pgrep redis-server || (redis-server --daemonize yes)
  wsl -d $WslDistro -- bash -lc "pgrep redis-server >/dev/null 2>&1 || (redis-server --daemonize yes >/dev/null 2>&1 || nohup redis-server >/dev/null 2>&1 & disown)" | Out-Null
} catch {
  Write-Host "[WSL:Redis] Failed to start redis-server quickly. You may need to install it in WSL (sudo apt install -y redis-server)." -ForegroundColor Yellow
}

# Poll a few times (short timeout) to confirm it's up
$maxTries = 10
for ($i=1; $i -le $maxTries; $i++) {
  try {
    $pong = wsl -d $WslDistro -- redis-cli ping 2>$null
    if ($pong -and $pong.Trim().ToUpper() -eq 'PONG') {
      Write-Host "[WSL:Redis] redis-cli: PONG"
      break
    }
  } catch {}
  Start-Sleep -Seconds 1
  if ($i -eq $maxTries) {
    Write-Host "[WSL:Redis] Redis not responding after $maxTries attempts. Continuing anyway..." -ForegroundColor Yellow
  }
}

# 2) Start OPA (skip if port 8181 already in use) in a new terminal
function Test-PortOpen {
  param([int]$Port)
  try {
    $client = New-Object System.Net.Sockets.TcpClient
    $async = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
    $wait = $async.AsyncWaitHandle.WaitOne(300)
    if ($wait -and $client.Connected) { $client.Close(); return $true } else { $client.Close(); return $false }
  } catch { return $false }
}

$opaPortInUse = Test-PortOpen -Port 8181
if ($opaPortInUse) {
  Write-Host "[OPA] Port 8181 already in use. Skipping OPA start (an instance may already be running)." -ForegroundColor Yellow
} elseif (-not (Test-Path $OpaExe)) {
  Write-Host "[OPA] $OpaExe not found. Download with setup_windows.ps1 first." -ForegroundColor Red
} else {
  Write-Host "[OPA] Starting OPA server in a new terminal..."
  $wtCmd = $null
  try { $tmp = Get-Command wt.exe -ErrorAction SilentlyContinue; if ($tmp) { $wtCmd = $tmp.Source } } catch {}
  if ($wtCmd) {
    Start-Process -FilePath $wtCmd -ArgumentList @('new-tab','--title','OPA','--startingDirectory',"$Root",'cmd','/k', '"' + $OpaExe + ' run --server opa\\policy.rego"') | Out-Null
  } else {
    Start-Process -FilePath "powershell" -ArgumentList @('-NoExit','-Command',"cd '$Root'; & '$OpaExe' run --server 'opa\\policy.rego'") | Out-Null
  }
}

# 3) Start Backend (Uvicorn) in a new terminal
Write-Host "[Backend] Starting Uvicorn in a new terminal..."
$wtCmd = $null
try { $tmp = Get-Command wt.exe -ErrorAction SilentlyContinue; if ($tmp) { $wtCmd = $tmp.Source } } catch {}
if ($wtCmd) {
  Start-Process -FilePath $wtCmd -ArgumentList @('new-tab','--title','Backend','--startingDirectory',"$Root",'powershell','-NoExit','-Command','python -m uvicorn trunk:app --reload') | Out-Null
} else {
  Start-Process -FilePath "powershell" -ArgumentList @('-NoExit','-Command',"cd '$Root'; python -m uvicorn trunk:app --reload") | Out-Null
}

# 4) Start Frontend (Next.js) in a new terminal
Write-Host "[Frontend] Starting Next.js dev server (npm run dev) in a new terminal..."
$FrontendDir = Join-Path $Root 'ascend-educate-nextjs'
$wtCmd = $null
try { $tmp = Get-Command wt.exe -ErrorAction SilentlyContinue; if ($tmp) { $wtCmd = $tmp.Source } } catch {}
if ($wtCmd) {
  Start-Process -FilePath $wtCmd -ArgumentList @('new-tab','--title','Frontend','--startingDirectory',"$FrontendDir",'cmd','/k','npm run dev') | Out-Null
} else {
  Start-Process -FilePath "cmd.exe" -ArgumentList @('/k','cd /d', '"' + $FrontendDir + '"', '&&', 'npm', 'run', 'dev') | Out-Null
}

Write-Host "[Windows Run] All processes launched in separate terminals." -ForegroundColor Green


