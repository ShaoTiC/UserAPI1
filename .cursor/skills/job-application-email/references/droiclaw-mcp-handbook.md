# DroiClaw 可调用的手机端 MCP 能力手册（Skill 设计参考 · 合并版）

> 一句话理解：**Skill** 负责理解用户需求、安排步骤；**MCP Tool** 负责真正调用手机能力执行操作。
> 本手册只收录当前资料中明确展示的 Tool 名，不凭空补充未提供的英文名称。
> 学生构思 skill 前先对照本手册划边界：找不到对应能力的，就是当前手机不支持，别硬做。

---

## 一、先记住这几条规则

1. **工具命名格式**：`{provider}_{tool_name}`，如 `dialer_place_call`、`notes_create_note`。
   设计 skill 时按这个格式引用工具。
2. **删除类能力普遍未开放**：删闹钟、删通话记录、删文件、删短信/会话、删笔记/待办等
   （下文加 ~~删除线~~ 的）目前**不能调用**，别设计依赖"删除"的流程。
3. **权限弹窗**：涉及通讯录、短信、通话、录音、存储的操作，执行前会弹权限确认，用户点同意才执行。
   skill 流程要预留"用户确认"这一步，不能假设静默执行。
4. **只做端上已有 App 能做的事**：所有能力都是系统自带 App（电话/短信/时钟/文件/便签/相册/录音机/设置）
   的封装。App 里没有的功能，MCP 也没有。
5. **不要自己造英文名**：只用平台真实提供的 Tool 名，不要按中文功能自行翻译创造英文名。

---

## 二、看懂英文 Tool 名（命名规则）

MCP Tool 采用 snake_case（小写单词 + 下划线）。记住关键词，第一次见到工具名也能猜出用途。

| 英文关键词 | 中文含义 | 例子 |
|-----------|---------|------|
| `search` | 搜索、查询 | `search_messages`：查询短信 |
| `read` / `get` | 读取、获取 | `read_latest_message`：读最新短信 |
| `list` | 列出列表 | `list_world_clocks`：世界时钟列表 |
| `create` / `add` | 创建、添加 | `create_recording_group`：新建录音分组 |
| `edit` / `rename` | 修改、重命名 | `edit_contact_name`、`rename_recording` |
| `start`/`pause`/`resume`/`stop` | 开始/暂停/继续/停止 | `start_recording`、`resume_timer` |
| `reset` / `lap` | 归零 / 计次 | `reset_stopwatch`、`lap_stopwatch` |
| `send` / `bulk` | 发送 / 批量 | `send_bulk_message_by_number` |
| `block` / `unblock` | 加黑名单 / 移出黑名单 | `block_number`、`unblock_contact` |
| `contact` / `number` | 按联系人 / 按号码 | `block_contact` vs `block_number` |

> **不要混淆**：`contact` = 按联系人姓名操作；`number` = 直接按电话号码操作。

---

## 三、各模块能力清单

### 1. 系统开关 / 设置（provider: `sysui`，27 个）

手机常见快捷开关和设置调节，**基本都能控制**。

- **开关类（17）**：自动旋转 `fast_auto_rotate`、深色主题 `fast_dark_theme`、Wi-Fi `fast_wifi`、蓝牙 `fast_bluetooth`、手电筒 `fast_flashlight`、省电模式 `fast_battery_saver`、飞行模式 `fast_airplane_mode`、护眼模式 `fast_eye_protection`、自动亮度 `fast_auto_brightness`、定位 `fast_location`、麦克风权限 `fast_mic_access`、相机权限 `fast_camera_access`、移动数据 `fast_mobile_data`、悬浮导航 `fast_assistive_touch`、屏保 `fast_screensaver`、流量节省 `fast_data_saver`、热点 `fast_hotspot`。
- **动作类（4）**：勿扰 `fast_dnd`、立即锁屏 `fast_lock_screen`、投屏 `fast_cast`、屏幕录制 `fast_screen_record`。
- **设置调节（4）**：
  - `set_ringer_mode` 铃声模式 —— 参数 `mode`: ring/vibrate/silent
  - `set_brightness` 屏幕亮度 —— 参数 `action` + `level`(0-100)
  - `set_screen_timeout` 息屏时间 —— 参数 `action` + `seconds`
  - `set_volume` 音量 —— 参数 `action` + `level` + `stream`
- **查询（2）**：网络状态 `fast_query_network`、电量百分比显示 `set_battery_percent`。

> 开关类/动作类（21 个）为纯切换或触发动作，通常无参数或仅一个开关值，故不逐一列参数。

> Skill 可玩性：一句话进入"睡眠场景"（关 Wi-Fi + 开勿扰 + 调低亮度 + 锁屏）这类组合完全可行。

---

### 2. 短信 / 彩信（provider: `messaging`）

用于查询、读取和发送短信，**不能删**。

- 发送短信/彩信 `send_message` —— 参数 `recipient`(单发) / `recipients`(群发) + `text` + 可选 `subject` + `sub_id`
- 跨会话搜索 `search_messages` —— 参数 `query` + `limit`
- 读取最新短信 `read_latest_message`（只读列表里最新一条；参数以平台为准）
- 获取会话详情 `get_conversation` —— 参数 `conversation_id` / `query` + `message_limit`
- 标记会话已读 `mark_conversation_read` —— 参数 `conversation_id` / `query`
- 获取未读数 `get_unread_count`（无参数）
- 按联系人群发 `send_bulk_message_from_contacts`（先匹配多个联系人再群发，**一次最多 50 位**；参数以平台为准）
- 按号码群发 `send_bulk_message_by_number`（不查联系人，直接对多个号码发；需有效号码 + 可用 SIM；参数以平台为准）
- ~~列出会话消息 list_messages~~、~~删除单条 delete_message~~、~~删除会话 delete_conversation~~（均不支持）

> 权限：读短信需短信读取权限；发短信/群发需短信发送权限，群发还需通讯录读取权限。只读取完成任务所需的短信。

---

### 3. 电话 / 联系人（provider: `dialer`）

- 拨打电话 `place_call` —— 参数 `number` / `query`(按姓名) + 可选 `phone_type` + `number_index`
- 接听来电 `answer_call`（无参数；仅确实有来电铃声时有效）
- 搜索联系人 `search_contacts` —— 参数 `query` + `limit`
- 获取联系人详情 `get_contact` —— 参数 `contact_id` / `query`（姓名重复时可能需二次确认）
- 新建联系人 `create_contact` —— 参数 `name` + `number` + 可选 `email` + `phone_type`
- 查询通话记录 `search_call_logs` —— 参数 `query` + `type` + `after` + `before` + `limit`（时间用时间戳）
- 修改联系人姓名 `edit_contact_name`（只改姓名；重名需用户选择；参数以平台为准）
- 修改联系人号码 `edit_contact_number`（只改号码；新号码格式需有效；参数以平台为准）
- ~~删除通话记录 delete_call_log~~（原资料划线，不列为推荐能力）

> 权限：拨号需电话权限；查通讯录/通话记录需读取权限；建/改联系人需通讯录写入编辑权限。

---

### 4. 黑名单（provider: `dialer`）

- 查看黑名单 `list_blocked_numbers`（返回已拦截号码及对应联系人）
- 按联系人加入 `block_contact` / 按号码加入 `block_number`
- 按联系人移出 `unblock_contact` / 按号码移出 `unblock_number`

> 注意：号码已在/不在黑名单时，要如实返回状态，不能假装成功。区分 `contact`（按联系人）与 `number`（按号码）。

---

### 5. 录音机（provider: `recording`）

控制录音状态，以及查询、播放、分组、移动、重命名录音。

- 启动录制 `start_recording`（需麦克风权限；已在录音不重复启动）
- 暂停录制 `pause_recording`（只有正在录音时可暂停）
- 恢复录制 `resume_recording`（只有暂停状态可恢复）
- 查询录音 `search_recording`（找不到时让用户确认名称）
- 播放录音/通话录音 `play_recording`（可能需存储/媒体读取权限）
- 新建录音分组 `create_recording_group`
- 移动录音到分组 `move_recording_to_group`（需确认录音名 + 目标分组）
- 录音重命名 `rename_recording` / 分组重命名 `rename_recording_group`
- ⚠️ "停止并保存录音"能力存在，但截图未展示确切英文 Tool 名，**别自行写成 stop_recording**，以平台工具列表为准。

---

### 6. 时钟 / 闹钟 / 计时器 / 秒表 / 世界时钟（provider: `deskclock`）

**闹钟**
- 创建闹钟 `create_alarm` —— 参数 `hour` + `minute` + `label` + `repeat` + `days_of_week` + `vibrate` + `enabled`
- 修改闹钟 `update_alarm` —— 参数 `id` / `query` + 待修改字段
- 查询闹钟 `list_alarms` —— 参数 `query` + `enabled` + `limit`
- ~~删除闹钟 delete_alarm~~（不支持）

**计时器（倒计时）**
- 创建倒计时 `create_timer` —— 参数 `duration_seconds` + `label`
- 停止倒计时 `stop_timer`（停止当前所有计时器）、继续倒计时 `resume_timer`（从暂停恢复）
- 说明：当前只明确展示 `create_timer` / `resume_timer` / `stop_timer`；"暂停倒计时"等未展示的名字不要猜。

**秒表**
- 开始秒表 `start_stopwatch`、停止秒表 `stop_stopwatch`
- 重置秒表 `reset_stopwatch`（清空计时和圈次）、计次 `lap_stopwatch`（运行中记一圈）

**世界时钟 / 时间查询（此类全部无需额外权限）**
- 添加城市时钟 `add_world_clock`（会加入列表，如"添加纽约时间"；参数以平台为准）
- 查看已添加世界时钟 `list_world_clocks`（无参数）
- 查询某地当前时间 `query_time`（只查一次、不加入列表，如"洛杉矶现在几点"；参数以平台为准）
- 查指定城市时间 `get_city_time` —— 参数 `query` / 查国家时间 `get_world_time` —— 参数 `query`

> 容易混淆：`add_world_clock` 会把城市加入列表；`query_time` 只查这一次，不添加。

---

### 7. 文件管理（provider: `filemanager`）

- 递归搜索文件/文件夹 `search_files` —— 参数 `query` + `path` + `include_hidden` + `max_depth` + `limit`
- 查看文件信息 `get_file_info` —— 参数 `path`
- 创建文件夹 `create_folder` —— 参数 `path` 或 `parent_path` + `name`
- 创建/覆盖文本文件 `create_text_file` —— 参数 `path` 或 `parent_path` + `name` + `content` + `overwrite`
- 重命名 `rename_file` —— 参数 `path` + `new_name`
- 复制 `copy_file` —— 参数 `source_path` + `destination_path` 或 `target_dir` + `overwrite`
- 移动 `move_file` —— 参数 `source_path` + `destination_path` 或 `target_dir` + `overwrite`
- ~~删除文件/文件夹 delete_file~~（不支持）

> 能建、能搜、能移、能复制、能重命名，唯独**不能删**。

---

### 8. 便签 / 待办（provider: `notes`）

**便签**
- 创建笔记 `create_note` —— 参数 `title` + `content` + `folder_id`
- 获取详情 `get_note` —— 参数 `id` / `query`
- 更新笔记 `update_note` —— 参数 `id` / `query` + `title` + `content` + `folder_id` + `private` + `top` + `reminder_time`
- ~~删除笔记 delete_note~~（不支持）

**待办**
- 创建待办 `create_todo` —— 参数 `content` + `reminder_time` + `important` + `complete` + `folder_id` + `repeat`
- 获取详情 `get_todo` —— 参数 `id` / `query`
- 更新待办 `update_todo` —— 参数 `id` / `query` + `content` + `reminder_time` + `important` + `complete` + `delay` + `folder_id` + `repeat`
- ~~列出待办 list_todos~~、~~删除待办 delete_todo~~（不支持）

---

### 9. 相册 / 图集（provider: `gallery`）

- 新建图集 `create_album` —— 参数 `name` + `media_type`
- 收藏媒体 `collect_media` —— 参数 `album` + `media_type` + `index`
- 取消收藏 `uncollect_media` —— 参数 `album` + `media_type` + `index`

> 能力较薄：只能建相册、收藏/取消收藏，**不能读取/搬移/删除照片本身**。

---

### 10. 系统模式（provider: `settings`）

- 超级省电模式 `handle_super_battery_mode` —— 参数 `enabled`: true(进入) / false(退出)
- ~~简易模式 handle_simple_mode~~（不支持）

---

### 11. 技能库查询（Skill 库）

- 获取/查询 Skill `list_skills`（按技能名称查询，返回名称和说明，判断是否可用；无需额外权限）
- 学生理解：名字里虽有 `list`，实际更接近"按 Skill 名精准查一个技能"。返回行为以运行环境为准。

---

### 12. 相机/相册中已支持、但暂无展示 Tool 名的能力

以下能力**目前已支持**，但截图未给出独立英文 Tool 名，**学生不要自行编造**：

- 精准录像（打开相机录制指定时长视频）
- 精准拍照（打开相机拍指定数量照片）
- 切换相机模式（如切到专业模式）

---

## 四、如何选对 Tool（快速对照）

| 用户表达 | 应选 Tool | 判断依据 |
|---------|----------|---------|
| "查短信" | `search_messages` | 查询匹配的短信 |
| "最新短信" | `read_latest_message` | 只读最新一条 |
| 给联系人姓名发短信 | `send_bulk_message_from_contacts` | 需先查联系人 |
| 直接给号码发短信 | `send_bulk_message_by_number` | 不依赖通讯录 |
| "把张三拉黑" | `block_contact` | 按联系人 |
| "把 138… 拉黑" | `block_number` | 按号码 |
| "改联系人名字" | `edit_contact_name` | 只改姓名 |
| "改手机号" | `edit_contact_number` | 只改号码 |
| "找录音" | `search_recording` | 只查询 |
| "播放录音" | `play_recording` | 查询后播放 |
| "添加纽约时钟" | `add_world_clock` | 加入世界时钟列表 |
| "纽约几点" | `query_time` | 只查询、不添加 |

---

## 五、一次完整的 Skill 调用流程

1. **理解需求**：识别联系人、号码、时间、录音名称等关键信息。
2. **选择 Tool**：按动作 + 对象选对应工具，不能只靠关键词生硬匹配。
3. **补齐信息**：缺联系人/号码/城市/录音名时先问用户，不要猜。
4. **请求权限/确认**：涉及短信、电话、联系人、录音、黑名单等敏感操作，按系统要求确认。
5. **执行调用**：传必要参数，等真实执行结果。
6. **按结果回复**：成功说明做了什么；失败说明原因和下一步，**不能假装成功**。

> 示例："把张三加入黑名单" → 先确认张三对应哪个联系人 → 选 `block_contact` → 请求权限和确认 → 调用 → 按返回结果告诉用户是否成功。

---

## 六、Skill 设计红线（速查）

| 想做的事 | 能不能做 |
|----------|----------|
| 开关 Wi-Fi/蓝牙/手电筒/勿扰、调亮度音量、锁屏、组合场景 | ✅ 能，最灵活 |
| 定闹钟、倒计时、秒表、查世界各地时间 | ✅ 能（删闹钟 ❌） |
| 打电话、查通讯录/通话记录、建/改联系人、拉黑 | ✅ 能（删通话记录 ❌） |
| 查短信、读最新短信、发短信/群发、标已读 | ✅ 能（删短信/会话 ❌） |
| 录音、暂停/恢复、查/播/分组/改名录音 | ✅ 能（停止保存的 Tool 名待确认） |
| 建文件夹、写文本、搜/移/复制/改名文件 | ✅ 能（删文件 ❌） |
| 记便签、建/改待办 | ✅ 能（删便签/待办、列待办 ❌） |
| 建相册、收藏照片 | ⚠️ 只能这些，读/搬/删照片 ❌ |
| 查 Skill 技能库 | ✅ `list_skills` |
| 精准拍照/录像/切模式 | ⚠️ 已支持但 Tool 名未展示，别编造 |
| **任何"删除"操作** | ❌ 基本没开放，别设计依赖删除的流程 |
| 装第三方 App、控制微信/抖音等非系统 App | ❌ 只封装系统自带 App |

**总结**：能"开关、创建、查询、修改、发送"，普遍**不能删除**；范围限系统自带 App。
构思 skill 时先在上表找对应能力，找不到就是当前手机不支持，别硬做。

---

## 七、学生使用必须遵守的原则

- 只用平台真实提供的 Tool 名，不要按中文功能自行翻译造英文名。
- 缺参数时先追问，不要猜联系人、号码、城市或文件名。
- 涉及发短信、拨号、改联系人、黑名单、录音等操作，要尊重权限确认。
- 工具返回失败、对象不存在或状态不允许时，如实说明，不能回"已经完成"。
- 区分查询与执行：`search`/`list`/`get` 通常是读取；`send`/`edit`/`block`/`rename` 会真实修改系统状态。
- 实际参数格式以 DroiClaw 当前环境的 Tool 描述为准，本手册"示例说法"只帮理解。

---

## 附录：Tool 名快速索引

| 模块 | Tool 名 |
|------|---------|
| 系统开关 sysui | `fast_*`（17 开关）、`fast_dnd`/`fast_lock_screen`/`fast_cast`/`fast_screen_record`、`set_ringer_mode`/`set_brightness`/`set_screen_timeout`/`set_volume`、`fast_query_network`/`set_battery_percent` |
| 短信 messaging | `search_messages`、`read_latest_message`、`send_message`、`send_bulk_message_from_contacts`、`send_bulk_message_by_number`、`get_conversation`、`mark_conversation_read`、`get_unread_count` |
| 电话/联系人 dialer | `place_call`、`answer_call`、`search_contacts`、`get_contact`、`create_contact`、`search_call_logs`、`edit_contact_name`、`edit_contact_number` |
| 黑名单 | `list_blocked_numbers`、`block_contact`、`block_number`、`unblock_contact`、`unblock_number` |
| 录音 recording | `start_recording`、`pause_recording`、`resume_recording`、`search_recording`、`play_recording`、`create_recording_group`、`move_recording_to_group`、`rename_recording`、`rename_recording_group` |
| 时钟 deskclock | `create_alarm`、`update_alarm`、`list_alarms`、`create_timer`、`resume_timer`、`stop_timer`、`start_stopwatch`、`stop_stopwatch`、`reset_stopwatch`、`lap_stopwatch`、`add_world_clock`、`list_world_clocks`、`query_time`、`get_city_time`、`get_world_time` |
| 文件 filemanager | `search_files`、`get_file_info`、`create_folder`、`create_text_file`、`rename_file`、`copy_file`、`move_file` |
| 便签待办 notes | `create_note`、`get_note`、`update_note`、`create_todo`、`get_todo`、`update_todo` |
| 相册 gallery | `create_album`、`collect_media`、`uncollect_media` |
| 系统模式 settings | `handle_super_battery_mode` |
| 技能库 | `list_skills` |
| 已支持但 Tool 名未展示 | 精准录像、精准拍照、切换模式、停止并保存录音 |

—— 供 DroiClaw / OPC 训练营学生学习使用 ——
