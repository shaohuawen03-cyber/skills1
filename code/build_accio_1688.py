#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the Accio x 1688 merchant value pack (Chinese).

Outputs:
  deliverable/accio_1688/accio_1688_merchant_guide.docx  (comprehensive guide)
  deliverable/accio_1688/accio_1688_quick_view.md        (one-page quick view)
  deliverable/OFFICE_HASHES.json                          (adds the docx entry)
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

from docx import Document
from docx.shared import Pt, Inches, RGBColor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'code'))
from build_commercial_cases import verify  # noqa: E402


def sha256(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

OUT_DIR = os.path.join(ROOT, 'deliverable', 'accio_1688')
DOCX = os.path.join(OUT_DIR, 'accio_1688_merchant_guide.docx')
MD = os.path.join(OUT_DIR, 'accio_1688_quick_view.md')
COVER = os.path.join(OUT_DIR, 'accio_1688_cover.png')

doc = Document()
try:
    doc.styles['Normal'].font.name = 'Microsoft YaHei'
    doc.styles['Normal'].font.size = Pt(10.5)
except Exception:
    pass


def h(text: str, level: int = 1) -> None:
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)


def para(text: str, bold: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold


def bullets(items) -> None:
    for it in items:
        doc.add_paragraph(it, style='List Bullet')


def table(headers, rows, widths=None) -> None:
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = 'Light Grid Accent 1'
    hdr = t.rows[0].cells
    for i, name in enumerate(headers):
        hdr[i].text = name
        for paragraph in hdr[i].paragraphs:
            for run in paragraph.runs:
                run.bold = True
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
    if widths:
        for i, w in enumerate(widths):
            for r in t.rows:
                r.cells[i].width = Inches(w)
    doc.add_paragraph()


# ---------------------------------------------------------------- cover
h('Accio Work x 1688 商家价值全解手册', 0)
para('能为商家带来什么好处, 能干什么, 一次讲透')
if os.path.exists(COVER):
    try:
        doc.add_picture(COVER, width=Inches(6.2))
    except Exception:
        pass
para('适用对象: 1688 商家 / 内贸工厂 / 跨境创业者 / 外贸业务员')
para('版本: v1.0 (基于公开资料整理, 数据与功能以官网为准)')

# ---------------------------------------------------------------- 1
h('一、认识 Accio Work', 1)
para('Accio Work 是阿里巴巴国际站团队于 2026 年 3 月发布的企业级 AI Agent 平台, '
     '定位是「一支会干活的 AI 商业团队」, 而不是只会聊天的问答机器人。'
     '它以桌面端 (Windows / macOS) 为载体, 本地优先, 可以读写电脑文件、运行命令、'
     '控制浏览器、调用外部应用, 把选品、找厂、谈判、建站、发品、营销、接单的全链路工作直接做完。')
table(
    ['项目', '内容'],
    [
        ['出品方', '阿里巴巴国际站 (Accio)'],
        ['发布', '2026 年 3 月 23 日'],
        ['用户规模', '超 1000 万月活用户'],
        ['产品形态', '桌面端 (Windows 10+ 64 位 / macOS 11+) + 网页版 + 移动 App'],
        ['内置技能', '39+ (电商与供应链 19 个 / 营销内容 20 个) + 国际站私有 Skills 7 大模块'],
        ['应用授权', '48 个: Gmail、Instagram、TikTok、X、Facebook、YouTube、LinkedIn、WhatsApp、Shopify、WooCommerce、Etsy、eBay、Amazon、Temu、Shein、1688、阿里国际站、OKKI、PayPal、Microsoft 365、Google Workspace 等'],
        ['大模型', '通义千问、DeepSeek、Kimi、MiniMax 等国内主流模型, 可给不同 Agent 配不同模型, 免管理 API Key'],
        ['远程操控', '微信、钉钉、飞书接入 Bot 后可下指令、自动回复'],
        ['安全', '本地优先 + 隔离沙箱 + 四级权限 (默认 / 询问 / 敏感需批准 / 高危隔离确认)'],
    ],
    [1.6, 5.0])

# ---------------------------------------------------------------- 2
h('二、1688 商家的机遇与痛点', 1)
para('1688 是中国最大的 B2B 内贸批发平台, 背后是全国最完整的产业带工厂资源。'
     '今天的 1688 商家普遍面临三个机遇和四个痛点:')
para('三个机遇', bold=True)
bullets([
    '跨境电商持续增长, 海外买家直接向中国工厂拿货的需求越来越旺。',
    'AI 工具普及, 一个人就能干过去一个部门的活, 小团队也能做全球生意。',
    '阿里系数据打通, 1688 货源 + 国际站渠道 + Accio AI 能力形成完整出海通路。',
])
para('四个痛点', bold=True)
bullets([
    '有好货但不会卖到海外: 缺外语、缺运营、缺投放, 招人成本高。',
    '找客难、接单难: 询盘来了不会跟, 客户背景不知道, 报价全靠拍脑袋。',
    '上品慢: 一条链接从拍图、抠图、写文案到上架要大半天, 商品多了根本做不过来。',
    '数据看不懂: 不知道什么好卖、同行卖多少、运费税费多少, 决策靠感觉。',
])
para('Accio Work 正是针对这些痛点设计的: 把 1688 的货源优势, 通过 AI 直接变成海外订单。')

# ---------------------------------------------------------------- 3
h('三、Accio 能为 1688 商家带来的 12 大好处', 1)

benefits = [
    ('1. 内贸一键转外贸, 货源通全球',
     'Accio 内置 1688 选品与供应商寻源能力, 还能一键把 1688 商品「搬」到阿里国际站 (官方「一键搬厂」计划, '
     '3 分钟完成铺品审核), 或用「一键建站」技能 30 分钟生成品牌独立站 (Shopify/WooCommerce/Shopline/独立站), '
     '把国内现货直接铺向海外市场。'),
    ('2. 一个人就是一支跨国团队',
     '「1 人 + 8 个 Agent」的架构: 选品、设计、上架、投放、接待、跟单各有专职 Agent。'
     '真实案例里, 教培转型卖家 7 分钟完成过去一周的产品上架与优化; 棒球帽卖家 2 个月把 3000 多顶帽子卖到欧美非洲。'
     '人效提升可达 10 倍, 不用养团队也能做大生意。'),
    ('3. 数据资产直接可用',
     'Accio 底座是 10 亿+ 商品数据、5000 万+ 企业数据、实时海关数据与汇率, '
     '选品、定价、找厂、谈判都有一句 prompt 就能调用的完整数据支撑, 不用自己满世界查。'),
    ('4. 选品不再凭感觉',
     '「电商市场数据分析」提供类目销量趋势、季节性周期、价格带分布; '
     '「商品趋势分析」用 Google Trends 预测趋势; 「竞品分析」自动识别同款最大出货商。'
     'TikTok/亚马逊爆品趋势与 1688 货源交叉验证, 找到「海外有热度、国内有现货」的蓝海款。'),
    ('5. 找厂谈判像有个老采购',
     '1688 深度搜索自动剔除贸易商, 只留源头工厂和实力商家; 支持按 MOQ (最小起订量)、'
     'OEM/ODM 定制能力、经营模式精准过滤; 一键生成供应商对比表 (出厂价、交期、评分、案例)。'
     '再用「AI 电商外贸业务员」自动给供应商发邮件询盘、多轮砍价、要样品、催交期。'),
    ('6. 上品效率指数级提升',
     '「发品生图」自动出白底图、场景图、模特图、营销图, 批量去背景、生成商品视频; '
     '「产品详情页设计」出高转化详情页; 「一键发品」把素材 zip 或选好的商品直接铺到国际站。'
     '传统 7 天的上品流程被压缩到几分钟, 详情页 9 分钟自动优化, 案例里转化率提升一倍。'),
    ('7. 询盘转化率大幅提升',
     '「买家挖掘与背调」自动验证买家真伪、识别真实需求, 发现隐藏的高价值单 (案例: 识别政府采购背景拿下 200 万意向单; '
     '挖出匿名客户背后的国际赛事大单);「询盘激活」全方位跟进回复, 询盘不再凉掉;'
     '「AI 智能接待」7x24 小时多语言接待, 抓关键需求、查运费税费、自动生成报价单。'),
    ('8. 营销素材和投放全自动',
     '「广告投放」「Google Ads 智能体」「社媒营销」自动做 YouTube/TikTok/Instagram/X 的视频营销、'
     '红人营销、节日营销策划, 自动写文案、出图、剪视频, 一条链接生成全平台素材。'),
    ('9. 经营有体检、决策有依据',
     '「国际站经营分析」「经营体检报告」分析流量、转化、客单价, 并给出同行水位对标和优化行动清单, '
     '相当于免费配了个电商分析师。'),
    ('10. 物流、合规、风险有人管',
     '「物流查询与询价」「查HS编码」「HS编码转换」「物流查税」「风险防护」覆盖运费查询、'
     '关税合规、知识产权与账号风险, 出海少踩坑。'),
    ('11. 多平台统一管理',
     'Amazon、Temu、Shein、TikTok Shop、Shopify、eBay、Etsy、WooCommerce、独立站数据直联, '
     '一个工作台看所有平台的经营情况, 统一发布、统一分析。'),
    ('12. 安全可控, 省钱省心',
     '本地优先架构, 核心数据默认留在本机; 隔离沙箱执行高危任务; 四级权限体系逐项确认敏感操作; '
     '微信/钉钉/飞书随时下指令盯进度。对比自建团队, 成本是零头; 对比传统 SaaS, 它是把活干完而不是只出报表。'),
]
for title, body in benefits:
    h(title, 2)
    para(body)

h('好处对照表: 以前 vs 用 Accio 之后', 2)
table(
    ['环节', '传统做法', '用 Accio Work'],
    [
        ['选品', '翻平台看数据, 凭经验押款', '类目趋势+蓝海词+竞品对标, 一句话出结论'],
        ['找厂', '1688 一家家点, 分不清贸易商', '自动剔除贸易商, 只看源头工厂实力商家'],
        ['比价', '手动记录 Excel', '自动对比出厂价/交期/评分生成表格'],
        ['谈判', '写邮件磨来磨去', 'AI 自动询盘、多轮砍价、催样品'],
        ['拍图做图', '外包或美工, 一张几十元', '白底图/场景图/模特图/视频批量生成'],
        ['上架', '一条链接半天', '几分钟一条, 一键铺国际站/Shopify'],
        ['接客', '守着电脑, 时差错过单', '7x24 多语言自动接待, 自动报价'],
        ['投广告', '请投手, 试错成本高', '广告智能体自动搭建优化广告'],
        ['看经营', '后台报表看不懂', '经营体检+同行对标+行动清单'],
        ['出海合规', '踩坑交学费', '查税/HS编码/风险防护内置'],
    ],
    [1.1, 2.6, 2.9])

# ---------------------------------------------------------------- 4
h('四、Accio 具体能干什么: 能力全景', 1)
para('39+ 内置技能按五大族群覆盖全链路, 再加 7 大国际站私有 Skills:')
table(
    ['能力族', '代表技能', '对 1688 商家的用处'],
    [
        ['电商与供应链 (19)', '电商市场数据分析、竞品分析、选爆品、找同款最大出货商、AI 电商外贸业务员、运营方案、商品趋势分析、Shopify 店铺装修、广告投放、报关单据合规审查、跨境电商销售数据分析、经济指标、政策法规、公司财报、CRM、销售管理、跨平台电商数据分析、科研文献、商业案例库', '选品、找厂、比价、谈判、开店、投放、报关、管客户'],
        ['营销与内容 (20)', '文案写作、产品文案、文章写作、SEO 营销、社交媒体营销、email 营销、网红营销、YouTube 视频营销、TikTok 视频营销、Instagram 图文视频、X 图文营销、产品图片设计、创意海报设计、电商详情图设计、产品场景图、模特换装、数字人视频、PPT 制作、论文写作、新闻检索', '图片、视频、文案、投放素材一站式产出'],
        ['国际站 Skills (7)', '选品洞察、发品生图、广告优化、经营分析、客户接待、物流查税、风险防护', '阿里国际站全流程私有能力, 一键搬厂后直接用'],
        ['工具与编程', '自然语言编程、Python、Excel、文件读写、浏览器自动化、定时任务', '让 Agent 生成表格、跑脚本、盯数据、定时汇报'],
        ['团队协作', 'Agent 群聊 (TL + 成员)、多 Agent 编排、微信/钉钉/飞书 Bot', '复杂项目拆给多个 Agent 并行干, 老板远程指挥'],
    ],
    [1.3, 3.4, 1.9])
para('补充: 平台支持 MCP 标准接入外部工具服务器, 技能市场可安装更多技能, 也可自建技能。'
     '浏览器自动化基于 Chrome DevTools Protocol 控制真实浏览器, 能搜索、抓取、填表、截图、跑多步流程。'
     '定时任务类似 cron, 本地运行, 断网也能跑, 错过的任务重启后补执行。')

# ---------------------------------------------------------------- 5
h('五、1688 商家 8 大实战场景 + 金牌指令', 1)
para('每个场景给出可直接复制的指令 (prompt), 在 Accio Work 里说人话即可执行。')

scenarios = [
    ('场景 1: 选品找蓝海',
     '「分析 1688 家居类目近 90 天销量趋势和价格带分布, 结合 TikTok 上 #homedecor 的热度, '
     '找出 5 个海外有热度、国内有现货的蓝海款, 按预估毛利排序。」'),
    ('场景 2: 一键找源头工厂',
     '「在 1688 找 5 家做硅胶折叠水杯的源头工厂, 剔除贸易商和二手贩子, 只要实力商家, '
     '支持 OEM 贴牌、MOQ 500 个以内, 输出对比表: 出厂价、交期、评分、案例。」'),
    ('场景 3: 自动询盘砍价',
     '「给对比表里前 3 家供应商发询盘邮件, 以 2000 个的量级谈价, 目标价降 8%, '
     '要求免费样品和交期保证, 后续回复自动跟进。」'),
    ('场景 4: 一键搬厂上国际站',
     '「把选好的 20 个 1688 商品整理成搬厂素材包, 按阿里国际站规则生成标题、类目、'
     '关键词和详情, 提交一键搬厂。」'),
    ('场景 5: 30 分钟建品牌独立站',
     '「用一键建站技能, 把这批货建成 Shopify 独立站, 品牌名 Aurora Gear, '
     '英文详情页、定价按成本加 2.5 倍、接 PayPal 收款。」'),
    ('场景 6: 发品生图和详情页',
     '「为这款水杯生成 5 张白底图、3 张户外场景图、2 张模特图, 再出一版高转化详情页, '
     '9 分钟内给我优化前后的对比。」'),
    ('场景 7: 买家背调与接待',
     '「对今天进来的 8 条询盘做买家背调: 公司规模、采购历史、风险点, 标出最值得跟的 2 条, '
     '并用英西双语生成针对性回复和报价单。」'),
    ('场景 8: 经营体检与复盘',
     '「做一份本月国际站经营体检报告: 流量、转化、客单价对比同行水位, '
     '列出最值得先做的 3 个改进行动。」'),
]
for title, prompt in scenarios:
    h(title, 2)
    para('金牌指令示例:')
    para(prompt)

# ---------------------------------------------------------------- 6
h('六、真实案例集 (来自 Accio 官方公开案例)', 1)
table(
    ['用户', '背景', '用 Accio 做到的事'],
    [
        ['张乾超', '棒球帽卖家', '1 人 + 8 个 Agent, 2 个月把 3000 多顶棒球帽卖到欧美及非洲, 选品到设计压缩到 1 天, 挪威客户靠几十款定制图样当场敲单'],
        ['温杰', '教培转型创业', '7 分钟完成过去一周的上架与优化, 9 分钟自动优化详情页, 转化率提升一倍, 一人公司高效运转'],
        ['李马辉', '体育用品创业', '一个人的工作拆给 Agent 团队, 健身器材设计与销售稳步增长'],
        ['王景田', '十年外贸老兵', '新店开业 7 天, 精准识别 OEM 询盘背后的政府采购背景, 前置解决合规风险, 200 万意向单推进到验厂'],
        ['徐琛', '潮玩品牌', '25 人初创团队用 Accio 背调, 识别匿名客户背后的国际赛事大单, 击败十几家老牌工厂拿下吉祥物采购合同'],
        ['金陈郸', '棒球赛道 TOP1', '深挖询盘买家价值, 拿下英国老牌体育商千万级采购及全美顶尖俱乐部大单'],
        ['Karl', '德国草莓品牌', '以往飞广州参展, 现在一个上午完成整场展会的采购工作, 17 年来首次不跑线下展'],
        ['Wispr Flow', '硅谷 AI 公司', '全程序员团队筛出埃及棉刺绣厂, 一站式打造爆款周边'],
        ['穆夏基金会', '布拉格博物馆', '一两天开发出首款艺术折叠伞, 百年名画焕发新生'],
    ],
    [1.1, 1.4, 4.1])
para('注: 以上案例来自 Accio 官方公开宣传, 个体结果因人因货而异, 不构成收益承诺。')

# ---------------------------------------------------------------- 7
h('七、ROI 速算 (示例模型)', 1)
table(
    ['投入项', '传统方式 (月)', '用 Accio (月)', '节省'],
    [
        ['运营/美工/客服人力 (3 人)', '25000-40000 元', '1 人 + Agent', '约 70%-90% 人力成本'],
        ['产品图/详情页外包', '3000-8000 元', '发品生图/详情图技能', '基本归零'],
        ['展会/拓客', '单次数万元', '买家挖掘+询盘激活', '大幅下降'],
        ['上品效率', '3-5 条/天', '数十条/天', '效率 5-10 倍'],
        ['接客覆盖', '8 小时', '7x24 小时', '时差询盘不再丢单'],
    ],
    [2.2, 1.7, 1.5, 1.4])
para('综合公开案例口径: 人效提升可达 10 倍, 常见首单周期从数月缩短到数周。'
     '实际效果取决于类目、货源、投入程度, 请以自身实测为准。')

# ---------------------------------------------------------------- 8
h('八、上手路线图 (建议 2 周跑通)', 1)
table(
    ['阶段', '做什么', '产出'],
    [
        ['第 1 天', '安装中文版桌面端, 注册登录, 设置中文界面和 E 盘工作目录', '可用的工作台'],
        ['第 2 天', '加载 Chrome 插件, 授权 1688 / 国际站等应用', '连接器就绪'],
        ['第 3-5 天', '跑通场景 1 选品 + 场景 2 找厂 (先挑一个最痛的场景)', '蓝海款清单 + 工厂对比表'],
        ['第 6-7 天', '场景 3 谈判 + 场景 4/5 铺货建站', '第一批链接上线'],
        ['第 2 周', '场景 6 素材 + 场景 7 接待 + 场景 8 复盘, 建定时任务自动盯数据', '稳定的获客-接单-复盘循环'],
    ],
    [1.1, 3.6, 2.0])
para('最佳实践: 先跑通一个场景再扩展; 复杂任务直接给大目标, 让 Accio 自己拆解执行; '
     '重要操作用权限确认把住安全关; 常用打法存成技能复用。')

# ---------------------------------------------------------------- 9
h('九、常见问题 FAQ', 1)
faqs = [
    ('Accio Work 和普通 AI 聊天有什么区别?',
     '普通聊天只能给文字建议; Accio Work 是执行导向的 Agent 平台, 能读本地文件、跑命令、'
     '控制浏览器、调外部 API, 直接把活干完交结果。'),
    ('1688 商家没有国际站店铺能用吗?',
     '能。可以先用 1688 选品、找厂、谈判、建 Shopify 独立站; 也可以走一键搬厂开通国际站, 享受双重流量扶持。'),
    ('中文版和国际版有什么区别?',
     '中国版 (accio-ai.com) 界面中文、手机号注册、国内大模型、微信/钉钉/飞书联动; '
     '国际版 (accio.com/work) 面向海外账户体系。1688 商家选中国版即可。'),
    ('数据安全吗?',
     '本地优先架构, 核心数据默认存本机; 敏感能力需明确授权; 高危任务在隔离沙箱中执行; 四级权限体系逐项确认。'),
    ('需要会写代码吗?',
     '不需要。说人话下指令即可。会 Python/Excel 的话还能让 Agent 帮你写脚本、做表。'),
    ('电脑配置要求?',
     'Windows 10/11 64 位或 macOS 11+, 8GB 内存推荐, Chrome 110+ (浏览器自动化推荐 Chrome 144+), 需联网。'),
    ('支持哪些大模型?',
     '通义千问、DeepSeek、Kimi、MiniMax 等国内主流模型, 可给不同 Agent 分配不同模型。'),
    ('手机上能用吗?',
     '有移动 App 看进度和确认关键步骤; 微信/钉钉/飞书接 Bot 后可直接下指令。'),
]
for q, a in faqs:
    para(q, bold=True)
    para(a)

# ---------------------------------------------------------------- 10
h('十、资料来源与免责声明', 1)
bullets([
    'Accio Work 官网 (中国版): https://www.accio-ai.com/work',
    'Accio 学习中心 (安装教程/上手文档): https://www.acciopro.com/learn/index.html',
    'Accio Work 官方帮助中心 (help.accio.com 中文)、Accio Skill 开发文档',
    '公开报道与教程: AI-BOT 资讯、MAIGC 实操指南、知乎专栏、amz123 等',
    '案例数据来自 Accio 官方公开案例页',
])
para('免责声明: 本手册为公开资料整理与工具用法说明, 非官方文件。产品功能、价格与政策以官网为准。'
     '案例结果因人因货而异, 本资料不构成任何收益承诺或投资建议。')

docx_bytes = os.path.getsize(DOCX) if os.path.exists(DOCX) else 0

os.makedirs(OUT_DIR, exist_ok=True)
doc.save(DOCX)
print('wrote', DOCX, os.path.getsize(DOCX), 'bytes (prev', docx_bytes, ')')

# ---------------------------------------------------------------- quick view md
quick = '''# Accio Work x 1688 商家速览 (一页版)

## 一句话
Accio Work 是阿里国际站的企业级 AI Agent 平台 (桌面端, 本地优先, 1000 万+ 月活),
把 1688 的好货源通过 AI 直接变成海外订单: 选品、找厂、谈判、建站、发品、营销、接单全链路自动干。

## 能为商家带来的好处 (12 条)
| # | 好处 | 一句话 |
| --- | --- | --- |
| 1 | 内贸转外贸 | 1688 货一键铺国际站/Shopify, 30 分钟建站 |
| 2 | 一人顶一队 | 1 人 + 8 个 Agent, 人效提升 10 倍 |
| 3 | 数据资产 | 10 亿+ 商品、5000 万+ 企业、海关汇率数据 |
| 4 | 选品有据 | 类目趋势+蓝海词+竞品对标, 押中率高 |
| 5 | 找厂会砍价 | 剔除贸易商只留源头厂, 自动询盘谈判 |
| 6 | 上品极快 | 发品生图/详情页/一键发品, 7 天流程变几分钟 |
| 7 | 询盘不丢 | 买家背调验真 + 7x24 多语言接待 |
| 8 | 营销自动 | 广告、社媒、红人、节日营销全自动 |
| 9 | 经营有体检 | 同行水位对标 + 行动清单 |
| 10 | 风险有人管 | 物流查税、HS 编码、风险防护 |
| 11 | 多平台一屏 | Amazon/Temu/Shein/TikTok Shop/Shopify 统一管 |
| 12 | 安全省钱 | 本地优先+沙箱+四级权限, 成本是自建团队零头 |

## 能干什么 (技能族)
- 电商与供应链 19 个: 市场分析、竞品分析、选爆品、外贸业务员、Shopify 装修、广告投放、报关合规...
- 营销与内容 20 个: 文案、详情图、场景图、模特换装、数字人视频、YouTube/TikTok/Instagram 营销...
- 国际站 7 大私有 Skills: 选品洞察、发品生图、广告优化、经营分析、客户接待、物流查税、风险防护
- 48 个应用授权: 1688、国际站、Gmail、Shopify、TikTok、Instagram、WhatsApp、OKKI...
- 微信/钉钉/飞书远程下指令, 定时任务本地跑, 支持 MCP 扩展

## 8 大实战场景
1. 选品找蓝海 (TikTok 热度 x 1688 现货交叉)
2. 一键找源头工厂 (剔除贸易商, MOQ/OEM 过滤, 对比表)
3. 自动询盘砍价 (多轮邮件谈判)
4. 一键搬厂上国际站 (3 分钟铺品审核)
5. 30 分钟建 Shopify 独立站
6. 发品生图 + 详情页 9 分钟优化
7. 买家背调 + 7x24 接待报价
8. 经营体检 + 同行对标复盘

每个场景的金牌指令见《Accio_1688 商家价值全解手册》第五章。

## 完整版
`deliverable/accio_1688/accio_1688_merchant_guide.docx` (含 12 大好处详解、能力全景表、
8 大场景金牌指令、真实案例集、ROI 速算、上手路线图、FAQ)

*公开资料整理, 非官方文件, 案例不构成收益承诺。*
'''
with open(MD, 'w', encoding='utf-8') as f:
    f.write(quick)
print('wrote', MD)

# ---------------------------------------------------------------- office hashes
hash_path = os.path.join(ROOT, 'deliverable', 'OFFICE_HASHES.json')
with open(hash_path, 'r', encoding='utf-8') as f:
    hash_doc = json.load(f)

entry = {
    'path': 'deliverable/accio_1688/accio_1688_merchant_guide.docx',
    'kind': 'docx',
    'bytes': os.path.getsize(DOCX),
    'sha256': sha256(DOCX),
    'required_parts': [
        '[Content_Types].xml', '_rels/.rels', 'word/document.xml',
        'word/styles.xml', 'word/_rels/document.xml.rels', 'docProps/core.xml',
    ],
    'main_part': 'word/document.xml',
    'must_contain': ['Accio', '1688', 'Shopify', '1688 商家'],
    'min_slides': None,
    'sandbox_selftest': {'parts': 0, 'slides': 0},
}
import zipfile
with zipfile.ZipFile(DOCX) as zf:
    entry['sandbox_selftest']['parts'] = len(set(zf.namelist()))
hash_doc['files'] = [e for e in hash_doc['files'] if e.get('path') != entry['path']]
hash_doc['files'].append(entry)
hash_doc['note'] = ('These are the generated Office documents of the case pack (01-04) '
                    'and the Accio x 1688 guide. sha256 must match until intentionally rebuilt. '
                    'checks.required/forbidden are tested against full text (python-docx on sandbox, '
                    'Word/WPS COM on user machine).')
result = verify(hash_doc)
hash_doc['verify'] = result
with open(hash_path, 'w', encoding='utf-8') as f:
    json.dump(hash_doc, f, ensure_ascii=False, indent=2)
    f.write('\n')
print('office hashes updated; verify problems:', result)
if result:
    sys.exit(1)
