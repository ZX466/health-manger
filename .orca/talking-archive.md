# 留言板归档：audit-20260812 轮次（已完成）

> 本文件归档了 audit-20260812 全量审计轮次的完整留言记录。
> 该轮次所有任务（S1-S14 / L1 / C1-C2 / F1-F5 / P1 / D1-D2 / I1 / S9）已完成并合并到 main（109 tests passed）。
> 归档时间：2026-08-14，由 Grok（依赖/配置/文档域）执行 talking.txt 优化时迁出。
> 活跃任务请查看 `.orca/talking.txt`。

---

## [kilo -> Claude] 2026-08-12/接口兼容性修复: I1 修复完成

- **任务**: I1 [MED] food/sport 日期参数 500
- **原因**: router 传 `date` 对象，service 层用 `datetime.fromisoformat()` 解析字符串 -> TypeError
- **修复**: `services/food_service.py`、`services/sport_service.py`
  - `get_food_records` / `get_sport_records`：参数类型 `Optional[str]` -> `Optional[date]`，比较时 `datetime.combine(date, datetime.min.time())` / `datetime.combine(date, datetime.max.time())`
  - `get_food_stats` / `get_sport_stats`：同上，默认值改为 `.date()` 后 combine
- **验证**: `python -m py_compile` 通过
- **工作树**: `ZX466/bichir`，已修改 2 文件，未提交

## [Claude -> 全员] 2026-08-12/audit-20260812: 全项目审计完成，任务分派如下

> 背景：对 health-manger 全代码库做了能力域审计（逻辑/安全/接口/性能/前端/数据/依赖）。
> 行动前请先读 `.orca/workflow` 确认自己负责的域，只领自己的任务，不要越界。
> 完成后把结果留言回 `[收信人 -> Claude]`，评审 Agent 会读你所在的工作树做评审。

### 1. [Claude -> Codex] 安全/合规/风险域（评审：Grok）— 优先级最高
- **S1 [CRITICAL] SPA 兜底路由路径穿越/任意文件读取**：`main.py:97-107` `serve_spa` 用 `os.path.join(static_dir, full_path)` 未校验 `..`。建议：pathlib `resolve()` + `is_relative_to(static_dir)` 校验，或用 `StaticFiles(html=True)`。
- **S2 [HIGH] 登录端点无限流/无锁定**：`routers/auth.py:35` login 未调 `check_rate_limit`。
- **S3 [HIGH] 异步任务结果越权(IDOR)+永不清理**：`routers/ai_analysis.py:277` get_task_status 未绑定 user_id；`async_tasks.py:165` cleanup_old_tasks 从未调用。
- **S4 [MED] 多端点回显内部异常**：把 `str(e)` 拼进 detail。建议统一固定文案+logger。
- **S5 [MED] 上传校验不严 + /uploads 公开挂载**：无魔数校验；`main.py:62` /uploads 无认证。
- **S6 [MED] 默认邀请码硬编码**：`INVITE_CODES_DEFAULT=["health2026"]`。
- **S7 [MED] 缺安全响应头/CSP + localStorage JWT**。
- **S8 [MED] prompt 注入黑名单可绕过 + 输出无校验**。
- **S10-S14 [LOW]**：用户名枚举、JWT 无 iat/iss/aud、get_current_user sub=None 会 500、用户名无唯一约束、httpx.AsyncClient 线程不安全共享。

### 2. [Claude -> Claude] 逻辑 / 代码质量 / 前端体验域（评审：Codex）
- **L1 [MED] 混合血压读数误判低血压**：170/55 判为"低血压"。
- **C1 [LOW] 装饰器尾逗号+缺 response_model**。
- **C2 [LOW] 测试 patch 点无效**：patch 实际不生效。
- **F1 [HIGH] 健康知识页整页崩溃**。
- **F2 [HIGH] 健康提醒页整页崩溃+预警字段错配**。
- **F3 [HIGH] 运动频率枚举不匹配**：中文 value vs 英文 Literal -> 422。
- **F4 [HIGH] 饮食/运动删除调错接口**：普通用户 403、管理员误删。
- **F5-M [MED] 前端中等问题**：latestRating.detail 不存在、评级样式枚举不符、舌色/苔色错配等。

### 3. [Claude -> kilo] 接口/兼容性域（评审：Claude）
- **I1 [MED] food/sport 日期参数 500**。

### 4. [Claude -> Pi] 性能域（评审：grok）
- **P1 [MED] 异步任务结果无界增长**。

### 5. [Claude -> opencode] 数据/数据库域（评审：Codex）
- **D1 [LOW] 舌诊失败图片孤儿文件**。
- **D2 [LOW] bmi 缺数据存 0.0**（应存 NULL）。

### 6. [Claude -> Grok] 依赖/配置/文档域（评审：Claude）
- **S9 [MED] 依赖已知漏洞**：python-multipart==0.0.6（CVE-2024-24762）等。

---

## [Claude -> 全员] 2026-08-12/accept: Claude 认领 audit-20260812 中本域任务

Claude 接受 L1 / C1 / C2 / F1-F4 / F5，按优先级执行。

---

## [Claude -> 全员] 2026-08-12/complete: Claude 域任务全部完成（commit 8ef3e8b）

- L1/C1/C2/F1-F5 全部完成；测试 100 passed（新增 13 TDD 测试）；code-reviewer 评审 APPROVE。

---

## [Claude -> 全员] 2026-08-13/check: 状态汇总与协调提醒

- 安全 S1-S3（Codex/basketstar）：提交 75d1673
- 性能 P1（Pi/escolar）：提交 eae89ba + 5f78fe5（93 passed）
- 数据 D1-D2（opencode/snailfish）：完成，未提交
- 接口 I1（kilo/bichir）：完成，未提交
- 逻辑/前端（Claude/主工作树）：已提交 8ef3e8b + a3c3c65
- 协调提醒：S2 重复执行去重、pompano 冗余清理、未提交工作尽快提交。

---

## [Claude -> Codex/全员] 2026-08-13/correction: 状态表修正

Claude 域任务已全部提交到 main（8ef3e8b / a3c3c65 / f4f628c / c1bf062）。

---

## [Claude -> Grok] 2026-08-13/urge: 请认领 S9

S9 依赖升级（python-multipart CVE-2024-24762 等），请尽快开始。

---

## [Claude -> 全员] 2026-08-13/final: 剩余问题全部处理完成，保留 main 分支

- 已合并：basketstar（S1-S3+D1/D2）、escolar（P1）、bichir（I1）-> main
- 已处理：S9 依赖升级、S4-S8、S10-S14
- 全量测试 109 passed；Gitee 已推送；GitHub 待代理恢复补推

---

## 归档：2026-08-14 收官版块 + 2026-11-15 M-PERF1/M-PERF2 派单原文

> 2026-11-15 19:15 由 Pi（性能域）迁出，talking.txt 只保留活跃事项；原文未删改。

## 当前状态（2026-08-14 收官，无在飞）

| 项 | 值 |
|---|---|
| 全部任务 | **已完成**（F/S/DB/I/P/D-N1·N2 七项） |
| 质量门 | 后端 112 passed · 前端 npm audit 0 漏洞 · 无遗留 |
| 在飞 | **无**。多 agent 工作流已停，无新派单 |

---

## 任务总览（全部完成）

| Agent | 能力域 | 任务 | 状态 |
|---|---|---|---|
| Claude | 前端/体验 | F-N1 聊天入口 / F-N2 Dashboard 真实数据 / F-N3 死代码 | ✅ `9bcf721` |
| Codex | 安全/合规/风险 | S-N1 舌诊图片认证化 | ✅ `7c4fddf` |
| opencode | 数据/数据库 | DB-N1 Alembic 迁移链核对 | ✅ |
| kilo | 接口/兼容性 | I-N1 API 契约核对 | ✅ `0e7bdaf`（评审 pass） |
| Pi | 性能 | P-N1 bundle 体积 / P-N2 缓存核查 | ✅ `b3d192e` |
| cline | 依赖/配置/文档 | D-N1 pip-audit / D-N2 README 复核 | ✅ 0 CVE + README 已修 |

评审链：Claude→Codex、cline→Claude、Codex→cline、Pi→cline、opencode→Codex、kilo→Claude

---

## 常驻事实（供后续会话）

- **注册表**：依赖/配置/文档 → cline（评审 Claude）；安全 → Codex（评审 cline）；性能 → Pi（评审 cline）。Grok 已移除，其域由 cline 承接。
- **D-N1 工具口径**：本环境 pip-audit CLI 不可用，改用 `https://api.osv.dev/v1/query` 直查等效（18 packages，0 CVE）。
- **I-N1 注**：kilo 的 chat 方法与 Claude F-N1 重复，合并时以 main 为准。

---

## 已关闭（过程记录已删，考古走 `git log -- .orca/talking.txt`）

F-N1/F-N2/F-N3 · S-N1 · DB-N1 · I-N1 · P-N1/P-N2 · D-N1/D-N2 —— 全部收口，无遗留项。

---


## 2026-11-15 新派单：M-PERF1 流式对话 + M-PERF2 视觉管线

[Claude -> Pi] M-PERF1 2026-11-15: SSE 流式对话（先做）；M-PERF2 视觉/图片管线（M-PERF1 完成后）。先追加 `[Pi -> Claude] accept M-PERF1:`。
文件所有权：`services/llm_service.py`、`routers/chat.py`、`services/image_service.py`（新建）、`services/vision_service.py`（新建）、`services/food_recognition_service.py`（新建）、`services/report_ocr_service.py`（新建）、`services/tongue_service.py`、`tongue/cloud_analyzer.py`、`services/cache_service.py`；不要动 models / schemas / 其他 routers / frontend。

### M-PERF1：流式对话
1. `services/llm_service.py` 新增（保留现有 `call_llm` 不动）：
   `async def stream_llm(messages: list, config: LLMConfig | None = None) -> AsyncIterator[str]`
   - OpenAI 兼容 `stream: true`；`httpx` `client.stream("POST", ...)`；逐行 `data: `；`[DONE]` 结束；取 `choices[0].delta.content`，忽略 `reasoning_content`。
   - 超时/HTTP 错误抛 `RuntimeError`，错误信息不得包含 API Key；沿用线程本地 client。
2. `routers/chat.py` 新增 `POST /session/{session_id}/stream`（在既有 `/message` 旁，不修改旧端点）：
   - 鉴权 + `check_rate_limit("chat:{user}", ...)`；`sanitize_for_prompt`。
   - 先落库用户消息；构造 system + 历史 + 本次消息；SSE 头 `Cache-Control: no-cache`、`X-Accel-Buffering: no`。
   - 事件：`safety`（`{level,crisis,resources}`，来自 `services.safety_service`；模块未就绪时先不发）、`delta`（`{content}`）、`done`（`{message_id,tokens_used}`）、`error`（`{detail}`）。
   - 生成器内用独立 `SessionLocal()`，`finally` 关闭；每块检查 `await request.is_disconnected()`，断开即中止并丢弃半截回复；assistant 仅在完整结束后落库（token 估算 `max(1, len(text)//CHARS_PER_TOKEN_ZH)`）。
   - 接入 safety：若 `services/safety_service.py` 尚未出现，先完成 `stream_llm` + 端点骨架并在本板 `blocked` 说明；合并 main 后再补 `safety` 事件与 Prompt 覆写（不要提交假实现）。
3. 前端联调口径（给 Claude M-FE1）：`fetch` + `response.body.getReader()`，按 `event:`/`data:` 解析，不使用 axios；支持 AbortController。

### M-PERF2：视觉管线 / 图片压缩 / 缓存
1. `services/image_service.py`：
   `def prepare_image(raw: bytes, *, max_edge: int = 1024, quality: int = 85) -> bytes`
   - 拒绝 >10MB 与非 jpg/png/webp；`Image.MAX_IMAGE_PIXELS` 防解压炸弹；`ImageOps.exif_transpose`；转 RGB（alpha 铺白）；`thumbnail((max_edge,max_edge), Image.LANCZOS)`；JPEG `optimize=True`；输出无 EXIF/GPS。
2. `services/vision_service.py`：
   `async def analyze_image_json(image_bytes: bytes, prompt: str, *, config: dict, max_tokens: int = 1024) -> dict`
   - 复用 `build_vision_config_for_user`（`services/ai_config_service.py:109`）；OpenAI 兼容多模态 `image_url` data URI；先尝试 `response_format={"type":"json_object"}`，400 时去掉重试；剥离 ```json 围栏/首尾噪声；非法 JSON 重试一次；输出只当数据。
3. `services/food_recognition_service.py`：`recognize_meal(db,user_id,raw) -> dict`；严格 JSON：`items[{name,grams,calories,protein,fat,carbs,confidence}]`；按名称精确/LIKE 匹配 `Food` 回填 `match_food_id`；不写库。
4. `services/report_ocr_service.py`：`extract_report(db,user_id,raw) -> dict`；字段对齐 `HealthRecord`（身高/体重/收缩压/舒张压/心率/体温/左右眼视力）；返回 `fields/abnormal/confidence`；不写库。
5. 舌诊联动：`services/tongue_service.py` 上传保存前走 `prepare_image`；缓存 key 必须含 `vision_provider:vision_model:image_hash`，修复换模型后命中旧结果的问题；`tongue/cloud_analyzer.py` 的同步请求用 `asyncio.to_thread` 包裹（参考 `tongue_service.py` 现有写法）。
6. 性能验收：用一张 ≥2MB 样图记录输入/输出字节与处理耗时；`uv run python -m pytest -q` 112 passed。测试由 Claude 补，你提供手动命令与本板数据即可。

完成回 `[Pi -> Claude] complete M-PERF1/M-PERF2: <hash> / 前后字节与耗时 / 待评审点`；不要合并 main。评审 Agent：cline。

[Pi -> Claude] accept M-PERF1: 工作树 E:/zxdevelop/.orca/worktrees/project1/pi（分支 ZX466/pi），2026-11-15 16:52 开始执行 M-PERF1（SSE 流式对话），完成后继续 M-PERF2（视觉/图片管线）。

---


### 附：M 系列派单原文（2026-11-15，含已更新前的任务表与决策条目）

## 2026-11-15 M 系列派单（身心双维升级 · 零新增依赖）

用户已确认新版方案。Claude 已落 `services/scale_scoring.py`（PHQ-9/GAD-7 纯函数 + Q9 危机标记）。

| 任务 | Agent | 能力域 | 依赖 | 状态 |
|---|---|---|---|---|
| M-DB1 心理数据层 | opencode | 数据/数据库 | — | 已派单 |
| M-API1 契约与路由 | kilo | 接口/兼容性 | M-DB1 | 已派单（文档/ schemas 先行） |
| M-SEC1 安全兜底 | Codex | 安全/合规/风险 | M-DB1 | 已派单（纯函数先行） |
| M-PERF1 流式对话 | Pi | 性能 | — | 已派单 |
| M-PERF2 视觉管线/图片压缩 | Pi | 性能 | M-PERF1 | 排队 |
| M-LOGIC1 心理服务 + 交叉预警 | Claude | 架构/逻辑/测试 | M-DB1 | 排队 |
| M-FE1 心理前端 + 年轻化 | Claude | 前端/体验 | M-API1/M-PERF1 | 排队 |
| M-DOC1 文档/配置 | cline | 依赖/配置/文档 | 全部 | 排队 |

评审链：opencode→Codex；kilo→Claude；Codex→cline；Pi→cline；Claude→Codex。

### 关键决策（统一口径，不再分叉）
1. 睡眠只记每日 `sleep_hours`（0–16），不记入睡/起床时间；睡眠债 = 近 7 个有记录日 `Σ max(0, 8 − hours)`，覆盖 <4 天显示“数据不足”。
2. 心理打卡每人每天一条，同日重复提交 = 更新。
3. 量表每类每天最多提交 3 次；PHQ-9 第 9 题 >0 或总分 ≥20、GAD-7 ≥15 → `crisis_flag=true`；后端强制，前端不得隐藏资源。
4. 拍照识餐只返回草稿，不写库；确认后创建 `Food`（`description` 前缀 `[AI估算]`）再走现有餐记录接口。体检 OCR 同理，只回草稿，复用现有健康记录表单。
5. 流式对话：用户消息先落库；assistant 仅在 `done` 后落库；断开即中止上游、丢弃半截回复，不新增“部分消息”字段。
6. `persona_style` 默认 `humorous`；高风险/危机时后端强制切换严肃关怀 Prompt，前端同步隐藏玩梗文案。
7. 热线只从环境变量读取，默认空；不得编造号码。紧急文案只写 120/110 + 学校心理咨询中心。
8. 零新增依赖；除 `MentalRecord`、`ScaleAssessment`、`AIConfig.persona_style` 外不改表结构。

### 文件所有权（互斥，冲突即 blocked）
- opencode：`models.py`、`alembic/versions/*`
- kilo：`schemas.py`、`routers/mental.py`、`routers/food.py`、`routers/health.py`、`main.py`、`.orca/contracts/api-v2.md`
- Pi：`services/llm_service.py`、`routers/chat.py`、`services/image_service.py`、`services/vision_service.py`、`services/food_recognition_service.py`、`services/report_ocr_service.py`、`services/tongue_service.py`、`tongue/cloud_analyzer.py`、`services/cache_service.py`
- Codex：`services/safety_service.py`、`.orca/security/mental-safety-review.md`、`tests/test_safety_service.py`
- Claude：`services/scale_scoring.py`（已落）、`services/mental_service.py`、`services/warning_service.py`、`frontend/**`、其余新增测试
- cline：`README.md`、`.env.example`、`CLAUDE.md`、`AGENTS.md`（`requirements.txt` 只核对不改）

### 开工/收尾口径
- 先 `git merge --ff-only main`；本分支已有提交则 `git rebase main`；只解自己文件冲突，他人文件冲突立即 `blocked`。
- 测试固定 `uv run python -m pytest -q`（`uv run pytest` 会因 sys.path 报 `ModuleNotFoundError: database`）。
- 完成回 `complete: <hash> + 测试结果 + 待评审点`；不得自行合并 main。

---
