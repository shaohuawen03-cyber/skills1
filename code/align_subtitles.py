#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""subtitle-align v2: character-level forced alignment of KNOWN narration text
to the narration audio. No ASR model needed (none is reachable offline).

Chinese TTS speaks ~one syllable per character, so we align characters to:
  1. syllable nuclei   - energy peaks (10 ms RMS, ~90 ms smoothing)
  2. speech runs       - silero VAD (ONNX model bundled in the PyPI wheel `silero-vad`)
A monotone Needleman-Wunsch matches characters to peaks, with a timing prior
(characters spread over the speech clock) so skipped characters stay in place.
Characters without a peak are interpolated; run starts snap to VAD onsets.
Subtitle lines are then built from the script (every character is shown) and
timed from their first/last character.

Usage:
  python3 code/align_subtitles.py --audio narr.mp3 --text script.txt \
      --stretch 1.2048 --delay 0.3 --out schedule.json [--srt out.srt] [--lines lines.json]

  --text     plain text (a '\n\n' header is stripped when present)
  --stretch  video_time = natural_time * stretch + delay  (stretch = 1/atempo)
  --lines    optional explicit subtitle lines (JSON list); default = auto split
  --max-chars  max characters per auto subtitle line (default 16)

Needs: numpy, onnxruntime, imageio-ffmpeg (or ffmpeg on PATH),
       silero_vad_16k_op15.onnx (path: --vad-model, default searched automatically).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

import numpy as np

SR = 16000
PUNCT_RE = re.compile(r'[\s，。！？、；：“”"「」《》（）()…—\-·,.!?;:\'`]+')
SENT_END = set('。！？!?')
CLAUSE_END = set('，。！？；：,.!?;:、')


def ffmpeg_exe():
    return shutil.which('ffmpeg') or __import__('imageio_ffmpeg').get_ffmpeg_exe()


def load_audio(path):
    p = subprocess.run([ffmpeg_exe(), '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR),
                        '-f', 'f32le', '-'], stdout=subprocess.PIPE, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32).copy()


def find_vad_model(explicit=None):
    cands = [explicit] if explicit else []
    cands += glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'models', 'silero_vad_16k_op15.onnx'))
    cands += ['/tmp/silero/silero_vad/data/silero_vad_16k_op15.onnx']
    for c in cands:
        if c and os.path.exists(c):
            return c
    # extract from the pip wheel if available locally
    for whl in glob.glob('/tmp/pk/silero_vad-*.whl'):
        with zipfile.ZipFile(whl) as z:
            name = 'silero_vad/data/silero_vad_16k_op15.onnx'
            out = '/tmp/silero/' + name
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, 'wb') as f:
                f.write(z.read(name))
            return out
    raise SystemExit('silero VAD model not found: pip download silero-vad, or pass --vad-model')


def vad_speech(x, model_path):
    import onnxruntime as ort
    sess = ort.InferenceSession(model_path)
    state = np.zeros((2, 1, 128), dtype=np.float32)
    sr = np.array(SR, dtype=np.int64)
    ctx = np.zeros(64, dtype=np.float32)
    probs = []
    for i in range(0, len(x) - 512, 512):
        frame = np.concatenate([ctx, x[i:i + 512]])[None, :].astype(np.float32)
        ctx = x[i + 512 - 64:i + 512].astype(np.float32)
        out, state = sess.run(None, {'input': frame, 'state': state, 'sr': sr})
        probs.append(float(np.ravel(out)[0]))
    probs = np.array(probs)
    runs, s = [], None
    for i, v in enumerate(probs > 0.5):
        if v and s is None:
            s = i
        if not v and s is not None:
            runs.append((s * 0.032, i * 0.032)); s = None
    if s is not None:
        runs.append((s * 0.032, len(probs) * 0.032))
    # drop blips, close VAD dropouts shorter than 80 ms
    out = []
    for a, b in runs:
        if b - a < 0.15:
            continue
        if out and a - out[-1][1] < 0.08:
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def syllable_peaks(x, min_gap=0.10, prom=1.5):
    hop, win = 160, 400
    n = (len(x) - win) // hop
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    rms = np.sqrt((x[idx] ** 2).mean(axis=1) + 1e-10)
    db = 20 * np.log10(rms + 1e-10)  # 10 ms frames
    sm = np.convolve(db, np.ones(9) / 9, mode='same')
    peaks, last = [], -1e9
    for i in range(26, len(sm) - 26):
        if sm[i] >= sm[i - 1] and sm[i] > sm[i + 1] and sm[i] > -45:
            p = sm[i] - max(sm[i - 25:i].min(), sm[i + 1:i + 26].min())
            t = i * 0.01
            if p >= prom and t - last >= min_gap:
                peaks.append(t); last = t
    return np.array(peaks)


def char_list(text):
    """[(char, idx_in_text)] for every syllable-bearing character."""
    return [(ch, k) for k, ch in enumerate(text) if not PUNCT_RE.fullmatch(ch)]


def expected_times(n, runs):
    S = sum(b - a for a, b in runs)
    out = []
    for i in range(n):
        f = (i + 0.5) / n * S
        acc, t = 0.0, runs[-1][1]
        for a, b in runs:
            if f <= acc + (b - a):
                t = a + (f - acc); break
            acc += (b - a)
        out.append(t)
    return np.array(out)


def nw_match(n, peaks, texp, skip_char=1.0, skip_peak=1.0, scale=0.25):
    m = len(peaks)
    D = np.zeros((n + 1, m + 1))
    B = np.zeros((n + 1, m + 1), dtype=np.int8)
    D[1:, 0] = np.arange(1, n + 1) * skip_char; B[1:, 0] = 1
    D[0, 1:] = np.arange(1, m + 1) * skip_peak; B[0, 1:] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cd = D[i - 1, j - 1] + min(abs(peaks[j - 1] - texp[i - 1]) / scale, 3.0)
            cs = D[i - 1, j] + skip_char
            cp = D[i, j - 1] + skip_peak
            best = min(cd, cs, cp)
            D[i, j] = best
            B[i, j] = 0 if best == cd else (1 if best == cs else 2)
    res = [-1] * n
    i, j = n, m
    while i > 0 and j > 0:
        b = B[i, j]
        if b == 0:
            res[i - 1] = j - 1; i -= 1; j -= 1
        elif b == 1:
            i -= 1
        else:
            j -= 1
    return res


def align_chars(x, text, vad_model=None):
    """returns (chars[], onset[], end[], dur, runs)"""
    dur = len(x) / SR
    runs = vad_speech(x, find_vad_model(vad_model))
    peaks = syllable_peaks(x)
    cl = char_list(text)
    n = len(cl)
    texp = expected_times(n, runs)
    mapping = nw_match(n, peaks, texp)
    onset = [None] * n
    for i, pi in enumerate(mapping):
        if pi >= 0:
            onset[i] = float(peaks[pi]) - 0.03
    # interpolate unmatched chars between matched neighbours
    known = [i for i in range(n) if onset[i] is not None]
    for i in range(n):
        if onset[i] is None:
            prv = [k for k in known if k < i]
            nxt = [k for k in known if k > i]
            lo_k, lo_t = (prv[-1], onset[prv[-1]]) if prv else (-1, 0.0)
            hi_k, hi_t = (nxt[0], onset[nxt[0]]) if nxt else (n, dur)
            onset[i] = lo_t + (hi_t - lo_t) * (i - lo_k) / (hi_k - lo_k)
    # a char that starts a speech run after a pause takes the VAD run start
    for a, b in runs:
        cand = [i for i in range(n) if a - 0.12 <= onset[i] <= a + 0.25]
        if cand:
            k = min(cand, key=lambda i: abs(onset[i] - a))
            onset[k] = a
    ends = []
    for i in range(n):
        nxt = onset[i + 1] if i + 1 < n else dur
        e = max(onset[i] + 0.12, nxt - 0.02)
        for a, b in runs:
            if a - 1e-6 <= onset[i] < b and e > b:
                e = max(onset[i] + 0.12, b)
        ends.append(e)
    return [c for c, _ in cl], [k for _, k in cl], onset, ends, dur, runs, len(peaks), sum(1 for m in mapping if m >= 0)


def auto_lines(text, max_chars=16):
    """Split the script into display lines that cover every character.
    Break at sentence ends first, then clause punctuation; never more than
    max_chars syllable characters per line (over-long clauses are hard-split)."""
    def n_of(s):
        return len(PUNCT_RE.sub('', s))

    clauses, cur = [], ''
    for ch in text:
        if ch in '"“”「」『』':   # quote marks are not shown on screen
            continue
        cur += ch
        if ch in CLAUSE_END:
            clauses.append(cur); cur = ''
    if cur.strip():
        clauses.append(cur)

    chunks = []  # (text, ends_sentence)
    for cl in clauses:
        parts, rest = [], cl
        while n_of(rest) > max_chars:
            k, cnt = 0, 0
            while k < len(rest) and (cnt < max_chars or PUNCT_RE.fullmatch(rest[k])):
                if not PUNCT_RE.fullmatch(rest[k]):
                    cnt += 1
                k += 1
            parts.append(rest[:k]); rest = rest[k:]
        parts.append(rest)
        chunks.extend(parts)

    lines, buf = [], ''
    for ch in chunks:
        if buf.strip() and n_of(buf) + n_of(ch) > max_chars:
            lines.append(buf.strip()); buf = ''
        buf += ch
        if buf.rstrip() and buf.rstrip()[-1] in SENT_END:
            lines.append(buf.strip()); buf = ''
    if buf.strip():
        lines.append(buf.strip())
    return [l for l in lines if l]


def build_schedule(audio, text, lines=None, max_chars=16, vad_model=None):
    x = load_audio(audio)
    chars, idx, onset, ends, dur, runs, npk, nmatch = align_chars(x, text, vad_model)
    if lines is None:
        lines = auto_lines(text, max_chars)
    # map each line onto its span of syllable characters (in order)
    sched, ci = [], 0
    for ln in lines:
        lc = [c for c in ln if not PUNCT_RE.fullmatch(c)]
        if not lc:
            continue
        s_i = ci
        ci += len(lc)
        if ci > len(chars):
            raise SystemExit('lines contain more characters than the script: ' + ln)
        start = onset[s_i]
        end = ends[ci - 1]
        sched.append({'start': start, 'end': end, 'text': ln.replace('\n', '\n'),
                      'chars': len(lc)})
    if ci != len(chars):
        raise SystemExit('lines cover %d of %d characters' % (ci, len(chars)))
    # display rules: min 0.8 s on screen, no overlap, short gap
    for k, it in enumerate(sched):
        it['end'] = max(it['end'], it['start'] + 0.8)
        if k + 1 < len(sched):
            it['end'] = min(it['end'], sched[k + 1]['start'] - 0.03)
    return sched, {'natural_dur': dur, 'vad_runs': len(runs), 'peaks': npk,
                   'matched_chars': nmatch, 'chars': len(chars)}


def to_video_time(sched, stretch, delay):
    return [{'start': round(it['start'] * stretch + delay, 3),
             'end': round(it['end'] * stretch + delay, 3),
             'text': it['text']} for it in sched]


def write_srt(items, path):
    def ts(t):
        h, rem = divmod(int(round(t * 1000)), 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return '%02d:%02d:%02d,%03d' % (h, m, s, ms)
    with open(path, 'w', encoding='utf-8') as f:
        for i, it in enumerate(items, 1):
            f.write('%d\n%s --> %s\n%s\n\n' % (i, ts(it['start']), ts(it['end']), it['text']))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--audio', required=True)
    ap.add_argument('--text', required=True)
    ap.add_argument('--lines')
    ap.add_argument('--stretch', type=float, default=1.0)
    ap.add_argument('--delay', type=float, default=0.0)
    ap.add_argument('--max-chars', type=int, default=16)
    ap.add_argument('--vad-model')
    ap.add_argument('--out', required=True)
    ap.add_argument('--srt')
    a = ap.parse_args()
    raw = open(a.text, encoding='utf-8').read()
    # the narration_script.txt files carry a one-line header before a blank line
    text = raw.split('\n\n', 1)[1] if ('\n\n' in raw and raw.index('\n\n') < 200) else raw
    lines = json.load(open(a.lines, encoding='utf-8')) if a.lines else None
    sched, info = build_schedule(a.audio, text, lines, a.max_chars, a.vad_model)
    vt = to_video_time(sched, a.stretch, a.delay)
    with open(a.out, 'w', encoding='utf-8') as f:
        json.dump(vt, f, ensure_ascii=False, indent=1)
    if a.srt:
        write_srt(vt, a.srt)
    print('lines %d | chars %d | matched %d | peaks %d | speech runs %d | natural %.2fs' % (
        len(vt), info['chars'], info['matched_chars'], info['peaks'], info['vad_runs'], info['natural_dur']))


if __name__ == '__main__':
    main()
