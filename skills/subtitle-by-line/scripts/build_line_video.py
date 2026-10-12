#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""subtitle-by-line: build a narrated video whose subtitles are exact BY CONSTRUCTION.

Input (all in one folder, --work):
  lines.json     ["字幕行1", "字幕行2", ...]     one subtitle line per TTS clip
  clip_01.mp3 .. clip_NN.mp3                    the TTS audio of line i (same order)
  scene images   (--scenes, 1..n jpg/png)        shown evenly across the video

Output (--out-dir):
  narration.mp3       clips joined in order, a fixed pause after each one
  schedule.json       [{start,end,text,clip,dur}] in video time
  subtitles.srt
  video.mp4           1080x1920 25 fps, burned subtitles, Ken Burns scenes

Rules that make it exact:
  * subtitle i starts when clip i starts and lasts exactly as long as clip i
    (a line shorter than --min-show may stretch into the pause, never into the next line);
  * durations come from DECODED samples, not the MP3 header (headers drift ~0.04 s/clip);
  * the clip text must match lines.json (the agent writes both from the same list).

Usage:
  python3 build_line_video.py --work <dir> --out-dir <dir> \
      --scenes a.jpg b.jpg [--pause 0.25] [--delay 0.3] [--fps 25] [--min-show 0.8]
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FF = shutil.which('ffmpeg') or imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FONT_CANDIDATES = [
    os.environ.get('SUB_FONT', ''),
    '/tmp/font/NotoSansSC.ttf',
    'C:/Windows/Fonts/msyh.ttc',
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
]


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        sys.stderr.write(p.stdout.decode('utf-8', 'replace')[-2000:])
        raise SystemExit('ffmpeg failed: ' + ' '.join(cmd[:4]))


def clip_seconds(path):
    """true duration from decoded samples (mono 24 kHz s16le)."""
    p = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', '24000',
                        '-f', 's16le', '-'], stdout=subprocess.PIPE, check=True)
    return len(p.stdout) / 2 / 24000


def font_path():
    for p in FONT_CANDIDATES:
        if p and os.path.exists(p):
            return p
    raise SystemExit('no CJK font found - set SUB_FONT=/path/to/NotoSansSC.ttf')


def make_sub(text, dst, font):
    """one subtitle card; '\n' in the text starts a new row (rows share one timing)."""
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    f = ImageFont.truetype(font, 54)
    rows = text.split('\n')
    y = int(H * 0.72) - (len(rows) - 1) * 42
    for row in rows:
        bbox = d.textbbox((0, 0), row, font=f, stroke_width=4)
        x = (W - (bbox[2] - bbox[0])) // 2
        d.text((x, y), row, font=f, fill=(255, 226, 140, 255),
               stroke_width=4, stroke_fill=(0, 0, 0, 255))
        y += 84
    canvas.save(dst)


def make_bg(src, dst):
    im = Image.open(src).convert('RGB')
    tw, th = 1296, 2304
    r = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l, t = (im.width - tw) // 2, (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(dst, quality=92)


def build(work, out_dir, scenes, pause, delay, fps, min_show):
    lines = json.load(open(os.path.join(work, 'lines.json'), encoding='utf-8'))
    clips = [os.path.join(work, 'clip_%02d.mp3' % (i + 1)) for i in range(len(lines))]
    for c in clips:
        if not os.path.exists(c):
            raise SystemExit('missing clip: ' + c)
    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, '_tmp')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)

    durs = [clip_seconds(c) for c in clips]
    sched, t = [], delay
    for i, (text, d) in enumerate(zip(lines, durs)):
        start = t
        end = start + max(d, min_show)
        t = start + d + pause
        sched.append({'start': round(start, 3), 'end': round(end, 3), 'text': text,
                      'clip': os.path.basename(clips[i]), 'dur': round(d, 3)})
    for k in range(len(sched) - 1):
        sched[k]['end'] = min(sched[k]['end'], round(sched[k + 1]['start'] - 0.02, 3))
    total = t + 0.5
    # ---- narration: each clip + exact pause, joined ----
    narr = os.path.join(out_dir, 'narration.mp3')
    cmd = [FF, '-y']
    for c in clips:
        cmd += ['-i', c]
    fc = ''.join(f'[{i}:a]aresample=24000,apad=pad_dur={pause},'
                 f'atrim=0:{d + pause:.4f},asetpts=PTS-STARTPTS[a{i}];'
                 for i, d in enumerate(durs))
    fc += ''.join(f'[a{i}]' for i in range(len(clips))) + f'concat=n={len(clips)}:v=0:a=1[n]'
    run(cmd + ['-filter_complex', fc, '-map', '[n]', '-c:a', 'libmp3lame', '-b:a', '128k', narr])

    # ---- picture: scenes evenly split over the full length ----
    per = total / len(scenes)
    segs = []
    for i, img in enumerate(scenes):
        bg = os.path.join(tmp, f'bg{i}.png')
        make_bg(img, bg)
        nfr = max(1, round(per * fps))
        zin = (i % 2 == 0)
        zexpr = 'min(zoom+0.0009,1.12)' if zin else f'1.12-0.12*on/{nfr}'
        fc2 = (f"[0:v]scale=1296:2304,zoompan=z='{zexpr}':d=1:x='iw/2-(iw/zoom/2)'"
               f":y='ih/2-(ih/zoom/2)':s=1080x1920:fps={fps},format=yuv420p[out]")
        seg = os.path.join(tmp, f'seg{i}.mp4')
        run([FF, '-y', '-loop', '1', '-framerate', str(fps), '-t', f'{per:.3f}', '-i', bg,
             '-filter_complex', fc2, '-map', '[out]', '-frames:v', str(nfr), '-r', str(fps),
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-an', seg])
        segs.append(seg)
    lst = os.path.join(tmp, 'list.txt')
    with open(lst, 'w') as f:
        for s in segs:
            f.write("file '" + s + "'\n")
    silent = os.path.join(tmp, 'silent.mp4')
    run([FF, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])

    # ---- subtitles burned as PNG overlays (no drawtext in imageio-ffmpeg builds) ----
    font = font_path()
    cmd = [FF, '-y', '-i', silent, '-i', narr]
    fc3, prev = '', '0:v'
    for j, it in enumerate(sched):
        sp = os.path.join(tmp, f'sub{j}.png')
        make_sub(it['text'], sp, font)
        cmd += ['-i', sp]
        fc3 += f"[{prev}][{j + 2}:v]overlay=0:0:enable='between(t,{it['start']},{it['end']})'[v{j}];"
        prev = f'v{j}'
    ms = int(delay * 1000)
    fc3 += f'[1:a]adelay={ms}|{ms}[a]'
    out = os.path.join(out_dir, 'video.mp4')
    cmd += ['-filter_complex', fc3, '-map', f'[{prev}]', '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-c:a', 'aac', '-b:a', '128k',
            '-t', f'{total:.3f}', '-movflags', '+faststart', out]
    run(cmd)

    with open(os.path.join(out_dir, 'schedule.json'), 'w', encoding='utf-8') as f:
        json.dump(sched, f, ensure_ascii=False, indent=1)
    write_srt(sched, os.path.join(out_dir, 'subtitles.srt'))
    shutil.rmtree(tmp, ignore_errors=True)
    return sched, total


def write_srt(items, path):
    def ts(x):
        h, rem = divmod(int(round(x * 1000)), 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return '%02d:%02d:%02d,%03d' % (h, m, s, ms)
    with open(path, 'w', encoding='utf-8') as f:
        for i, it in enumerate(items, 1):
            f.write('%d\n%s --> %s\n%s\n\n' % (i, ts(it['start']), ts(it['end']), it['text']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    ap.add_argument('--out-dir', required=True)
    ap.add_argument('--scenes', nargs='+', required=True)
    ap.add_argument('--pause', type=float, default=0.25)
    ap.add_argument('--delay', type=float, default=0.3)
    ap.add_argument('--fps', type=int, default=25)
    ap.add_argument('--min-show', type=float, default=0.8)
    a = ap.parse_args()
    # ffmpeg resolves paths inside concat lists relative to the list file: use absolute paths
    sched, total = build(os.path.abspath(a.work), os.path.abspath(a.out_dir),
                         [os.path.abspath(s) for s in a.scenes], a.pause, a.delay, a.fps, a.min_show)
    print('wrote %s: %d lines, %.2f s' % (a.out_dir, len(sched), total))


if __name__ == '__main__':
    main()
