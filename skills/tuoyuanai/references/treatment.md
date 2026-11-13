# 从真实画布制作导演提案

先通过 tuoyuan_sessions 确定用户项目 用 tuoyuan_query 取得该会话信息 再用 tuoyuan_results 读取当前画布 不通过聊天截图猜测素材

查看用户选定的已完成图片 视频 音频和剧本文字 编排 1 到 30 页中文 16:9 创作提案 每页不超过六个素材 说明应围绕作品的创意 人物 空间 镜头与声音 不能把内部任务字段当成提案文案

对每个选定媒体节点调用 tuoyuan_download_info 得到原始下载 URL 将会话结果 当前 nodes 和对应下载回执保存到本地 JSON

```json
{
  "session": {"sessionId": 123, "project": {"ref_type": "content_task", "ref_id": 456}, "projectUrl": "/assistant?session=123"},
  "nodes": [],
  "downloads": {"789": {"url": "https://your-storage.example/original-media"}}
}
```

示例编号与 URL 仅说明格式 必须使用当前 MCP 的真实回执 下载地址可能短期有效 不将这个文件提交到 Git

提纲文件格式

```json
{"title":"作品提案","sections":[{"title":"创意方向","body":"按作品内容撰写的导演阐述","node_ids":[789]}]}
```

```bash
python scripts/export_mcp.py treatment --receipt-file ./receipt.json --outline-file ./outline.json --output-dir ./treatment
python scripts/export_mcp.py download --receipt-file ./receipt.json --node-id 789 --output-dir ./outputs
```

无需配置平台令牌 Python 3.10+ 即可运行 结果是可翻页并编辑保存的 index.html 原始 assets manifest.json 和 treatment.zip 浏览器验收第一页 末页 文字编辑保存和真实媒体播放 失败下载要单独说明 已下载文件不能删除或覆盖
