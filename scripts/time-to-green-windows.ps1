#Requires -Version 5.1
<#
.SYNOPSIS
  Time-to-green drill on Windows: install → doctor → demo → repair semantics.

.DESCRIPTION
  Uses a workspace-built curbpack.exe when release install is unavailable.
  Does not claim certification. Exit 0 on green demo.
#>
[CmdletBinding()]
param(
  [string]$Bin = ""
)

$ErrorActionPreference = "Stop"
$Claim = "Prepares evidence for human review — not a conformity assessment."
Write-Host "== time-to-green-windows =="
Write-Host "  $Claim"

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if (-not $root) { $root = (Get-Location).Path }
# scripts/ → repo root
$root = Resolve-Path (Join-Path $PSScriptRoot "..")

if (-not $Bin) {
  $Bin = Join-Path $root "bin\curbpack.exe"
}
if (-not (Test-Path $Bin)) {
  Write-Host "Building $Bin"
  New-Item -ItemType Directory -Force -Path (Split-Path $Bin) | Out-Null
  Push-Location $root
  go build -o $Bin ./cmd/curbpack
  Pop-Location
}

& $Bin doctor
if ($LASTEXITCODE -ne 0) { throw "doctor failed" }

$demo = Join-Path $env:TEMP ("curbpack-ttg-" + [guid]::NewGuid().ToString("n"))
& $Bin demo --out $demo --keep
if ($LASTEXITCODE -ne 0) { throw "demo failed" }
$one = Join-Path $demo "review-pack\buyer-onepager.html"
if (-not (Test-Path $one)) { throw "missing onepager" }

& $Bin doctor --repair
# repair may exit 0 even when only refreshing PATH/alias

Write-Host ""
Write-Host "[+] time-to-green-windows PASS (demo green) — not certification"
Write-Host $Claim
exit 0
