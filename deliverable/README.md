# 爆款商业变现实战 Skill 案例包（结果路径总览）

本目录是 5 个商业 Skills 的**成功案例输出**，由 `code/build_commercial_cases.py` 一键生成并通过 3a-3g 结构自检（哈希/字节、OOXML 必需部件、XML 解析、关系不断链、内容类型、文本标记、页数），清单见 [OFFICE_HASHES.json](./OFFICE_HASHES.json)。本机值守会在 `code/local_check.ps1` 中复验同一份清单（3h 还会用真 Word/WPS 只读打开每个 Office 文件）。

## 案例 01 · 闲鱼电商从 0-1 保姆级实战（`xianyu-ecommerce-sop`）

| 产物 | 路径 |
|---|---|
| 《2026 闲鱼电商从 0-1 保姆级实战手册》Word | [`cases/01_xianyu_ecommerce/xianyu_ecommerce_manual.docx`](./cases/01_xianyu_ecommerce/xianyu_ecommerce_manual.docx) |
| 飞书多维表格订单复盘模板 CSV | [`cases/01_xianyu_ecommerce/xianyu_review_tracker.csv`](./cases/01_xianyu_ecommerce/xianyu_review_tracker.csv) |
| 闲鱼商品首图视觉示意（AI 生成） | [`cases/01_xianyu_ecommerce/xianyu_product_scene.png`](./cases/01_xianyu_ecommerce/xianyu_product_scene.png) |

内容：双轨模型（虚拟资料盘/高客单无货源）、店铺四件套包装、五步循环选品法、黄金 30 字 SEO 标题公式、5 图黄金主图结构、详情页 6 段式模板、无痕代发 6 步 SOP、客服逼单与防骗话术、飞书数据复盘诊断表、30 天冷启动日历。

## 案例 02 · AI 民间故事视频·视频号分成计划（`ai-folktale-video-sop`）

| 产物 | 路径 |
|---|---|
| 《雪夜来客》视频制作包 Word（剧本+12 镜分镜表+运营） | [`cases/02_folktale_video/folktale_video_package.docx`](./cases/02_folktale_video/folktale_video_package.docx) |
| Coze 三节点一键工作流蓝图 JSON | [`cases/02_folktale_video/coze_workflow_blueprint.json`](./cases/02_folktale_video/coze_workflow_blueprint.json) |
| 分镜 03 概念图（国风悬疑，AI 生成） | [`cases/02_folktale_video/folktale_scene_01_carpenter.png`](./cases/02_folktale_video/folktale_scene_01_carpenter.png) |
| 视频号竖屏封面概念图（9:16，AI 生成） | [`cases/02_folktale_video/folktale_cover_vertical.png`](./cases/02_folktale_video/folktale_cover_vertical.png) |

内容：黄金前 3 秒钩子 + 三幕六段式约 560 字剧本全文、Character Lock 角色一致性锁死 12 镜分镜表（每镜中文提示词）、统一画风前缀、Coze 工作流四节点配置（含 5 组爆款标题与置顶评论话术）、剪映 10 分钟成片参数、视频号分成计划高 RPM 运营。

## 案例 03 · 学科课件 0 到 1 变现全流程（`courseware-monetization-sop`）

| 产物 | 路径 |
|---|---|
| 《秋天的雨》10 页全可编辑公开课 PPTX | [`cases/03_courseware_sop/autumn_rain_courseware.pptx`](./cases/03_courseware_sop/autumn_rain_courseware.pptx) |
| 新课标教案 + 逐页逐字稿 + 小红书种草笔记 Word | [`cases/03_courseware_sop/autumn_rain_teaching_package.docx`](./cases/03_courseware_sop/autumn_rain_teaching_package.docx) |
| 秋天主题课件插图（AI 生成） | [`cases/03_courseware_sop/courseware_illustration_autumn.png`](./cases/03_courseware_sop/courseware_illustration_autumn.png) |
| 小红书种草笔记首图（AI 生成） | [`cases/03_courseware_sop/xiaohongshu_cover_note.png`](./cases/03_courseware_sop/xiaohongshu_cover_note.png) |

内容：10 页大单元情境教学课件（封面/情境导入/核心素养目标/字词闯关表/五彩秋色卡片/气味品读/悟情升华/小练笔分层作业表/结构化板书/封底，57 个原生可编辑形状）、2022 版新课标教案、逐页课堂逐字稿（含互动预设与评价语）、SKU 三档定价、小红书爆款标题 3 组与种草正文、话题标签与挂链闭环。

## 案例 04 · AI 代做商业计划书·一单 1000+（`ai-business-plan-sop`）

| 产物 | 路径 |
|---|---|
| 《智护银龄》天使轮商业计划书 Word 详版（含 3 年财务三表+接单 SOP 附录） | [`cases/04_business_plan/smart_eldercare_bp.docx`](./cases/04_business_plan/smart_eldercare_bp.docx) |
| 12 页咨询级路演 PPTX（全可编辑） | [`cases/04_business_plan/smart_eldercare_pitch.pptx`](./cases/04_business_plan/smart_eldercare_pitch.pptx) |
| BP 封面视觉大图（AI 生成） | [`cases/04_business_plan/bp_cover_visual.png`](./cases/04_business_plan/bp_cover_visual.png) |

内容：8 大黄金模块完整成稿（执行摘要/痛点与 TAM-SAM-SOM 三层测算/产品方案与 3 大壁垒/商业模式与单位经济/竞争五维矩阵/GTM 三阶段路线图/团队与股权/融资方案与 3 年财务预测表），Word 详版附录含三档阶梯报价、老板 8 问诊断问卷、8 大接单渠道清单、334 分阶段收款防跑单 SOP。

## 复现方法（一键重建全部案例）

```bash
python3 code/build_commercial_cases.py            # 构建 4 案例 + 写 OFFICE_HASHES.json
python3 code/build_commercial_cases.py --only bp  # 只重建一个案例
python3 code/build_commercial_cases.py --verify   # 只复验 3a-3g 结构
```

## 免责声明

本案例包为技能方法论与流程示例，不构成任何收益承诺；文中市场与财务数据为教学示例测算。请遵守各平台（闲鱼、视频号、小红书等）规则与相关法律法规，AI 生成内容请按平台要求声明。
