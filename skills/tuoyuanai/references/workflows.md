# 创作工作流

所有命令从本 Skill 目录执行。使用 Python 3.10+。将占位 ID 替换为平台回执；用 `--message-file` 传递长文本，避免 shell 改变引号或换行。

## 自然语言创作与模型选择

保留用户的原始描述、限制、对白、比例、时长与指定模型。由拓元服务端 Agent 决定创意规划、分镜和调用顺序，不要自行拆成逐镜头请求或扩写未要求的情节。

1. 首次连接或用户指定模型时，执行 `python3 scripts/tuoyuanai.py capabilities`
2. 根据返回的实时能力判断请求是否可用；不要写死模型名单或承诺任意模型都可调用
3. 文字或规划直接 `create --message-file ./brief.txt`
4. 用户要求生成媒体且密钥允许时，在同一命令加 `--allow-media`
5. 查询真实状态，读取当前画布结果，下载本次完成的输出

`--allow-media` 只表示执行用户已要求的媒体类型。图片请求不能扩大成视频或音频。用户要求生成属于授权，无需反复要求确认同一事项。

## 参考素材与编辑

用户提供本地文件时先创建空会话，再上传并绑定附件。多个参考文件逐一上传，在提交中重复 `--attachment-id`。保留每份素材的用途，如角色、产品、环境或风格，不从文件名猜测含义。

```bash
python3 scripts/tuoyuanai.py create
python3 scripts/tuoyuanai.py upload SESSION_ID ./reference.png
python3 scripts/tuoyuanai.py attachments SESSION_ID
python3 scripts/tuoyuanai.py send SESSION_ID --message-file ./brief.txt --attachment-id ATTACHMENT_ID --allow-media
```

不要上传不相关的本地文件。上传限额与格式以平台返回为准，客户端单文件上限为 100 MiB。平台附件 ID 仅能用于所属会话，不要照搬其他平台的 OSS 地址或上传接口。

## 连续场景与分镜

剧本、角色设定、场景参考、画幅与时长要求一起交给服务端。需要故事板时可用 `--creation-type storyboard`，不要把故事板的格数等同于镜头数或视频时长，也不要为填格擅自新增情节。

在同一会话追加修改，附上用户明确指定的节点或作品描述。不要把一次修改拆成多个并行生成请求；服务端会维持项目上下文与素材关系。

## 多素材提案

将客户选定的素材上传到同一会话，发送提案目标、受众、交付形式和用户给出的参考方向。仅要求创意提案时不加 `--allow-media`；明确要求出图或视频时才开启对应生成。

交付可包含创意方向、角色与场景设定、分镜规划及已完成作品。若用户另需 HTML、PDF 或演示文档，使用当前助手已有的文档能力整理实际结果；不得把平台未返回的素材或功能描述成已经完成。

## 继续或切换项目

- 继续修改：`send SESSION_ID --message-file ./revision.txt`
- 独立任务或用户要求新项目：`create` 返回新的 `sessionId` 与项目地址
- 切换回旧项目：使用先前记录的 `sessionId` 查询或继续，不会删除任何项目
- 同一会话有任务执行时先查询，不重复提交

拓元通过显式会话 ID 选择项目，不修改 Access Key 的全局项目绑定。保留每个项目的会话 ID、执行 ID、请求 ID 和地址即可，不保存密钥或浏览器会话。

## 查询与批量交付

```bash
python3 scripts/tuoyuanai.py query SESSION_ID --wait 180
python3 scripts/tuoyuanai.py query SESSION_ID --after-seq NEXT_SEQ
python3 scripts/tuoyuanai.py results SESSION_ID
python3 scripts/tuoyuanai.py download SESSION_ID --node-id NODE_ID --output-dir ./outputs
```

- `nextSeq` 用于下一次查询，`hasMore` 为真时继续分页
- `queued`、`running`、`waiting` 仍在执行；`waiting_user` 需要用户输入；`blocked`、`canceled` 不能当作成功
- 默认每次等待最长 180 秒，可显式增加至 1800 秒；等待超时不会取消服务器任务
- 完成后自动下载本次目标的完成节点，可重复 `--node-id` 批量选择
- 不传 `--node-id` 会下载当前画布全部完成节点，可能包含参考素材和旧版本；仅当客户要整板导出时这样使用
- 根据任务命名输出目录；下载不会覆盖已有文件
- 使用返回的真实结果链接、本地文件和 `project_url` 交付，并说明仍在执行或未完成的部分
- 不通过聊天文本里的 URL 推断成功，不自行拼接项目地址或过期的媒体链接

## 中断与失败

查询遇到临时网络故障可在当前等待期限内再次读取。写请求的回执不确定时先查已知会话；只能用同一请求 ID 和同一正文恢复原请求，不生成新 ID 重复提交付费任务。

缺少密钥、权限不足、余额不足、上传失败或模型不可用时，说明具体阻塞与已保留的会话。用户明确停止才执行 `stop SESSION_ID`；关闭客户端不代表停止创作。
