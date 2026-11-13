# Remote MCP 工具

连接地址 https://tuoyuanai.com/mcp

客户端自动读取 OAuth 元数据 用 PKCE S256 完成浏览器授权 客户端保存授权信息 不将凭据传给模型上下文

| 工具 | 用途 |
| --- | --- |
| tuoyuan_capabilities | 当前模型与能力 |
| tuoyuan_sessions | 当前用户项目列表与分页 |
| tuoyuan_create | 新建或继续项目 保留请求 UUID |
| tuoyuan_query | 执行状态与增量事件 |
| tuoyuan_results | 当前画布节点与执行记录 |
| tuoyuan_download_info | 指定当前节点的原始文件下载地址 |
| tuoyuan_stop | 取消当前会话执行 |
| tuoyuan_prepare_upload | 为当前会话申请上传 |
| tuoyuan_upload_part | 获取分块上传地址 |
| tuoyuan_complete_upload | 完成分块上传 |
| tuoyuan_register_attachment | 将已上传文件登记到会话 |
| tuoyuan_attachments | 当前会话附件 |
| tuoyuan_cancel_upload | 取消未完成的上传 |

参数与边界以 MCP tools/list 为准 回执保留原服务端 ID 原错误与项目链接 工具返回 isError 时不能报告成功 仅成功受理的 requestId 可用于恢复 同 UUID 不同正文会被拒绝

授权默认允许文字与规划 用户在授权页勾选媒体权限且具体请求 allowMedia 为真时才允许生成媒体 断开连接和账户停用后不能继续调用 已完成项目不删除
