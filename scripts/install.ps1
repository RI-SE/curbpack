#Requires -Version 5.1
<#
.SYNOPSIS
  Install Curbpack on Windows (amd64).

.DESCRIPTION
  Downloads curbpack_windows_amd64.exe from GitHub Releases, verifies sha256 via
  checksums.txt (fail-closed), atomically replaces the binary, persists User PATH,
  writes install-marker.json, and copies curb.exe alias.

  Repair mode (-Repair) is local-only: re-asserts PATH + alias; never downloads.

.PARAMETER Version
  Release tag (default from install-manifest.json / v0.5.3). Use 'latest' for newest.

.PARAMETER InstallDir
  Default: $env:LOCALAPPDATA\Programs\Curbpack

.PARAMETER Repair
  Local PATH/alias repair only (same semantics as: curbpack doctor --repair).

.PARAMETER Repo
  GitHub repo (default afelin/curbpack)
#>
[CmdletBinding()]
param(
  [string]$Version = "",
  [string]$InstallDir = "",
  [switch]$Repair,
  [string]$Repo = "afelin/curbpack"
)

$ErrorActionPreference = "Stop"
$Claim = "Prepares evidence for human review — not a conformity assessment."

function Get-DefaultVersion {
  $here = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
  $manifest = Join-Path $here "install-manifest.json"
  if (Test-Path $manifest) {
    try {
      $j = Get-Content -Raw -Path $manifest | ConvertFrom-Json
      if ($j.default_version) { return [string]$j.default_version }
    } catch {}
  }
  return "v0.5.3"
}

function Get-InstallDir {
  if ($InstallDir) { return $InstallDir }
  if ($env:CURBPACK_INSTALL_DIR) { return $env:CURBPACK_INSTALL_DIR }
  return (Join-Path $env:LOCALAPPDATA "Programs\Curbpack")
}

function Get-MarkerPath {
  return (Join-Path (Get-InstallDir) "install-marker.json")
}

function Write-Marker {
  param([string]$Tag, [string]$Dir, [string]$Binary)
  $marker = @{
    schema       = "curbpack-install-marker:1"
    version      = $Tag
    install_dir  = $Dir
    binary       = $Binary
    installed_at = (Get-Date).ToUniversalTime().ToString("o")
    goos         = "windows"
  } | ConvertTo-Json
  $path = Get-MarkerPath
  $null = New-Item -ItemType Directory -Force -Path (Split-Path $path)
  # UTF-8 without BOM (Windows PowerShell 5.1 Set-Content -Encoding utf8 writes BOM)
  $utf8NoBom = New-Object System.Text.UTF8Encoding $false
  [System.IO.File]::WriteAllText($path, ($marker + [Environment]::NewLine), $utf8NoBom)
  Write-Host "Marker:    $path"
}

function Ensure-UserPath {
  param([string]$Dir)
  $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
  if (-not $userPath) { $userPath = "" }
  $parts = @($userPath -split ';' | Where-Object { $_ -ne '' })
  if ($parts -notcontains $Dir) {
    $newPath = ($Dir.TrimEnd('\') + ';' + $userPath).TrimEnd(';')
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "PATH:      added User PATH entry for $Dir"
  } else {
    Write-Host "PATH:      already present"
  }
  # Session PATH
  if (-not (($env:Path -split ';') -contains $Dir)) {
    $env:Path = $Dir + ';' + $env:Path
  }
}

function Invoke-Repair {
  $dir = Get-InstallDir
  $exe = Join-Path $dir "curbpack.exe"
  $alias = Join-Path $dir "curb.exe"
  Write-Host "Curbpack repair (local only — no network / no auto-update)"
  Write-Host "  $Claim"
  Write-Host ""
  if (-not (Test-Path $exe)) {
    Write-Host "Binary missing — reinstall:" -ForegroundColor Red
    Write-Host '  irm https://raw.githubusercontent.com/afelin/curbpack/main/scripts/install.ps1 | iex'
    exit 2
  }
  Copy-Item -Force -Path $exe -Destination $alias
  Ensure-UserPath -Dir $dir
  $ver = & $exe version 2>$null
  if (-not $ver) { $ver = "unknown" }
  Write-Marker -Tag ($ver -replace '^curbpack\s+', 'v') -Dir $dir -Binary $exe
  Write-Host ""
  Write-Host "[+] Repair done. Open a new shell if PATH was just updated."
  Write-Host $Claim
  exit 0
}

if ($Repair) {
  Invoke-Repair
}

Write-Host "Curbpack installer (Windows amd64)"
Write-Host "  $Claim"
Write-Host ""

if (-not $Version) {
  if ($env:CURBPACK_VERSION) { $Version = $env:CURBPACK_VERSION }
  else { $Version = Get-DefaultVersion }
}

$dir = Get-InstallDir
$null = New-Item -ItemType Directory -Force -Path $dir
$asset = "curbpack_windows_amd64.exe"
$dest = Join-Path $dir "curbpack.exe"
$alias = Join-Path $dir "curb.exe"

$headers = @{ "Accept" = "application/vnd.github+json"; "User-Agent" = "curbpack-install.ps1" }
if ($env:GITHUB_TOKEN) { $headers["Authorization"] = "Bearer $($env:GITHUB_TOKEN)" }

if ($Version -eq "latest") {
  $rel = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -Headers $headers
  $tag = $rel.tag_name
  $url = ($rel.assets | Where-Object { $_.name -eq $asset } | Select-Object -First 1).browser_download_url
  $checksumsUrl = ($rel.assets | Where-Object { $_.name -eq "checksums.txt" } | Select-Object -First 1).browser_download_url
} else {
  $tag = $Version
  $url = "https://github.com/$Repo/releases/download/$tag/$asset"
  $checksumsUrl = "https://github.com/$Repo/releases/download/$tag/checksums.txt"
}

if (-not $url) {
  Write-Error "could not resolve download URL for $asset (tag=$tag)"
  exit 1
}
if (-not $checksumsUrl) {
  Write-Error "checksums.txt URL missing — refusing install (fail closed)"
  exit 1
}

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("curbpack-install-" + [guid]::NewGuid().ToString("n"))
$null = New-Item -ItemType Directory -Force -Path $tmp
try {
  $tmpExe = Join-Path $tmp $asset
  $tmpSum = Join-Path $tmp "checksums.txt"
  Write-Host "Downloading $tag → $asset"
  Invoke-WebRequest -Uri $url -OutFile $tmpExe -Headers $headers -UseBasicParsing
  Invoke-WebRequest -Uri $checksumsUrl -OutFile $tmpSum -Headers $headers -UseBasicParsing

  $line = Get-Content $tmpSum | Where-Object { $_ -match [regex]::Escape($asset) + '\s*$' } | Select-Object -First 1
  if (-not $line) {
    Write-Error "no checksum entry for $asset in checksums.txt — refusing install"
    exit 1
  }
  $expected = ($line -split '\s+')[0].Trim().ToLowerInvariant()
  $actual = (Get-FileHash -Algorithm SHA256 -Path $tmpExe).Hash.ToLowerInvariant()
  if ($actual -ne $expected) {
    Write-Error "checksum mismatch for $asset`n  expected: $expected`n  actual:   $actual"
    exit 1
  }
  Write-Host "Checksum OK ($actual)"

  # Atomic replace: write .new then Move (helps when exe is locked briefly)
  $newPath = "$dest.new"
  Copy-Item -Force -Path $tmpExe -Destination $newPath
  try {
    Move-Item -Force -Path $newPath -Destination $dest
  } catch {
    Remove-Item -Force -Path $newPath -ErrorAction SilentlyContinue
    Write-Error "access denied replacing $dest — close running curbpack.exe and retry (or Defender quarantine → full reinstall). $_"
    exit 1
  }
  Copy-Item -Force -Path $dest -Destination $alias
  try { Unblock-File -Path $dest -ErrorAction SilentlyContinue } catch {}
  try { Unblock-File -Path $alias -ErrorAction SilentlyContinue } catch {}

  Ensure-UserPath -Dir $dir
  Write-Marker -Tag $tag -Dir $dir -Binary $dest

  Write-Host "Installed: $dest"
  Write-Host "Alias:     $alias"
  Write-Host ""
  Write-Host "Next (safe sandbox, never touches your product):"
  Write-Host "  curbpack doctor"
  Write-Host "  curbpack demo"
  Write-Host "After PATH loss: curbpack doctor --repair   (or: install.ps1 -Repair)"
  Write-Host ""
  Write-Host $Claim
} finally {
  Remove-Item -Recurse -Force -Path $tmp -ErrorAction SilentlyContinue
}
