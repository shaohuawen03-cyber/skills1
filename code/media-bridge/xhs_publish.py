#!/usr/bin/env python3
# xhs_publish.py - Xiaohongshu channel status wrapper. XHS has no personal
# content API, so publishing rides on social-auto-upload (browser
# automation with locally stored cookies - low risk, your own logged-in
# session). This script reports what is installed and what is still
# missing; the actual publish calls go through the `sau` CLI:
#   venv\Scripts\sau.exe xiaohongshu login --account <name>  (once, scan QR)
#   venv\Scripts\sau.exe xiaohongshu ...            (after cookies exist)
# ASCII-only.

import glob
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
SAU = os.path.join(BASE, 'social-auto-upload')
VENV_PY = os.path.join(BASE, 'venv', 'Scripts', 'python.exe')
SAU_EXE = os.path.join(BASE, 'venv', 'Scripts', 'sau.exe')


def main():
    print('== xhs channel status ==')
    ok = True
    if os.path.isdir(os.path.join(SAU, '.git')) or os.path.isdir(SAU):
        print('social-auto-upload: cloned at ' + SAU)
    else:
        print('social-auto-upload: MISSING')
        ok = False
    print('venv python: ' + ('yes' if os.path.exists(VENV_PY) else 'no'))
    print('sau CLI: ' + ('installed' if os.path.exists(SAU_EXE)
                         else 'not installed yet (follow-up round)'))
    cookies = (glob.glob(os.path.join(BASE, 'cookies', '*xhs*'))
               + glob.glob(os.path.join(SAU, 'cookies', '*xhs*'))
               + glob.glob(os.path.join(BASE, 'conf', '*xhs*')))
    if cookies:
        print('cookies: ' + ', '.join(cookies[:5]))
    else:
        print('cookies: none yet - once sau is installed, run '
              '"sau xiaohongshu login --account <name>" and scan the QR with '
              'the XHS app')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
