# SYS-05: run on the Windows packaging runner. Downloads and PATH changes stay in fixtures.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../scripts/install/windows.ps1"
$originalSetInstallPath = (Get-Command Set-InstallPath).ScriptBlock

$root = Join-Path ([IO.Path]::GetTempPath()) ('curbpack-install-test-' + [Guid]::NewGuid())
$fixture = Join-Path $root 'release'
$destination = Join-Path $root 'installed programs'
$env:CURBPACK_VERSION = 'fixture-release'
$env:CURBPACK_INSTALL_DIR = $destination
$script:pathAdded = $null

function Set-InstallPath([string]$Directory) { $script:pathAdded = $Directory }
function Invoke-WebRequest([string]$Uri, [string]$OutFile, [switch]$UseBasicParsing) {
    $script:downloads += $Uri
    Copy-Item -LiteralPath (Join-Path $fixture ($Uri.Split('/')[-1])) -Destination $OutFile
}
function Invoke-RestMethod([string]$Uri) { return @{ tag_name = 'fixture-release' } }
function Assert-Equal($Actual, $Expected) {
    if ($Actual -cne $Expected) { throw "Expected '$Expected', got '$Actual'" }
}
function Reset-Fixture {
    $env:CURBPACK_VERSION = 'fixture-release'
    $env:CURBPACK_INSTALL_DIR = $destination
    New-Item -ItemType Directory -Force -Path $fixture, $destination | Out-Null
    $sums = @()
    foreach ($name in @('curbpack-studio', 'curbcheck')) {
        $asset = "$name-windows-x64.exe"
        [IO.File]::WriteAllText((Join-Path $fixture $asset), "new $name")
        [IO.File]::WriteAllText((Join-Path $destination "$name.exe"), "old $name")
        $hash = (Get-FileHash -LiteralPath (Join-Path $fixture $asset) -Algorithm SHA256).Hash
        $sums += "$hash  $asset"
    }
    $sums | Set-Content -LiteralPath (Join-Path $fixture 'SHA256SUMS') -Encoding ascii
    $script:pathAdded = $null
    $script:downloads = @()
}
function Assert-InstallFails {
    $failed = $false
    try { Install-Programs @('curbpack-studio', 'curbcheck') }
    catch { $failed = $true }
    if (-not $failed) { throw 'Expected installation to fail' }
    foreach ($name in @('curbpack-studio', 'curbcheck')) {
        Assert-Equal (Get-Content -Raw -LiteralPath (Join-Path $destination "$name.exe")) "old $name"
    }
    Assert-Equal $script:pathAdded $null
}

try {
    Reset-Fixture
    Install-Programs @('curbpack-studio', 'curbcheck')
    Assert-Equal (Get-Content -Raw -LiteralPath (Join-Path $destination 'curbpack-studio.exe')) 'new curbpack-studio'
    Assert-Equal (Get-Content -Raw -LiteralPath (Join-Path $destination 'curbcheck.exe')) 'new curbcheck'
    Assert-Equal $script:pathAdded $destination
    foreach ($url in $script:downloads) {
        if (-not $url.Contains('/releases/download/fixture-release/')) { throw "Unexpected release URL: $url" }
    }

    Reset-Fixture
    Install-Programs @('curbcheck')
    Assert-Equal (Get-Content -Raw -LiteralPath (Join-Path $destination 'curbpack-studio.exe')) 'old curbpack-studio'
    Assert-Equal (Get-Content -Raw -LiteralPath (Join-Path $destination 'curbcheck.exe')) 'new curbcheck'

    Reset-Fixture
    [IO.File]::WriteAllText((Join-Path $fixture 'curbcheck-windows-x64.exe'), 'tampered')
    Assert-InstallFails

    Reset-Fixture
    Remove-Item -LiteralPath (Join-Path $fixture 'curbcheck-windows-x64.exe')
    Assert-InstallFails

    Reset-Fixture
    Set-Content -LiteralPath (Join-Path $fixture 'SHA256SUMS') -Value ''
    Assert-InstallFails

    Reset-Fixture
    $env:CURBPACK_VERSION = 'latest'
    Install-Programs @('curbcheck')
    Assert-Equal (Get-Content -Raw -LiteralPath (Join-Path $destination 'curbcheck.exe')) 'new curbcheck'

    Reset-Fixture
    Install-Programs @('curbpack-studio', 'curbcheck')
    Install-Programs @('curbpack-studio', 'curbcheck')
    Assert-Equal @(Get-ChildItem -LiteralPath $destination).Count 2

    Reset-Fixture
    $env:CURBPACK_VERSION = '../invalid'
    Assert-InstallFails
    Assert-Equal $script:downloads.Count 0

    Reset-Fixture
    $env:CURBPACK_INSTALL_DIR = $null
    $env:LOCALAPPDATA = Join-Path $root 'default user'
    Install-Programs @('curbcheck')
    $defaultDirectory = Join-Path $env:LOCALAPPDATA 'Programs\Curbpack'
    Assert-Equal (Get-Content -Raw -LiteralPath (Join-Path $defaultDirectory 'curbcheck.exe')) 'new curbcheck'
    Assert-Equal $script:pathAdded $defaultDirectory

    Write-Host 'PowerShell installers: 9 scenarios passed (fixture downloads and PATH callback; native Windows PATH persistence is a separate acceptance check).'

    if ([Environment]::OSVersion.Platform -eq [PlatformID]::Win32NT) {
        $originalUserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        $originalProcessPath = $env:Path
        try {
            & $originalSetInstallPath $destination
            & $originalSetInstallPath $destination
            $entries = @([Environment]::GetEnvironmentVariable('Path', 'User') -split ';')
            Assert-Equal @($entries | Where-Object { $_ -eq $destination }).Count 1
            if (@($env:Path -split ';') -notcontains $destination) { throw 'Process PATH was not updated' }
            Write-Host 'Native Windows user PATH persistence and idempotence: passed.'
        }
        finally {
            [Environment]::SetEnvironmentVariable('Path', $originalUserPath, 'User')
            $env:Path = $originalProcessPath
        }
    }
    else {
        Write-Host 'Native Windows user PATH persistence: NOT RUN (this runtime is not Windows).'
    }
}
finally {
    Remove-Item -Recurse -Force -LiteralPath $root
}
