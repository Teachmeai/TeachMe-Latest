<#
.SYNOPSIS
  Runs Redis (in WSL Ubuntu), OPA (Windows), Backend (Uvicorn), and Frontend (Next.js) without modifying env files.

.USAGE
  Run PowerShell (recommended as Administrator):
    powershell -ExecutionPolicy Bypass -File .\scripts\run_windows.ps1
#>

Param(
  [string]$WslDistro = "Ubuntu",
  [string]$OpaExe = "$env:USERPROFILE\opa.exe",
  [switch]$SkipRedis = $false,
  [switch]$OpenWSLRedisCli = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$LogDir = Join-Path $Root 'scripts\logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "[Windows Run] Starting Redis (WSL), OPA, Backend, Frontend in separate terminals..." -ForegroundColor Cyan

if (-not $SkipRedis) {
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
} else {
  Write-Host "[WSL:Redis] Skipping Redis management (-SkipRedis specified)." -ForegroundColor Yellow
}

# 1b) Open an interactive WSL terminal with redis-cli (like doing: wsl -> redis-cli)
if ($OpenWSLRedisCli) {
  Write-Host "[WSL] Opening a terminal running 'wsl -d $WslDistro -e redis-cli'..."
  # Use a simple, robust launcher to avoid Windows Terminal argument quirks
  Start-Process -FilePath "powershell" -ArgumentList @('-NoExit','-Command',"wsl -d '$WslDistro' -e redis-cli") | Out-Null
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

# Helper: get current WSL IP (first address)
function Get-WSL-IP {
  param([string]$Distro)
  try {
    $ips = wsl -d $Distro -- hostname -I 2>$null
    if ($ips) {
      $first = ($ips -split '\s+')[0].Trim()
      if ($first) { return $first }
    }
  } catch {}
  return $null
}

# Configure Windows portproxy from 127.0.0.1:6379 -> <WSL_IP>:6379 so backend can use localhost
function Ensure-Redis-PortProxy {
  param([string]$TargetIp)
  if (-not $TargetIp) { return }
  try {
    # Remove existing rule for 6379 if present, then add with current IP
    netsh interface portproxy delete v4tov4 listenaddress=127.0.0.1 listenport=6379 2>$null | Out-Null
    netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=6379 connectaddress=$TargetIp connectport=6379 | Out-Null
    # Open firewall if needed
    netsh advfirewall firewall add rule name="Redis 6379" dir=in action=allow protocol=TCP localport=6379 2>$null | Out-Null
    Write-Host "[Windows] Port proxy 127.0.0.1:6379 -> $TargetIp:6379 configured." -ForegroundColor Green
  } catch {
    Write-Host "[Windows] Failed to configure portproxy. Run PowerShell as Administrator." -ForegroundColor Yellow
  }
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

# Set up portproxy so backend can reach Redis on localhost even if Redis is in WSL
$wslIpForProxy = Get-WSL-IP -Distro $WslDistro
if ($wslIpForProxy) { Ensure-Redis-PortProxy -TargetIp $wslIpForProxy }
if ($wtCmd) {
  if (Test-PortOpen -Port 8000) {
    Write-Host "[Backend] Port 8000 already in use. Skipping backend start." -ForegroundColor Yellow
  } else {
    Start-Process -FilePath $wtCmd -ArgumentList @('new-tab','--title','Backend','--startingDirectory',"$Root",'powershell','-NoExit','-Command','python -m uvicorn trunk:app --reload') | Out-Null
  }
} else {
  if (Test-PortOpen -Port 8000) {
    Write-Host "[Backend] Port 8000 already in use. Skipping backend start." -ForegroundColor Yellow
  } else {
    Start-Process -FilePath "powershell" -ArgumentList @('-NoExit','-Command',"cd '$Root'; python -m uvicorn trunk:app --reload") | Out-Null
  }
}

# 4) Start Frontend (Next.js) in a new terminal
Write-Host "[Frontend] Starting Next.js dev server (npm run dev) in a new terminal..."
$FrontendDir = Join-Path $Root 'ascend-educate-nextjs'
$wtCmd = $null
try { $tmp = Get-Command wt.exe -ErrorAction SilentlyContinue; if ($tmp) { $wtCmd = $tmp.Source } } catch {}
if ($wtCmd) {
  if (Test-PortOpen -Port 3000) {
    Write-Host "[Frontend] Port 3000 already in use. Skipping frontend start." -ForegroundColor Yellow
  } else {
    Start-Process -FilePath $wtCmd -ArgumentList @('new-tab','--title','Frontend','--startingDirectory',"$FrontendDir",'cmd','/k','npm run dev') | Out-Null
  }
} else {
  if (Test-PortOpen -Port 3000) {
    Write-Host "[Frontend] Port 3000 already in use. Skipping frontend start." -ForegroundColor Yellow
  } else {
    Start-Process -FilePath "cmd.exe" -ArgumentList @('/k','cd /d', '"' + $FrontendDir + '"', '&&', 'npm', 'run', 'dev') | Out-Null
  }
}

Write-Host "[Windows Run] All processes launched in separate terminals." -ForegroundColor Green


