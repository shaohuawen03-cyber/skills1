#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Folktale video v3 - subtitles by construction (no alignment algorithm).

Each subtitle line is its own TTS clip (deliverable/cases/02_folktale_video/tts_lines/line_NN.mp3,
voice-00). Clips are concatenated in order with a fixed pause after each one. A line's subtitle
starts where its clip starts and stays on screen for exactly the clip's length, so text and
voice match by construction. Scene timing is unchanged from build_folktale_video.py.

Writes:
  folktale_narration.mp3          - the joined narration (38 clips + pauses)
  folktale_schedule.json          - [{start,end,text,clip,dur}] in video time
  folktale_story_video.srt
  folktale_story_video.mp4        - 130 s, 1080x1920, 25 fps, burned subtitles
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'code'))
import build_folktale_video as V  # noqa: E402  (SEGS, make_bg, make_sub, FFMPEG, run, CASE, WORK)
import align_subtitles as A  # noqa: E402  (auto_lines only)

CLIP_DIR = os.path.join(V.CASE, 'tts_lines')
PAUSE = 0.25        # silence after every clip (seconds)
DELAY = 0.30        # narration starts after this (video time)
MIN_SHOW = 0.80     # minimum on-screen time for very short lines


def probe_dur(path):
    """True duration from decoded samples. The container header of an MP3 is an
    estimate (off by ~0.04 s per clip from encoder padding), which would drift
    the subtitle timeline over 38 clips."""
    p = subprocess.run([V.FFMPEG, '-v', 'error', '-i', path, '-ac', '1', '-ar', '24000',
                        '-f', 's16le', '-'], stdout=subprocess.PIPE, check=True)
    return len(p.stdout) / 2 / 24000


def main():
    script = open(os.path.join(V.CASE, 'narration_script.txt'), encoding='utf-8').read()
    body = script.split('\n\n', 1)[1] if '\n\n' in script else script
    lines = A.auto_lines(body)            # same 38 display lines the clips were made from
    n = len(lines)
    clips = [os.path.join(CLIP_DIR, 'line_%02d.mp3' % (i + 1)) for i in range(n)]
    for c in clips:
        if not os.path.exists(c):
            raise SystemExit('missing clip: ' + c)

    os.makedirs(V.WORK, exist_ok=True)
    durs = [probe_dur(c) for c in clips]

    # ---- timeline (video time) ----
    sched, t = [], DELAY
    for i, (ln, d) in enumerate(zip(lines, durs)):
        start = t
        end = start + max(d, MIN_SHOW)
        t = start + d + PAUSE
        sched.append({'start': round(start, 3), 'end': round(end, 3),
                      'text': ln.replace('\n', ''), 'clip': os.path.basename(clips[i]),
                      'dur': round(d, 3)})
    # no overlaps: a short line may stretch into the pause but never into the next line
    for k in range(len(sched) - 1):
        sched[k]['end'] = min(sched[k]['end'], round(sched[k + 1]['start'] - 0.02, 3))
    total = t
    if total > 130:
        raise SystemExit('narration too long for the 130 s picture: %.2f s' % total)

    # ---- joined narration (exact pauses) ----
    narr = os.path.join(V.CASE, 'folktale_narration.mp3')
    cmd = [V.FFMPEG, '-y']
    for c in clips:
        cmd += ['-i', c]
    fc = ''
    for i, d in enumerate(durs):
        fc += (f'[{i}:a]aresample=24000,apad=pad_dur={PAUSE},'
               f'atrim=0:{d + PAUSE:.4f},asetpts=PTS-STARTPTS[a{i}];')
    fc += ''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[narr]'
    cmd += ['-filter_complex', fc, '-map', '[narr]', '-c:a', 'libmp3lame', '-b:a', '128k', narr]
    V.run(cmd)

    # ---- subtitle files ----
    sched_path = os.path.join(V.CASE, 'folktale_schedule.json')
    with open(sched_path, 'w', encoding='utf-8') as f:
        json.dump(sched, f, ensure_ascii=False, indent=1)
    srt = os.path.join(V.CASE, 'folktale_story_video.srt')
    write_srt(sched, srt)

    # ---- picture (same scenes as v2) ----
    silent = build_silent_picture()

    # ---- burn subtitles + narration ----
    out = V.OUT
    cmd = [V.FFMPEG, '-y', '-i', silent, '-i', narr]
    fc, prev = '', '0:v'
    for j, it in enumerate(sched):
        sp = os.path.join(V.WORK, f'sub{j}.png')
        V.make_sub(it['text'], sp)
        cmd += ['-i', sp]
        fc += f"[{prev}][{j + 2}:v]overlay=0:0:enable='between(t,{it['start']},{it['end']})'[v{j}];"
        prev = f'v{j}'
    fc += f'[1:a]adelay={int(DELAY * 1000)}|{int(DELAY * 1000)}[a]'
    cmd += ['-filter_complex', fc, '-map', f'[{prev}]', '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-c:a', 'aac', '-b:a', '128k',
            '-t', '130', '-movflags', '+faststart', out]
    V.run(cmd)
    print('wrote', out, os.path.getsize(out), 'bytes; narration %.2f s; lines %d' % (total, n))


def write_srt(items, path):
    def ts(x):
        h, rem = divmod(int(round(x * 1000)), 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return '%02d:%02d:%02d,%03d' % (h, m, s, ms)
    with open(path, 'w', encoding='utf-8') as f:
        for i, it in enumerate(items, 1):
            f.write('%d\n%s --> %s\n%s\n\n' % (i, ts(it['start']), ts(it['end']), it['text']))


def build_silent_picture():
    import shutil
    from PIL import Image  # noqa: F401  (make_bg needs PIL)
    shutil.rmtree(V.WORK + '/pic', ignore_errors=True)
    os.makedirs(V.WORK + '/pic', exist_ok=True)
    seg_files = []
    for i, (img, dur, zin) in enumerate(V.SEGS):
        bg = os.path.join(V.WORK, 'pic', f'bg{i}.png')
        V.make_bg(os.path.join(V.CASE, img), bg)
        nfr = dur * V.FPS
        zexpr = 'min(zoom+0.0009,1.12)' if zin else f'1.12-0.12*on/{nfr}'
        fc = (f"[0:v]scale=1296:2304,zoompan=z='{zexpr}':d=1:x='iw/2-(iw/zoom/2)'"
              f":y='ih/2-(ih/zoom/2)':s=1080x1920:fps={V.FPS},format=yuv420p[out]")
        seg = os.path.join(V.WORK, 'pic', f'seg{i}.mp4')
        V.run([V.FFMPEG, '-y', '-loop', '1', '-framerate', str(V.FPS), '-t', str(dur), '-i', bg,
               '-filter_complex', fc, '-map', '[out]', '-frames:v', str(nfr), '-r', str(V.FPS),
               '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-an', seg])
        seg_files.append(seg)
    lst = os.path.join(V.WORK, 'pic', 'list.txt')
    with open(lst, 'w') as f:
        for s in seg_files:
            f.write("file '" + s + "'\n")
    silent = os.path.join(V.WORK, 'pic', 'silent.mp4')
    V.run([V.FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])
    return silent


if __name__ == '__main__':
    main()
