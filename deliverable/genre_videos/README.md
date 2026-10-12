# 类型菜单 12 款文案视频 全部完成

每款 1 支竖屏成片（1080x1920，25fps，时长随旁白约 32-42 秒）：AI 配音旁白 + **对齐到语音的字幕** + 双场景 Ken Burns 运镜（11/12 为单场景）。

字幕对齐采用本仓库新技能 `skills/subtitle-align/`（停顿感知强制对齐）：由 `code/align_subtitles.py` 先听旁白停顿、把每句字幕映射到语音真实时间，再烧录字幕、合成视频。每款附 `<id>.srt`（通用字幕文件）与 `<id>_schedule.json`（对齐时间表）。

| # | 类型 | 标题 | 成片 | 旁白 | 文案 | 对齐表 | 时长 |
|--|--|--|--|--|--|--|--|
| 02 | 历史人物 | 苏东坡：一蓑烟雨任平生 | `02_history_video.mp4` | `02_history_narration.mp3` | `02_history_script.txt` | `02_history_schedule.json` / `02_history.srt` | 42s |
| 03 | 情感鸡汤 | 致负重前行的你 | `03_emotion_video.mp4` | `03_emotion_narration.mp3` | `03_emotion_script.txt` | `03_emotion_schedule.json` / `03_emotion.srt` | 32s |
| 04 | 童话寓言 | 小狐狸的月亮灯笼 | `04_fable_video.mp4` | `04_fable_narration.mp3` | `04_fable_script.txt` | `04_fable_schedule.json` / `04_fable.srt` | 32s |
| 05 | 悬疑推理 | 末班车的第三位乘客 | `05_suspense_video.mp4` | `05_suspense_narration.mp3` | `05_suspense_script.txt` | `05_suspense_schedule.json` / `05_suspense.srt` | 37s |
| 06 | 科普知识 | 冬天晒太阳的大学问 | `06_science_video.mp4` | `06_science_narration.mp3` | `06_science_script.txt` | `06_science_schedule.json` / `06_science.srt` | 32s |
| 07 | 书单推荐 | 人到中年必读三本书 | `07_booklist_video.mp4` | `07_booklist_narration.mp3` | `07_booklist_script.txt` | `07_booklist_schedule.json` / `07_booklist.srt` | 32s |
| 08 | 带货种草 | 这条加绒牛仔裤 卖爆十万条 | `08_product_video.mp4` | `08_product_narration.mp3` | `08_product_script.txt` | `08_product_schedule.json` / `08_product.srt` | 33s |
| 09 | 美食教程 | 外婆的红烧肉 | `09_food_video.mp4` | `09_food_narration.mp3` | `09_food_script.txt` | `09_food_schedule.json` / `09_food.srt` | 32s |
| 10 | 旅行种草 | 风花雪月的尽头是洱海 | `10_travel_video.mp4` | `10_travel_narration.mp3` | `10_travel_script.txt` | `10_travel_schedule.json` / `10_travel.srt` | 33s |
| 11 | 古诗词 | 将进酒（李白） | `11_poetry_video.mp4` | `11_poetry_narration.mp3` | `11_poetry_script.txt` | `11_poetry_schedule.json` / `11_poetry.srt` | 35s |
| 12 | 商业案例 | 一个人开公司的第一课 | `12_business_video.mp4` | `12_business_narration.mp3` | `12_business_script.txt` | `12_business_schedule.json` / `12_business.srt` | 38s |

（第 1 款「小猫钓鱼」为技能定位示例词，不做成片；民间故事（雪夜来客）成片在 `deliverable/cases/02_folktale_video/`。）

## 本地重跑

```powershell
python3 code/build_genre_videos.py            # 全部 11 款
python3 code/build_genre_videos.py 07_booklist # 只做一款
```

素材图在 `scenes/`（AI 生成底图，竖版 2:3）；字幕对齐细节见 `skills/subtitle-align/SKILL.md`。
