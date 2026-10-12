# subtitle-align（字幕-配音强制对齐）

> 解决的问题：AI 生成的配音和字幕**时间轴对不上**（字幕按固定秒数轮播，声音还在讲上一句）。
> 做法：不做语音识别（文案本来就是已知的），用「停顿感知的字符分布对齐」把每一行字幕
> 钉到配音里它真正被读到的时间点，误差通常在 0.5 秒内。

## 原理（3 步）

1. **找停顿**：ffmpeg `silencedetect` 扫出配音里的所有静音段（句读停顿）。
2. **钉字位**：把每行字幕在剧本原文里定位（difflib 模糊匹配、按阅读顺序推进），
   再按「字符数 / 有效发声时长」把字符位置换算成时间，静音段自动跳过。
3. **吸边**：每行的开始/结束时间吸附到最近的停顿边界（±1.6s 内），字幕永远整句起、整句落。

## 用法

```bash
python3 code/align_subtitles.py \
  --audio  deliverable/genre_videos/02_history_narration.mp3 \
  --text   deliverable/genre_videos/02_history_script.txt \
  --lines  lines.json \
  --stretch 1.0 --delay 0.3 \
  --out    /tmp/sched.json --srt /tmp/out.srt
```

- `lines.json`：字幕行数组（显示顺序）
- `--stretch`：配音被拉伸的倍数（成片时长/自然时长），对齐结果自动换算
- `--delay`：配音在视频里的起始偏移（秒）
- 输出：schedule JSON（给烧字幕用）+ 可选 SRT

## 何时该上 ASR 强制对齐

如果配音文案与字幕**不对应**（比如字幕是改写/翻译），用 whisper.cpp 的
`ggml-tiny.bin`（GitHub releases 直接下载，无需 HuggingFace）做词级时间戳，
本 skill 的第 2 步替换为 ASR 词表对齐即可，其余不变。

*配套脚本：`code/build_genre_videos.py`（字幕按 schedule 烧录）。*
