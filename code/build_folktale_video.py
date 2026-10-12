#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the folktale story video (case 02) with ALIGNED subtitles:
6 scenes x [10,20,30,30,25,15]s, Ken Burns + narration stretched to fit.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(ROOT, 'deliverable', 'cases', '02_folktale_video')
OUT = os.path.join(CASE, 'folktale_story_video.mp4')
WORK = '/tmp/folktale_video'
ALIGN = os.path.join(ROOT, 'code', 'align_subtitles.py')
W, H, FPS = 1080, 1920, 25

FONT = None
for p in ['/tmp/font/NotoSansSC.ttf', 'C:/Windows/Fonts/msyh.ttc']:
    if os.path.exists(p):
        FONT = p
        break

SEGS = [
    ('folktale_cover_vertical.png', 10, True),
    ('folktale_scene_02_silver.png', 20, False),
    ('folktale_scene_03_workshop.png', 30, True),
    ('folktale_scene_04_village.png', 30, False),
    ('folktale_scene_05_reveal.png', 25, True),
    ('folktale_scene_01_carpenter.png', 15, False),
]

SUBS = [
    '老辈人常说：木匠忌讳接三更活', '渡人莫渡无影客', '乾隆十八年的除夕雪夜\n他接了一单不露脸的急活',
    '那天雪下得正紧\n柴门被叩响三声', '门外立着披蓑衣的黑影 看不清脸', '只递进一锭冰凉的官银',
    '照这尺寸 打一口小匣子\n今夜就要', '陈三斤本不想接', '可想起卧病老妻等着抓药\n他攥紧了银子',
    '他点起灯开工 越做越不对', '那木料奇香 入手沉如铁', '鲁班尺上"病""离"二字\n正对木纹',
    '门外雪地上 来时的一行脚印', '竟浅得几乎看不见', '这单三更活 处处透着古怪',
    '他越想越心惊 却停不下手\n匣子将成 天已三更', '三更天 村口忽然传来锣声',
    '乡邻披衣来报：\n渡口的无影客又出来了！', '专在除夕夜敲老实人的门', '众人劝他把银子扔了',
    '陈三斤摇摇头：\n活可以不做 人不能失信', '他提灯出了门', '走进漫天风雪里',
    '雪地尽头 蓑衣客接过匣子', '缓缓掀开斗笠', '竟是二十年前\n被他从冰河里捞起的落难书生！',
    '如今的新任县令', '以官银谢一饭一宿之恩\n并赠良药医其老妻', '原来如此',
    '所谓无影客\n不过是试人心的把戏', '手艺人守的是规矩\n行的是良心', '但行好事 莫问前程',
    '善有善报\n评论区留下您的祝福',
]

FFMPEG = shutil.which('ffmpeg') or __import__('imageio_ffmpeg').get_ffmpeg_exe()


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        sys.stderr.write(p.stdout.decode('utf-8', 'replace')[-1500:])
        raise SystemExit('ffmpeg failed')


def mp3_dur(path):
    p = subprocess.run([FFMPEG, '-i', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', p.stdout.decode('utf-8', 'replace'))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


def make_bg(src, dst):
    im = Image.open(src).convert('RGB')
    tw, th = 1296, 2304
    r = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l = (im.width - tw) // 2
    t = (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(dst, quality=92)


def make_sub(text, dst):
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, 54)
    y = int(H * 0.72)
    for ln in text.split('\n'):
        bbox = d.textbbox((0, 0), ln, font=font, stroke_width=4)
        x = (W - (bbox[2] - bbox[0])) // 2
        d.text((x, y), ln, font=font, fill=(255, 226, 140, 255),
               stroke_width=4, stroke_fill=(0, 0, 0, 255))
        y += 84
    canvas.save(dst)


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    seg_files = []
    for i, (img, dur, zin) in enumerate(SEGS):
        bg = os.path.join(WORK, f'bg{i}.png')
        make_bg(os.path.join(CASE, img), bg)
        nfr = dur * FPS
        zexpr = 'min(zoom+0.0009,1.12)' if zin else f'1.12-0.12*on/{nfr}'
        fc = (f"[0:v]scale=1296:2304,zoompan=z='{zexpr}':d=1:x='iw/2-(iw/zoom/2)'"
              f":y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS},format=yuv420p[out]")
        seg = os.path.join(WORK, f'seg{i}.mp4')
        run([FFMPEG, '-y', '-loop', '1', '-framerate', str(FPS), '-t', str(dur), '-i', bg,
             '-filter_complex', fc, '-map', '[out]', '-frames:v', str(nfr), '-r', str(FPS),
             '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-an', seg])
        seg_files.append(seg)
    lst = os.path.join(WORK, 'list.txt')
    with open(lst, 'w') as f:
        for s in seg_files:
            f.write("file '" + s + "'\n")
    silent = os.path.join(WORK, 'silent.mp4')
    run([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])

    narr = os.path.join(CASE, 'folktale_narration.mp3')
    d = mp3_dur(narr)
    tempo = d / 128.0                 # stretch narration to ~128s (video is 130s)
    stretch = 1.0 / tempo

    # narration text without the file header
    with open(os.path.join(CASE, 'narration_script.txt'), encoding='utf-8') as f:
        raw = f.read()
    body = raw.split('\n\n', 1)[1] if '\n\n' in raw else raw
    txt = os.path.join(WORK, 'body.txt')
    with open(txt, 'w', encoding='utf-8') as f:
        f.write(body)
    sched_json = os.path.join(CASE, 'folktale_schedule.json')
    srt = os.path.join(CASE, 'folktale_story_video.srt')
    # subtitle-align v2: character-level alignment of the known script to the audio;
    # lines are auto-split from the script so every character is shown.
    run([sys.executable, ALIGN, '--audio', narr, '--text', txt,
         '--stretch', f'{stretch:.4f}', '--delay', '0.3', '--out', sched_json, '--srt', srt])
    with open(sched_json, encoding='utf-8') as f:
        sched = json.load(f)

    cmd = [FFMPEG, '-y', '-i', silent, '-i', narr]
    fc = ''
    prev = '0:v'
    for j, it in enumerate(sched):
        sp = os.path.join(WORK, f'sub{j}.png')
        make_sub(it['text'], sp)
        cmd += ['-i', sp]
        fc += f"[{prev}][{j+2}:v]overlay=0:0:enable='between(t,{it['start']},{it['end']})'[v{j}];"
        prev = f'v{j}'
    fc += f'[1:a]atempo={tempo:.4f},adelay=300|300[a]'
    cmd += ['-filter_complex', fc, '-map', f'[{prev}]', '-map', '[a]',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24', '-c:a', 'aac', '-b:a', '128k',
            '-t', '130', '-movflags', '+faststart', OUT]
    run(cmd)
    print('wrote', OUT, os.path.getsize(OUT), 'bytes (tempo=%.3f)' % tempo)


if __name__ == '__main__':
    main()
