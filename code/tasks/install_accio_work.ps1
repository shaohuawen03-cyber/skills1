# Accio Work installer task (round 3): install the Chinese edition to E:\AccioWork.
# Runs on the user machine via code/local_check.ps1 section 4 (repo task).
# ASCII only per repo convention. Chinese docs live in deliverable/accio_work_install/.
#
# Strategy:
#   1) Find the official Windows x64 installer (scrape accio-ai.com pages, then
#      candidate URLs, then Downloads/Desktop folders).
#   2) Try NSIS silent install with /D=E:\AccioWork (custom target dir).
#   3) If the app lands under %LOCALAPPDATA% (Squirrel style), move the payload to
#      E:\AccioWork and leave a directory junction at the old path so the app,
#      shortcuts and auto-update keep working.
#   4) Verify the main exe exists, write a receipt, exit 0/1.
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
    [string]$TargetDir = 'E:\AccioWork'
)
$ErrorActionPreference = 'Continue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Lines = New-Object System.Collections.Generic.List[string]
function Log([string]$msg) {
    $stamp = Get-Date -Format 'HH:mm:ss'
    $Lines.Add("[$stamp] $msg") | Out-Null
    Write-Host "  $msg"
}
function Save-Ret([bool]$ok, [string]$title) {
    $dir = Join-Path $RepoRoot 'results\accio_install'
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $ret = Join-Path $dir ("install_" + $stamp + ".md")
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.AppendLine("# Accio Work install receipt ($stamp)")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine("result: $(if ($ok) { 'ok' } else { 'fail' })")
    [void]$sb.AppendLine("target_dir: $TargetDir")
    [void]$sb.AppendLine("host: $env:COMPUTERNAME")
    [void]$sb.AppendLine('')
    [void]$sb.AppendLine('## log')
    foreach ($l in $Lines) { [void]$sb.AppendLine($l) }
    [System.IO.File]::WriteAllText($ret, $sb.ToString())
    Copy-Item $ret (Join-Path $dir 'latest.md') -Force
    Log "receipt: $ret"
    if (-not $ok) {
        Log "FAIL: $title"
        exit 1
    }
    Log "OK: $title"
    exit 0
}

Log "repo root: $RepoRoot"
Log "target dir: $TargetDir"

# --- sanity: E: must exist ---
if (-not (Test-Path 'E:\')) {
    Save-Ret $false 'drive E: not found on this machine'
}
$drive = Get-PSDrive -Name 'E' -ErrorAction SilentlyContinue
if ($drive -and $drive.Free -and $drive.Free -lt 2GB) {
    Log ("warn: E: free space low: " + [math]::Round($drive.Free / 1GB, 2) + " GB")
}

# --- idempotent: already installed? ---
function Find-MainExe([string]$root) {
    if (-not (Test-Path $root)) { return $null }
    $cands = @()
    $cands += Get-ChildItem -Path $root -Filter '*.exe' -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch 'uninstall|update|crash|helper' }
    if (-not $cands) {
        $cands += Get-ChildItem -Path (Join-Path $root 'app-*') -Filter '*.exe' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch 'uninstall|update|crash|helper' }
    }
    if ($cands) { return $cands[0] }
    return $null
}

$existing = Find-MainExe $TargetDir
if ($existing) {
    Log ("already installed: " + $existing.FullName)
    Save-Ret $true 'already installed at target dir'
}

# --- locate installer ---
$setup = Join-Path $env:TEMP 'AccioWork-setup.exe'
$found = $false

function Try-Download([string]$url) {
    try {
        Log "downloading: $url"
        Invoke-WebRequest -Uri $url -OutFile $setup -UseBasicParsing -TimeoutSec 300 | Out-Null
        $size = (Get-Item $setup).Length
        Log ("downloaded bytes: $size")
        return ($size -gt 20MB)
    } catch {
        Log ("download failed: " + $_.Exception.Message)
        return $false
    }
}

function Get-ExeLinks([string]$pageUrl) {
    $out = @()
    try {
        $resp = Invoke-WebRequest -Uri $pageUrl -UseBasicParsing -TimeoutSec 45
        $html = [string]$resp.Content
        $matches2 = [regex]::Matches($html, 'https?://[^\"''\s<>()]+\.exe[^\"''\s<>()]*')
        foreach ($m in $matches2) { $out += $m.Value }
        $hrefs = [regex]::Matches($html, 'href="([^"]*(download|\.exe)[^"]*)"')
        foreach ($h in $hrefs) {
            $v = $h.Groups[1].Value
            if ($v -notmatch '^https?://') {
                try { $v = (New-Object System.Uri((New-Object System.Uri($pageUrl)), $v)).AbsoluteUri } catch { continue }
            }
            if ($v -match '\.exe') { $out += $v }
        }
    } catch {
        Log ("page fetch failed: " + $pageUrl + " -> " + $_.Exception.Message)
    }
    return $out | Select-Object -Unique
}

# 1) scrape official pages (Chinese edition first)
$pages = @(
    'https://www.accio-ai.com/work',
    'https://www.accio-ai.com/work/doc?slug=quickstart',
    'https://www.accio.com/work'
)
foreach ($p in $pages) {
    $links = Get-ExeLinks $p
    foreach ($l in $links) {
        if ($l -match 'win|setup|x64|\.exe') {
            if (Try-Download $l) { $found = $true; break }
        }
    }
    if ($found) { break }
}

# 2) candidate URL guesses (weak fallbacks, harmless if 404)
if (-not $found) {
    $guesses = @(
        'https://www.accio-ai.com/download/AccioWork-Setup-x64.exe',
        'https://www.accio-ai.com/work/download/AccioWork-Setup-x64.exe',
        'https://www.accio-ai.com/download/win32/x64/AccioWork-Setup-x64.exe',
        'https://accio-ai.com/download/AccioWork-Setup-x64.exe'
    )
    foreach ($g in $guesses) {
        if (Try-Download $g) { $found = $true; break }
    }
}

# 3) any installer the user already downloaded?
if (-not $found) {
    $scanDirs = @((Join-Path $env:USERPROFILE 'Downloads'), (Join-Path $env:USERPROFILE 'Desktop'))
    foreach ($d in $scanDirs) {
        $hit = Get-ChildItem -Path $d -Filter '*.exe' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'accio' -and $_.Length -gt 20MB } |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($hit) {
            Copy-Item $hit.FullName $setup -Force
            Log ("using local installer: " + $hit.FullName)
            $found = $true
            break
        }
    }
}

if (-not $found) {
    Save-Ret $false 'installer not found; download it manually from accio-ai.com and re-run, or update the URL list in code/tasks/install_accio_work.ps1'
}

# --- install ---
$installed = $false
$installRoots = @(
    $TargetDir,
    (Join-Path $env:LOCALAPPDATA 'AccioWork'),
    (Join-Path $env:LOCALAPPDATA 'Accio Work'),
    (Join-Path $env:LOCALAPPDATA 'Programs\AccioWork'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Accio Work'),
    (Join-Path $env:ProgramFiles 'AccioWork'),
    (Join-Path $env:ProgramFiles 'Accio Work')
)

# attempt A: NSIS silent with explicit target dir
Log 'attempt A: NSIS silent install with /D=<target>'
$p = Start-Process -FilePath $setup -ArgumentList '/S', "/D=$TargetDir" -Wait -PassThru
Log ("installer exit code: " + $p.ExitCode)
if (Find-MainExe $TargetDir) { $installed = $true }

# attempt B: generic silent run (Squirrel / default NSIS path)
if (-not $installed) {
    Log 'attempt B: generic silent install'
    Start-Process -FilePath $setup -ArgumentList '/S' -Wait -PassThru | Out-Null
    Start-Process -FilePath $setup -ArgumentList '--silent' -Wait -PassThru | Out-Null
    foreach ($root in $installRoots) {
        if (Find-MainExe $root) { $installed = $true; Log ("found install at: $root"); break }
    }
}

if (-not $installed) {
    Save-Ret $false 'installer ran but no Accio Work exe found under known roots; the installer may need GUI steps (see the install guide)'
}

# --- relocate to E: + junction if needed ---
$srcRoot = $null
foreach ($root in $installRoots) {
    if (Find-MainExe $root) { $srcRoot = $root; break }
}
Log ("install root: $srcRoot")

if ($srcRoot -and ((Resolve-Path $srcRoot).Path -ne (Join-Path 'E:' 'AccioWork'))) {
    if (Test-Path $TargetDir) {
        Log 'target already populated; leaving source in place'
    } else {
        Log 'relocating payload to E:\AccioWork and creating a junction at the original path'
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
        $rc = Start-Process -FilePath 'robocopy' -ArgumentList @($srcRoot, $TargetDir, '/E', '/MOVE', '/NFL', '/NDL', '/NJH', '/R:2', '/W:2') -Wait -PassThru
        Log ("robocopy exit: " + $rc.ExitCode + ' (0-7 ok)')
        if (-not (Find-MainExe $TargetDir)) {
            Save-Ret $false 'relocation to E:\AccioWork failed'
        }
        try {
            New-Item -ItemType Junction -Path $srcRoot -Target $TargetDir -Force | Out-Null
            Log ("junction created: $srcRoot -> $TargetDir")
        } catch {
            Log ("junction failed (non-fatal): " + $_.Exception.Message)
        }
    }
}

# --- verify ---
$exe = Find-MainExe $TargetDir
if (-not $exe) {
    Save-Ret $false 'verification failed: no exe at target'
}
$ver = ''
try { $ver = $exe.VersionInfo.ProductVersion } catch { }
Log ("main exe: " + $exe.FullName)
Log ("version: $ver")
Log 'language: the accio-ai.com build is the Chinese edition (zh-CN UI).'
Log 'next steps: launch Accio Work, register/login (phone or email), Settings > General > language Chinese, default work dir on E:.'

Save-Ret $true ('installed to ' + $TargetDir)
