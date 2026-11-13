<p align="center"><img src="assets/tuoyuanai.svg" width="80" alt="拓元 AI" /></p>

# 拓元 AI Plugin 与 Skill

让你的 Agent 开始创作。用自然语言调用拓元 AI 创作图像、视频、剧本和故事板，上传参考素材，在同一项目中持续修改，并把完成的成果批量下载到本地。

[拓元 AI](https://tuoyuanai.com) · [安装与连接](https://tuoyuanai.com/plugin) · [使用指引](skills/tuoyuanai/SKILL.md) · [MIT 许可证](LICENSE)

> 当前为 OpenAPI 预览版本，需要平台提供 `/openapi/` 与 Access Key 功能。仓库更新不表示平台生产发布；能力与模型以实际连接环境为准。原有 v0.1.1、v0.2.0-rc.1 标签保持不变。

## 可以做什么

| 创作场景 | 使用方式 |
|---|---|
| 多模型图像与视频创作 | 用自然语言描述需求，读取当前模型能力后交给拓元完成 |
| 参考图与素材编辑 | 先上传参考素材，再在同一会话中提交生成或修改要求 |
| 剧本与连续场景分镜 | 保留角色、场景、对白和时长要求，由平台规划故事板与生成流程 |
| 多素材创意提案 | 汇集参考素材与创作方向，整理提案并继续完善作品 |
| 独立项目与持续修改 | 创建新会话作为新项目，或用原会话 ID 继续修改 |
| 查询与批量交付 | 增量查看真实进度，下载完成节点，同时交付结果与画布链接 |

客户端负责上传、传递需求、查询和交付；拓元负责创作规划、调用模型与云端执行。关闭终端不会取消任务。生成范围、模型、费用和素材限制由平台当前能力与账户权限决定。

## 安装

### OpenAI / Codex Plugin

```bash
codex plugin marketplace add https://github.com/tuoyuan-ai/tuoyuanai-skill.git --ref main
codex plugin add tuoyuanai@tuoyuanai
```

安装后新建任务，并按下方说明配置 Access Key。这里的 OpenAI 入口面向 Codex 客户端，普通 ChatGPT 网页对话不能直接运行本地命令。

### Claude Code Plugin

```bash
claude plugin marketplace add tuoyuan-ai/tuoyuanai-skill
claude plugin install tuoyuanai@tuoyuanai
```

安装后新建对话，使用拓元技能。插件沿用同一份 `skills/tuoyuanai`，无需另装重复技能。

### 通用 Skill

适用于支持本地 Skill、Python 与外部网络的 Claude、OpenClaw、Hermes、CodeBuddy 及其他 Agent 环境。使用安装器时按提示选择实际客户端；若安装器未列出客户端，使用其技能导入功能或将 `skills/tuoyuanai` 文件夹放入该客户端的技能目录。

```bash
npx skills add https://github.com/tuoyuan-ai/tuoyuanai-skill --skill tuoyuanai
```

使用只提供网页聊天的客户端时，先确认其是否支持执行此类 Skill。不要把仅支持 Remote MCP 的连接器页面当成 Skill 安装入口。

### 已有预览版本

需要固定旧版行为时，原标签仍可安装：

```bash
npx skills add https://github.com/tuoyuan-ai/tuoyuanai-skill/tree/v0.2.0-rc.1 --skill tuoyuanai
```

原标签不包含本次新增的原生 Plugin 包装和创作工作流文档。当前更新从 `main` 安装。

## 连接账户

1. Python 3.10 或更新版本，无第三方 Python 依赖
2. 打开[拓元 Plugin](https://tuoyuanai.com/plugin)，登录后点击「获取 Access Key」；也可从「头像菜单 → Access Key」创建
3. 在客户端的安全环境配置中设置 `TUOYUANAI_ACCESS_KEY`，不要把密钥发到聊天或提交到仓库
4. 新建对话，先查询能力确认连接成功，再开始创作

| 环境变量 | 用途 |
|---|---|
| `TUOYUANAI_ACCESS_KEY` | 必填，独立账户密钥 |
| `TUOYUANAI_BASE_URL` | 可选，默认 `https://tuoyuanai.com`，非本机地址要求 HTTPS |

密钥默认仅允许文字与规划。图片或视频生成需要密钥启用媒体权限，且用户明确要求本次对应的生成类型。已经明确提出的生成请求无需反复确认；图片请求不包含视频授权。

本 Plugin 使用 Access Key，不包含 Remote MCP 或 OAuth 服务，不会索取账户密码或读取浏览器登录状态。详见[认证说明](skills/tuoyuanai/references/authentication.md)。

## 从需求到成果

在 `skills/tuoyuanai` 目录执行，或让已安装技能的 Agent 自动调用：

```bash
python3 scripts/tuoyuanai.py capabilities
python3 scripts/tuoyuanai.py create --message-file ./brief.txt
python3 scripts/tuoyuanai.py query SESSION_ID --wait 180
python3 scripts/tuoyuanai.py results SESSION_ID
python3 scripts/tuoyuanai.py download SESSION_ID --node-id NODE_ID --output-dir ./outputs
```

`brief.txt` 保存用户原始创作描述。需要生成媒体且已获授权时为 `create` 加上 `--allow-media`。回执包含 `sessionId`、`executionId`、`request_id` 与 `project_url`，后续使用真实 ID。

### 带参考素材创作

```bash
python3 scripts/tuoyuanai.py create
python3 scripts/tuoyuanai.py upload SESSION_ID ./reference.png
python3 scripts/tuoyuanai.py send SESSION_ID --message-file ./brief.txt --attachment-id ATTACHMENT_ID --allow-media
```

多个参考文件分别上传，重复 `--attachment-id` 传入实际附件 ID。支持格式与限额以平台为准，配套平台支持 PNG/JPG/WebP 图片 10 MiB、PDF/DOCX/TXT/MD 文档 30 MiB、MP4/MOV/WebM 视频 200 MiB、MP3/WAV/M4A/AAC/OGG/FLAC 音频 50 MiB；具体以服务器受理结果为准。

### 继续修改或新建项目

```bash
python3 scripts/tuoyuanai.py sessions
python3 scripts/tuoyuanai.py send SESSION_ID --message-file ./revision.txt
python3 scripts/tuoyuanai.py create
```

`send` 延续原项目，`create` 创建独立会话与项目。切回旧项目直接使用原会话 ID，不删除或重置已有作品。

### 查询 下载与停止

```bash
python3 scripts/tuoyuanai.py query SESSION_ID --after-seq LAST_SEQ
python3 scripts/tuoyuanai.py attachments SESSION_ID
python3 scripts/tuoyuanai.py download SESSION_ID --node-id NODE_ID --node-id ANOTHER_NODE_ID --output-dir ./outputs
python3 scripts/tuoyuanai.py stop SESSION_ID
```

完成后 Agent 自动下载本次成果并提供结果文件和项目链接。省略 `--node-id` 可以导出当前画布全部完成节点，包含可能存在的参考素材与旧版本。下载默认并发 5 个文件，最多 8 个，可用 `--workers` 调整；默认保存到 `~/Downloads/tuoyuanai_results`，可用 `--prefix` 加文件名前缀。下载不覆盖已有文件，单个失败不丢弃其他成功文件，部分成功返回 `partial` 并以退出码 2 结束。

等待超时不会取消后台任务，结果 URL 出现也不等于整个任务已完成。按服务端状态交付，未完成部分如实说明。网络中断时保留原请求 ID，不以新请求重复提交付费生成。

### 直接下载与导演提案

```bash
python3 scripts/tuoyuanai.py download --urls HTTPS_MEDIA_URL HTTPS_MEDIA_URL --prefix campaign- --workers 5
python3 scripts/tuoyuanai.py treatment SESSION_ID --outline-file ./outline.json --output-dir ./treatment
```

直接下载用户指定的素材 URL 不需要 Access Key，不发送账户凭据。导演提案从当前画布读取真实节点，按已编写的提案大纲导出 16:9 HTML、素材目录和 ZIP，支持翻页、本地音视频播放、编辑文字与保存修改。不会为了提案重新生成媒体，也不会把临时签名 URL 写入交付包。

大纲格式与完整步骤见 [导演提案](skills/tuoyuanai/references/treatment.md)。原生 Plugin 同时提供 `tuoyuanai-to-treatment` 和 `tuoyuanai-director-previs` 场景技能。

## 工作流与接口

- [创作工作流](skills/tuoyuanai/references/workflows.md)：自然语言生成、素材编辑、分镜、提案、项目切换与批量交付
- [Skill 指令](skills/tuoyuanai/SKILL.md)：Agent 调用规则与授权边界
- [API 契约](skills/tuoyuanai/references/api.md)：受理、进度、上传、下载和停止
- [当前边界](KNOWN_LIMITATIONS.md) · [安全说明](SECURITY.md)

核心 Skill 已提供自然语言会话、会话列表与切换、图片／视频／音频上传、增量查询、并发批量下载和导演提案 HTML 导出。三维预演使用拓元已有的可编辑导演流程。连接方式仍是独立 Access Key；LibTV 的 Remote MCP／OAuth、Blender 运行环境和 Zen Piano 演奏服务不由本仓库提供。

## 开源范围

MIT 许可证。保留迁移前提交历史与原始版权。本仓库仅包含客户端技能、插件声明、品牌资源与使用文档，不包含平台私有后端、渠道配置、密钥或验收账户。
