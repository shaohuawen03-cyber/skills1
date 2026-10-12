# run_tg_bridge.ps1 - keeps tg_bridge.py alive. Registered as the
# media-bridge-tg scheduled task (at logon). Restarts the bridge after
# 30s if it ever exits (proxy down, laptop sleep-wake, etc).
# ASCII-only.

$ErrorActionPreference = 'Continue'
$dir = $PSScriptRoot
$py = Join-Path $dir 'venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $py)) { $py = 'python' }
while ($true) {
    try { & $py -X utf8 (Join-Path $dir 'tg_bridge.py') } catch { }
    Start-Sleep -Seconds 30
}
