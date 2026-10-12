# sync_desktop.ps1 - round 2 task, runs ON THE USER MACHINE via watch.ps1.
# Keeps exactly ONE up-to-date copy of deliverable/ on the Desktop:
#   * fixed folder name: Desktop\skills1-deliverables   (no timestamped copies)
#   * if the deliverable tree hash is unchanged since the last sync AND the
#     folder exists, nothing is copied (no churn when there are no updates)
#   * if it changed, robocopy /MIR overwrites in place (removed files are
#     deleted from the copy, so the folder always mirrors deliverable/)
#   * old timestamped 'skills1-deliverables-*' folders from earlier versions of
#     this task are deleted (keep only the newest single copy)
# Receipt: results/desktop_sync/latest.md (ONE file, overwritten each run).
# ASCII-only on purpose (Windows PowerShell 5.1 decodes .ps1 as ANSI/GBK).
# Exit 0 = ok (or nothing to do), 1 = failed.

$ErrorActionPreference = 'Continue'
Set-Location (Join-Path $PSScriptRoot '..\..')   # repo root (this file lives in code\tasks\)

$fail = 0

$desk = [Environment]::GetFolderPath('Desktop')
if (-not $desk -or -not (Test-Path -LiteralPath $desk)) {
    Write-Output '[FAIL] desktop folder not found'
    exit 1
}

$dest = Join-Path $desk 'skills1-deliverables'
$src = '.\deliverable'

if (-not (Test-Path -LiteralPath $src)) {
    Write-Output '[FAIL] deliverable\ not found in the repo'
    exit 1
}

# ---- content hash of the deliverable tree (path + size + mtime) -------------
$hasher = [System.Security.Cryptography.SHA256]::Create()
$sb = New-Object System.Text.StringBuilder
foreach ($f in @(Get-ChildItem -LiteralPath $src -Recurse -File | Sort-Object FullName)) {
    $rel = $f.FullName.Substring((Resolve-Path $src).Path.Length)
    [void]$sb.AppendLine(('{0}|{1}|{2}' -f $rel, $f.Length, $f.LastWriteTimeUtc.Ticks))
}
$treeHash = [BitConverter]::ToString($hasher.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($sb.ToString()))).Replace('-', '').ToLower()
$hasher.Dispose()

$stateFile = '.\results\desktop_sync\state.txt'
$lastHash = ''
if (Test-Path -LiteralPath $stateFile) {
    $lastHash = (Get-Content -LiteralPath $stateFile -Raw).Trim()
}

$destOk = (Test-Path -LiteralPath $dest) -and (Test-Path -LiteralPath (Join-Path $dest 'deliverable'))

if ($destOk -and ($lastHash -eq $treeHash)) {
    Write-Output ('== desktop copy already up to date (hash ' + $treeHash.Substring(0, 12) + ') - nothing copied')
} else {
    Write-Output ('== desktop sync target: ' + $dest)
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    # /MIR = overwrite in place + delete files that no longer exist in source
    & robocopy 'deliverable' (Join-Path $dest 'deliverable') /MIR /NFL /NDL /NJH /NJS | Out-Null
    $rc = $LASTEXITCODE
    if ($rc -ge 8) {
        Write-Output ('[FAIL] robocopy deliverable exit ' + $rc)
        $fail = 1
    } else {
        Write-Output ('== deliverable tree mirrored (robocopy exit ' + $rc + ')')
    }
    foreach ($extra in @('README.md', 'CHANGELOG.md')) {
        if (Test-Path -LiteralPath $extra) {
            Copy-Item -LiteralPath $extra -Destination $dest -Force
        }
    }
}

# ---- remove old timestamped copies (keep only the single folder above) -----
foreach ($old in @(Get-ChildItem -LiteralPath $desk -Directory -Filter 'skills1-deliverables-*' -ErrorAction SilentlyContinue)) {
    Write-Output ('== removing old copy: ' + $old.FullName)
    Remove-Item -LiteralPath $old.FullName -Recurse -Force -ErrorAction SilentlyContinue
}

# ---- bookkeeping -----------------------------------------------------------
New-Item -ItemType Directory -Force -Path '.\results\desktop_sync' | Out-Null
Set-Content -LiteralPath $stateFile -Value $treeHash -Encoding ASCII

$files = @(Get-ChildItem -LiteralPath (Join-Path $dest 'deliverable') -Recurse -File -ErrorAction SilentlyContinue)
$rep = '.\results\desktop_sync\latest.md'
$lines = @()
$lines += '# desktop sync receipt (latest)'
$lines += ''
$lines += ('- host: ' + $env:COMPUTERNAME)
$lines += ('- time: ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
$lines += ('- dest: ' + $dest)
$lines += ('- files: ' + $files.Count)
$lines += ('- tree_hash: ' + $treeHash)
$lines += ('- action: ' + $(if ($destOk -and ($lastHash -eq $treeHash)) { 'skipped (unchanged)' } else { 'mirrored' }))
$lines += ''
$lines += '## file list'
foreach ($f in $files) {
    $lines += ('- ' + $f.FullName + '  (' + $f.Length + ' B)')
}
Set-Content -LiteralPath $rep -Value $lines -Encoding UTF8
Write-Output ('== receipt: ' + $rep)

if ($files.Count -lt 15) {
    Write-Output '[FAIL] expected at least 15 deliverable files'
    $fail = 1
}

if ($fail -eq 0) { Write-Output '== desktop sync task passed' }
exit $fail
