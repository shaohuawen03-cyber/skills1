#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check a subtitle-by-line video against its schedule, using the video's own audio.

  python3 verify_line_video.py --video out/video.mp4 --schedule out/schedule.json

Passes when every subtitle window contains speech and every gap after a clip is quiet.
Exit code 0 = pass, 2 = at least one failure.
"""
import argparse
import json
import subprocess
import sys

import imageio_ffmpeg
import numpy as np

FF = imageio_ffmpeg.get_ffmpeg_exe()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--video', required=True)
    ap.add_argument('--schedule', required=True)
    ap.add_argument('--speech-rms', type=float, default=0.01)
    ap.add_argument('--quiet-rms', type=float, default=0.01)
    a = ap.parse_args()

    p = subprocess.run([FF, '-v', 'error', '-i', a.video, '-vn', '-ac', '1', '-ar', '16000',
                        '-f', 'f32le', '-'], stdout=subprocess.PIPE, check=True)
    x = np.frombuffer(p.stdout, dtype=np.float32)
    sched = json.load(open(a.schedule, encoding='utf-8'))

    def rms(t0, t1):
        seg = x[int(t0 * 16000):int(t1 * 16000)]
        return float(np.sqrt((seg ** 2).mean())) if len(seg) else 0.0

    no_speech = [(it['text'], round(rms(it['start'], it['start'] + it['dur']), 4))
                 for it in sched if rms(it['start'], it['start'] + it['dur']) < a.speech_rms]
    not_quiet = []
    for it in sched[:-1]:
        g0, g1 = it['start'] + it['dur'] + 0.05, it['start'] + it['dur'] + 0.20
        if rms(g0, g1) > a.quiet_rms:
            not_quiet.append((it['text'], round(rms(g0, g1), 4)))

    print('lines: %d | without speech in their window: %d %s' % (len(sched), len(no_speech), no_speech[:3]))
    print('gaps that are not quiet: %d %s' % (len(not_quiet), not_quiet[:3]))
    print('audio length: %.2f s' % (len(x) / 16000))
    ok = not no_speech and not not_quiet
    print('RESULT:', 'PASS' if ok else 'FAIL')
    sys.exit(0 if ok else 2)


if __name__ == '__main__':
    main()
