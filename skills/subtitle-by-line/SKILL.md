---
name: subtitle-by-line
description: Make subtitles match a narration EXACTLY, in ONE turn, by generating one TTS clip per subtitle CARD (a card = one or more rows shown together) and building the video from those clips. Use for any narrated video whose subtitles must line up with the voice. Replaces estimate-based alignment (subtitle-align), which put text in the wrong place.
---

# subtitle-by-line

## Why this exists

Estimating where each character sits inside a finished narration (energy peaks,
VAD, DP alignment) left subtitles visibly out of step with the voice, and no ASR
model is reachable to check it. This skill avoids guessing: each subtitle card
IS its own audio clip, so its start and length come from that clip.

## Limits that shape the recipe

- `generate_speech` makes at most **10 clips per turn**. So the video needs at most
  **10 cards**, and all 10 are generated in the same turn.
- A card can have up to **4 rows** of about 18 characters (the rows appear together).
  So a card holds about 50 to 60 characters, and a video of about 500 characters fits in 10 cards.
- A single-row line per clip (old recipe) only works for <= 10 lines in total.

## One-turn recipe

1. **Cut the script into cards.**
   ```bash
   python3 skills/subtitle-by-line/scripts/split_cards.py narration_script.txt \
       --cards 9 --out-dir work/
   ```
   It writes `work/cards.json` (TTS text, one per card) and `work/lines.json`
   (subtitle rows, joined by newline). Cuts only happen at clause punctuation,
   and card sizes are balanced. Raise `--cards` (up to 10) if a card needs more than 4 rows.
2. **Generate one clip per card, all in ONE turn**, in parallel, with the same
   `voice_id`. Save as `work/clip_01.mp3`, ... in the same order. The clip text
   must equal `cards.json[i]` exactly.
3. **Build:**
   ```bash
   SUB_FONT=/tmp/font/NotoSansSC.ttf \
   python3 skills/subtitle-by-line/scripts/build_line_video.py \
       --work work --out-dir out --scenes s1.png s2.png ...
   ```
   Output in `out/`: `video.mp4`, `narration.mp3`, `schedule.json`, `subtitles.srt`.
4. **Verify** (do not skip):
   ```bash
   python3 skills/subtitle-by-line/scripts/verify_line_video.py \
       --video out/video.mp4 --schedule out/schedule.json
   ```
   It checks that every card's window holds speech and every gap is quiet. Exit 0 = PASS.
5. Copy the results to the deliverable folder, `bash code/check_all.sh`, commit, push.

Short videos (<= 10 lines, one row each) can skip step 1 and use one clip per line.

## How timing is computed

- Clip `i` starts at `t_i` (video time) and lasts `d_i` seconds. `d_i` is decoded
  from the MP3 samples, not the header (headers are off by about 0.04 s per clip).
- After each clip there is a fixed pause (default 0.25 s), then clip `i+1`.
- The card shows from `t_i` to `t_i + max(d_i, 0.8)`, capped so it never overlaps the next card.
- The narration is the clips joined with the same pauses, so voice and subtitles share one clock.

## Font

Imageio-ffmpeg has no drawtext, so subtitles are PIL-rendered PNG overlays, which
need a CJK font. The sandbox may not have one. Fetch Noto Sans SC from npm and convert:
```bash
cd /tmp/font && npm pack @fontsource/noto-sans-sc@5 && tar xzf fontsource-noto-sans-sc-5.3.1.tgz
pip install --user fonttools brotli
python3 -c "from fontTools.ttLib import TTFont; t=TTFont('package/files/noto-sans-sc-chinese-simplified-400-normal.woff2'); t.flavor=None; t.save('/tmp/font/NotoSansSC.ttf')"
```
Then set `SUB_FONT=/tmp/font/NotoSansSC.ttf`.

## Pitfalls already hit

- ffmpeg `concat` list files resolve relative paths against the list file's folder.
  Pass absolute paths (the scripts do this).
- Do not use `-shortest` with `-c:v copy` and `apad` (it hangs). Use `-t`.
- Inside a card, rows are one subtitle, so they appear and disappear together.
  That is the trade-off for one-turn exactness.
- The sandbox can lose `/tmp` and pip packages between sessions. Re-check the font and `numpy` / `Pillow` / `imageio-ffmpeg` / `onnxruntime` before building.

## Files

- `scripts/split_cards.py` - script -> balanced cards (TTS text) + subtitle rows.
- `scripts/build_line_video.py` - clips -> narration + schedule + SRT + MP4.
- `scripts/verify_line_video.py` - checks the finished MP4 against its schedule.
- Examples:
  - `deliverable/cases/02_folktale_video/cards_v4/` (9 cards) -> `folktale_story_video.mp4` (this version).
  - `deliverable/genre_videos/03_emotion_lines/` (10 lines) -> `03_emotion_video.mp4`.
