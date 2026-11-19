# 设计原型 vs 真实前端差异对照：对话 / 设置 / 全局壳体

> 原型为纯 HTML mock（无后端、无鉴权、写死数据），真实前端有 SSE 安全首帧、会话 CRUD、错误/断流处理。以下只对照呈现与交互形态，不把 mock 行为当需求，也不建议回退真实功能。

**对照文件（行号均指以下文件）**

- 原型根：`E:\zxdevelop\opendesign\8d699fa3-6b49-4dbf-b40b-29c55c1d6429`（`index.html`、`styles.css`、`app.js`）
- 前端根：`E:\zxdevelop\project1\frontend\src`
  - `views\ChatView.vue`、`views\AISettings.vue`
  - `components\AppSidebar.vue`、`components\AppTopbar.vue`、`components\MobileTabs.vue`
  - `layouts\AppShell.vue`、`components\mental\PersonaCard.vue`
  - `styles\v21.css`、`styles\layout.css`

## 一、对话

| 差异项 | 原型（行号） | 当前前端（行号） | 类型 | 优先级 | 工作量 |
| --- | --- | --- | --- | --- | --- |
| 主体信息架构 | `index.html:534-545`；`styles.css:1127-1136`：280px「对话设置」栏 + 主区 | `ChatView.vue:17-64`；`v21.css:1343-1358`：280px「会话列表」栏 + 主区 | 结构 | P1 | M |
| 模式切换形态 | `index.html:538-541`；`styles.css:1138-1153`：栏内竖排卡片、带副文案、选中反黑 | `ChatView.vue:95-108`；`styles.css` scoped `700-734`：主区顶部横排胶囊、带图标 | 视觉 | P1 | S |
| 快捷问题 | `index.html:543`；`app.js:66,71`：左栏常驻，每模式 4 条 | `ChatView.vue:181-195,310-320`：仅空态居中 chips，文案已重写 | 交互/文案 | P1 | S |
| 模式语义 | `app.js:56-59,577-591`：body/mental 各自独立消息史 | `ChatView.vue:376-382,397-399`：同一会话不切历史，仅影响新会话 context | 交互 | P1 | M |
| 会话头部 | `index.html:548`；`app.js:586,624,647`：头像 + AI 校医/树洞搭子 + 实时状态 + 示例 badge | `ChatView.vue:68-93`：圆点 + 模式名 + 安全 pill + 「需要帮助？」 | 视觉/文案 | P1 | S |
| 医疗免责 | `index.html:555`：AI 回复不替代医生诊断 | `ChatView.vue:1-233` 无对应 fineprint | 文案 | P1 | S |
| 气泡视觉 | `styles.css:1178-1183`：78% 宽、12.5px、助手浅底/用户墨底、时间 meta | `ChatView.vue:834-860,196-201`：82% 宽、14px、角色 chip、用户 accent-soft | 视觉 | P2 | S |
| 输入交互 | `index.html:550-554`；`styles.css:1190-1192`；`app.js:1061-1066`：textarea 自增高，Enter 发送 / Shift+Enter 换行 | `ChatView.vue:204-229`：单行 input、maxlength 2000、流式时显示「停止」 | 交互 | P2 | M |
| 平板断点 | `styles.css:1436-1439`：1024 起单列，aside 转顶部横条，消息区 380 | `v21.css:1343-1346`；`ChatView.vue:950-951`：769–1024 仍 280+1fr，768 才单列 | 视觉 | P1 | S |
| 页头 | `index.html:523-531`：folio 07 / CHAT / COMPANION / AI 对话 / 在线 | `ChatView.vue:3-14`：folio 09 / DIALOGUE / CARE / 对话 / 可对话或关怀模式优先 | 文案 | P2 | S |

## 二、设置

| 差异项 | 原型（行号） | 当前前端（行号） | 类型 | 优先级 | 工作量 |
| --- | --- | --- | --- | --- | --- |
| 页头 | `index.html:560-569`：folio 08、SETTINGS/PERSONA、标题「设置」、主按钮「保存设置」 | `AISettings.vue:3-15`：folio 10、SYSTEM/MODELS、标题「AI 设置」、状态 chip | 文案/结构 | P2 | S |
| 信息架构 | `index.html:571-607`；`styles.css:1196`：两列 1.1fr/0.9fr、四面板 | `AISettings.vue:17-54`；`v21.css:1447-1452`：单列三面板、max 760 | 结构/视觉 | P2 | M |
| 人设 | `index.html:575-579`；`styles.css:1202-1222`：「幽默宿舍搭子风 / 严谨校医风」+ 示例引语 + 墨色 PREVIEW | `PersonaCard.vue:83-94,17-53,297-304`：「玩梗搭子 / 理性陪伴」+ 头像 + 当前标签，无引语预览 | 文案/视觉 | P1 | M |
| 保存交互 | `index.html:568`；`app.js:1076-1086`：手动保存 + toast + localStorage | `AISettings.vue:158-203`；`PersonaCard.vue:112-148`：各表单自动保存；校验/重置用原生 alert/confirm | 交互 | P2 | S |
| 提醒 / 目标 / 隐私 | `index.html:582-606`：4 个开关（含锁定的高危关怀）、3 项目标、隐私面板 | `AISettings.vue:1-55` 无；注意目标后端已由 DB-2b 移除，勿恢复 | 结构 | P2 | M |

## 三、全局壳体与响应式

| 差异项 | 原型（行号） | 当前前端（行号） | 类型 | 优先级 | 工作量 |
| --- | --- | --- | --- | --- | --- |
| 导航 IA / 编号 | `index.html:42-54`：8 项，对话 07、设置 08 | `AppSidebar.vue:125-141`：10 项，新增健康分析 06、预警 08，对话 09、设置 10 | 结构/文案 | P2 | S |
| 侧栏底部 | `index.html:56-60`：林知夏 / 大二·新闻系 / 在线点 | `AppSidebar.vue:72-98`：动态用户名 / 在校大学生 + 音效、退出按钮 | 文案/结构 | P2 | S |
| 顶栏内容 | `index.html:64-74`：日期 + 「示例数据·本地原型」+ 铃铛 | `AppTopbar.vue:3-31,63-67`：日期 + 路由标题 + 预警链接/未读点 + 用户 | 文案/交互 | P2 | S |
| 侧栏宽度节奏 | `styles.css:1400-1420`：1200→216px；1024→72px 图标栏 | `v21.css:29,3084-3137`：基线 240px；1024→72px，无 1200 档 | 视觉 | P2 | S |
| 768 侧栏 | `styles.css:1443-1447`：display:none，仅底部 Tab | `v21.css:3168-3235`；`AppShell.vue:78-129`：固定抽屉 + 背板 + 焦点陷阱 + body 锁 | 交互 | P1 | M |
| 「更多」 | `index.html:621-629`；`styles.css:1270-1286,1506,1571`：dialog 四卡片，92/94vw | `MobileTabs.vue:13-22`；`AppShell.vue:26,78-80`：打开整栏抽屉，无卡片网格 | 结构/交互 | P1 | M |
| 560 页头 | `styles.css:1513-1514`：38px + 1fr，folio 32px | `v21.css:3365-3371`：单列，folio 隐藏 | 视觉 | P2 | S |

## 原型有、前端缺

- 左栏常驻模式说明 + 快捷问题（`index.html:536-543`）。
- 助手身份头与实时状态（`index.html:548`；`app.js:624,647`）。
- 聊天医疗免责声明（`index.html:555`）。
- 按模式独立的消息历史（`app.js:56-59,577-591`）。
- 手动「保存设置」+ toast（`index.html:568`；`app.js:1076-1086`）。
- 提醒开关，含锁定不可关的「高危关怀」（`index.html:585-588`）。
- 健康目标三字段（`index.html:595-597`）；DB-2b 已删后端，勿恢复。
- 数据隐私面板（`index.html:601-606`）。
- 人设示例引语 + PREVIEW 墨色块（`index.html:576-579`）。
- 「更多」dialog 四页面卡片（`index.html:621-629`）。
- 1200px 侧栏收窄到 216px（`styles.css:1400-1404`）。
- 1024px 对话变单列（`styles.css:1436-1439`）。

## 前端有、原型没有（勿回退）

- 会话列表 CRUD、删除二次确认、切换会话（`ChatView.vue:19-64,440-472`）。
- SSE 安全首帧、crisis/high 资源、serious 状态联动（`ChatView.vue:550-559,322-344`）。
- 停止生成、断流/错误/空回复处理（`ChatView.vue:506-508,582-604`）。
- 舌诊上下文注入与 404 引导（`ChatView.vue:111-122,479-504`）。
- 人设持久化、高危自动切理性陪伴、禁用玩梗（`PersonaCard.vue:102-104,112-158`）。
- 聊天/舌诊双模型配置、测试、保存、恢复默认（`AISettings.vue:17-54,65-203`）。
- 顶栏预警未读入口、侧栏未读计数（`AppTopbar.vue:19-26`；`AppSidebar.vue:46-52`）。
- 健康分析、预警两个真实页面（`AppSidebar.vue:133-135`）。
- 移动抽屉焦点陷阱、Escape、body 滚动锁（`AppShell.vue:99-141`）。
- 移动端会话下拉选择与删除（`ChatView.vue:128-148,950-971`）。

## 落地建议

1. **先修平板对话布局（P1）**：769–1024 保持 280px 双栏偏挤，建议在该区间降为单列或让左栏可折叠；保留会话 CRUD。顺带统一 `v21.css:1343-1346` 的 280px 与 `ChatView.vue:641` 的 260px，避免断点处跳变。测试 769/900/1024 三档。
2. **再定「模式语义」再搬 UI（P1）**：原型是双消息史，真实是单会话 + `context_type`。若产品要独立历史需后端改造；否则保留单会话，把模式卡片/说明/常驻快捷问题作为「对话设置」抽屉放回，不改数据模型，风险最低。
3. **补身份与免责（P1，S/M）**：聊天头加入人设名 + 流式/安全状态，底部补 `AI 回复仅供参考，不替代医生诊断`；复用 `seriousMode`，不要恢复打字机（真实已有 stream cursor）。
4. **设置与壳体（P2）**：设置页保留模型配置，补人设引语预览与只读「数据与安全」面板；不要加回已删的目标功能，提醒需先定后端。移动端「更多」二选一：恢复原型卡片 dialog，或维持抽屉；若恢复，保留抽屉的无障碍能力。清理 `layout.css:156-198` 与 `v21.css:3084-3357` 双套壳体规则的 68/72px、82/84vw、z-index 29/59 冲突，重点回归 1024/768/560。
