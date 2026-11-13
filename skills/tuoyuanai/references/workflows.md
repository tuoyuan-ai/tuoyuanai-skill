# 创作工作流

先阅读主 SKILL.md 的 MCP 连接与授权规则

## 图片或连续镜头

读取当前 capabilities 选择已有项目或创建新项目 将用户完整创作要求交给 tuoyuan_create 服务端完成创意规划 保留用户指定的风格 比例 时长 台词与故事边界 生成时显式传 allowMedia 只生成用户要求的媒体类型

## 参考素材

创建空项目 准备上传 上传原始字节 登记附件 再将附件 ID 与用户要求提交给同一会话 可用 tuoyuan_attachments 查看现有附件 不假设本地路径已经上传

## 切换和继续

tuoyuan_sessions 分页列出当前用户的 Plugin 项目 根据用户描述选择真实 sessionId 不默认使用第一项 继续修改使用原 sessionId 和新 requestId 恢复原请求使用原 requestId

## 原始素材下载

tuoyuan_results 只选当前画布上存在且已完成的交付节点 对每个节点使用 tuoyuan_download_info 获取原始地址 由 export_mcp.py 并发下载 部分失败保留成功文件 重复目标文件会被拒绝覆盖

## 导演提案

按 treatment.md 收集素材 编写逐页导演阐述 导出可编辑 HTML 和原片 ZIP 在可见浏览器检查排版 翻页和播放

## 空间预演和音乐

只能使用 capabilities 中当前支持的导演和音频能力 用户已有音乐可以上传作为参考 不声称已经操作 Blender 或演奏 Zen Piano 不为展示而擅自提交新视频生成
