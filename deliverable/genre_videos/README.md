# 12 类视频成片包（genre_videos）

> 每款 = 竖屏成片 MP4（1080x1920，中文字幕 + 说书配音）+ 配音稿音频。
> 全部由同一套流水线生成（`code/build_genre_videos.py`），可复现。

| # | 品类 | 成片 | 状态 |
|---|---|---|---|
| 01 | 民间故事/奇闻 | [`../cases/02_folktale_video/folktale_story_video.mp4`](../cases/02_folktale_video/folktale_story_video.mp4)《雪夜来客》2:10 | ✅ |
| 02 | 历史人物解说 | [`02_history_video.mp4`](02_history_video.mp4)《苏东坡：一蓑烟雨任平生》 | ✅ |
| 03 | 情感语录/情感电台 | [`03_emotion_video.mp4`](03_emotion_video.mp4)《致负重前行的你》 | ✅ |
| 04 | 童话寓言/睡前故事 | [`04_fable_video.mp4`](04_fable_video.mp4)《小狐狸的月亮灯笼》 | ✅ |
| 05 | 都市传说/悬疑反转 | [`05_suspense_video.mp4`](05_suspense_video.mp4)《末班车的第三位乘客》 | ✅ |
| 06 | 生活科普/健康常识 | [`06_science_video.mp4`](06_science_video.mp4)《冬天晒太阳的大学问》 | ✅ |
| 07 | 书单号/读书推荐 | 《人到中年必读三本书》 | 生成中 |
| 08 | 商品带货短视频 | 《这条加绒牛仔裤 卖爆十万条》 | 生成中 |
| 09 | 美食菜谱解说 | 《外婆的红烧肉》 | 生成中 |
| 10 | 旅行风光/地理解说 | 《风花雪月的尽头是洱海》 | 生成中 |
| 11 | 诗词朗诵/国学 | 《将进酒（李白）》 | 生成中 |
| 12 | 职场/商业知识口播 | 《一个人开公司的第一课》 | 生成中 |

## 规格

- 竖屏 1080x1920 / 25fps / H.264 + AAC 说书配音（voice-00，配速自动对齐画面）
- 每款约 60 秒：分镜 Ken Burns 运镜 + 下三分之一黄字黑边字幕
- 命名规则：`<id>_video.mp4`（成片）、`<id>_narration.mp3`（配音）、`scenes/<id>_<n>.jpg`（分镜图）

## 复现

```bash
python3 code/build_genre_videos.py            # 全部重建
python3 code/build_genre_videos.py 02_history  # 只重建一款
```

*发布建议：视频号勾选原创声明；标题/置顶评论话术见各品类配音稿结尾的互动引导。*
