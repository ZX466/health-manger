# API v2 契约（M 系列 · 身心双维升级，零新增依赖）

| 项 | 值 |
|---|---|
| 版本 | v2.0（2026-11-15） |
| 负责人 | kilo（接口 / 兼容性），评审 Claude |
| 适用范围 | `routers/mental.py`（新建）、`routers/food.py`、`routers/health.py`、`routers/chat.py`（SSE，仅契约，实现属 Pi M-PERF1）、`schemas.py`、`main.py` |
| 状态 | 契约先行；路由/服务按下方「归属与依赖」并行落地 |

> 本文件是 v2 接口的唯一权威口径。字段名、限流阈值、错误码若与其他文档冲突，以本文件为准；改动需同步修订本文件与 `schemas.py`。

## 0. 通用约定（不变量）

- 认证：一律 `Authorization: Bearer <JWT>` + `Depends(get_current_user)`；未登录/失效 → `401`。
- 数据库会话：`Depends(get_db)`；事务边界在 service 层，路由不直接 `commit`。
- 错误：统一 `HTTPException`，响应体 `{"detail": "<中文提示>"}`。
  - `400` 业务/参数语义错误（未知量表、作答非法、文件不是有效图片等）
  - `401` 未认证 · `404` 资源不存在 · `422` Pydantic 结构校验失败 · `429` 触发限流（带 `Retry-After` 秒数头）
- 时间：ISO 8601，本地 naive（与 SQLite 现状一致）；日期型字段统一用 `datetime`（当天 00:00:00 亦可）。
- 上传：单文件 ≤ **10 MiB**；允许 `image/jpeg`、`image/png`、`image/webp`（扩展名 `.jpg/.jpeg/.png/.webp`）；服务端用 PIL 校验真实图像（防伪造 content-type）。
- 兼容：**所有 v2 新增请求字段均可省略**；新增响应字段不改变既有字段语义。旧客户端/旧前端调用 v1 接口行为不变。
- AI 内容边界：识别类接口只返回**草稿**（`needs_confirm: true`），不写业务表；危机资源只从环境变量读取，缺失即返回空列表，不得编造热线号码。

## 1. 心理维度（`routers/mental.py`，prefix `/api/mental`）

路由只做鉴权、结构校验、限流与响应装配；全部业务落库走 `services.mental_service`（Claude M-LOGIC1）。

### 1.1 `POST /api/mental/mood` — 心理打卡（同日 upsert）

请求：

```json
{
  "mood_score": 3,
  "stress_tags": ["学业压力", "睡眠不足"],
  "sleep_hours": 7.5,
  "note": "今天状态一般"
}
```

| 字段 | 类型 | 约束 |
|---|---|---|
| `mood_score` | int | 必填，1–5 |
| `stress_tags` | string[] | 可选，≤5 项，每项去空格后 1–12 字 |
| `sleep_hours` | float \| null | 可选，0–16 |
| `note` | string \| null | 可选，≤500 字 |

响应 `200` `MentalRecord`：

```json
{
  "id": 12,
  "user_id": 3,
  "mood_score": 3,
  "stress_tags": ["学业压力", "睡眠不足"],
  "sleep_hours": 7.5,
  "note": "今天状态一般",
  "record_date": "2026-11-15T00:00:00",
  "created_at": "2026-11-15T21:04:11",
  "updated_at": "2026-11-15T21:04:11"
}
```

语义：同一用户同一天（本地日期）仅一条，重复提交即**更新**该条，不新增行。

字段落地口径：`record_date` 落库为 `Date`，响应按 `datetime` 序列化为当天 `00:00:00`；`updated_at` 当前未持久化，返回 `null` 保留字段位以便后续扩展；`mood_label`（如「一般」）由服务端生成，属于可选新增字段，前端不应依赖。

### 1.2 `GET /api/mental/mood?days=30`

查询参数：`days` int，默认 30，范围 1–365。响应 `200` `MentalRecord[]`，按 `record_date` 倒序。

### 1.3 `GET /api/mental/trend?days=30`

查询参数同 1.2。响应 `200`：

```json
{
  "dates": ["2026-11-09", "2026-11-10", "..."],
  "mood_score": [4, null, 3],
  "sleep_hours": [7.0, null, 6.5]
}
```

- 三个数组等长、按 `dates` 升序；缺失日 `null` 占位（连续日期序列，供前端折线图直接消费）。
- 睡眠债口径（写入口径，不在本接口内计算）：近 7 个**有记录**日 `Σ max(0, 8 − sleep_hours)`；有记录日 <4 天视为「数据不足」，由 `summary` 用 `null` 表达。

### 1.4 `GET /api/mental/scales` — 量表定义

响应 `200`（由 `services.scale_scoring.SCALES[...].to_dict()` 生成，前端不硬编码题目）：

```json
[
  {
    "key": "phq9",
    "name": "PHQ-9 抑郁初筛",
    "questions": ["做事时提不起劲或没有兴趣", "..."],
    "options": [{"score": 0, "label": "完全不会"}, {"score": 1, "label": "好几天"}],
    "max_score": 27
  }
]
```

### 1.5 `POST /api/mental/scales/{scale_type}/submit`

`scale_type` ∈ `phq9` | `gad7`；其余 → `400`（未知量表类型）。

请求：

```json
{"answers": [0, 1, 2, 0, 1, 0, 3, 1, 0]}
```

校验顺序：结构校验（`422`）→ 量表类型与作答（长度必须等于题数、每项为 0–3 整数，`400`）→ 限流（每用户每量表 **3 次/86400 秒**，超出 `429`）→ 落库。

响应 `200`：

```json
{
  "id": 41,
  "scale_type": "phq9",
  "score": 8,
  "max_score": 27,
  "risk_level": "mild",
  "label": "轻度",
  "crisis_flag": false,
  "resources": []
}
```

- `risk_level` ∈ `minimal` | `mild` | `moderate` | `moderately_severe` | `severe`。
- `crisis_flag`：PHQ-9 第 9 题 >0 **或** 总分 ≥20；GAD-7 总分 ≥15。**后端强制**，前端不得隐藏。
- `resources`：`CrisisResource[]`，仅当 `crisis_flag=true` 时返回 `services.safety_service.crisis_resources()` 的结果，否则 `[]`：

```json
[
  {"name": "心理援助热线", "phone": "0000-000000", "description": "请核实服务地区与开放时间。"},
  {"name": "学校心理咨询中心", "phone": null, "description": "请联系学校心理咨询中心/当地精神卫生中心"}
]
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `name` | string | 资源名称，1–100 字 |
| `phone` | string \| null | 热线号码；仅接受环境变量配置且通过格式校验的号码，**不得编造**；无号码时为 `null` |
| `description` | string | 说明文案，≤300 字 |

热线只从环境变量读取，**未配置（或安全模块尚未合入）时返回 `[]`**，属正常状态；前端必须固定展示 120/110 + 学校心理咨询中心文案，不得因空数组隐藏求助入口。
- 落库前由 service 计算并持久化 `score/max_score/risk_level/crisis_flag`，供交叉预警复用。

### 1.6 `GET /api/mental/scales/history?scale_type=&limit=20`

- `scale_type` 可选（缺省返回全部类型）；`limit` 默认 20，范围 1–100。
- 响应 `200` `ScaleAssessment[]`，按 `created_at` 倒序：

```json
[
  {
    "id": 41,
    "user_id": 3,
    "scale_type": "phq9",
    "answers": [0, 1, 2, 0, 1, 0, 3, 1, 0],
    "score": 8,
    "max_score": 27,
    "risk_level": "mild",
    "label": "轻度",
    "crisis_flag": false,
    "created_at": "2026-11-15T21:10:02"
  }
]
```

### 1.7 `GET /api/mental/summary`

首页/预警汇总，单次查询返回：

```json
{
  "latest_mood": { "...MentalRecord..." },
  "sleep_avg_7d": 6.8,
  "sleep_debt_7d": 4.2,
  "latest_phq9": {"id": 41, "scale_type": "phq9", "score": 8, "max_score": 27, "risk_level": "mild", "label": "轻度", "crisis_flag": false, "created_at": "2026-11-15T21:10:02"},
  "latest_gad7": null,
  "serious_mode": false
}
```

- `sleep_avg_7d` / `sleep_debt_7d`：有记录日 <4 天时为 `null`（前端展示「数据不足」），不返回 0 误导。
- `serious_mode`：为 `true` 时前端同步隐藏玩梗文案、后端强制使用严肃关怀 Prompt（决策 6）。
- `latest_mood` / `latest_phq9` / `latest_gad7` 无数据时为 `null`。

### 1.8 数据模型对齐（M-DB1 口径，opencode 落地）

| 模型 | 字段 | 说明 |
|---|---|---|
| `MentalRecord` | `id` PK, `user_id` FK→`users.id`（索引）, `record_date` `Date`, `mood_score` int 1–5, `mood_label` str(16), `stress_tags` Text（JSON 字符串）, `sleep_hours` float nullable, `note` text nullable, `created_at` datetime | 唯一约束 `(user_id, record_date)`；`stress_tags` 以 JSON 字符串落库，响应层兼容 JSON 文本与列表两种形态 |
| `ScaleAssessment` | `id` PK, `user_id` FK→`users.id`（索引）, `scale_type` str(8), `answers` Text（JSON 整数列表）, `score` int, `risk_level` str(20), `crisis_flag` bool, `created_at` datetime | 表内**不存** `max_score`/`label`，由 `services.mental_service` 依据 `scale_scoring.SCALES` 在响应层派生，接口字段保持本节定义不变；每天每类最多 3 条由路由限流保证 |
| `AIConfig` | 新增 `persona_style` str(16)，默认 `humorous` | 仅新增列；迁移 `9f1a2b3c4d5e` 已用 `server_default='humorous'` 兼容存量行 |

## 2. 拍照识餐（`routers/food.py`）

### 2.1 `POST /api/food/recognize`

`multipart/form-data`，字段名 `file`（必填，≤10 MiB，jpg/png/webp）。

响应 `200`（**只读草稿，不写任何表**）：

```json
{
  "items": [
    {
      "name": "番茄炒蛋",
      "grams": 220,
      "calories": 210,
      "protein": 11.2,
      "fat": 14.0,
      "carbs": 9.6,
      "confidence": 0.82,
      "match_food_id": 17
    }
  ],
  "needs_confirm": true
}
```

| 字段 | 说明 |
|---|---|
| `items[].name` | 识别到的食物名，1–50 字 |
| `items[].grams` | 估算克重，0–5000 |
| `items[].calories/protein/fat/carbs` | 按估算克重计算的绝对量（非每 100g） |
| `items[].confidence` | 0–1 |
| `items[].match_food_id` | 命中的既有 `Food.id`，未命中为 `null` |
| `needs_confirm` | 恒为 `true`：前端确认后才落库 |

错误：无文件/非图片 `400`；识别服务不可用 `503`（`detail` 说明可重试）；限流 `429`（每用户 10 次/60 秒）。

落库路径（前端确认后，复用 v1 接口）：先 `POST /api/food/custom` 创建 `Food`，再 `POST /api/food/records`。

### 2.2 `POST /api/food/custom`

请求：

```json
{
  "name": "食堂红烧肉",
  "calories_per_100g": 380,
  "protein_per_100g": 12.0,
  "fat_per_100g": 30.0,
  "carbs_per_100g": 8.0
}
```

| 字段 | 类型 | 约束 |
|---|---|---|
| `name` | string | 必填，1–50 字 |
| `calories_per_100g` | float | 必填，0–10000 |
| `protein_per_100g` / `fat_per_100g` / `carbs_per_100g` | float \| null | 可选，0–1000 |

响应 `200` `FoodResponse`（v1 结构，`id` 供后续餐记录引用）。副作用：`description` 固定以 `[AI估算]` 前缀开头，便于数据溯源与统计剔除。

## 3. 体检报告 OCR（`routers/health.py`）

### 3.1 `POST /api/health/reports/ocr`

`multipart/form-data`，字段名 `file`（必填，≤10 MiB，jpg/png/webp）。

响应 `200`（**只回草稿，不写 `HealthRecord`**）：

```json
{
  "fields": {
    "height": 172.0,
    "weight": 65.5,
    "blood_pressure_systolic": 118,
    "blood_pressure_diastolic": 76,
    "heart_rate": 72,
    "temperature": 36.5,
    "vision_left": 4.8,
    "vision_right": 4.9
  },
  "abnormal": ["血压偏高"],
  "confidence": 0.74,
  "needs_confirm": true
}
```

- `fields` 所有键恒存在，未识别为 `null`；取值语义与 v1 `HealthRecordCreate` 一致（前端复用现有健康记录表单，用户确认后 `POST /api/health/records`）。识别到的越界值由服务层置 `null`，本接口不对草稿做 422 拦截（草稿容错优先），最终范围校验仍由 v1 表单接口把关。
- `abnormal`：0–10 条的异常提示短语，仅作展示，不构成诊断。
- `confidence`：0–1 的整体置信度。

错误：同 2.1（`400` / `503` / `429`，每用户 10 次/60 秒）。

## 4. 流式对话（`POST /api/chat/session/{id}/stream`）

实现属 Pi M-PERF1；本节仅固定事件契约。

- 请求：`Content-Type: application/json`，body `{"message": "..."}`，1–5000 字。
- 响应：`200`，`Content-Type: text/event-stream; charset=utf-8`
- 响应头：`Cache-Control: no-cache`、`X-Accel-Buffering: no`、`Connection: keep-alive`
- 事件顺序：`safety`（至多 1 次，必发首个）→ `delta`（0..n）→ `done` 或 `error`（二选一，必发末尾）

```
event: safety
data: {"level":"high","crisis":true,"resources":[{"name":"心理援助热线","phone":null,"description":"请核实服务地区与开放时间。"}]}

event: delta
data: {"content":"你"}

event: delta
data: {"content":"好"}

event: done
data: {"message_id": 501, "tokens_used": 128}
```

```
event: error
data: {"detail":"上游模型超时"}
```

- `safety.level` ∈ `normal` | `elevated` | `high`（与 `services.safety_service.RiskState.level` 一致，不再使用 `caution`/`crisis` 取值）。
- `crisis`（bool）与 `resources`（`CrisisResource[]`，结构同 §1.5）：`crisis=true` 时前端必须展示资源且隐藏玩梗文案；`resources` 为空数组时仍展示 120/110 + 校心理中心固定文案。
- 持久化口径（决策 5）：用户消息先落库；assistant **仅**在 `done` 后落库；客户端断开即中止上游并丢弃半截回复，**不新增**「部分消息」字段。
- 消息内容含非法字符/控制字符时按文本转义，`data` 行必须为单行 JSON（`\n` 转义）。
- 前端断线重连语义：同一 `session_id` 重新发送上一条用户消息即可，不提供断点续传事件。

## 5. AI 配置扩展（`schemas.AIConfigUpdate` / `AIConfigResponse`）

- `AIConfigUpdate` 新增 **可选** `persona_style`（缺省 `null` = 不修改已存值），取值 `humorous` | `clinical`（口径 6），超出取值 → `422`。
- `AIConfigResponse` 新增 `persona_style`，未配置时返回默认 `humorous`。
- 兼容：v1 客户端不传该字段时行为完全不变；未落库列时响应仍返回默认值，不报 500。

## 6. 兼容性与回归红线

1. 既有 v1 路由的路径、请求体、响应字段**零变更**；仅新增可选字段与新路由。
2. `main.py` 注册顺序追加 `mental` 路由，不得挤占既有路由；`/api/health` 健康检查保持原样。
3. 新路由在同模块内**先静态路径后动态路径**声明，避免 `/{id}` 吞掉 `/summary`、`/scales`。
4. 上游服务未就绪时（M-DB1/M-LOGIC1/M-SEC1/M-PERF2 未落地），应用仍须可 `import main`、既有 112 项测试全绿——路由对未落地服务采用**函数内延迟导入**，落地后无需改动路由签名。
5. 数值字段一律在边界收敛范围（见各表约束），越界返回 `422`，不在 service 内静默截断。

## 7. 归属与依赖

| 交付 | 归属 | 依赖 |
|---|---|---|
| `schemas.py`、本契约 | kilo | — |
| `routers/mental.py`、`routers/food.py`、`routers/health.py`、`main.py` | kilo | M-DB1（模型）、M-LOGIC1（mental_service）、M-SEC1（crisis_resources）、M-PERF2（识别/OCR 服务） |
| `models.py`、`alembic/versions/*` | opencode（M-DB1） | — |
| `services/mental_service.py`、`services/warning_service.py` | Claude（M-LOGIC1） | M-DB1 |
| `services/safety_service.py` | Codex（M-SEC1） | — |
| `services/food_recognition_service.py`、`services/report_ocr_service.py` | Pi（M-PERF2） | M-PERF1 |
| `routers/chat.py` SSE | Pi（M-PERF1） | 本契约第 4 节 |

### 落地状态（2026-11-15 实测，main @ `5eddc66`）

- 已合入并对齐：M-DB1 模型/迁移（`9f1a2b3c4d5e`）、M-PERF1 SSE、M-PERF2 识餐/OCR 服务、M-LOGIC1 心理服务（`mental_service` 返回的 history/summary 字典字段与本契约一致）。
- 未合入：M-SEC1 `services/safety_service.py` → `resources` 暂返回 `[]`（按本节口径属正常空配置，路由已对缺失模块降级）。
- 待接线（非 kilo 文件）：`AIConfig.persona_style` 已落库（M-DB1），但 `services/ai_config_service.save_config` 未透传、`routers/ai_analysis.py` PUT/GET 未读写该字段 → 目前请求可接受、响应恒返回默认 `humorous`，需在 M-FE1 前补齐。
- 新增文件 `routers/_uploads.py`（识餐/OCR 共用上传校验）由 kilo 维护，请纳入所有权清单。
