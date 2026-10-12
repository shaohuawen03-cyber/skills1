# harness-anything - vendored install (yb2460/harness-anything @ master 2026-09-26)

Upstream: https://github.com/yb2460/harness-anything (MIT).
Only the installable package is vendored here: `cli_anything/` (wps + zotero)
plus setup.py and docs. The WPS/ showcase assets were NOT vendored (15MB).

## What it gives us
`cli-anything-wps` - CLI harness that drives WPS Office through COM
(KWPS/KET/KWPP.Application) to create REAL, editable DOCX/XLSX/PPTX files.

## Offline install on a Windows machine (Python 3.12, no internet needed)

    py -3.12 -m pip install --no-index --find-links <repo>\skills\harness-anything\vendor_wheels <repo>\skills\harness-anything

If `py` is missing use the full python.exe path. Verify:

    py -3.12 -m cli_anything.wps --help

(entry point also installed as Scripts\cli-anything-wps.exe when Scripts is on PATH)

## Smoke test (impress -> editable pptx)

    cd <workdir>
    py -3.12 -m cli_anything.wps document new --type impress --name "test" -o proj.json
    py -3.12 -m cli_anything.wps --project proj.json impress add-slide -t "Title" -c "Body text"
    py -3.12 -m cli_anything.wps --project proj.json export render test.pptx -p pptx

Requires WPS installed with COM ProgIDs registered. NOTE: COM automation may
fail with E_FAIL when launched from a non-interactive session (sshd /
scheduled-task headless context) - run the generator through an INTERACTIVE
scheduled task (same pattern as agyrelaunch) if that happens.
