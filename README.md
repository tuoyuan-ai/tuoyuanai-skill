# 拓元 Plugin

在 AI 助手中连接拓元创作平台 完成图像 视频 剧本 故事板 素材管理与导演提案

通过 HTTP Remote MCP 和浏览器授权连接 无需手动配置 Access Key

> 当前为 1.0.0-rc.1 需要平台同步部署 Remote MCP 与浏览器授权接口 仓库更新不代表生产平台已上线

## 安装

Codex

```bash
codex plugin marketplace add https://github.com/tuoyuan-ai/tuoyuanai-skill.git --ref main
codex plugin add tuoyuanai@tuoyuanai
```

Claude Code

```bash
claude plugin marketplace add tuoyuan-ai/tuoyuanai-skill
claude plugin install tuoyuanai@tuoyuanai
```

安装后重新加载插件或新建任务 在客户端 MCP 连接管理中对 tuoyuanai 完成拓元浏览器登录与授权

其他支持 HTTP MCP 的客户端可添加 `https://tuoyuanai.com/mcp` 再安装所需工作流

```bash
npx skills add https://github.com/tuoyuan-ai/tuoyuanai-skill --skill tuoyuanai
```

## 工作流

| Skill | 用途 |
| --- | --- |
| tuoyuanai | 自然语言创作 素材上传 继续项目 查询进度与下载 |
| tuoyuanai-to-treatment | 将真实画布素材整理成可编辑导演提案 HTML 与 ZIP |
| tuoyuanai-director-previs | 使用拓元已有导演能力组织空间参考与连续镜头 |

先读取当前平台模型与能力 用户明确要求媒体生成且账户授权允许时才提交相应生成 请求 UUID 与项目执行 ID 用于恢复并防止重复提交 已完成素材与客户编辑会保留

本地提案导出支持真实图片 视频 音频与文字 保留原始媒体字节 并发下载 不覆盖文件 部分失败时保留已完成结果

本插件尚不提供 Blender 联动或 Zen Piano 演奏 不将这些描述成已实现功能

## 账户与授权

每位用户使用自己的拓元账户授权 客户端管理授权信息 个人中心的已连接助手可断开连接 项目与素材不会因此删除

原 Skill 的历史标签和已有项目保留 旧教程中的 Access Key 入口现在展示 Plugin 升级说明 新安装请使用上面的浏览器授权流程

## 许可

MIT
