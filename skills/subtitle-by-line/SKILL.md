---
name: subtitle-by-line
description: Make subtitles match narration EXACTLY by generating one TTS clip per subtitle line, then building the video from those clips. Use whenever a narrated video's subtitles must line up with the voice (short videos, story videos, courseware). Replaces estimate-based alignment (subtitle-align), which drifted or put text in the wrong place.
---

# subtitle-by-line

## Why this exists

Estimating where each character sits in a finished narration (energy peaks, VAD,
DP alignment) gave subtitles that visibly did not match the voice. There is no
ASR model in the sandbox to check it. This skill avoids guessing: every subtitle
line IS its own audio clip, so its start and length come from the clip itself.

## One-turn recipe (up to 10 lines)

Platform limit: `generate_speech` produces at most **10 clips per turn**.
So one turn covers a video with **<= 10 subtitle lines**. For longer scripts
either split the script into several videos of <= 10 lines, or accept one
extra turn per 10 lines.

1. **Write the lines.** Split the script into display lines (<= 16 Chinese
   characters each, ends at sentence or clause punctuation). Keep the list in
   `work/lines.json`. Quote marks are not shown on screen.
   `python3 code/align_subtitles.py` has `auto_lines()` if you want a starting split.
2. **Generate one clip per line, all in ONE turn**, in parallel, with the same
   `voice_id` for the whole video. Save as `work/clip_01.mp3`, `work/clip_02.mp3`, ...
   in the same order as `lines.json`. The clip text must be exactly that line.
3. **Build:**
   ```bash
   SUB_FONT=/tmp/font/NotoSansSC.ttf \
   python3 skills/subtitle-by-line/scripts/build_line_video.py \
       --work work --out-dir out \
       --scenes scene1.jpg scene2.jpg
   ```
   Output in `out/`: `video.mp4`, `narration.mp3`, `schedule.json`, `subtitles.srt`.
4. **Verify** (do not skip): every subtitle window must contain speech and every
   gap between lines must be quiet. Run the check in
   `skills/subtitle-by-line/scripts/verify_line_video.py` (prints the bad lines).
5. Copy the results to the deliverable folder, update `schedule.json` and the
   README table, `bash code/check_all.sh`, commit, push.

## How timing is computed

- Clip `i` starts at `t_i` (video time) and lasts `d_i` seconds, where `d_i` is
  decoded from the MP3 samples, not the MP3 header. Headers are off by about
  0.04 s per clip, which drifts over 30+ clips.
- After each clip there is a fixed pause (default 0.25 s), then clip `i+1`.
- Subtitle `i` shows from `t_i` to `t_i + max(d_i, 0.8)`, capped so it never
  overlaps the next line.
- The narration track is the clips joined with the same pauses, so the voice
  and the subtitle clock are the same clock.

## Pitfalls already hit

- ffmpeg `concat` list files resolve relative paths against the list file's
  folder. Pass absolute paths (the script does this).
- Do not use `-shortest` with `-c:v copy` and `apad` (it hangs). Use `-t`.
- imageio-ffmpeg has no `drawtext`. Subtitles are rendered as RGBA PNG overlays
  with PIL, one overlay per line, with `enable='between(t,start,end)'`.
- In the overlay chain, the first input is the silent picture, the second is the
  narration, and the subtitle PNGs start at input 2.
- Find the CJK font with `SUB_FONT`. Without a font the build stops with a message.

## Files

- `scripts/build_line_video.py` - builder (clips -> narration + schedule + SRT + MP4).
- `scripts/verify_line_video.py` - checks the finished MP4 against its schedule.
- Example run: `deliverable/genre_videos/03_emotion_lines/` (lines.json + clip_01..10.mp3)
  -> `03_emotion_video.mp4`, `03_emotion_narration.mp3`, `03_emotion_schedule.json`, `03_emotion.srt`.
