---
name: tuoyuanai
description: 使用拓元 Plugin 创作与修改图像 视频 剧本和故事板 上传参考素材 继续已有项目 查询进度并批量下载成果 适用于用户要求用拓元创作 产品广告 多场景分镜 角色或风格参考及素材提案
---

# 拓元 Plugin

使用已连接的 `tuoyuanai` Remote MCP 完成用户的创作需求 保留用户的情节 对白 参考素材与创作约束 由服务端创作 Agent 规划和编排 不把普通叙事改成程序生成的逐镜技术表

## 连接

本插件自带 `https://tuoyuanai.com/mcp` 的 HTTP MCP 连接 在客户端连接管理中完成拓元浏览器登录与授权即可 不需要用户创建 复制或发送 Access Key 不读取网页登录缓存 不要求用户提供账号密码

未连接或授权过期时引导用户完成客户端的拓元授权 连接前不要猜测项目或声称已调用平台 详细安装见 [authentication.md](references/authentication.md)

## 创作流程

1. 先调用 `tuoyuan_capabilities` 获取当前模型和能力 不固定模型或宣称尚未提供的模式
2. 新项目调用 `tuoyuan_create` 已有项目用 `tuoyuan_sessions` 按用户描述选择真实会话 不默认选择第一项
3. 每个新请求生成一个 UUID 作为 `requestId` 继续原项目时传入同一个 `sessionId` 可传原始 `message` 当前 `settings` 与 `attachmentIds`
4. 请求默认只进行文字与规划 仅在用户明确要求相应媒体创作且当前账户已授权时传 `allowMedia: true` 图片授权不扩大为视频生成
5. 保存返回的 sessionId executionId requestId 和项目链接 用 `tuoyuan_query` 查询同一执行的进度 `afterSeq` 使用该会话的上一次游标
6. `queued` `running` `waiting` 不是完成 `waiting_user` 需要用户补充信息 `blocked` 或 `canceled` 不能报告成功
7. 完成后调用 `tuoyuan_results` 读取当前画布 并按本次交付选取已完成节点 用 `tuoyuan_download_info` 获取原始文件地址 不从聊天文本猜测 URL 不把预览图当作原图
8. 最终交付实际结果文件与项目链接 可以继续使用原会话追加修改 不重建或覆盖客户项目

## 素材上传

先创建空项目 再调用 `tuoyuan_prepare_upload` 传 sessionId filename content_type size_bytes 用返回地址上传原始字节 不向对象存储发送平台凭据

大文件按返回 part_size 分块 用 `tuoyuan_upload_part` 获取每个分块地址 按原样 PUT 并记录 ETag 完成后调用 `tuoyuan_complete_upload` 小文件直接按返回 transport 上传

然后调用 `tuoyuan_register_attachment` 登记原 upload_id 和 session_id 将返回的 attachment ID 连同用户要求传给 `tuoyuan_create` 由创作 Agent 导入节点或作为参考 `tuoyuan_attachments` 可查询当前会话已有附件

图片上限 10 MiB 文档 30 MiB 视频 200 MiB 音频 50 MiB 上传本身不代表媒体生成授权 仅对同一个上传 ID 的失败分块重试 最多三次 总时限十分钟 不能重复提交付费生成

## 下载和导演提案

需要导演提案时读取 [treatment.md](references/treatment.md) 用真实项目素材组成可编辑的 16:9 HTML 素材目录和 ZIP 不把素材列表当成完整提案

本地导出工具 `scripts/export_mcp.py` 只需要 MCP 已返回的节点和下载地址 不读取授权凭据 支持并发下载 不覆盖已有文件 部分失败时保留已完成文件并说明失败项

## 中断与恢复

受理后始终查询同一执行 不盲目重交 创作回执丢失时只能使用原 UUID 和相同正文恢复 同 UUID 不同正文会被拒绝 用户要取消时调用 `tuoyuan_stop` 不删除已完成结果

授权可在个人中心的已连接助手中断开 客户端负责保存授权信息 不把令牌写进聊天 源码 提案或日志

三维预演按平台已有导演能力进行 不宣称已提供 Blender MCP 或 Zen Piano 演奏工具
