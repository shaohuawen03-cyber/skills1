#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""subtitle-align: pause-aware forced alignment of narration audio + subtitle
lines. No ASR needed - the narration TEXT is known, so we map each subtitle
line to its span in the script (difflib, in order), distribute characters
across the speech/silence segments detected by ffmpeg silencedetect, and snap
line boundaries to pauses. Output: schedule JSON [{start,end,text}] (+ SRT).

Usage:
  python3 code/align_subtitles.py --audio narr.mp3 --text script.txt \
      --lines lines.json --stretch 1.0 --delay 0.3 --out schedule.json

  lines.json: ["字幕行1", "字幕行2", ...]   (display order)
  stretch:    final_audio_dur / natural_dur (the atempo factor inverted)
  delay:      audio start offset inside the video (seconds)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import difflib


def ffmpeg_exe():
    return shutil.which('ffmpeg') or __import__('imageio_ffmpeg').get_ffmpeg_exe()


def get_duration(audio):
    p = subprocess.run([ffmpeg_exe(), '-i', audio], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', p.stdout.decode('utf-8', 'replace'))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def detect_silences(audio, noise='-35dB', min_dur=0.35):
    """Return [(sil_start, sil_end), ...] in seconds."""
    p = subprocess.run([ffmpeg_exe(), '-i', audio, '-af',
                        f'silencedetect=noise={noise}:d={min_dur}', '-f', 'null', '-'],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode('utf-8', 'replace')
    starts = [float(m) for m in re.findall(r'silence_start: (\d+\.?\d*)', out)]
    ends = [float(m) for m in re.findall(r'silence_end: (\d+\.?\d*)', out)]
    sil = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else s + 0.4
        sil.append((s, e))
    return sil


PUNCT = re.compile(r'[\s，。！？、；：""''（）《》…—\-·,\.!\?;:\'\"()]+')


def norm(text):
    return PUNCT.sub('', text)


class CharClock:
    """Map normalized narration char index -> seconds, respecting pauses."""

    def __init__(self, n_chars, audio_dur, silences):
        self.n = max(1, n_chars)
        sil_total = sum(e - s for s, e in silences)
        self.speech = max(0.5, audio_dur - sil_total)
        self.sil = silences
        self.audio_dur = audio_dur

    def t(self, ci):
        # chars spread evenly over SPEECH time; pauses inserted where detected
        speech_pos = (ci / self.n) * self.speech
        t = speech_pos
        for s, e in self.sil:
            if e <= t + (e - s):  # silence lies before this speech point
                pass
        # add every pause that sits before this speech point
        acc = 0.0
        for s, e in self.sil:
            sil_dur = e - s
            # speech point in absolute time = speech_pos + pauses before it.
            # approximate: if speech_pos + acc >= s then this pause is before.
            if speech_pos + acc >= s - acc:
                acc += sil_dur
        return min(self.audio_dur, speech_pos + acc)


def find_spans(narr_norm, lines_norm):
    spans = []
    cursor = 0
    for ln in lines_norm:
        if not ln:
            spans.append((cursor, cursor))
            continue
        window = narr_norm[cursor:]
        m = difflib.SequenceMatcher(None, ln, window).find_longest_match(0, len(ln), 0, len(window))
        if m.size >= max(2, int(len(ln) * 0.45)):
            a = cursor + m.b
            b = a + m.size
        else:
            # fallback: proportional guess by line order
            frac = (len(spans) + 1) / (len(lines_norm) + 1)
            a = int(len(narr_norm) * max(0.0, frac - 0.08))
            b = min(len(narr_norm), a + len(ln))
        spans.append((a, b))
        cursor = max(cursor, a + 1)
    return spans


def snap(t, silences, which, window=1.6):
    """which='start' snaps to pause END (voice resumes); 'end' to pause START."""
    best, bd = t, window
    for s, e in silences:
        cand = e if which == 'start' else s
        if abs(cand - t) < bd:
            best, bd = cand, abs(cand - t)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--audio', required=True)
    ap.add_argument('--text', required=True)
    ap.add_argument('--lines', required=True)
    ap.add_argument('--stretch', type=float, default=1.0)
    ap.add_argument('--delay', type=float, default=0.3)
    ap.add_argument('--out', required=True)
    ap.add_argument('--srt', default='')
    args = ap.parse_args()

    with open(args.text, encoding='utf-8') as f:
        narr = f.read()
    with open(args.lines, encoding='utf-8') as f:
        lines = json.load(f)

    narr_norm = norm(narr)
    lines_norm = [norm(x) for x in lines]
    audio_dur = get_duration(args.audio)
    sil = detect_silences(args.audio)
    clock = CharClock(len(narr_norm), audio_dur, sil)
    spans = find_spans(narr_norm, lines_norm)

    sched = []
    for i, (a, b) in enumerate(spans):
        t0 = clock.t(a) * args.stretch + args.delay
        t1 = clock.t(b) * args.stretch + args.delay
        t0 = snap(t0, [(s * args.stretch + args.delay, e * args.stretch + args.delay) for s, e in sil], 'start')
        t1 = snap(t1, [(s * args.stretch + args.delay, e * args.stretch + args.delay) for s, e in sil], 'end')
        if t1 <= t0 + 1.0:
            t1 = t0 + 2.8
        sched.append({'start': round(t0, 2), 'end': round(t1, 2), 'text': lines[i]})

    # hard rule: lines are in order, never overlap
    for i in range(1, len(sched)):
        if sched[i]['start'] < sched[i - 1]['end'] + 0.15:
            sched[i]['start'] = sched[i - 1]['end'] + 0.15
        if sched[i]['end'] <= sched[i]['start'] + 0.8:
            sched[i]['end'] = sched[i]['start'] + 2.5

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(sched, f, ensure_ascii=False, indent=1)

    if args.srt:
        def fmt(x):
            h = int(x // 3600); m = int((x % 3600) // 60); s = x % 60
            return f'{h:02d}:{m:02d}:{s:06.3f}'.replace('.', ',')
        with open(args.srt, 'w', encoding='utf-8') as f:
            for i, it in enumerate(sched, 1):
                f.write(f"{i}\n{fmt(it['start'])} --> {fmt(it['end'])}\n{it['text']}\n\n")

    print(f"aligned {len(sched)} lines over {audio_dur:.1f}s audio -> {args.out}")
    for it in sched:
        print(f"  {it['start']:6.2f} - {it['end']:6.2f}  {it['text'][:22]}")


if __name__ == '__main__':
    main()
