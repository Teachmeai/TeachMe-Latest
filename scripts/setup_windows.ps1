<#
.SYNOPSIS
  Sets up WSL (Ubuntu), installs Redis in WSL, and installs OPA on Windows.

.USAGE
  Run PowerShell as Administrator:
    powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1

  If WSL gets installed for the first time, you may need to reboot.
#>

Param(
  [string]$WslDistro = "Ubuntu",
  [string]$OpaUrl = "https://openpolicyagent.org/downloads/latest/opa_windows_amd64.exe"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Write-Host "[Windows Setup] Starting setup for WSL, Redis (in WSL), and OPA..." -ForegroundColor Cyan

# 1) Ensure WSL is enabled
Write-Host "[WSL] Enabling WSL (if not already enabled)..."
Try {
  wsl --status | Out-Null
} Catch {
  Write-Host "WSL not detected. Enabling Windows features..." -ForegroundColor Yellow
  dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart | Out-Null
  dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart | Out-Null
  Write-Host "WSL features enabled. A reboot may be required before proceeding." -ForegroundColor Yellow
}

# 2) Install a default Ubuntu distro if missing
Write-Host "[WSL] Checking for $WslDistro distro..."
$haveDistro = $false
try {
  $list = wsl -l -q 2>$null
  if ($list -and ($list | ForEach-Object { $_.Trim() }) -contains $WslDistro) {
    $haveDistro = $true
  }
} catch {}

if (-not $haveDistro) {
  Write-Host "[WSL] Installing $WslDistro... (this can take a while)"
  wsl --install -d $WslDistro
  Write-Host "If prompted, reboot your machine and re-run this script." -ForegroundColor Yellow
}

# 3) Install Redis inside WSL Ubuntu
Write-Host "[WSL:Redis] Installing redis-server in $WslDistro..."
wsl -d $WslDistro -- sudo apt update -y
wsl -d $WslDistro -- sudo apt install -y redis-server
wsl -d $WslDistro -- sudo sed -i 's/^#* *supervised .*/supervised systemd/' /etc/redis/redis.conf
wsl -d $WslDistro -- sudo /etc/init.d/redis-server restart || wsl -d $WslDistro -- sudo systemctl restart redis-server || $true

Write-Host "[WSL:Redis] Testing redis-cli ping..."
Try {
  $pong = wsl -d $WslDistro -- redis-cli ping
  Write-Host "redis-cli: $pong"
} Catch {
  Write-Host "Redis ping failed. Ensure redis-server is running in WSL." -ForegroundColor Yellow
}

# 4) Install OPA on Windows
Write-Host "[OPA] Downloading OPA for Windows..."
$OpaExe = Join-Path $env:USERPROFILE 'opa.exe'
Invoke-WebRequest -Uri $OpaUrl -OutFile $OpaExe -UseBasicParsing
Write-Host "OPA downloaded to $OpaExe"

Write-Host "[OPA] Version:" -NoNewline; & $OpaExe version

Write-Host "
To run OPA with your project policy (in a new terminal from repo root):

  `"$OpaExe`" run --server .\opa\policy.rego

OPA will listen on http://localhost:8181. Test with:

  curl -sS -X POST http://localhost:8181/v1/data/authz/allow `
    -H 'Content-Type: application/json' `
    -d '{"input": {"user": "u", "role": "teacher", "action": "x", "resource": "y"}}'
" -ForegroundColor Green

Write-Host "[Done] Windows setup complete." -ForegroundColor Cyan


