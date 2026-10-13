# collect_upload.ps1 - runs ON THE USER MACHINE via watch.ps1 (manifest round 7).
# Finds the AWB core-rights PDF the user attached in WeChat (or any *AWB*.pdf in
# the usual folders), copies it into the repo under uploads\, extracts its text
# when a Python PDF library exists, and writes a receipt. The verdict commit
# pushes uploads\ and results\collect_upload\ back to the branch, so the agent
# can read them without any extra step from the user.
# ASCII-only on purpose (Windows PowerShell 5.1 decodes .ps1 as ANSI/GBK).
# Exit 0 = copied, 1 = not found / copy failed.

$ErrorActionPreference = 'Continue'
Set-Location (Join-Path $PSScriptRoot '..\..')   # repo root

$fail = 0
$wechat = 'E:\' + [char]0x5FAE + [char]0x4FE1    # WeChat file folder, built from code points
$roots = @(
    (Join-Path $wechat 'xwechat_files'),
    (Join-Path $env:USERPROFILE 'Desktop'),
    (Join-Path $env:USERPROFILE 'Downloads'),
    (Join-Path $env:USERPROFILE 'Documents'),
    (Join-Path $env:USERPROFILE 'Desktop\skills1-deliverables'),
    (Join-Path (Get-Location) 'uploads')
)

$found = @()
foreach ($r in $roots) {
    if (-not (Test-Path -LiteralPath $r)) { continue }
    $found += @(Get-ChildItem -LiteralPath $r -Filter '*AWB*.pdf' -Recurse -File -ErrorAction SilentlyContinue)
}
$found = @($found | Sort-Object LastWriteTime -Descending)

$receipt = Join-Path (Get-Location) 'results\collect_upload'
New-Item -ItemType Directory -Force -Path $receipt | Out-Null
$lines = @()
$lines += '# collect_upload receipt (latest)'
$lines += ''
$lines += ('- time: ' + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))
$lines += ('- host: ' + $env:COMPUTERNAME)
$lines += ('- candidates: ' + $found.Count)

if ($found.Count -eq 0) {
    $lines += '- result: NOT FOUND (no *AWB*.pdf under the WeChat file folder, Desktop, Downloads, Documents)'
    $lines | Out-File -LiteralPath (Join-Path $receipt 'latest.md') -Encoding UTF8
    Write-Output '[FAIL] collect_upload: no *AWB*.pdf found'
    exit 1
}

$src = $found[0]
$dstDir = Join-Path (Get-Location) 'uploads'
New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
$dst = Join-Path $dstDir 'AWB_core_rights_script.pdf'
try {
    Copy-Item -LiteralPath $src.FullName -Destination $dst -Force
    $hash = (Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash
    $lines += ('- source: ' + $src.FullName)
    $lines += ('- copied to: uploads\AWB_core_rights_script.pdf (' + $src.Length + ' B)')
    $lines += ('- sha256: ' + $hash)
    Write-Output ('== copied ' + $src.FullName + ' -> uploads\AWB_core_rights_script.pdf')
} catch {
    $lines += ('- result: COPY FAILED ' + $_.Exception.Message)
    $lines | Out-File -LiteralPath (Join-Path $receipt 'latest.md') -Encoding UTF8
    Write-Output ('[FAIL] copy failed: ' + $_.Exception.Message)
    exit 1
}

# text extraction (optional): needs python with pypdf or PyMuPDF on PATH
$py = Join-Path $receipt 'extract_text.py'
$pyCode = @'
import sys
path, out = sys.argv[1], sys.argv[2]
text = None
try:
    import fitz  # PyMuPDF
    doc = fitz.open(path)
    text = "\n\n".join(page.get_text() for page in doc)
except Exception:
    try:
        from pypdf import PdfReader
        text = "\n\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    except Exception as e:
        print("no PDF text library: " + str(e))
if text is not None:
    open(out, "w", encoding="utf-8").write(text)
    print("text chars: %d" % len(text))
'@
$pyCode | Out-File -LiteralPath $py -Encoding UTF8
$txtOut = Join-Path $receipt 'awb_text.txt'
$pyRes = ''
try {
    $pyRes = (& python -X utf8 $py $dst $txtOut 2>&1 | Out-String).Trim()
} catch {
    $pyRes = 'python not runnable: ' + $_.Exception.Message
}
if (Test-Path -LiteralPath $txtOut) {
    $lines += ('- text: results\collect_upload\awb_text.txt (' + $pyRes + ')')
} else {
    $lines += ('- text: not extracted (' + $pyRes + ')')
}

$lines | Out-File -LiteralPath (Join-Path $receipt 'latest.md') -Encoding UTF8
Write-Output '== collect_upload ok'
exit $fail
