#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the folktale story video (case 02): vertical 1080x1920, 6 scenes,
Ken Burns zoom + burned-in Chinese subtitles (PIL overlays; this ffmpeg build
has no drawtext). Output: deliverable/cases/02_folktale_video/folktale_story_video.mp4
"""
from __future__ import annotations

import os
import subprocess
import sys
import shutil

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASE = os.path.join(ROOT, 'deliverable', 'cases', '02_folktale_video')
OUT = os.path.join(CASE, 'folktale_story_video.mp4')
WORK = '/tmp/folktale_video'
W, H = 1080, 1920
FPS = 25

FONT_CANDS = [
    '/tmp/font/NotoSansSC.ttf',
    'C:/Windows/Fonts/msyh.ttc',
    'C:/Windows/Fonts/simhei.ttf',
]


def find_font():
    for p in FONT_CANDS:
        if os.path.exists(p):
            return p
    raise SystemExit('no CJK font found')


FONT = find_font()

# (image, [(t_start, t_end, text), ...], zoom_in?)
SEGS = [
    ('folktale_cover_vertical.png', [
        (0.0, 3.2, '老辈人常说：木匠忌讳接三更活'),
        (3.2, 6.2, '渡人莫渡无影客'),
        (6.2, 10.0, '乾隆十八年的除夕雪夜\\n他接了一单不露脸的急活'),
    ], True),
    ('folktale_scene_02_silver.png', [
        (0.0, 3.5, '那天雪下得正紧\\n柴门被叩响三声'),
        (3.5, 7.0, '门外立着披蓑衣的黑影 看不清脸'),
        (7.0, 10.5, '只递进一锭冰凉的官银'),
        (10.5, 14.0, '照这尺寸 打一口小匣子\\n今夜就要'),
        (14.0, 17.0, '陈三斤本不想接'),
        (17.0, 20.0, '可想起卧病老妻等着抓药\\n他攥紧了银子'),
    ], False),
    ('folktale_scene_03_workshop.png', [
        (0.0, 3.5, '他点起灯开工 越做越不对'),
        (3.5, 7.5, '那木料奇香 入手沉如铁'),
        (7.5, 11.5, '鲁班尺上"病""离"二字\\n正对木纹'),
        (11.5, 15.5, '门外雪地上 来时的一行脚印'),
        (15.5, 19.0, '竟浅得几乎看不见'),
        (19.0, 23.0, '这单三更活 处处透着古怪'),
        (23.0, 30.0, '他越想越心惊 却停不下手\\n匣子将成 天已三更'),
    ], True),
    ('folktale_scene_04_village.png', [
        (0.0, 4.0, '三更天 村口忽然传来锣声'),
        (4.0, 8.0, '乡邻披衣来报：\\n渡口的无影客又出来了！'),
        (8.0, 12.0, '专在除夕夜敲老实人的门'),
        (12.0, 16.0, '众人劝他把银子扔了'),
        (16.0, 20.5, '陈三斤摇摇头：\\n活可以不做 人不能失信'),
        (20.5, 25.0, '他提灯出了门'),
        (25.0, 30.0, '走进漫天风雪里'),
    ], False),
    ('folktale_scene_05_reveal.png', [
        (0.0, 4.0, '雪地尽头 蓑衣客接过匣子'),
        (4.0, 8.5, '缓缓掀开斗笠'),
        (8.5, 13.0, '竟是二十年前\\n被他从冰河里捞起的落难书生！'),
        (13.0, 17.5, '如今的新任县令'),
        (17.5, 22.0, '以官银谢一饭一宿之恩\\n并赠良药医其老妻'),
        (22.0, 25.0, '原来如此'),
    ], True),
    ('folktale_scene_01_carpenter.png', [
        (0.0, 4.0, '所谓无影客\\n不过是试人心的把戏'),
        (4.0, 8.5, '手艺人守的是规矩\\n行的是良心'),
        (8.5, 12.0, '但行好事 莫问前程'),
        (12.0, 15.0, '善有善报\\n评论区留下您的祝福'),
    ], False),
]


def make_bg(src: str, dst: str) -> None:
    im = Image.open(src).convert('RGB')
    # cover-crop to 1296x2304 (1.2x of 1080x1920, zoom headroom)
    tw, th = 1296, 2304
    r = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left = (im.width - tw) // 2
    top = (im.height - th) // 2
    im.crop((left, top, left + tw, top + th)).save(dst, quality=92)


def make_sub(text: str, dst: str) -> None:
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    lines = text.split('\\n')
    font = ImageFont.truetype(FONT, 54)
    y = int(H * 0.72)
    for ln in lines:
        bbox = d.textbbox((0, 0), ln, font=font, stroke_width=4)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        d.text((x, y), ln, font=font, fill=(255, 226, 140, 255),
               stroke_width=4, stroke_fill=(0, 0, 0, 255))
        y += 84
    canvas.save(dst)


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        sys.stderr.write(p.stdout.decode('utf-8', 'replace')[-2000:])
        raise SystemExit('ffmpeg failed: ' + ' '.join(cmd[:6]))


def main():
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)

    seg_files = []
    for i, (img, subs, zin) in enumerate(SEGS):
        bg = os.path.join(WORK, f'bg{i}.png')
        make_bg(os.path.join(CASE, img), bg)
        dur = max(b for _, b, _ in subs)
        nframes = int(dur * FPS)

        sub_ids = []
        for j, (a, b, txt) in enumerate(subs):
            sp = os.path.join(WORK, f'sub{i}_{j}.png')
            make_sub(txt, sp)
            sub_ids.append((sp, a, b))

        if zin:
            zexpr = 'min(zoom+0.0009,1.12)'
        else:
            zexpr = f'1.12-0.12*on/{nframes}'
        fc = (
            f"[0:v]scale=1296:2304,"
            f"zoompan=z='{zexpr}':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS}[bg]"
        )
        prev = 'bg'
        for j, (sp, a, b) in enumerate(sub_ids):
            fc += f";[{prev}][{j+1}:v]overlay=0:0:enable='between(t,{a},{b})'[v{j}]"
            prev = f'v{j}'
        fc += f';[{prev}]format=yuv420p[out]'

        seg = os.path.join(WORK, f'seg{i}.mp4')
        cmd = [ffmpeg, '-y', '-loop', '1', '-framerate', str(FPS),
               '-t', str(dur), '-i', bg]
        for sp, _, _ in sub_ids:
            cmd += ['-i', sp]
        cmd += ['-filter_complex', fc, '-map', '[out]',
                '-frames:v', str(nframes), '-r', str(FPS),
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '24',
                '-an', seg]
        print(f'seg {i}: {img} {dur}s subs={len(sub_ids)} zoom={"in" if zin else "out"}')
        run(cmd)
        seg_files.append(seg)

    lst = os.path.join(WORK, 'list.txt')
    with open(lst, 'w', encoding='utf-8') as f:
        for s in seg_files:
            f.write("file '" + s + "'\n")
    run([ffmpeg, '-y', '-f', 'concat', '-safe', '0', '-i', lst,
         '-c', 'copy', '-movflags', '+faststart', OUT])
    size = os.path.getsize(OUT)
    print('wrote', OUT, size, 'bytes')
    p = subprocess.run([ffmpeg, '-i', OUT], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in p.stdout.decode('utf-8', 'replace').splitlines():
        if 'Duration' in line or 'Video:' in line:
            print(line.strip())


if __name__ == '__main__':
    main()
