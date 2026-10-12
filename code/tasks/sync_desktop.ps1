# sync_desktop.ps1 - round 2 task, runs ON THE USER MACHINE via watch.ps1.
# Copies the whole deliverable tree (last round case pack + new Accio material)
# into a NEW timestamped folder on the Desktop, then writes a receipt under
# results/ so the watcher pushes it back to the branch.
# ASCII-only on purpose (Windows PowerShell 5.1 decodes .ps1 as ANSI/GBK).
# Exit 0 = ok, 1 = failed.

$ErrorActionPreference = 'Continue'
Set-Location (Join-Path $PSScriptRoot '..\..')   # repo root (this file lives in code\tasks\)

$fail = 0

$desk = [Environment]::GetFolderPath('Desktop')
if (-not $desk -or -not (Test-Path -LiteralPath $desk)) {
    Write-Output '[FAIL] desktop folder not found'
    exit 1
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$dest = Join-Path $desk ('skills1-deliverables-' + $stamp)
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Write-Output ('== desktop sync target: ' + $dest)

if (-not (Test-Path -LiteralPath '.\deliverable')) {
    Write-Output '[FAIL] deliverable\ not found in the repo'
    exit 1
}

# robocopy exit codes 0-7 are success (files copied / no change / extras), >= 8 is failure
& robocopy 'deliverable' (Join-Path $dest 'deliverable') /E /NFL /NDL /NJH /NJS | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) {
    Write-Output ('[FAIL] robocopy deliverable exit ' + $rc)
    $fail = 1
} else {
    Write-Output ('== deliverable tree copied (robocopy exit ' + $rc + ')')
}

foreach ($extra in @('README.md', 'CHANGELOG.md')) {
    if (Test-Path -LiteralPath $extra) {
        Copy-Item -LiteralPath $extra -Destination $dest -Force
    }
}

# receipt in the repo: the watcher auto-pushes it back to the branch
$repDir = '.\results\desktop_sync'
New-Item -ItemType Directory -Force -Path $repDir | Out-Null
$rep = Join-Path $repDir ('sync_' + $stamp + '.md')
$files = @(Get-ChildItem -LiteralPath (Join-Path $dest 'deliverable') -Recurse -File -ErrorAction SilentlyContinue)
$lines = @()
$lines += '# desktop sync receipt'
$lines += ''
$lines += ('- host: ' + $env:COMPUTERNAME)
$lines += ('- time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$lines += ('- dest: ' + $dest)
$lines += ('- files: ' + $files.Count)
$lines += ''
$lines += '## file list'
foreach ($f in $files) {
    $lines += ('- ' + $f.FullName + '  (' + $f.Length + ' B)')
}
Set-Content -LiteralPath $rep -Value $lines -Encoding UTF8
Write-Output ('== receipt: ' + $rep)

Write-Output ('== copied ' + $files.Count + ' file(s) to ' + $dest)
if ($files.Count -lt 15) {
    Write-Output '[FAIL] expected at least 15 deliverable files'
    $fail = 1
}

if ($fail -eq 0) { Write-Output '== desktop sync task passed' }
exit $fail
