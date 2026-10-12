# media-bridge 配置指南（Telegram / 公众号 / 小红书）

笔记本上的部署目录：`E:\0github\git-sync\media-bridge\`

- `tg_bridge.py` — Telegram 遥控器（官方 Bot API，纯标准库，走本机代理 127.0.0.1:10808）
- `wxmp_cli.py` — 公众号小工具（官方 API + wechatpy，直连 api.weixin.qq.com，不走代理）
- `xhs_publish.py` — 小红书通道状态检查（发布走 social-auto-upload 的 `sau` CLI）
- `run_tg_bridge.ps1` — 遥控器守护（计划任务 `media-bridge-tg`，开机自启，掉线 30 秒自动拉起）

## ① Telegram（2 分钟）

1. 在 Telegram 里找 **@BotFather** → 发 `/newbot` → 起名字 → 得到 token（形如 `123456:ABC-xxx`）
2. 把 token 粘成一行，保存到 `E:\0github\git-sync\media-bridge\conf\tg_token.txt`（不用重启，桥每 60 秒自动重读）
3. 给你的 bot 发 `/start`（认主，只有这个聊天号能指挥）→ `/ping` 验证
4. token 不要发给任何人、不要提交进仓库

## ② 微信公众号（3 分钟）

1. [mp.weixin.qq.com](https://mp.weixin.qq.com) → 设置与开发 → 开发设置 → 拿 **AppID** 和 **AppSecret**（没账号可先注册“测试号”做通路验证）
2. 写入 `E:\0github\git-sync\media-bridge\conf\wxmp.txt`，两行：
   ```
   appid=你的AppID
   secret=你的AppSecret
   ```
3. 验证：`venv\Scripts\python.exe wxmp_cli.py check`
   - 报 `access_token OK` 即通
   - 报 40164 → 按提示把本机公网 IP 加进公众号后台的 IP 白名单再试
4. 发文流程：`upload-thumb 封面.jpg` → `draft "标题" 文章.md` → 后台预览 → `publish 草稿media_id`（草稿/发布接口需要**认证**的订阅号/服务号）

## ③ 小红书（装好 sau 后 3 分钟）

小红书没有个人内容 API，发布走浏览器自动化（你自己的登录态，低风险）：

1. 等 sau 安装完成（第二轮任务自动装）
2. `venv\Scripts\sau.exe xhs login --account 你的账号名` → 用小红书 App 扫码
3. 之后发布/定时发布都通过 `sau xiaohongshu ...`，可由值守或 Telegram 遥控器调用

## 安全约定

- `conf/` 目录（token、AppSecret、cookies）永远不进 git 仓库
- Telegram 桥只认第一个 `/start` 的聊天号；换号就删 `conf/tg_owner.txt` 重新认主
- 公众号接口直连（国内线路），不要给它挂代理

## 已安装状态（2026-10-03，r178-r183）

- Telegram 桥：已注册为计划任务 `media-bridge-tg` 并运行中（等 token）
- 公众号 CLI：纯 requests 实现就绪（等 AppID/Secret）
- 小红书：sau CLI 可用（平台名 `xiaohongshu`）+ patchright chromium 就绪（等扫码）
