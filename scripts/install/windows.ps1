# Shared implementation; package_installers.py adds the fixed program selection.
$ErrorActionPreference = 'Stop'

function Set-InstallPath([string]$Directory) {
    $userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
    if (@($userPath -split ';') -notcontains $Directory) {
        [Environment]::SetEnvironmentVariable('Path', "$Directory;$userPath", 'User')
    }
    if (@($env:Path -split ';') -notcontains $Directory) {
        $env:Path = "$Directory;$env:Path"
    }
}

function Install-Programs([string[]]$Programs) {
    $architecture = $env:PROCESSOR_ARCHITEW6432
    if (-not $architecture) { $architecture = $env:PROCESSOR_ARCHITECTURE }
    if ($env:OS -ne 'Windows_NT' -or $architecture -ne 'AMD64') {
        throw 'This installer requires Windows x64.'
    }
    $version = $env:CURBPACK_VERSION
    if (-not $version -or $version -eq 'latest') {
        $version = (Invoke-RestMethod -Uri 'https://api.github.com/repos/RI-SE/curbpack/releases/latest').tag_name
    }
    if (-not $version -or $version -notmatch '^[a-zA-Z0-9._-]+$') { throw 'Invalid release tag.' }
    $installDir = $env:CURBPACK_INSTALL_DIR
    if (-not $installDir) { $installDir = Join-Path $env:LOCALAPPDATA 'Programs\Curbpack' }
    $base = "https://github.com/RI-SE/curbpack/releases/download/$version"
    $temporary = Join-Path ([IO.Path]::GetTempPath()) ('curbpack-install-' + [Guid]::NewGuid())
    $staging = $null
    New-Item -ItemType Directory -Path $temporary | Out-Null
    try {
        Write-Host "Installing release $version for Windows x64"
        $sumsPath = Join-Path $temporary 'SHA256SUMS'
        Invoke-WebRequest -UseBasicParsing -Uri "$base/SHA256SUMS" -OutFile $sumsPath
        $sums = Get-Content -LiteralPath $sumsPath
        foreach ($program in $Programs) {
            $asset = "$program-windows-x64.exe"
            $download = Join-Path $temporary $asset
            Invoke-WebRequest -UseBasicParsing -Uri "$base/$asset" -OutFile $download
            $entries = @($sums | Where-Object { $_ -cmatch ('^[0-9a-fA-F]{64}  ' + [regex]::Escape($asset) + '$') })
            if ($entries.Count -ne 1) { throw "Expected one checksum for $asset" }
            $expected = ($entries[0] -split '  ')[0]
            $actual = (Get-FileHash -LiteralPath $download -Algorithm SHA256).Hash
            if ($actual -ine $expected) { throw "Checksum mismatch for $asset" }
            Write-Host "${asset}: OK"
        }
        foreach ($program in $Programs) {
            $target = Join-Path $installDir "$program.exe"
            if (Test-Path -LiteralPath $target -PathType Container) { throw "Cannot replace directory $target" }
        }
        New-Item -ItemType Directory -Force -Path $installDir | Out-Null
        $staging = Join-Path $installDir ('.curbpack-install-' + [Guid]::NewGuid())
        New-Item -ItemType Directory -Path $staging | Out-Null
        foreach ($program in $Programs) {
            Copy-Item -LiteralPath (Join-Path $temporary "$program-windows-x64.exe") -Destination (Join-Path $staging "$program.exe")
        }
        foreach ($program in $Programs) {
            $target = Join-Path $installDir "$program.exe"
            Move-Item -Force -LiteralPath (Join-Path $staging "$program.exe") -Destination $target
            Write-Host "Installed: $target"
        }
        Set-InstallPath $installDir
        Write-Host 'Installation complete. Open a new terminal if the commands are not yet available.'
    }
    finally {
        Remove-Item -Recurse -Force -LiteralPath $temporary
        if ($staging -and (Test-Path -LiteralPath $staging)) { Remove-Item -Recurse -Force -LiteralPath $staging }
    }
}
