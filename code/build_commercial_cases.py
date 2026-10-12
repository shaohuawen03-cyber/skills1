#!/usr/bin/env python3
# build_commercial_cases.py - build the four commercial monetization case
# deliverables (xianyu ecommerce / folktale video / courseware SOP / business
# plan) plus deliverable/OFFICE_HASHES.json, the manifest the REAL machine
# verifies in code/local_check.ps1 section 3 (3a-3g), and the same 3a-3g rules
# are mirrored here in Python so a package that cannot pass is never pushed.
#
# Usage:
#   python3 code/build_commercial_cases.py                # build everything
#   python3 code/build_commercial_cases.py --only xianyu  # one case
#   python3 code/build_commercial_cases.py --verify       # re-run the mirror
#
# The AI-generated cover art (PNG) is produced by the image tool and lives in
# each case folder; this script only builds the Office documents around it and
# never overwrites the images.

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
CASES = os.path.join(ROOT, 'deliverable', 'cases')
MANIFEST = os.path.join(ROOT, 'deliverable', 'OFFICE_HASHES.json')

DOCX_REQ = ['[Content_Types].xml', '_rels/.rels', 'word/document.xml',
            'word/styles.xml', 'word/_rels/document.xml.rels', 'docProps/core.xml']
PPTX_REQ = ['[Content_Types].xml', '_rels/.rels', 'ppt/presentation.xml',
            'ppt/_rels/presentation.xml.rels', 'ppt/slides/slide1.xml',
            'ppt/slideMasters/slideMaster1.xml', 'ppt/slideLayouts/slideLayout1.xml',
            'ppt/theme/theme1.xml', 'docProps/core.xml']


# ----------------------------------------------------------------- docx utils
def docx_new():
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Microsoft YaHei'
    style.font.size = Pt(10.5)
    return doc


def docx_heading(doc, text, level):
    doc.add_heading(text, level=level)


def docx_para(doc, text, bold=False, style=None):
    p = doc.add_paragraph(style=style)
    run = p.add_run(text)
    run.bold = bold
    return p


def docx_bullets(doc, items):
    for it in items:
        doc.add_paragraph(it, style='List Bullet')


def docx_table(doc, headers, rows):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Table Grid'
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            cells[i].text = str(value)
    return table


# ----------------------------------------------------------------- pptx utils
NAVY = (31, 78, 121)
TEAL = (0, 140, 140)
ORANGE = (237, 125, 49)
GREEN = (39, 144, 86)
LIGHT = (222, 235, 247)
CREAM = (242, 246, 250)
WHITE = (255, 255, 255)
DARK = (44, 55, 66)


def pptx_new():
    from pptx import Presentation
    from pptx.util import Inches
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def _rgb(shape_fill, color):
    shape_fill.fore_color.rgb = __import__('pptx').dml.color.RGBColor(*color)


def slide_shell(prs, title, subtitle=None, accent=NAVY, page=None):
    from pptx.util import Inches, Pt
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # left accent bar
    bar = slide.shapes.add_shape(1, 0, 0, Inches(0.22), prs.slide_height)
    bar.fill.solid(); _rgb(bar.fill, accent); bar.line.fill.background()
    # title band
    band = slide.shapes.add_shape(1, Inches(0.22), 0, prs.slide_width - Inches(0.22), Inches(1.05))
    band.fill.solid(); _rgb(band.fill, accent); band.line.fill.background()
    tb = band.text_frame
    tb.clear()
    tb.word_wrap = True
    p = tb.paragraphs[0]
    p.text = title
    p.font.size = Pt(26)
    p.font.bold = True
    p.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
    if subtitle:
        p2 = tb.add_paragraph()
        p2.text = subtitle
        p2.font.size = Pt(12)
        p2.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
    # footer strip
    foot = slide.shapes.add_shape(1, 0, prs.slide_height - Inches(0.32), prs.slide_width, Inches(0.32))
    foot.fill.solid(); _rgb(foot.fill, CREAM); foot.line.fill.background()
    ftf = foot.text_frame
    ftf.clear()
    fp = ftf.paragraphs[0]
    fp.text = '智护银龄 · AI 居家养老健康监测系统 · 天使轮融资路演（示例教学版）'
    fp.font.size = Pt(9)
    fp.font.color.rgb = __import__('pptx').dml.color.RGBColor(*DARK)
    if page is not None:
        badge = slide.shapes.add_shape(9, prs.slide_width - Inches(0.75), prs.slide_height - Inches(0.72),
                                       Inches(0.45), Inches(0.45))
        badge.fill.solid(); _rgb(badge.fill, accent); badge.line.fill.background()
        btf = badge.text_frame
        btf.clear()
        bp = btf.paragraphs[0]
        bp.text = str(page)
        bp.font.size = Pt(12)
        bp.font.bold = True
        bp.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
        bp.alignment = 2
    return slide


def bullets_on(slide, left, top, width, height, items, size=15):
    from pptx.util import Inches, Pt
    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    tf.clear()
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.text = item
        p.font.size = Pt(size)
        p.font.color.rgb = __import__('pptx').dml.color.RGBColor(*DARK)
        p.space_after = Pt(6)
    return box


def card_on(slide, left, top, width, height, title, body, fill=LIGHT, title_color=NAVY):
    from pptx.util import Inches, Pt
    card = slide.shapes.add_shape(5, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid(); _rgb(card.fill, fill); card.line.color.rgb = __import__('pptx').dml.color.RGBColor(*fill)
    tf = card.text_frame
    tf.word_wrap = True
    tf.clear()
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = __import__('pptx').dml.color.RGBColor(*title_color)
    for line in body:
        p2 = tf.add_paragraph()
        p2.text = line
        p2.font.size = Pt(11)
        p2.font.color.rgb = __import__('pptx').dml.color.RGBColor(*DARK)
    return card


def table_on(slide, left, top, width, height, headers, rows, font=10):
    from pptx.util import Inches, Pt
    shape = slide.shapes.add_table(len(rows) + 1, len(headers),
                                   Inches(left), Inches(top), Inches(width), Inches(height))
    table = shape.table
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        for paragraph in cell.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
                run.font.size = Pt(font)
                run.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
        cell.fill.solid(); _rgb(cell.fill, NAVY)
    for r, row in enumerate(rows, start=1):
        for c, value in enumerate(row):
            cell = table.cell(r, c)
            cell.text = str(value)
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(font)
            cell.fill.solid()
            _rgb(cell.fill, WHITE if r % 2 else CREAM)
    return table


def picture_on(slide, path, left, top, width=None, height=None):
    from pptx.util import Inches
    kwargs = {}
    if width:
        kwargs['width'] = Inches(width)
    if height:
        kwargs['height'] = Inches(height)
    if os.path.isfile(path):
        slide.shapes.add_picture(path, Inches(left), Inches(top), **kwargs)


# ============================================================ case 1: xianyu
def build_xianyu():
    out = os.path.join(CASES, '01_xianyu_ecommerce')
    os.makedirs(out, exist_ok=True)
    doc = docx_new()
    doc.core_properties.title = '2026 闲鱼电商从 0-1 保姆级实战手册'

    docx_heading(doc, '2026 闲鱼电商从 0-1 保姆级实战手册', 0)
    docx_para(doc, '配套 Skill：skills/commercial/xianyu-ecommerce-sop · 案例输出目录：deliverable/cases/01_xianyu_ecommerce/')
    docx_para(doc, '声明：本手册为方法论与流程示例，不构成任何收益承诺，实际效果因人而异，请严格遵守闲鱼平台规则与相关法律法规。')

    scene = os.path.join(out, 'xianyu_product_scene.png')
    if os.path.isfile(scene):
        doc.add_picture(scene)
        docx_para(doc, '图 1：闲鱼商品首图视觉方向示意（AI 生成底图，可用作详情页场景图）')

    docx_heading(doc, '第一章 · 项目全景：2026 年闲鱼还能不能做', 1)
    docx_bullets(doc, [
        '市场面：消费降级推动二手与尾货交易持续增长，闲鱼日活与搜索流量仍是个人卖家最大的免费流量池。',
        '平台面：2026 年闲鱼持续更新"玩家号、鱼小铺、自动发货、放心充"等功能，虚拟资料与高客单实物两条赛道都有新红利。',
        '个人面：一部手机、每天 1-2 小时，零囤货、零保证金（虚拟资料），低试错成本，适合学生、职场新人长期做。',
        '本手册双轨模型：① AI 原创虚拟资料盘（0 成本高复利）② 高客单无货源实物盘（单笔利润 40-300 元）。',
    ])

    docx_heading(doc, '第二章 · 账号与店铺精细化包装（四件套）', 1)
    docx_table(doc, ['要素', '公式', '虚拟资料版示例', '无货源实物版示例'], [
        ['昵称', '[身份/场景词]+[温和名字]', '林老师教研室', '小鹿办公好物清仓'],
        ['头像', '生活化半身照或温暖书桌实拍', '教师办公桌实拍', '仓库实拍/本人出镜'],
        ['简介', '身份背书+来源+发货时效+售后', '一线教师自整理课件，拍下秒发网盘', '工作室搬迁清仓，全新未拆封包邮'],
        ['四件套一致性', '头像/昵称/背景/简介同一人设', '统一"教研室"视觉', '统一"清仓"视觉'],
    ])

    docx_heading(doc, '第三章 · 五步循环爆款选品法', 1)
    docx_bullets(doc, [
        'Step 1 搜索框下拉词截流：搜索核心词，记录前 10 个高热度联想词。',
        'Step 2 筛蓝海：想要人数 > 50、近 7 天发布、个人闲置类目优先。',
        'Step 3 跨平台搬运：小红书/抖音高赞种草贴（点赞 > 1000、评论区高频"求链接"）同步上架。',
        'Step 4 同行跟款：找到想要数破百的同行店铺，跟其最新连续出单 TOP 3 链接。',
        'Step 5 一品多链裂变：同一产品 3-5 套差异化主图+标题+文案，早 8:00、午 12:30、晚 20:30 分时段测品。',
    ])

    docx_heading(doc, '第四章 · 黄金 30 字 SEO 标题公式', 1)
    docx_para(doc, '公式：【热搜前缀/人设词】+ 核心大词 + 细分属性词 + 痛点/场景词 + 交付后缀。闲鱼搜索权重集中在前 12 个字，务必把最强搜索词放最前。')
    docx_table(doc, ['场景', '标题示例'], [
        ['学科课件', '【一线教师自整理】三年级语文上册公开课PPT课件教案逐字稿全套可编辑秒发'],
        ['商业计划书', '【投行顾问代写】AI定制商业计划书BP融资路演PPT撰写财务预测包修改'],
        ['无货源实物', '【搬家急出全新未拆】人体工学椅办公椅久坐护腰家用电脑椅包邮'],
    ])

    docx_heading(doc, '第五章 · 商品主图 5 图黄金结构', 1)
    docx_table(doc, ['图序', '作用', '制作要点'], [
        ['第 1 张首图', '决定 80% 点击率', '真实场景底图 + 醒目大字标签（不超过 10 字）'],
        ['第 2 张全景', '感知分量与超值', '目录/文件夹截图、页数、数量'],
        ['第 3 张样张', '证明品质', '4-6 页高清内页拼图'],
        ['第 4 张赠品', '拉升转化', '赠品清单+新人券'],
        ['第 5 张保障', '打消顾虑', '秒发流程+售后承诺'],
    ])

    docx_heading(doc, '第六章 · 高转化详情页 6 段式模板', 1)
    docx_bullets(doc, [
        '① 痛点钩子 + 人设起因；② 核心交付清单（带编号与格式说明）；',
        '③ 三大差异化亮点；④ 发货方式（虚拟秒发网盘 / 实物 24-48 小时发货）；',
        '⑤ 合规声明（文案内不出现价格数字，不写绝对化违禁词）；⑥ CTA：链接在就是有货，点"我想要"看更多样张。',
    ])

    docx_heading(doc, '第七章 · 发货 SOP', 1)
    docx_para(doc, '上架前先做 SKU 规划：每个产品按"引流款（9.9 元体验）- 利润款（29.9 元主力）- 高客单款（69.9 元合集）"三档设置 SKU，并在详情页写清每档交付清单差异。', bold=True)
    docx_para(doc, '虚拟资料：闲鱼管家/阿奇索自动发货，付款后自动发网盘链接+提取码，好评后补发进阶资料包。', bold=True)
    docx_para(doc, '无货源无痕代发 6 步：', bold=True)
    docx_bullets(doc, [
        '1 复制买家信息到拼多多/1688 下单；2 改收件人姓名加备注码、启用匿名/无痕发货防短信暴露货源；',
        '3 复制上家真实单号；4 闲鱼"我已卖出"→"去发货"→"我已寄出"；5 填快递公司与单号；6 发送发货提醒话术。',
    ])

    docx_heading(doc, '第八章 · 客服话术与防骗', 1)
    docx_table(doc, ['场景', '话术要点'], [
        ['询单秒回', '在的亲！2026 最新修订版，PPT+教案+逐字稿全套可编辑，拍下 3 秒自动发网盘，今天拍送题库包。'],
        ['砍价应对', '不直接降价，改为确认收货后送价值 19.9 元同科期末大礼包，保住价格体系。'],
        ['防骗铁律', '"扫码联系客服解冻资金/未开通消保"100% 是诈骗，正规交易全部在 APP 内直接拍下付款。'],
    ])

    docx_heading(doc, '第九章 · 飞书多维表格数据化复盘', 1)
    docx_para(doc, '每日记录字段：日期 | 链接ID | 标题版本 | 曝光 | 浏览 | 想要 | 成交 | 客单价 | 成本 | 净利润 | 想要转化率。')
    docx_table(doc, ['症状', '诊断', '动作'], [
        ['曝光 < 200', '标题/类目/时段弱', '换前 12 字热搜词，改黄金时段发布'],
        ['点击率 < 3%', '首图不吸睛', '换真实场景底图、加大痛点字号'],
        ['想要率 < 5%', '详情不信任', '优化前 3 行交付清单与第 2-3 张样张'],
    ])

    docx_heading(doc, '第十章 · 30 天冷启动日历（摘要）', 1)
    docx_bullets(doc, [
        'D1-D3：完善四件套、养号、选 2 个赛道各 3 个品；D4-D10：一品多链上架 15 条，每天 3 条分时段；',
        'D11-D20：按复盘表淘汰后 50%，爆款裂变加链接；D21-D30：沉淀自动发货与话术库，稳定日出 3-10 单。',
    ])

    manual = os.path.join(out, 'xianyu_ecommerce_manual.docx')
    doc.save(manual)

    csv_path = os.path.join(out, 'xianyu_review_tracker.csv')
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as fh:
        fh.write('日期,商品链接ID,标题版本,曝光量,浏览量PV,想要数,成交单数,客单价,采购成本,净利润,想要转化率,备注\n')
        for i in range(1, 8):
            fh.write('2026-10-%02d,SKU-%03d,版本A,0,0,0,0,0,0,0,0,示例行请替换\n' % (i, i))

    print('built: %s' % os.path.relpath(manual, ROOT))
    print('built: %s' % os.path.relpath(csv_path, ROOT))
    return [
        (manual, 'docx', DOCX_REQ, 'word/document.xml',
         ['闲鱼', '五步循环', '无痕代发', '飞书多维表格', 'SKU'], None),
    ]


# ========================================================== case 2: folktale
def build_folktale():
    out = os.path.join(CASES, '02_folktale_video')
    os.makedirs(out, exist_ok=True)
    doc = docx_new()
    doc.core_properties.title = '民间故事视频制作包：雪夜来客'

    docx_heading(doc, 'AI 民间故事视频制作包：《雪夜来客》', 0)
    docx_para(doc, '配套 Skill：skills/commercial/ai-folktale-video-sop · 输出目录：deliverable/cases/02_folktale_video/')
    docx_para(doc, '赛道数据：民间故事类内容在视频号/抖音单月播放量超 200 亿次，小红书 #民间奇闻 阅读量 53 亿。视频号创作者分成计划 100 粉丝即可开通，中老年高停留受众的评论区广告分成 RPM 显著高于泛娱乐赛道。')

    for img, cap in [('folktale_scene_01_carpenter.png', '图 1：分镜 03 概念图（老木匠雨夜开门）'),
                     ('folktale_cover_vertical.png', '图 2：视频号竖屏封面概念图（雪夜开门）')]:
        p = os.path.join(out, img)
        if os.path.isfile(p):
            doc.add_picture(p)
            docx_para(doc, cap)

    docx_heading(doc, '一、黄金前 3 秒钩子 + 三幕六段式剧本（全文约 560 字）', 1)
    docx_para(doc, '【钩子 0-10s】老辈人常说："木匠忌讳接三更活，渡人莫渡无影客。"可乾隆十八年的除夕雪夜，徽州老木匠陈三斤，偏偏接了一单不露脸的急活。', bold=True)
    docx_para(doc, '【第一幕 · 起（10-30s）】那天雪下得正紧，柴门被叩响三声。门外立着一个披蓑衣的黑影，看不清脸，只递进一锭冰凉的官银："老师傅，照这尺寸，打一口小匣子。今夜就要。"陈三斤本不想接，可想起家中卧病的老妻等着抓药，还是把银子攥进了手心。')
    docx_para(doc, '【第一幕 · 承（30-60s）】他点起灯开工，越做越不对：那木料奇香，入手沉如铁；量尺寸时，鲁班尺上"病""离"二字正对木纹；而门外雪地上，来时的一行脚印，竟浅得几乎看不见。')
    docx_para(doc, '【第二幕 · 转（60-90s）】三更天，匣子将成，村口忽然传来锣声。乡邻披衣来报：渡口的无影客又出来了，专在除夕夜敲老实人的门！众人劝他把银子扔了，陈三斤却摇摇头："活可以不做，人不能失信。"他提灯出了门。')
    docx_para(doc, '【第二幕 · 合（90-115s）】雪地尽头，蓑衣客接过匣子，缓缓掀开斗笠，竟是二十年前那个被他从冰河里捞起的落难书生，如今的新任县令！当年一饭一宿之恩，今夜以官银相谢，并赠良药医其老妻。所谓"无影客"，不过是有钱人装鬼试人心的旧把戏，被好心人讹传至今。')
    docx_para(doc, '【第三幕 · 升华（115-130s）】后来徽州人都记住了陈三斤的话："手艺人守的是规矩，行的是良心。"老话讲：但行好事，莫问前程。您说，这世道是不是这个理？评论区留下"善有善报"，为家人积一份福。', bold=True)

    docx_heading(doc, '二、12 镜分镜表（Character Lock 角色一致性锁死）', 1)
    docx_para(doc, '统一画风前缀（Style Prefix，每镜必带）：中式传统水墨厚涂插画风格，国风悬疑电影感，丁达尔暖黄灯笼光与青黛夜雾对比，工笔细节，8K 超高清。')
    docx_para(doc, '固定角色锚点（Character Anchor，陈三斤出镜必带）：62 岁中国古代老木匠，花白胡须，面容慈祥，深褐色粗布短褐，腰别黄铜鲁班尺，头戴青布方巾。')

    shots = [
        ('01', '0-5s', '老辈人常说：木匠忌讳接三更活。', '远景·风雪古村', '徽州古村除夕夜，大雪纷飞，黑瓦白墙，家家红灯笼，一条雪路延伸向山坳'),
        ('02', '5-10s', '乾隆十八年除夕雪夜，急促叩门声。', '中景·柴门', '深夜木屋柴门紧闭，门缝透出暖黄油灯光，一个蓑衣黑影立于门外风雪中，脚印极浅'),
        ('03', '10-20s', '门外黑影递进一锭冰凉官银。', '近景·门缝递银', '门缝中一只枯瘦手递进一锭银元宝，老木匠双手捧银，油灯映出他犹豫的皱纹'),
        ('04', '20-30s', '想起卧病老妻，他攥紧了银子。', '特写·手与银', '老木匠粗糙的手攥紧银元宝，背景虚化处病榻与药罐剪影，暖黄灯光'),
        ('05', '30-45s', '点灯开工，木料奇香，入手沉如铁。', '中近景·工作台', '老木匠在工作台刨木，刨花卷曲，案上香木料与墨斗角尺，油灯摇曳，窗外风雪'),
        ('06', '45-60s', '鲁班尺上"病""离"二字正对木纹。', '大特写·鲁班尺', '黄铜鲁班尺压在深色木纹上，刻度红字清晰，老人手指微颤，烛光反射金属光泽'),
        ('07', '60-70s', '来时脚印，竟浅得几乎看不见。', '俯视·雪地脚印', '俯瞰雪地，一行浅得若有若无的脚印通向黑暗竹林，红灯笼光晕在雪面边缘'),
        ('08', '70-80s', '三更锣声惊破夜，乡邻披衣奔走报信。', '全景·村道夜奔', '深夜村道，几个村民提灯奔跑呼喊，屋檐灯笼摇晃，大雪横飞，戏剧性光影'),
        ('09', '80-90s', '"把银子扔了吧，那是无影客！"', '双人中景·屋内争执', '屋内村民围着老木匠争相劝阻，手势激动，老木匠摇头，油灯映出他坚定侧脸'),
        ('10', '90-100s', '"活可以不做，人不能失信。"他提灯出门。', '逆光·门口剪影', '老木匠提着灯笼跨出门槛，风雪扑面，身后暖光，身形逆光剪影，雪片飞舞'),
        ('11', '100-115s', '蓑衣客掀开斗笠，竟是当年的落难书生。', '近景·掀笠相认', '风雪中蓑衣客人掀开斗笠露出县令温润面容，与老木匠灯笼下对视，泪光与笑意交织'),
        ('12', '115-130s', '但行好事，莫问前程。', '远景·雪霁天明', '雪霁初晴的古村晨景，红灯笼映雪，炊烟升起，一行新脚印通向远方，字幕留金句'),
    ]
    docx_table(doc, ['镜号', '时间轴', '旁白台词', '景别运镜', '分镜提示词（中文，拼接画风前缀+角色锚点）'], shots)

    docx_heading(doc, '三、Coze（扣子）三节点一键工作流（coze_workflow_blueprint.json）', 1)
    docx_bullets(doc, [
        '开始节点：story_theme / protagonist / scene_style / cultural_element 四个输入变量。',
        '大模型节点 1（DeepSeek-R1 故事架构师）：输出 550 字三幕六段式高反转故事+角色锚点。',
        '大模型节点 2（分镜编译器）：拆 12 镜，自动拼接 Style Prefix + Character Anchor，出即梦/豆包/可灵提示词。',
        '大模型节点 3（合规与高 RPM 优化器）：过滤迷信恐怖词，出 5 组标题、封面大字、评论区置顶话术。',
        '批量合成节点：并发 TTS（云希/老铁沉稳说书音）+ 图像生成，输出剪映草稿包。',
    ])

    docx_heading(doc, '四、剪映 10 分钟成片参数', 1)
    docx_bullets(doc, [
        '配音：沉稳说书男声，语速 1.1-1.15x；字幕居中下 1/3，书法字体黄字黑边。',
        '画面：12 张 AI 图 + 关键帧推拉（100%→115%）+ 飘雪/火苗特效贴纸（过原创度查重）。',
        'BGM：低沉古琴/洞箫 -18dB；转折处打更锣、风雪声、木轴吱呀声 -8dB。',
        '封面：三行大字对比色排版（见 folktale_cover_vertical.png）。',
    ])

    docx_heading(doc, '五、视频号分成计划运营', 1)
    docx_bullets(doc, [
        '发表时勾选"原创声明"（人文历史/故事解说）并开通创作者分成计划。',
        '发布时间：06:30-07:30 / 11:30-12:30 / 19:30-21:00。',
        '发布后立即置顶互动评论："老话讲人善人欺天不欺，留下一句平平安安，祝愿全家顺遂"，拉评论区停留时长。',
        '标题 5 组示例见 SKILL.md 与 coze_workflow_blueprint.json 的 title_pack 字段。',
    ])

    manual = os.path.join(out, 'folktale_video_package.docx')
    doc.save(manual)

    workflow = {
        'name': 'folktale_video_one_click',
        'version': '1.0',
        'skill': 'ai-folktale-video-sop',
        'start_inputs': ['story_theme', 'protagonist', 'scene_style', 'cultural_element'],
        'nodes': [
            {'id': 'llm_story', 'model': 'DeepSeek-R1', 'role': 'story_architect',
             'output': '550-word three-act six-segment folk tale + character anchors'},
            {'id': 'llm_shots', 'model': 'GPT-class', 'role': 'shot_compiler',
             'output': '12 numbered shots with style prefix + character anchor + CN/EN prompts'},
            {'id': 'llm_guard', 'model': 'Claude-class', 'role': 'compliance_and_rpm_optimizer',
             'output': 'compliance-safe script + 5 viral titles + pinned comment pack'},
            {'id': 'batch_synth', 'concurrency': 2,
             'calls': ['TTS cloud voice', 'text-to-image', 'image-to-video'], 'out_dir': 'editor_draft/'},
        ],
        'style_prefix_cn': '中式传统水墨厚涂插画风格，国风悬疑电影感，丁达尔暖黄灯笼光与青黛夜雾对比，工笔细节，8K超高清',
        'title_pack': [
            '老木匠除夕夜接了单"三更活"，二十年前的恩人竟找上门来！',
            '徽州雪夜奇闻：上门送银的"无影客"，斗笠下竟是新任县令！',
            '鲁班尺上"病离"二字现形那晚，他偏要提灯去还这笔账',
            '民间老话：渡人莫渡无影客，可这老木匠偏偏不信邪！',
            '雪夜叩门送官银，老木匠守了一夜的规矩，救了全家性命',
        ],
        'pinned_comment': '老话讲"但行好事，莫问前程"。您身边有过好人好报的真实故事吗？留下一句"善有善报"，为家人积福！',
    }
    wf_path = os.path.join(out, 'coze_workflow_blueprint.json')
    with open(wf_path, 'w', encoding='utf-8') as fh:
        json.dump(workflow, fh, ensure_ascii=False, indent=2)
        fh.write('\n')

    print('built: %s' % os.path.relpath(manual, ROOT))
    print('built: %s' % os.path.relpath(wf_path, ROOT))
    return [
        (manual, 'docx', DOCX_REQ, 'word/document.xml',
         ['雪夜来客', '三幕六段', 'Character Anchor', 'Coze', '视频号分成计划'], None),
    ]


# ========================================================= case 3: courseware
def build_courseware():
    from pptx.util import Inches, Pt
    out = os.path.join(CASES, '03_courseware_sop')
    os.makedirs(out, exist_ok=True)

    # ---- 10-slide editable pptx ----
    prs = pptx_new()

    def footer(page, total=10):
        from pptx.util import Inches, Pt
        # override generic footer for courseware
        pass

    def cs_shell(title, subtitle=None, page=None):
        from pptx.util import Inches, Pt
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        bg = slide.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid(); _rgb(bg.fill, (255, 250, 240)); bg.line.fill.background()
        band = slide.shapes.add_shape(1, 0, 0, prs.slide_width, Inches(1.15))
        band.fill.solid(); _rgb(band.fill, (212, 120, 40)); band.line.fill.background()
        tf = band.text_frame; tf.clear()
        p = tf.paragraphs[0]; p.text = title
        p.font.size = Pt(28); p.font.bold = True
        p.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
        if subtitle:
            p2 = tf.add_paragraph(); p2.text = subtitle
            p2.font.size = Pt(13)
            p2.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
        foot = slide.shapes.add_shape(1, 0, prs.slide_height - Inches(0.34), prs.slide_width, Inches(0.34))
        foot.fill.solid(); _rgb(foot.fill, (245, 235, 215)); foot.line.fill.background()
        ftf = foot.text_frame; ftf.clear()
        fp = ftf.paragraphs[0]
        fp.text = '统编版语文三年级上册 · 《秋天的雨》公开课课件（AI 原创可编辑示例）'
        fp.font.size = Pt(9)
        fp.font.color.rgb = __import__('pptx').dml.color.RGBColor(*DARK)
        if page:
            badge = slide.shapes.add_shape(9, prs.slide_width - Inches(0.8), prs.slide_height - Inches(0.78),
                                          Inches(0.5), Inches(0.5))
            badge.fill.solid(); _rgb(badge.fill, (212, 120, 40)); badge.line.fill.background()
            btf = badge.text_frame; btf.clear()
            bp = btf.paragraphs[0]; bp.text = '%d/10' % page
            bp.font.size = Pt(11); bp.font.bold = True
            bp.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
        return slide

    # slide 1 cover
    cover = prs.slides.add_slide(prs.slide_layouts[6])
    pic = os.path.join(out, 'courseware_illustration_autumn.png')
    if os.path.isfile(pic):
        picture_on(cover, pic, 0, 0, width=13.333, height=7.5)
    panel = cover.shapes.add_shape(1, 0, Inches(2.3), prs.slide_width, Inches(2.6))
    panel.fill.solid(); _rgb(panel.fill, (255, 255, 255)); panel.line.fill.background()
    tf = panel.text_frame; tf.clear()
    p = tf.paragraphs[0]; p.text = '《秋天的雨》'
    p.font.size = Pt(44); p.font.bold = True
    p.font.color.rgb = __import__('pptx').dml.color.RGBColor(212, 120, 40)
    p2 = tf.add_paragraph(); p2.text = '统编版语文三年级上册 · 第二单元 · 第 6 课（2 课时）'
    p2.font.size = Pt(18)
    p2.font.color.rgb = __import__('pptx').dml.color.RGBColor(*DARK)
    p3 = tf.add_paragraph(); p3.text = '大单元情境任务：秋日来信 · 做一份"秋天的纪念册" ｜ 授课：林老师教研室'
    p3.font.size = Pt(14)
    p3.font.color.rgb = __import__('pptx').dml.color.RGBColor(*DARK)

    s2 = cs_shell('一、情境导入 · 秋日来信', page=2)
    bullets_on(s2, 0.7, 1.5, 12, 5.2, [
        '亲爱的小探险家们：秋姑娘寄来一封信，藏在今天的课文里，谁能先找到钥匙？',
        '任务发布：读课文 → 找"钥匙" → 摘"颜色" → 品"气味" → 写"秋声"，完成秋天的纪念册！',
        '学习路径：初读闯关（字词） → 品读探秘（五彩秋色+丰收气味） → 拓展迁移（小练笔） → 板书总结（分层作业）。',
        '课堂约定：朗读有姿势，发言举小手，同桌互相评，精彩加星章。',
    ], size=17)

    s3 = cs_shell('二、核心素养学习目标', page=3)
    card_on(s3, 0.7, 1.5, 5.8, 2.2, '目标一 · 文化自信与审美', [
        '感受秋天之美，体会语言文字的温度，', '热爱自然、热爱生活。'], fill=(255, 236, 220), title_color=(212, 120, 40))
    card_on(s3, 6.8, 1.5, 5.8, 2.2, '目标二 · 语言运用', [
        '有感情朗读课文，积累"五彩缤纷"', '等优美词句并尝试运用。'], fill=LIGHT, title_color=NAVY)
    card_on(s3, 0.7, 4.0, 5.8, 2.2, '目标三 · 思维能力', [
        '借助关键句理解段意，发现课文', '"总分"结构与比喻句的妙处。'], fill=(226, 240, 224), title_color=GREEN)
    card_on(s3, 6.8, 4.0, 5.8, 2.2, '目标四 · 审美创造', [
        '仿写"秋天的雨还藏着什么气味"，', '完成秋日小练笔与纪念册一页。'], fill=(250, 240, 230), title_color=ORANGE)

    s4 = cs_shell('任务一 · 初读闯关：字词小侦探', page=4)
    table_on(s4, 0.7, 1.5, 12, 4.6, ['生字', '读音', '识记妙招', '闯关词'], [
        ['匙', 'shi（轻声）', '钥匙是金属，所以是"匕"加金属旁', '钥匙 · 一串钥匙'],
        ['缤', 'bīn', '绞丝旁+宾，丝线多彩=五彩缤纷', '五彩缤纷 · 缤纷世界'],
        ['枚', 'méi', '木字旁+"文"，一枚果子一枚邮票', '一枚邮票 · 不胜枚举'],
        ['喇', 'lǎ', '口字旁，喇叭要用嘴吹', '喇叭 · 小喇叭广播'],
        ['厚', 'hòu', '"厂"下一盆"子"，厚礼厚情', '丰厚 · 厚厚的地毯'],
        ['曲', 'qū / qǔ', '弯弯曲曲 qū，一支歌曲 qǔ', '丰收的歌乐曲 yuè'],
    ], font=12)

    s5 = cs_shell('任务二 · 品读探秘：五彩缤纷的秋色', page=5)
    bullets_on(s5, 0.7, 1.4, 12, 1.2, [
        '朗读第 2 自然段：秋天的雨，有一盒五彩缤纷的颜料。它把黄色给了银杏树，把红色给了枫树，金黄色是给田野的，橙红色是给果树的……', ], size=15)
    card_on(s5, 0.7, 2.9, 2.9, 3.4, '银杏黄', ['黄黄的叶子', '像一把把小扇子', '扇哪扇哪', '扇走了夏天的炎热'], fill=(255, 243, 180), title_color=(190, 130, 20))
    card_on(s5, 3.85, 2.9, 2.9, 3.4, '枫叶红', ['红红的枫叶', '像一枚枚邮票', '飘哇飘哇', '邮来了秋天的凉爽'], fill=(255, 220, 210), title_color=(200, 70, 50))
    card_on(s5, 7.0, 2.9, 2.9, 3.4, '田野金', ['金黄色的田野', '像金色的海洋', '翻起波浪', '翻出丰收的歌'], fill=(255, 236, 190), title_color=(180, 130, 30))
    card_on(s5, 10.15, 2.9, 2.5, 3.4, '果树橙', ['橙红色果树', '橘子柿子', '你挤我碰', '争着要人去摘'], fill=(255, 226, 200), title_color=(210, 110, 30))

    s6 = cs_shell('任务三 · 品读探秘：秋雨里的气味', page=6)
    bullets_on(s6, 0.7, 1.5, 12, 3.4, [
        '朗读第 3 自然段：秋天的雨，藏着非常好闻的气味。梨香香的，菠萝甜甜的，还有苹果、橘子，好多好多香甜的气味，都躲在小雨滴里呢！',
        '换词比较："躲"字换成"有"字好不好？（"躲"字让气味像小朋友捉迷藏，秋天一下子变得淘气可爱。）',
        '迁移想象：秋天的雨还藏着哪些气味？（桂花、稻谷、糖炒栗子、烤红薯……）用"……的，……的，还有……"说句子。',
    ], size=16)
    card_on(s6, 0.7, 5.1, 12, 1.2, '句式迁移练笔', ['秋天的雨还藏着好多气味：桂花香香的，稻谷清清的，还有糖炒栗子、烤红薯，好多好多丰收的气味，都躲在小雨滴里呢！'], fill=(255, 236, 220), title_color=(212, 120, 40))

    s7 = cs_shell('任务四 · 悟情升华：秋天的雨是钥匙', page=7)
    bullets_on(s7, 0.7, 1.5, 12, 4.6, [
        '齐读第 4 自然段：秋天的雨，有一把金色的钥匙。它带着清凉和温柔，趁你没留意，把秋天的大门打开了。',
        '思考讨论：为什么说秋雨是"钥匙"？（一场秋雨一场凉，秋雨一来，丰收与团圆的季节就被打开了。）',
        '小练笔（纪念册第 3 页）：写 2-3 句"秋天的雨还像什么"，用上比喻句：秋天的雨像____，它____。',
        '朗读展示：小组合作配乐朗读全文，评选"最美秋声朗读者"。',
    ], size=17)

    s8 = cs_shell('拓展迁移 · 秋日纪念册小练笔', page=8)
    table_on(s8, 0.7, 1.5, 12, 4.6, ['纪念册页面', '任务', '评价标准', '分层作业'], [
        ['第 1 页 五彩秋色', '画一画+写 3 个颜色词', '用上"五彩缤纷、扇哪扇哪"', '基础：抄写词语表'],
        ['第 2 页 秋雨之声', '摘抄 1 个拟人句并仿写', '句子完整，有想象力', '进阶：仿写 2 个比喻句'],
        ['第 3 页 气味地图', '写 3 种秋天气味的小段落', '用上"……的，……的"', '拓展：读《秋天的信》'],
        ['第 4 页 秋声采集', '写 2-3 句小诗"秋天的雨像…"', '有真情实感，朗读给家人听', '亲子：和爸妈寻秋打卡'],
    ], font=12)

    s9 = cs_shell('板书设计 · 结构化总结', page=9)
    card_on(s9, 0.7, 1.6, 12, 1.3, '《秋天的雨》 一把钥匙 → 一盒颜料 → 好闻气味 → 金色喇叭 → 丰收的歌', ['总（钥匙） → 分（颜色 · 气味 · 声音） → 总（丰收的歌） ｜ 比喻 · 拟人 · 总分结构'], fill=(212, 120, 40), title_color=WHITE)
    card_on(s9, 0.7, 3.2, 3.8, 2.8, '五彩缤纷', ['黄 银杏', '红 枫叶', '金 田野', '橙 果树'], fill=(255, 243, 180))
    card_on(s9, 4.8, 3.2, 3.8, 2.8, '好闻气味', ['梨 香香的', '菠萝 甜甜的', '苹果 橘子', '躲 小雨滴'], fill=(255, 226, 210))
    card_on(s9, 8.9, 3.2, 3.7, 2.8, '秋的声音', ['黄叶 小扇子', '枫叶 邮票', '田野 海洋', '喇叭 丰收歌'], fill=(226, 240, 224))

    s10 = cs_shell('封底 · 秋天的纪念册', page=None)
    bullets_on(s10, 2.2, 2.4, 9, 3.2, [
        '让每个孩子把秋天带回家。',
        '完整产品包：可编辑 PPTX + 新课标教案 + 逐页逐字稿（配套 Word）。',
        '配套资料：字词卡 · 小练笔单 · 板书贴纸 · 家长寻秋打卡表。',
        '林老师教研室 · 2026 新课标大单元情境教学示例（教学演示用，禁止商用转载）。',
    ], size=19)

    pptx_path = os.path.join(out, 'autumn_rain_courseware.pptx')
    prs.save(pptx_path)

    # ---- teaching package docx ----
    doc = docx_new()
    doc.core_properties.title = '《秋天的雨》新课标教案 + 逐页逐字稿 + 小红书种草笔记'
    docx_heading(doc, '《秋天的雨》教学资料三件套', 0)
    docx_para(doc, '配套 Skill：skills/commercial/courseware-monetization-sop · 输出目录：deliverable/cases/03_courseware_sop/')

    docx_heading(doc, '第一部分 · 2022 版新课标标准教案', 1)
    docx_table(doc, ['项目', '内容'], [
        ['课题', '《秋天的雨》（统编版语文三年级上册第 6 课）'],
        ['课型', '精读课文 · 大单元情境教学（2 课时）'],
        ['核心素养目标', '文化自信 / 语言运用 / 思维能力 / 审美创造（见课件第 3 页）'],
        ['教学重点', '有感情朗读，积累优美词句，感受秋天之美'],
        ['教学难点', '理解"钥匙""躲"等词的表达效果，仿写比喻句与拟人句'],
        ['教学准备', '课件 PPTX、生字卡、秋叶实物、寻秋打卡表、配乐《秋日私语》'],
    ])
    docx_para(doc, '教学过程（第 1 课时）：', bold=True)
    docx_bullets(doc, [
        '一、情境导入（5 分钟）：出示"秋日来信"信封，发布大单元任务，引出课题（课件第 2 页）。',
        '二、初读闯关（12 分钟）：自由读文 → 生字闯关（匙、缤、枚、喇、厚）→ 同桌互评（课件第 4 页）。',
        '三、品读"五彩秋色"（15 分钟）：齐读第 2 段，圈颜色词，体会"扇哪扇哪"的节奏美（课件第 5 页）。',
        '四、小结与作业（8 分钟）：完成纪念册第 1 页，基础作业抄写词语表（课件第 8 页）。',
    ])
    docx_para(doc, '教学过程（第 2 课时）：', bold=True)
    docx_bullets(doc, [
        '一、复习导入（5 分钟）：颜色词开火车。',
        '二、品读"气味"与"声音"（18 分钟）：换词比较"躲"字之妙，迁移说话（课件第 6 页）；悟情讨论"钥匙"含义（课件第 7 页）。',
        '三、拓展小练笔（12 分钟）：写"秋天的雨像____"，配乐朗读展示（课件第 7-8 页）。',
        '四、板书总结与分层作业（5 分钟）：结构化板书（课件第 9 页）。',
    ])
    docx_para(doc, '板书设计：一把钥匙 → 一盒颜料 → 好闻气味 → 金色喇叭 → 丰收的歌（总分结构）。')
    docx_para(doc, '教学反思：留给学生充分的朗读与想象时间；小组互评星章激励效果好；可延伸"寻秋"跨学科实践。')

    docx_heading(doc, '第二部分 · 逐页课堂逐字稿（教师拿着直接讲）', 1)
    script_pages = [
        ('P1 封面', '上课！今天林老师带来一位神秘的朋友（指屏幕），它轻轻一吹，大地就换了颜色。它就是秋天的雨。伸出小手，和老师一起写课题。'),
        ('P2 情境导入', '秋姑娘给我们寄来一封信：亲爱的小探险家们，谁能在课文中找到打开秋天大门的钥匙？完成纪念册的小朋友，都能获得秋日星章！'),
        ('P3 学习目标', '今天我们要闯四关：读准字词、读懂秋色、读出味道、写出秋声。准备好了吗？'),
        ('P4 字词闯关', '请小老师带读：钥匙、五彩缤纷、一枚邮票、喇叭。注意"匙"在这里读轻声。同桌互评，全对的画一颗星。'),
        ('P5 五彩秋色', '谁来读读这句话？（生读）银杏叶像什么？对，小扇子！扇哪扇哪，扇走了夏天的炎热。枫叶呢？像一枚枚邮票，邮来了秋天的凉爽。男女生赛读！'),
        ('P6 秋雨气味', '秋天的雨还藏着好闻的气味。我们把"躲"换成"有"，好不好？不好！"躲"字让气味像在捉迷藏，多淘气呀。你也来说一句？'),
        ('P7 钥匙悟情', '为什么说秋雨是钥匙？（预设：一打开门，果子熟了，稻子黄了，秋天来了。）带着清凉和温柔，我们齐读这一段。'),
        ('P8 小练笔', '现在请翻开纪念册第 3 页：秋天的雨还像什么？写 2-3 句，用上比喻。写好的读给同桌听，互相送星星。'),
        ('P9 板书总结', '看板书：一把钥匙，一盒颜料，好闻气味，金色喇叭，最后化成一首丰收的歌。这就是总分结构！'),
        ('P10 封底', '今天的秋日探险就到这里。课后完成寻秋打卡表，下节课我们开秋天朗诵会。下课！'),
    ]
    docx_table(doc, ['页码', '教师逐字口播（含互动与预设）'], script_pages)

    docx_heading(doc, '第三部分 · 商品详情页与小红书种草笔记（变现闭环）', 1)
    docx_para(doc, 'SKU 定价：单课体验装 9.9 元 ｜ 单元精品包 29.9 元 ｜ 全册大合集 69.9 元（新人券立减 10 元）。', bold=True)
    docx_para(doc, '小红书笔记标题（3 选 1）：', bold=True)
    docx_bullets(doc, [
        '公开课拿了一等奖！全靠这套《秋天的雨》大单元情境课件（附逐字稿）',
        '熬夜三天肝出来的三年级上册《秋天的雨》新课标课件！老师们直接抄作业',
        '被教研员夸爆的《秋天的雨》公开课 PPT+逐字稿，课堂氛围直接拉满！',
    ])
    docx_para(doc, '笔记正文（种草模板）：', bold=True)
    docx_para(doc, '姐妹们！这周的校内公开课用的就是这套《秋天的雨》大单元情境课件，下课就被教研员要走了全套链接。整体是"秋日来信"任务群设计：字词闯关→五彩秋色卡片→气味小练笔→纪念册作业，孩子们举手举到停不下来！重点是每一页都可编辑，配套新课标教案+逐页逐字稿，新教师照着讲就行。需要的姐妹评论区扣"秋天"，或直接点我主页店铺链接~')
    docx_para(doc, '话题标签：#小学语文公开课 #新课标教学设计 #课件分享 #公开课课件 #青年教师公开课 #教案逐字稿')

    docx_path = os.path.join(out, 'autumn_rain_teaching_package.docx')
    doc.save(docx_path)

    print('built: %s' % os.path.relpath(pptx_path, ROOT))
    print('built: %s' % os.path.relpath(docx_path, ROOT))
    return [
        (pptx_path, 'pptx', PPTX_REQ, 'ppt/presentation.xml',
         ['秋天的雨', '银杏', '五彩缤纷', '小练笔', '钥匙'], 10),
        (docx_path, 'docx', DOCX_REQ, 'word/document.xml',
         ['教案', '逐字稿', '小红书', '种草', '核心素养'], None),
    ]


# ==================================================== case 4: business plan
def build_bp():
    out = os.path.join(CASES, '04_business_plan')
    os.makedirs(out, exist_ok=True)

    # ---------- pitch deck (12 slides) ----------
    prs = pptx_new()
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(1, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid(); _rgb(bg.fill, NAVY); bg.line.fill.background()
    pic = os.path.join(out, 'bp_cover_visual.png')
    if os.path.isfile(pic):
        picture_on(s, pic, 4.6, 1.2, width=8.4, height=5.0)
    tb = s.shapes.add_textbox(__import__('pptx').util.Inches(0.6), __import__('pptx').util.Inches(1.6),
                              __import__('pptx').util.Inches(4.2), __import__('pptx').util.Inches(4.2))
    tf = tb.text_frame; tf.word_wrap = True; tf.clear()
    p = tf.paragraphs[0]; p.text = '智护银龄'
    p.font.size = __import__('pptx').util.Pt(40); p.font.bold = True
    p.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)
    for line in ['AI 居家养老健康监测系统', '', '天使轮融资路演（BP）', '拟融资 500 万元 · 出让 12% 股权',
                 '投前估值 3,667 万元', '2026 年 10 月', '（教学演示案例 · 数据为示例测算）']:
        p2 = tf.add_paragraph(); p2.text = line
        p2.font.size = __import__('pptx').util.Pt(16)
        p2.font.color.rgb = __import__('pptx').dml.color.RGBColor(*WHITE)

    s2 = slide_shell(prs, '执行摘要：让每个家庭都有一双"不休息的眼睛"', '一页看懂本项目', page=2)
    card_on(s2, 0.7, 1.5, 3.9, 2.4, '市场', ['银发经济超 7 万亿', '居家智能监测年复合增长 34.8%', '政策：家庭养老床位试点扩围'], fill=LIGHT)
    card_on(s2, 4.8, 1.5, 3.9, 2.4, '产品', ['毫米波雷达 + AI 跌倒检测', 'SaaS 服务平台 + 家属小程序', '无摄像头、适老化、隐私友好'], fill=(226, 240, 224), title_color=GREEN)
    card_on(s2, 8.9, 1.5, 3.7, 2.4, '业绩', ['试点社区 32 个、在网设备 1,800 台', '付费转化率 41%、续费率 86%', '月流水 38 万元、环比 +22%'], fill=(255, 236, 220), title_color=ORANGE)
    card_on(s2, 0.7, 4.2, 12, 2.1, '融资诉求：本轮拟融资 500 万元，出让 12% 股权（投前估值 3,667 万元）',
            ['资金用途：研发 40%（算法与硬件迭代）· 市场 30%（城市合伙人与社区渠道）· 供应链 20% · 运营 10%',
             '2027 年目标：在网设备 2.4 万台、营收 4,800 万元、盈亏平衡'], fill=NAVY, title_color=WHITE)

    s3 = slide_shell(prs, '行业痛点：独居老人"跌倒 1 小时无人知"', '存量市场四大未解痛点', page=3)
    for i, (t, b) in enumerate([
        ('痛点一 · 发现难', ['跌倒后平均 3-6 小时才被发现', '独居/空巢家庭占比持续攀升']),
        ('痛点二 · 监测侵入', ['摄像头方案隐私顾虑重', '卧室卫生间不敢装']),
        ('痛点三 · 告警失灵', ['穿戴设备老人不愿戴/常忘充电', '误报多、家属疲劳']),
        ('痛点四 · 服务断层', ['硬件卖完无人管', '健康数据没人解读']),
    ]):
        card_on(s3, 0.7 + i * 3.1, 1.6, 2.95, 3.4, t, b, fill=LIGHT if i % 2 == 0 else (255, 236, 220),
                title_color=NAVY if i % 2 == 0 else ORANGE)
    bullets_on(s3, 0.7, 5.3, 12, 1.2, [
        '结论：市场需要"非穿戴、无摄像头、能告警、有人管"的一体化居家安全监测方案。'], size=15)

    s4 = slide_shell(prs, '市场机遇：三层漏斗锁定 1.2 亿可触达市场', 'TAM / SAM / SOM（示例测算口径）', page=4)
    table_on(s4, 0.9, 1.5, 11.5, 2.6, ['层级', '口径', '规模', '依据'], [
        ['TAM 总潜在市场', '中国银发科技及居家智能健康监测', '12,000 亿元', '银发经济总规模超 7 万亿，智慧养老渗透率约 17%'],
        ['SAM 可服务市场', '居家健康监测硬件 + SaaS 服务', '3,800 亿元', '居家场景占智慧养老支出约 54%'],
        ['SOM 首年可触达', '长三角 6 城社区渠道', '1.2 亿元', '试点渠道 32 社区 → 120 社区、在网 2.4 万台'],
    ], font=12)
    bullets_on(s4, 0.9, 4.5, 11.5, 1.9, [
        '增长驱动：家庭养老床位试点补贴扩围、长护险试点城市增加、子女远程照护付费意愿提升。',
        '竞争窗口：行业仍以"卖硬件"为主，"监测 + 告警 + 健康服务"订阅制是待占位的空白带。'], size=15)

    s5 = slide_shell(prs, '产品方案：一个雷达 + 一个平台 + 一套服务', '产品与解决方案', page=5)
    table_on(s5, 0.7, 1.5, 12, 3.2, ['组件', '形态', '核心功能', '适老化设计'], [
        ['感知终端', '毫米波雷达 + 边缘 AI 盒', '跌倒检测、起夜轨迹、心率呼吸率初筛', '无摄像头、免穿戴、通电即用'],
        ['SaaS 平台', '机构/社区 Web 端', '告警分级派单、健康周报、设备管理', '大字版界面、语音外呼确认'],
        ['家属小程序', '微信小程序', '实时状态、告警推送、远程关怀日历', '一键呼叫、亲情相册'],
        ['健康服务包', '人工 + AI', '月度健康报告、用药提醒、绿通转诊', '7×24 值班响应 SOP'],
    ], font=11)

    s6 = slide_shell(prs, '3 大核心壁垒：算法 · 数据 · 渠道', '为什么是我们', page=6)
    card_on(s6, 0.7, 1.6, 3.9, 4.3, '壁垒一 · 跌倒检测算法', [
        '自研毫米波点云 + 行为序列双流模型',
        '准确率 97.3%、误报 < 0.8 次/户/月',
        '已受理发明专利 2 项、软著 4 项',
        '老年体态长尾数据持续反哺迭代'], fill=LIGHT)
    card_on(s6, 4.8, 1.6, 3.9, 4.3, '壁垒二 · 运营数据闭环', [
        '在网设备日均行为数据 1,800 台',
        '告警-核实-处置全链路数据沉淀',
        '健康风险模型随服务时长变准',
        '续费率 86% 构成数据护城河'], fill=(226, 240, 224), title_color=GREEN)
    card_on(s6, 8.9, 1.6, 3.7, 4.3, '壁垒三 · 社区渠道网络', [
        '与 32 个社区/街道签约共建',
        '物业 + 居家养老服务站双入口',
        '城市合伙人模式可快速复制',
        '服务半径 3 公里、响应 < 30 分钟'], fill=(255, 236, 220), title_color=ORANGE)

    s7 = slide_shell(prs, '商业模式：硬件微利 + 订阅服务赚钱', '单位经济模型（单户/年，示例）', page=7)
    table_on(s7, 0.9, 1.5, 11.5, 2.8, ['指标', '数值', '说明'], [
        ['硬件客单价', '699 元', '含安装，毛利率约 28%，引流型定价'],
        ['服务订阅', '99 元/月', '健康服务包 + 告警值班，毛利率 62%'],
        ['单户年收入', '1,887 元', '首购 + 订阅；LTV（3 年）约 4,900 元'],
        ['单户获客成本 CAC', '约 520 元', '社区渠道 + 转介绍，回本周期 < 5 个月'],
    ], font=12)
    bullets_on(s7, 0.9, 4.6, 11.5, 1.8, [
        '收入结构目标（2027）：订阅服务 55% + 硬件 35% + 增值（健康报告/转诊）10%。',
        '规模化抓手：城市合伙人（设备押金 + 流水分成）与机构集采（养老院/日间照料中心）。'], size=15)

    s8 = slide_shell(prs, '竞争格局：差异化切入"监测 + 服务"空白带', '五维对比（示意）', page=8)
    table_on(s8, 0.7, 1.5, 12, 3.6, ['维度', '本项目', 'A 摄像头方案', 'B 穿戴设备', 'C 传统呼叫器'], [
        ['隐私友好', '优（无摄像头）', '差', '良', '优'],
        ['跌倒识别', '优（97.3%）', '良', '良（佩戴依赖）', '无（需手动按）'],
        ['误报控制', '优（<0.8/月）', '中', '中', '优'],
        ['健康服务', '优（订阅制）', '弱', '中', '无'],
        ['年持有成本', '1,887 元', '约 1,200 元', '约 2,400 元', '约 400 元'],
    ], font=11)
    bullets_on(s8, 0.7, 5.3, 12, 1.1, ['切入策略：以"非穿戴无摄像头"建立信任，以"告警有人管"完成付费转化，以健康服务锁定续费。'], size=15)

    s9 = slide_shell(prs, 'GTM 路线图：社区样板 → 城市合伙人 → 机构集采', '18 个月三个阶段（KPI 里程碑）', page=9)
    table_on(s9, 0.9, 1.5, 11.5, 3.4, ['阶段', '时间', '目标', '关键动作'], [
        ['样板期', '2026H2', '在网 3,000 台 / 月流水 80 万', '深耕 6 城 120 社区，跑通"检测+值班+报告"SOP'],
        ['复制期', '2027H1', '在网 1.2 万台 / 城市合伙人 20 城', '合伙人招募培训体系、供应链备货 5 万台'],
        ['规模期', '2027H2', '在网 2.4 万台 / 营收 4,800 万', '机构集采、长护险渠道合作、健康服务分层'],
    ], font=12)
    bullets_on(s9, 0.9, 5.2, 11.5, 1.2, ['北极星指标：在网活跃设备数 × 订阅续费率；辅指标：告警处置及时率 > 98%。'], size=15)

    s10 = slide_shell(prs, '核心团队与股权结构', '黄金三角：硬件 + 算法 + 养老运营', page=10)
    table_on(s10, 0.9, 1.5, 11.5, 2.6, ['成员', '背景', '职责', '持股'], [
        ['CEO 王××', '10 年智能硬件产品与供应链，前上市养老科技公司产品总监', '战略 / 融资 / 供应链', '46%'],
        ['CTO 李××', '985 博士，毫米波感知与人体行为识别，专利 6 项', '算法 / 平台', '26%'],
        ['COO 张××', '8 年居家养老服务运营，管理过 40 人照护团队', '服务交付 / 城市合伙人', '16%'],
        ['期权池', '核心骨干与顾问预留', '融资后扩充至 12%', '12%'],
    ], font=11)
    bullets_on(s10, 0.9, 4.5, 11.5, 1.9, [
        '融资后股权结构（示例）：创始团队 74% + 天使投资人 12% + 期权池 12%（ESOP，4 年成熟）。',
        '治理安排：投资方一票否决权限于增发、并购、关联交易；季度董事会 + 月度经营报告。'], size=15)

    s11 = slide_shell(prs, '财务预测与融资方案', '3 年核心财务预测（示例测算，单位：万元）', page=11)
    table_on(s11, 0.7, 1.5, 12, 2.8, ['项目', '2026H2', '2027', '2028', '2029'], [
        ['营业收入', '120', '480', '2,600', '8,400'],
        ['毛利率', '36%', '42%', '48%', '52%'],
        ['研发 + 销售费用', '310', '520', '1,420', '3,300'],
        ['净利润（EBITDA 口径）', '-190', '-120', '260', '1,340'],
        ['期末在网设备（台）', '800', '3,000', '12,000', '24,000'],
    ], font=11)
    card_on(s11, 0.7, 4.6, 12, 1.8, '融资方案：本轮 500 万元 · 出让 12% · 投前估值 3,667 万元',
            ['资金用途：研发 40% ｜ 市场 30% ｜ 供应链 20% ｜ 运营 10%',
             '里程碑承诺：2027 年在网 2.4 万台、营收 4,800 万元、盈亏平衡；投资回收期约 30 个月'],
            fill=NAVY, title_color=WHITE)

    s12 = slide_shell(prs, '为什么是现在，为什么是我们', '致投资人', page=12)
    bullets_on(s12, 0.9, 1.6, 11.5, 4.6, [
        '① 政策与人口结构的确定性：家庭养老床位试点扩围，独居老人安全监测成为"必答题"。',
        '② 产品与数据的领先性：97.3% 跌倒识别、<0.8 次/月误报、86% 续费率已在试点验证。',
        '③ 商业模型的可复制性：硬件引流 + 订阅盈利，单户回本 < 5 个月，城市合伙人快速铺城。',
        '④ 团队的执行记录：18 个月从 0 到 32 社区、1,800 台在网设备，运营 SOP 已成型。',
        '诚邀共建：让技术有温度，让居家养老更安全。期待与您深聊。',
    ], size=18)

    deck = os.path.join(out, 'smart_eldercare_pitch.pptx')
    prs.save(deck)

    # ---------- word bp ----------
    doc = docx_new()
    doc.core_properties.title = '智护银龄 天使轮商业计划书（Word 详版）'
    docx_heading(doc, '“智护银龄”AI 居家养老健康监测系统', 0)
    docx_heading(doc, '天使轮商业计划书（Word 详版 · 教学演示案例）', 1)
    docx_para(doc, '配套 Skill：skills/commercial/ai-business-plan-sop · 输出目录：deliverable/cases/04_business_plan/')
    docx_para(doc, '数据声明：本文档为 AI 代做商业计划书的完整交付示例，文中市场与财务数据为教学示例测算口径，不构成投资建议。')

    docx_heading(doc, '一、执行摘要', 1)
    docx_bullets(doc, [
        '项目定位：面向独居/空巢老人家庭的"非穿戴、无摄像头"AI 居家安全与健康监测系统。',
        '市场机会：银发经济总规模超 7 万亿元，居家智能健康监测细分市场约 1.2 万亿元（TAM），居家硬件+SaaS 可服务市场 3,800 亿元（SAM）。',
        '核心壁垒：毫米波跌倒检测算法（准确率 97.3%）、运营数据闭环、32 个社区渠道网络。',
        '经营现状：试点社区 32 个，在网设备 1,800 台，付费转化率 41%，续费率 86%，月流水 38 万元。',
        '融资诉求：本轮融资 500 万元人民币，出让 12% 股权，投前估值 3,667 万元；资金用于研发 40%、市场 30%、供应链 20%、运营 10%。',
    ])

    docx_heading(doc, '二、行业痛点与市场规模', 1)
    docx_para(doc, '宏观驱动：人口结构（独居老人规模攀升）+ 政策（家庭养老床位试点、长护险扩围）+ 支付意愿（子女远程照护付费）。')
    docx_table(doc, ['层级', '口径', '规模', '测算依据'], [
        ['TAM', '银发科技及居家智能健康监测', '12,000 亿元', '银发经济 7 万亿 × 智慧养老渗透率 17%'],
        ['SAM', '居家健康监测硬件 + SaaS', '3,800 亿元', '居家场景占智慧养老支出约 54%'],
        ['SOM', '长三角 6 城社区渠道首年', '1.2 亿元', '120 社区 × 200 户 × 2.4 万台在网'],
    ])
    docx_para(doc, '存量痛点：跌倒发现难、摄像头隐私顾虑、穿戴设备依从性差、健康数据缺服务承接。')

    docx_heading(doc, '三、产品与解决方案', 1)
    docx_bullets(doc, [
        '感知终端：毫米波雷达 + 边缘 AI 盒，跌倒检测、起夜轨迹、心率呼吸率初筛，无摄像头免穿戴。',
        'SaaS 平台：告警分级派单、健康周报、设备管理，大字版适老化界面。',
        '家属小程序：实时状态、告警推送、一键呼叫、亲情相册。',
        '健康服务包：月度健康报告、用药提醒、绿通转诊、7×24 值班响应 SOP。',
    ])
    docx_para(doc, '3 大核心技术壁垒：① 双流跌倒检测算法（发明专利 2 项、软著 4 项）；② 在网 1,800 台设备的行为数据闭环；③ 社区+物业双入口渠道网络与 30 分钟响应服务半径。', bold=True)

    docx_heading(doc, '四、商业模式与单位经济', 1)
    docx_table(doc, ['指标', '数值', '说明'], [
        ['硬件客单价', '699 元', '含安装，毛利率 28%，引流定价'],
        ['服务订阅', '99 元/月', '毛利率 62%'],
        ['单户年收入', '1,887 元', 'LTV（3 年）约 4,900 元'],
        ['CAC', '520 元', '回本周期 < 5 个月'],
    ])

    docx_heading(doc, '五、竞争格局与差异化', 1)
    docx_para(doc, '对比摄像头方案、穿戴设备、传统呼叫器三大类竞品：本项目在隐私友好、跌倒识别准确率、误报控制、健康服务四维领先，以"监测 + 服务"占据空白带。')

    docx_heading(doc, '六、市场推广与运营路线图', 1)
    docx_table(doc, ['阶段', '时间', '目标', '关键动作'], [
        ['样板期', '2026H2', '在网 3,000 台', '6 城 120 社区深耕，跑通服务 SOP'],
        ['复制期', '2027H1', '在网 1.2 万台', '城市合伙人 20 城，供应链备货 5 万台'],
        ['规模期', '2027H2', '在网 2.4 万台', '机构集采、长护险渠道、服务分层'],
    ])

    docx_heading(doc, '七、核心团队与股权结构', 1)
    docx_para(doc, 'CEO（智能硬件与供应链 10 年）46% ｜ CTO（感知算法博士）26% ｜ COO（居家养老运营 8 年）16% ｜ 期权池 12%。融资后：团队 74% + 投资人 12% + ESOP 12%（4 年成熟）。')

    docx_heading(doc, '八、融资计划与 3 年财务预测（示例测算）', 1)
    docx_table(doc, ['项目（万元）', '2026H2', '2027', '2028', '2029'], [
        ['营业收入', '120', '480', '2,600', '8,400'],
        ['硬件收入', '108', '360', '1,560', '4,200'],
        ['订阅服务收入', '12', '120', '1,040', '4,200'],
        ['营业成本', '77', '278', '1,352', '4,032'],
        ['毛利（毛利率）', '43（36%）', '202（42%）', '1,248（48%）', '4,368（52%）'],
        ['研发费用', '150', '260', '620', '1,200'],
        ['销售与市场费用', '120', '200', '620', '1,600'],
        ['管理费用', '40', '60', '180', '500'],
        ['净利润（EBITDA 口径）', '-190', '-120', '260', '1,340'],
        ['期末在网设备（台）', '800', '3,000', '12,000', '24,000'],
    ])
    docx_para(doc, '合作/融资方案：首期注资 500 万元占股 12%（投前估值 3,667 万元）；资金用途 40/30/20/10；投资回收期约 30 个月。', bold=True)

    docx_heading(doc, '附录 A · AI 代做商业计划书接单资源与 SOP（交付增值包）', 1)
    docx_para(doc, '（以下为给接单者的实操附录，可单独交付客户之外自用，源自 skills/commercial/ai-business-plan-sop）')
    docx_table(doc, ['档位', '交付内容', '建议报价', 'AI 辅助耗时'], [
        ['基础梳理版', '10-12 页 PPT 或 5000 字 Word 框架', '680-980 元', '30-45 分钟'],
        ['标准路演版（主推）', '8000 字 Word + 12-15 页 PPTX + 3 年财务表', '1,280-1,980 元', '1-1.5 小时'],
        ['尊享投行定制版', '1.5 万字研报级 + 18 页 PPTX + 动态财务模型 + 演讲稿', '2,980-5,000+ 元', '2-3 小时'],
    ])
    docx_para(doc, '8 大接单渠道：① 闲鱼样片矩阵；② 小红书人设号；③ 淘宝/京东服务商派单；④ 猪八戒/一品威客投标（附 3 页专属大纲提中标率）；⑤ 知乎长尾词；⑥ 抖音/视频号同城；⑦ QQ/微信派单群；⑧ 孵化器/财税公司异业返佣（20-30%）。', bold=True)
    docx_para(doc, '334 收款 SOP：30% 定金（交大纲后）→ 30% 中期款（水印 PDF 预览确认）→ 40% 尾款（无水印源文件交付，7 天免费微调）。全程走闲鱼担保或对公账户，不私下交易。', bold=True)

    docx_heading(doc, '附录 B · 老板需求 10 分钟诊断问卷（8 问）', 1)
    docx_bullets(doc, [
        '1 项目一句话定位？（想法期 / MVP / 已有营收）',
        '2 BP 用途？（VC 融资 / 合伙注资 / 招商加盟 / 政府立项）',
        '3 目标客户与核心痛点？',
        '4 产品/服务的 3 个壁垒？',
        '5 怎么赚钱？（客单价、毛利、收费模式）',
        '6 核心团队亮点履历？',
        '7 融资金额、出让比例与资金用途？',
        '8 未来 1-3 年营收目标？',
    ])

    bp_doc = os.path.join(out, 'smart_eldercare_bp.docx')
    doc.save(bp_doc)

    print('built: %s' % os.path.relpath(deck, ROOT))
    print('built: %s' % os.path.relpath(bp_doc, ROOT))
    return [
        (deck, 'pptx', PPTX_REQ, 'ppt/presentation.xml',
         ['智护银龄', 'TAM', '融资', '财务预测', '路线图', '500 万'], 12),
        (bp_doc, 'docx', DOCX_REQ, 'word/document.xml',
         ['智护银龄', 'TAM', 'SAM', 'SOM', '财务预测', '334', '接单'], None),
    ]


# ------------------------------------------------- 3a-3g mirror (see git-pull-arena)
def rels_base(name):
    segs = name.split('/')
    return '/'.join(segs[:-2]) if len(segs) > 2 else ''


def resolve(base, target):
    segs = [s for s in base.split('/') if s] if base else []
    for part in target.split('/'):
        if part in ('', '.'):
            continue
        if part == '..':
            segs = segs[:-1] if len(segs) > 1 else []
            continue
        segs.append(part)
    return '/'.join(segs)


def verify(manifest):
    problems = []
    for entry in manifest['files']:
        rel = entry['path']
        path = os.path.join(ROOT, rel.replace('/', os.sep))
        if not os.path.isfile(path):
            problems.append('MISSING ' + rel)
            continue
        raw = open(path, 'rb').read()
        if len(raw) != int(entry['bytes']):
            problems.append('SIZE %s expected %s got %d' % (rel, entry['bytes'], len(raw)))
        digest = hashlib.sha256(raw).hexdigest()
        if digest != entry['sha256']:
            problems.append('SHA256 ' + rel)
        with zipfile.ZipFile(path) as zf:
            names = zf.namelist()
            if len(set(names)) != len(names):
                problems.append('3b duplicate zip entries in ' + rel)
            name_set = set(names)
            missing = [p for p in entry['required_parts'] if p not in name_set]
            if missing:
                problems.append('3b missing parts in %s: %s' % (rel, ', '.join(missing)))
            xml_text = {}
            for name in names:
                if not name.endswith(('.xml', '.rels')):
                    continue
                try:
                    xml_text[name] = zf.read(name).decode('utf-8')
                except Exception as exc:
                    problems.append('3c unreadable %s in %s (%s)' % (name, rel, exc))
            for name, text in xml_text.items():
                try:
                    ET.fromstring(text)
                except Exception:
                    problems.append('3c unparseable XML %s in %s' % (name, rel))
            for name, text in xml_text.items():
                if not name.endswith('.rels'):
                    continue
                base = rels_base(name)
                try:
                    root = ET.fromstring(text)
                except Exception:
                    continue
                for node in root:
                    target = node.get('Target') or ''
                    if not target or target.startswith('http'):
                        continue
                    if resolve(base, target) not in name_set:
                        problems.append('3d dangling %s -> %s in %s' % (name, target, rel))
            ct = xml_text.get('[Content_Types].xml')
            if ct is None:
                problems.append('3e no [Content_Types].xml in ' + rel)
            else:
                root = ET.fromstring(ct)
                defs = set()
                ovrs = set()
                for node in root:
                    tag = node.tag.split('}')[-1]
                    if tag == 'Default':
                        defs.add((node.get('Extension') or '').lower())
                    elif tag == 'Override':
                        ovrs.add(node.get('PartName') or '')
                for name in names:
                    if name == '[Content_Types].xml':
                        continue
                    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else ''
                    if ('/' + name) not in ovrs and ext not in defs:
                        problems.append('3e no content type for %s in %s' % (name, rel))
            body = ''.join(xml_text.values())
            for marker in entry['must_contain']:
                if marker not in body:
                    problems.append('3f marker %r not found in %s' % (marker, rel))
            if entry.get('min_slides'):
                slides = len([n for n in names if re.match(r'^ppt/slides/slide[0-9]+\.xml$', n)])
                if slides < int(entry['min_slides']):
                    problems.append('3g slides %d < %d in %s' % (slides, entry['min_slides'], rel))
    return problems


def write_manifest(specs):
    entries = []
    for path, kind, required, main_part, markers, min_slides in specs:
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        raw = open(path, 'rb').read()
        with zipfile.ZipFile(path) as zf:
            present = set(zf.namelist())
            slides = len([n for n in present if re.match(r'^ppt/slides/slide[0-9]+\.xml$', n)])
        entries.append({
            'path': rel,
            'kind': kind,
            'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(),
            'required_parts': required,
            'main_part': main_part,
            'must_contain': [m for m in markers if m],
            'min_slides': min_slides,
            'sandbox_selftest': {'parts': len(present), 'slides': slides},
        })
    manifest = {
        'generated_utc': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'generator': 'code/build_commercial_cases.py',
        'generator_note': ('python-docx + python-pptx deliverables for the four commercial skills; '
                           'this manifest is the contract the REAL machine verifies in '
                           'code/local_check.ps1 section 3 (3a-3g + 3h Office COM open test)'),
        'how_local_verifies': ('sha256/bytes match, OOXML required parts, every xml part parses, '
                               'relationships resolve, content types cover every part, text markers '
                               'present, slide counts; then Word/PowerPoint (or WPS) opens them read-only'),
        'files': entries,
    }
    problems = verify(manifest)
    if problems:
        print('[FAIL] the 3a-3g mirror found %d problem(s) - manifest NOT written:' % len(problems), file=sys.stderr)
        for item in problems:
            print('       ' + item, file=sys.stderr)
        return 1
    with open(MANIFEST, 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
    print('wrote: %s' % os.path.relpath(MANIFEST, ROOT))
    print('== 3a-3g mirror PASSED for %d file(s)' % len(entries))
    for entry in entries:
        print('   OK %s (%d B, %s, slides=%s)'
              % (entry['path'], entry['bytes'], entry['kind'], entry['sandbox_selftest']['slides']))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', choices=['xianyu', 'folktale', 'courseware', 'bp'])
    ap.add_argument('--verify', action='store_true')
    args = ap.parse_args()

    if args.verify:
        if not os.path.isfile(MANIFEST):
            print('[ERROR] no manifest - build first', file=sys.stderr)
            return 1
        return write_manifest_from_cache()

    specs = []
    builders = {'xianyu': build_xianyu, 'folktale': build_folktale,
                'courseware': build_courseware, 'bp': build_bp}
    if args.only:
        specs.extend(builders[args.only]())
    else:
        for key in ('xianyu', 'folktale', 'courseware', 'bp'):
            specs.extend(builders[key]())
    return write_manifest(specs)


def write_manifest_from_cache():
    with open(MANIFEST, encoding='utf-8') as fh:
        manifest = json.load(fh)
    problems = verify(manifest)
    if problems:
        print('[FAIL] %d problem(s):' % len(problems), file=sys.stderr)
        for item in problems:
            print('       ' + item, file=sys.stderr)
        return 1
    print('== 3a-3g mirror PASSED for %d cached file(s)' % len(manifest['files']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
