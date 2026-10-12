# Accio Work 中文版安装到 E 盘 完整指南

> 适用系统: Windows 10/11 64 位。目标: 把 Accio Work 中文版安装到 `E:\AccioWork`，
> 并完成中文界面、Chrome 插件、账号登录的全部配置。
> 自动化脚本: `code/tasks/install_accio_work.ps1` (watcher 第 3 轮任务会自动执行)。

---

## 一、为什么要装中文版 + 装到 E 盘

| 项目 | 说明 |
| --- | --- |
| 中文版 | `accio-ai.com` 是中国版官网 (国际版是 `accio.com/work`)。中国版界面中文、
| | 手机号可注册、内置国内大模型 (通义千问/DeepSeek/Kimi/MiniMax)、支持微信/钉钉/飞书。 |
| E 盘 | C 盘系统盘空间紧张时, 把约 500MB 的应用和后续生成文件放 E 盘, 重装系统也不丢。 |
| 安装包 | 官网下载的 Windows 64 位 .exe, 约 150MB。 |

---

## 二、自动安装 (推荐, 三步)

1. 保持 git-sync watcher 在后台运行 (`watch.ps1`, 计划任务 `git-sync-watch-skills1-def3bdd3`)。
2. 我这边发起第 3 轮握手后, 你的机器会自动执行:
   `code/tasks/install_accio_work.ps1` (下载 -> 静默安装到 `E:\AccioWork` -> 写回执)。
3. 完成后回执在 `results/accio_install/latest.md`, 我会在握手里报告安装结果。

脚本的安装策略 (全自动, 无需手动点):
- 先尝试 NSIS 静默安装并指定目录: `AccioWork-setup.exe /S /D=E:\AccioWork`。
- 如果安装器不支持自定义目录 (Squirrel 类, 默认装到 `%LOCALAPPDATA%\AccioWork`):
  自动把安装目录搬到 `E:\AccioWork`, 并在原位置留一个目录联接 (junction),
  快捷方式和自动更新依然正常。
- 全部失败时回执会写明原因, 照着第三节手动装即可。

---

## 三、手动安装 (备用)

### 第 1 步: 下载
- 打开 `https://www.accio-ai.com/work`, 点「下载桌面版」, 选 Windows 版本。
- 下载完成后得到类似 `AccioWork-Setup-x64.exe` 的安装包。

### 第 2 步: 安装到 E 盘
按 Win+R, 输入 `cmd`, 回车, 执行 (路径按实际安装包名调整):

```text
"%USERPROFILE%\Downloads\AccioWork-Setup-x64.exe" /S /D=E:\AccioWork
```

- `/S` 静默安装, `/D=E:\AccioWork` 指定安装目录 (NSIS 安装器支持)。
- 如果弹出 UAC 或图形界面一路「下一步」, 且安装路径选 `E:\AccioWork`。

### 第 3 步: 如果安装器不给选目录 (装到了 C 盘)
1. 完成默认安装 (通常在 `C:\Users\<你>\AppData\Local\AccioWork`)。
2. 关闭 Accio Work (右下角托盘也退出)。
3. 管理员 cmd 执行搬移 + 联接:

```text
robocopy "%LOCALAPPDATA%\AccioWork" "E:\AccioWork" /E /MOVE
mklink /J "%LOCALAPPDATA%\AccioWork" "E:\AccioWork"
```

4. 重新打开 Accio Work, 一切照常 (它以为自己还在 C 盘, 实体文件在 E 盘)。

---

## 四、安装后的 5 项必备配置

1. **语言**: 设置 -> 通用 -> 界面语言 -> 中文 (中国版默认就是中文)。
2. **默认工作目录**: 设置 -> 通用 -> 默认工作目录, 改成 `E:\AccioWorkData` 之类的 E 盘目录,
   Agent 生成的文件都存这里。
3. **注册登录**: 手机号或邮箱注册, 也可用阿里巴巴国际站账号直接登录。
4. **Chrome 插件**: 打开 Chrome 扩展页 `chrome://extensions`, 开启「开发者模式」,
   「加载已解压的扩展程序」选择安装目录下的 `plugin` 文件夹
   (`E:\AccioWork\plugin`, 若用了联接则 `%LOCALAPPDATA%\AccioWork\plugin`)。
   Chrome 建议 110+ 版本, 并把 Chrome 设为系统默认浏览器 (排查打不开问题的第一招)。
5. **应用授权**: 在「连接器/应用」里按需授权 1688、阿里国际站、Gmail、Shopify 等 (共支持 48 个)。

---

## 五、常见问题

| 问题 | 处理 |
| --- | --- |
| 杀毒软件拦截 | 选「允许运行」。Accio Work 是本地优先桌面应用, 核心数据默认在本地。 |
| 双击无反应 / 打不开 | 90% 是 Chrome 没设为默认浏览器导致本地端口没起来, 改默认浏览器后重启。 |
| 装完想确认版本 | 打开 Accio Work -> 设置 -> 关于, 或看回执 `results/accio_install/latest.md` 里的版本号。 |
| 想卸载 | 设置 -> 应用 -> Accio Work 卸载; 若做过搬移, 先删联接 (`rmdir "%LOCALAPPDATA%\AccioWork"`) 再卸载。 |
| 自动更新会不会失败 | 联接模式下更新写入的仍是 `E:\AccioWork`, 不受影响。 |

---

## 六、验收标准

- [ ] `E:\AccioWork` 下能找到 Accio Work 主程序 .exe
- [ ] 打开后界面为中文, 可登录
- [ ] Chrome 插件加载成功
- [ ] `results/accio_install/latest.md` 显示 result: ok

---

*本指南由 skills1 自动化任务生成, 配套脚本 `code/tasks/install_accio_work.ps1`。*
