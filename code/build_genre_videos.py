#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Batch-build genre demo videos (vertical 1080x1920, 2 scenes x 30s,
Ken Burns + Chinese subtitles + narration). Reads deliverable/genre_videos/
scenes/<id>_<n>.jpg + <id>_narration.mp3, writes <id>_video.mp4.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.join(ROOT, 'deliverable', 'genre_videos')
SCENES = os.path.join(BASE, 'scenes')
WORK = '/tmp/genre_videos'
W, H, FPS = 1080, 1920, 25

FONT_CANDS = ['/tmp/font/NotoSansSC.ttf', 'C:/Windows/Fonts/msyh.ttc']


def find_font():
    for p in FONT_CANDS:
        if os.path.exists(p):
            return p
    raise SystemExit('no CJK font')


FONT = find_font()

# id: (title, [(sub lines scene1 x3, scene2 x3)], zoom_in for scene1)
SPECS = {
    '02_history': ('苏东坡：一蓑烟雨任平生', [
        '一千年前 有个大文豪', '一生被贬三次 却活成最羡慕的样子', '乌台诗案 他差点死在牢里',
        '被贬黄州 他买地种粮 炖出东坡肉', '三贬儋州 他办学堂挖水井', '回首向来萧瑟处 也无风雨也无晴'], True),
    '03_emotion': ('致负重前行的你', [
        '你有多久 没有好好心疼自己了', '人到中年 不敢病 不敢停 不敢倒', '可淋着雨赶路的人',
        '也值得有一盏灯', '累了就歇一歇 天塌不下来', '愿你三冬暖 愿你春不寒'], False),
    '04_fable': ('小狐狸的月亮灯笼', [
        '从前呀 森林里有只小狐狸', '它呀 最怕黑了', '月亮掉进池塘 碎成满天星星',
        '小狐狸捞起一盏月亮灯笼', '送小兔回家 帮刺猬照路', '照亮别人的光 也会温暖自己'], True),
    '05_suspense': ('末班车的第三位乘客', [
        '深夜十一点四十分 末班地铁', '只有三个人 司机、我、红裙女人', '再抬头 女人不见了',
        '座位上多了一把车钥匙', '司机说：今天只有你一个人上来', '手里多了一张十年前的车票'], False),
    '06_science': ('冬天晒太阳的大学问', [
        '冬天晒太阳 可不是小事', '上午十点 下午三点 每次二十分钟', '别隔着玻璃晒 紫外线进不来',
        '重点晒后背 全身血脉都通', '有高血压的 别空腹戴好帽子', '转给家里的老人 健康是福'], True),
    '07_booklist': ('人到中年必读三本书', [
        '人到中年 只能读三本书', '第一本《活着》', '除了生死 全是小事',
        '第二本《苏东坡传》', '第三本《平凡的世界》', '平凡人最大的体面'], False),
    '08_product': ('这条加绒牛仔裤 卖爆十万条', [
        '这条加绒牛仔裤 卖了十万条', '外面高支牛仔 里面baby绒', '零下单穿不透风',
        '高腰直筒 遮胯显瘦', '工厂直发 只要七十九', '点击下方小黄车'], True),
    '09_food': ('外婆的红烧肉', [
        '外婆的红烧肉 走多远都忘不掉', '五花肉冷水下锅 撇净浮沫', '冰糖炒出琥珀色',
        '小火慢炖四十分钟', '秘诀三个字：别着急', '汤汁拌饭能吃三碗'], False),
    '10_travel': ('风花雪月的尽头是洱海', [
        '如果你累了 就去大理吧', '洱海不是海 却比海更懂人心', '清晨的日出把湖面染成金色',
        '风花雪月 是大理的四封信', '不必赶景点 看云发呆一整天', '艾特TA 欠自己一场旅行'], True),
    '11_poetry': ('将进酒（李白）', [
        '君不见 黄河之水天上来', '奔流到海不复回', '人生得意须尽欢 莫使金樽空对月',
        '天生我材必有用', '千金散尽还复来', '难过了就读一遍 什么坎都过得去'], False),
    '12_business': ('一个人开公司的第一课', [
        '一个人开公司 第一课是活下来', '先找客户再做产品', '算清三笔钱 启动/生活/应急',
        '商业计划书写成一页纸', '别租办公室 先用AI跑通流程', '关注我 少交十万学费'], True),
}


def make_bg(src, dst):
    im = Image.open(src).convert('RGB')
    tw, th = 1296, 2304
    r = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    l = (im.width - tw) // 2
    t = (im.height - th) // 2
    im.crop((l, t, l + tw, t + th)).save(dst, quality=90)


def make_sub(text, dst):
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(FONT, 56)
    y = int(H * 0.72)
    bbox = d.textbbox((0, 0), text, font=font, stroke_width=4)
    x = (W - (bbox[2] - bbox[0])) // 2
    d.text((x, y), text, font=font, fill=(255, 226, 140, 255),
           stroke_width=4, stroke_fill=(0, 0, 0, 255))
    canvas.save(dst)


def run(cmd):
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode != 0:
        sys.stderr.write(p.stdout.decode('utf-8', 'replace')[-1500:])
        raise SystemExit('ffmpeg failed')


def mp3_dur(path):
    p = subprocess.run([FFMPEG, '-i', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    m = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', p.stdout.decode('utf-8', 'replace'))
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))


FFMPEG = shutil.which('ffmpeg') or __import__('imageio_ffmpeg').get_ffmpeg_exe()


def build_one(gid, title, lines, zoom1):
    gdir = os.path.join(WORK, gid)
    os.makedirs(gdir, exist_ok=True)
    seg_files = []
    for si in range(2):
        img = os.path.join(SCENES, f'{gid}_{si+1}.jpg')
        if not os.path.exists(img):
            raise SystemExit('missing scene ' + img)
        bg = os.path.join(gdir, f'bg{si}.png')
        make_bg(img, bg)
        dur = 30
        nfr = dur * FPS
        subs = []
        for j in range(3):
            sp = os.path.join(gdir, f'sub{si}_{j}.png')
            make_sub(lines[si * 3 + j], sp)
            subs.append((sp, j * 10, (j + 1) * 10))
        zin = zoom1 if si == 0 else (not zoom1)
        zexpr = 'min(zoom+0.0009,1.12)' if zin else f'1.12-0.12*on/{nfr}'
        fc = f"[0:v]scale=1296:2304,zoompan=z='{zexpr}':d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS}[bg]"
        prev = 'bg'
        for j, (sp, a, b) in enumerate(subs):
            fc += f";[{prev}][{j+1}:v]overlay=0:0:enable='between(t,{a},{b})'[v{j}]"
            prev = f'v{j}'
        fc += f';[{prev}]format=yuv420p[out]'
        seg = os.path.join(gdir, f'seg{si}.mp4')
        cmd = [FFMPEG, '-y', '-loop', '1', '-framerate', str(FPS), '-t', str(dur), '-i', bg]
        for sp, _, _ in subs:
            cmd += ['-i', sp]
        cmd += ['-filter_complex', fc, '-map', '[out]', '-frames:v', str(nfr), '-r', str(FPS),
                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '26', '-an', seg]
        run(cmd)
        seg_files.append(seg)
    lst = os.path.join(gdir, 'list.txt')
    with open(lst, 'w') as f:
        for s in seg_files:
            f.write("file '" + s + "'\n")
    silent = os.path.join(gdir, 'silent.mp4')
    run([FFMPEG, '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', silent])

    out = os.path.join(BASE, f'{gid}_video.mp4')
    narr = os.path.join(BASE, f'{gid}_narration.mp3')
    if os.path.exists(narr):
        d = mp3_dur(narr)
        tempo = max(0.6, min(1.5, d / 58.0))  # stretch/compress narration to ~58s
        run([FFMPEG, '-y', '-i', silent, '-i', narr,
             '-filter_complex', f'[1:a]atempo={tempo:.4f},adelay=300|300[a]',
             '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k',
             '-t', '60', '-movflags', '+faststart', out])
    else:
        shutil.copy(silent, out)
    print(f'{gid}: {title} -> {os.path.getsize(out)} bytes')


def main():
    shutil.rmtree(WORK, ignore_errors=True)
    os.makedirs(WORK)
    only = sys.argv[1:] or list(SPECS.keys())
    for gid in only:
        title, lines, zoom1 = SPECS[gid]
        build_one(gid, title, lines, zoom1)


if __name__ == '__main__':
    main()
