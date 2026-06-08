# Deploy Franklin CRM to a remote KVM/VPS via SSH (password or key auth).
# Usage:
#   .\deploy\deploy-from-windows.ps1
#   .\deploy\deploy-from-windows.ps1 -Server root@194.238.19.53 -SshKey "$env:USERPROFILE\.ssh\id_ed25519"

param(
    [string]$Server = "root@194.238.19.53",
    [string]$SshKey = "",
    [switch]$SkipBootstrap
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

if (-not (Test-Path "$ProjectRoot\backend\server.py")) {
    throw "Cannot find backend/server.py — run from the Franklin_Mgmt repo root."
}

$sshArgs = @()
if ($SshKey) { $sshArgs += @("-i", $SshKey) }

function Invoke-Ssh([string]$Command) {
    & ssh @sshArgs $Server $Command
    if ($LASTEXITCODE -ne 0) { throw "SSH failed: $Command" }
}

function Invoke-Scp([string[]]$ExtraArgs) {
    & scp @sshArgs @ExtraArgs
    if ($LASTEXITCODE -ne 0) { throw "SCP failed" }
}

Write-Host "==> Project: $ProjectRoot"
Write-Host "==> Target:  $Server"

$tarball = Join-Path $env:TEMP "franklin-crm-deploy.tgz"
if (Test-Path $tarball) { Remove-Item $tarball -Force }

Write-Host "==> Creating deployment archive..."
Push-Location $ProjectRoot
tar --exclude=node_modules --exclude=.venv --exclude=frontend/build --exclude=.git --exclude=__pycache__ -czf $tarball .
Pop-Location

Write-Host "==> Uploading (enter SSH password if prompted)..."
Invoke-Scp @($tarball, "${Server}:/tmp/franklin-crm-deploy.tgz")

$bootstrap = ""
if (-not $SkipBootstrap) {
    $bootstrap = "bash /tmp/franklin-crm-src/deploy/setup-server.sh && "
}

Write-Host "==> Installing on server..."
$remoteCmd = "${bootstrap}bash /tmp/franklin-crm-src/deploy/install-app.sh"
Invoke-Ssh "set -e; rm -rf /tmp/franklin-crm-src && mkdir -p /tmp/franklin-crm-src && tar xzf /tmp/franklin-crm-deploy.tgz -C /tmp/franklin-crm-src && $remoteCmd"

$localEnv = Join-Path $ProjectRoot "backend\.env"
if (Test-Path $localEnv) {
    Write-Host "==> Uploading backend/.env..."
    Invoke-Scp @($localEnv, "${Server}:/opt/franklin-crm/backend/.env")
    Invoke-Ssh "systemctl restart franklin-backend"
}

Write-Host ""
Write-Host "Done. Open http://194.238.19.53/ in your browser."
Write-Host "CEO login: ceo@franklinwardcorpp.com / ceo12345"
