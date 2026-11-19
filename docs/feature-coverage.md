# 功能覆盖矩阵（feature-coverage）

> 基线：main `c577392`（AI P1 端点收口后），2026-11-19 DOC-2 文档校准 + FE-2 前端闭环。
> 端点数为 FastAPI 路由表实测 **72**（含 `GET /api/health` 探活；业务端点 **71**）。
> 状态口径：**已接入** = 前端有 UI 调用链（证据到视图/组件/store）；**仅封装** = `frontend/src/api` 已封装但无 UI 调用；**未封装** = 前端无对应方法。
> 上一轮 P0（W-1 / A-1 / K-1）与 P1（K-2 / DASH-1 / CHAT-1）均已合并；FE-2 已把 P2 的 10 个端点接入 UI，仅剩聊天 v1 非流式消息为遗留封装。

## 1. 模块总览

| 模块 | 路由文件 | 端点数 | 已接入 | 仅封装 | 未封装 | 前端入口 |
|---|---|---|---|---|---|---|
| 认证 | [routers/auth.py](../routers/auth.py) | 3 | 3 | 0 | 0 | `Login.vue` / `Register.vue` |
| 健康数据 | [routers/health.py](../routers/health.py) | 9 | 9 | 0 | 0 | `/health-record`、`/health-analysis`、Dashboard（7/30 天评分） |
| 饮食 | [routers/food.py](../routers/food.py) | 11 | 11 | 0 | 0 | `/diet-management`（管理员可编辑/删除全库，内置与自定义一致；非管理员只读） |
| 运动 | [routers/sport.py](../routers/sport.py) | 9 | 9 | 0 | 0 | `/sport-management`（管理员可编辑/删除全库，内置与自定义一致；非管理员只读） |
| AI 分析与配置 | [routers/ai_analysis.py](../routers/ai_analysis.py) | 12 | 12 | 0 | 0 | `/ai-settings`（配置）、`/health-analysis`（深度 / 快速 / 规则 + AI / 后台异步） |
| 健康预警 | [routers/warning.py](../routers/warning.py) | 6 | 6 | 0 | 0 | `/warnings`（侧栏 / 顶栏 / Dashboard 未读入口） |
| 舌诊 | [routers/tongue.py](../routers/tongue.py) | 7 | 7 | 0 | 0 | `/tongue-diagnosis`（统计卡 / 删除） |
| 聊天 | [routers/chat.py](../routers/chat.py) | 7 | 6 | 1 | 0 | `/chat`（身体问诊引用舌诊、会话删除） |
| 心理 | [routers/mental.py](../routers/mental.py) | 7 | 7 | 0 | 0 | `/mental` |
| 探活 | [main.py](../main.py) | 1 | — | — | — | 运维 `GET /api/health` |
| **合计** | 9 个路由文件 + main.py | **72**（业务 71） | **70** | **1** | **0** | 12 个视图 |

前端视图 12 个（[frontend/src/router/index.js](../frontend/src/router/index.js)）：Login、Register、Dashboard、HealthRecord、HealthAnalysis、DietManagement、SportManagement、TongueDiagnosis、MentalView、ChatView、AISettings、WarningView。`/warnings` 已注册。

## 2. 本轮缺口收口与剩余

| 缺口 | 端点 | 现状证据 | 任务 | 状态 |
|---|---|---|---|---|
| 预警前端闭环 | `/api/warning/*` 全部 6 个 | `WarningView.vue` + `stores/warnings.js`；侧栏 / 顶栏 / Dashboard 未读入口 | W-1 | ✅ `182195e` |
| AI 分析生成入口 | `/api/ai/analysis`、`/analysis/history`、`/analysis/{id}` GET/DELETE | `HealthAnalysis.vue` 生成 / 查看 / 删除；错误分缺 Key / 无数据 / 限流 / 超时 | A-1 | ✅ `008f098` |
| 记录/量表提交后自动预警 | `POST /health/records`、`POST /mental/scales/{type}/submit` | 提交后调用 `safe_check_health_warnings`，失败不阻断主流程 | K-1 | ✅ `84d0bc3` |
| Dashboard 7/30 天评分 | `GET /health/rating/history` | K-2 端点 + Dashboard 今日 / 近 7 天 / 近 30 天切换，缺失日不计 0 | K-2 → DASH-1 | ✅ `008f098` |
| 聊天引用舌诊 | `POST /chat/session/{id}/tongue-context` | 身体问诊“引用最近舌诊”，无记录时跳转 `/tongue-diagnosis` | CHAT-1 | ✅ `008f098` |
| AI 快捷 / 评价 / 异步分析 | `/quick-analysis`、`/health-evaluation`、`/async-analysis`、`/task/{id}` | `HealthAnalysis.vue` 三种模式按钮：快速分析、规则 + AI 评价、后台分析轮询；异步完成后落库并刷新历史 | P1 收口 | ✅ 本轮 |
| P2 端点前端闭环 | 聊天会话删除、健康记录详情、舌诊统计/删除、食物/运动详情/更新/删除 | `ChatView.vue` / `HealthRecord.vue` / `TongueDiagnosis.vue` / `DietManagement.vue` / `SportManagement.vue`；食物/运动库编辑删除仅管理员可见（后端 `get_admin_user`） | FE-2 | ✅ 本轮 |
| 异步分析后台队列持久化 | `/api/ai/async-analysis`、`/api/ai/task/{id}` | `async_tasks` 表 + 原子领取/启动恢复；worker 单事务写 `ai_analyses` 与任务终态，终态写入校验领取令牌 | ASYNC-1 | ✅ `6ac3dbb`+`0fdf884` |
| 无引用表清理 | — | 迁移 `b2c3d4e5f6a7` 删除 `health_articles`/`user_health_goals`；模型、schema、清理/种子脚本同步 | DB-2b | ✅ `625f957` |
| E2E 冒烟 | 登录 + 流式聊天冒烟 | `tests/test_e2e_smoke.py`；CI backend 用 uv + ruff，frontend 单测 + 构建 | E2E-1 | ✅ 本轮 |

## 3. 逐端点矩阵

### 3.1 认证（3/3 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/auth/register | [auth.py:24](../routers/auth.py) | index.js `register` | Register.vue | 已接入 |
| POST /api/auth/login | [auth.py:45](../routers/auth.py) | index.js `login` | Login.vue | 已接入 |
| GET /api/auth/me | [auth.py:72](../routers/auth.py) | index.js `getCurrentUser` | Dashboard / Diet / Sport | 已接入 |

### 3.2 健康数据（9/9 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/health/records | [health.py:29](../routers/health.py) | health.js `createHealthRecord` | HealthRecord.vue（含 OCR 草稿确认入库） | 已接入；K-1 补自动预警 |
| GET /api/health/records | [health.py:41](../routers/health.py) | health.js `getHealthRecords` | Dashboard.vue / HealthRecord.vue | 已接入 |
| GET /api/health/records/{id} | [health.py:49](../routers/health.py) | health.js `getHealthRecord` | HealthRecord.vue（详情弹窗，接口优先、列表快照兜底） | 已接入（FE-2） |
| DELETE /api/health/records/{id} | [health.py:58](../routers/health.py) | health.js `deleteHealthRecord` | HealthRecord.vue | 已接入 |
| GET /api/health/analysis/latest | [health.py:67](../routers/health.py) | health.js `getLatestAnalysis` | Dashboard / HealthAnalysis.vue | 已接入 |
| GET /api/health/analysis/history | [health.py:75](../routers/health.py) | health.js `getAnalysisHistory` | HealthAnalysis.vue | 已接入 |
| GET /api/health/rating/latest | [health.py:83](../routers/health.py) | health.js `getLatestRating` | wellness.js / Dashboard / HealthRecord | 已接入 |
| GET /api/health/rating/history | [health.py:105](../routers/health.py) | health.js `getRatingHistory` | Dashboard.vue（今日 / 7 天 / 30 天） | 已接入（K-2 → DASH-1） |
| POST /api/health/reports/ocr | [health.py:117](../routers/health.py) | health.js `ocrHealthReport` | HealthRecord.vue | 已接入（草稿→确认入库） |

注：`GET /health/rating/history` 缺失日返回 `score: null`；Dashboard 只对非空分数求均值，并显示覆盖天数。

### 3.3 饮食（11/11 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/food/foods | [food.py:30](../routers/food.py) | food.js `createFood` | DietManagement.vue | 已接入 |
| GET /api/food/foods | [food.py:39](../routers/food.py) | food.js `getFoods` | DietManagement.vue | 已接入 |
| GET /api/food/foods/{id} | [food.py:49](../routers/food.py) | food.js `getFood` | DietManagement.vue（管理员编辑前拉取详情） | 已接入（FE-2） |
| PUT /api/food/foods/{id} | [food.py:58](../routers/food.py) | food.js `updateFood` | DietManagement.vue（管理员编辑） | 已接入（FE-2） |
| DELETE /api/food/foods/{id} | [food.py:68](../routers/food.py) | food.js `deleteFood` | DietManagement.vue（管理员删除确认） | 已接入（FE-2） |
| POST /api/food/records | [food.py:77](../routers/food.py) | food.js `createFoodRecord` | DietManagement.vue | 已接入 |
| GET /api/food/records | [food.py:86](../routers/food.py) | food.js `getFoodRecords` | DietManagement.vue | 已接入 |
| GET /api/food/records/stats | [food.py:96](../routers/food.py) | food.js `getFoodStats` | DietManagement.vue | 已接入 |
| DELETE /api/food/records/{id} | [food.py:106](../routers/food.py) | food.js `deleteFoodRecord` | DietManagement.vue:527 | 已接入 |
| POST /api/food/recognize | [food.py:115](../routers/food.py) | food.js `recognizeFoodImage` | DietManagement.vue | 已接入（草稿→确认入库） |
| POST /api/food/custom | [food.py:133](../routers/food.py) | food.js `createCustomFood` | DietManagement.vue | 已接入 |

### 3.4 运动（9/9 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/sport/sports | [sport.py:25](../routers/sport.py) | index.js `createSport` | SportManagement.vue | 已接入 |
| GET /api/sport/sports | [sport.py:34](../routers/sport.py) | index.js `getSports` | SportManagement.vue | 已接入 |
| GET /api/sport/sports/{id} | [sport.py:44](../routers/sport.py) | index.js `getSport` | SportManagement.vue（管理员编辑前拉取详情） | 已接入（FE-2） |
| PUT /api/sport/sports/{id} | [sport.py:53](../routers/sport.py) | index.js `updateSport` | SportManagement.vue（管理员编辑） | 已接入（FE-2） |
| DELETE /api/sport/sports/{id} | [sport.py:63](../routers/sport.py) | index.js `deleteSport` | SportManagement.vue（管理员删除确认） | 已接入（FE-2） |
| POST /api/sport/records | [sport.py:72](../routers/sport.py) | index.js `createSportRecord` | SportManagement.vue | 已接入 |
| GET /api/sport/records | [sport.py:81](../routers/sport.py) | index.js `getSportRecords` | wellness.js / SportManagement.vue | 已接入 |
| GET /api/sport/records/stats | [sport.py:91](../routers/sport.py) | index.js `getSportStats` | SportManagement.vue | 已接入 |
| DELETE /api/sport/records/{id} | [sport.py:101](../routers/sport.py) | index.js `deleteSportRecord` | SportManagement.vue | 已接入 |

### 3.5 AI 分析与配置（12/12 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/ai/analysis | [ai_analysis.py:71](../routers/ai_analysis.py) | index.js `createAIAnalysis` | HealthAnalysis.vue（生成分析） | 已接入（A-1） |
| GET /api/ai/analysis/history | [ai_analysis.py:120](../routers/ai_analysis.py) | index.js `getAIAnalysisHistory` | HealthAnalysis.vue（AI 历史） | 已接入（A-1） |
| GET /api/ai/analysis/{id} | [ai_analysis.py:137](../routers/ai_analysis.py) | index.js `getAIAnalysis` | HealthAnalysis.vue（点击查看） | 已接入（A-1） |
| DELETE /api/ai/analysis/{id} | [ai_analysis.py:155](../routers/ai_analysis.py) | index.js `deleteAIAnalysis` | HealthAnalysis.vue（二次确认删除） | 已接入（A-1） |
| POST /api/ai/quick-analysis | [ai_analysis.py:176](../routers/ai_analysis.py) | index.js `quickHealthAnalysis` | HealthAnalysis.vue（快速分析） | 已接入 |
| POST /api/ai/health-evaluation | [ai_analysis.py:226](../routers/ai_analysis.py) | index.js `getHealthEvaluation` | HealthAnalysis.vue（规则 + AI 评价） | 已接入 |
| POST /api/ai/async-analysis | [ai_analysis.py:327](../routers/ai_analysis.py) | index.js `asyncAIAnalysis` | HealthAnalysis.vue（后台分析） | 已接入 |
| GET /api/ai/task/{id} | [ai_analysis.py:367](../routers/ai_analysis.py) | index.js `getTaskStatus` | HealthAnalysis.vue（轮询，完成后落库） | 已接入 |
| GET /api/ai/config | [ai_analysis.py:408](../routers/ai_analysis.py) | index.js `getAiConfig` | AISettings / PersonaCard.vue | 已接入 |
| PUT /api/ai/config | [ai_analysis.py:442](../routers/ai_analysis.py) | index.js `saveAiConfig` | AISettings / PersonaCard.vue | 已接入 |
| DELETE /api/ai/config | [ai_analysis.py:486](../routers/ai_analysis.py) | index.js `deleteAiConfig` | AISettings.vue | 已接入 |
| POST /api/ai/config/test | [ai_analysis.py:496](../routers/ai_analysis.py) | index.js `testAiConfig` | AISettings.vue | 已接入 |

注：AI 分析 12 个端点的契约/测试由 K-3 保障；`HealthAnalysis.vue` 同时展示规则引擎分析（`/health/analysis/*`）和 LLM 深度解读（`/ai/analysis/*`）。快速分析复用最新记录缓存；规则 + AI 评价展示规则评分与 LLM 综合结论；后台分析轮询 `task/{id}`，完成后由任务查询端点落库并返回 `analysis_id`，可继续在历史中查看。

### 3.6 健康预警（6/6 已接入 → W-1）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/warning/check | [warning.py:15](../routers/warning.py) | index.js `checkWarnings` | WarningView.vue（重新检查） | 已接入；K-1 后提交自动触发 |
| GET /api/warning/list | [warning.py:24](../routers/warning.py) | index.js `getWarnings` | WarningView.vue | 已接入 |
| PUT /api/warning/read/{id} | [warning.py:40](../routers/warning.py) | index.js `markWarningAsRead` | WarningView.vue | 已接入 |
| PUT /api/warning/read-all | [warning.py:65](../routers/warning.py) | index.js `markAllWarningsAsRead` | WarningView.vue | 已接入 |
| DELETE /api/warning/{id} | [warning.py:77](../routers/warning.py) | index.js `deleteWarning` | WarningView.vue（二次确认） | 已接入 |
| GET /api/warning/stats | [warning.py:100](../routers/warning.py) | index.js `getWarningStats` | stores/warnings.js → 侧栏 / 顶栏 / Dashboard | 已接入（未读徽标） |

注：后端预警闭环完整（含心理交叉预警，M-LOGIC1）；W-1 未改后端。

### 3.7 舌诊（7/7 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/tongue/upload | [tongue.py:23](../routers/tongue.py) | index.js `uploadTongueImage` | stores/tongue.js → TongueDiagnosis.vue | 已接入 |
| GET /api/tongue/list | [tongue.py:32](../routers/tongue.py) | index.js `getTongueList` | stores/tongue.js | 已接入 |
| GET /api/tongue/latest/result | [tongue.py:42](../routers/tongue.py) | index.js `getLatestTongueResult` | stores/tongue.js | 已接入 |
| GET /api/tongue/stats/summary | [tongue.py:75](../routers/tongue.py) | index.js `getTongueStats` | TongueDiagnosis.vue（累计/最近证型统计卡） | 已接入（FE-2） |
| GET /api/tongue/image/{id} | [tongue.py:83](../routers/tongue.py) | index.js `getTongueImage` | TongueDiagnosis.vue | 已接入 |
| GET /api/tongue/{id} | [tongue.py:93](../routers/tongue.py) | index.js `getTongueDetail` | TongueDiagnosis.vue | 已接入 |
| DELETE /api/tongue/{id} | [tongue.py:102](../routers/tongue.py) | index.js `deleteTongueRecord` | TongueDiagnosis.vue（历史记录删除确认） | 已接入（FE-2） |

### 3.8 聊天（6/7 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/chat/session | [chat.py:94](../routers/chat.py) | chat.js `createChatSession` | ChatView.vue | 已接入 |
| GET /api/chat/sessions | [chat.py:117](../routers/chat.py) | chat.js `getChatSessions` | ChatView.vue | 已接入 |
| GET /api/chat/session/{id}/messages | [chat.py:138](../routers/chat.py) | chat.js `getChatMessages` | ChatView.vue | 已接入 |
| POST /api/chat/session/{id}/message | [chat.py:156](../routers/chat.py) | chat.js `sendChatMessage` | 无（v1 遗留封装，前端只走流式） | 仅封装（保留兼容，不补 UI） |
| POST /api/chat/session/{id}/stream | [chat.py:207](../routers/chat.py) | stream.js `streamChatMessage` | ChatView.vue（主路径，safety→delta*→done\|error） | 已接入 |
| POST /api/chat/session/{id}/tongue-context | [chat.py:296](../routers/chat.py) | chat.js `addTongueContext` | ChatView.vue（引用最近舌诊） | 已接入（CHAT-1） |
| DELETE /api/chat/session/{id} | [chat.py:337](../routers/chat.py) | chat.js `deleteChatSession` | ChatView.vue（会话列表删除确认，删除后切换/清空） | 已接入（FE-2） |

### 3.9 心理（7/7 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/mental/mood | [mental.py:40](../routers/mental.py) | mental.js `createMentalRecord` | MoodCheckIn.vue | 已接入（每日一条 upsert） |
| GET /api/mental/mood | [mental.py:57](../routers/mental.py) | mental.js `getMentalRecords`（别名 `getMentalMood`） | wellness.js / MentalView.vue | 已接入 |
| GET /api/mental/trend | [mental.py:66](../routers/mental.py) | mental.js `getMentalTrend` | Dashboard / MentalView.vue | 已接入 |
| GET /api/mental/scales | [mental.py:75](../routers/mental.py) | mental.js `getMentalScales` | MentalView.vue | 已接入 |
| GET /api/mental/scales/history | [mental.py:81](../routers/mental.py) | mental.js `getMentalAssessments`（别名 `getMentalScaleHistory`） | MentalView.vue | 已接入 |
| POST /api/mental/scales/{type}/submit | [mental.py:93](../routers/mental.py) | mental.js `createMentalAssessment`（别名 `submitMentalScale`） | ScaleRunner.vue | 已接入；K-1 补自动预警 |
| GET /api/mental/summary | [mental.py:123](../routers/mental.py) | mental.js `getMentalSummary` | wellness.js / MentalView / ChatView / Dashboard / AISettings | 已接入 |

### 3.10 探活

| 端点 | 证据 | 用途 |
|---|---|---|
| GET /api/health | [main.py](../main.py)（`health_check`） | 部署验证（README「5. 验证」使用） |

## 4. 复核方法（可复现）

1. 后端路由表：`uv run python -c "from main import app; ..."` 枚举 `app.routes`（需设 `SECRET_KEY`），共 72 个 `/api` 路由（71 业务 + 1 探活）。
2. 前端封装：`frontend/src/api/*.js` 中 `http.get/post/put/delete` 调用逐一对照。
3. UI 调用链：在 `frontend/src`（排除 `api/`）grep `api.<方法名>` 与别名（mental.js 尾部有 v1 别名导出）。
4. 本文档只描述已实现功能；「待补」均对应已派单任务（当前为 FE-2）或明确标注未派单。

## 5. 校准记录

| 日期 | 基线 | 说明 |
|---|---|---|
| 2026-11-18 | main `ef6c68f`（对齐 `a967496`） | C-1 首轮：43 已接入 / 25 仅封装 / 2 未封装 / 1 探活 |
| 2026-11-18 | main `008f098` | C-1 二次校准：55 已接入 / 14 仅封装 / 2 未封装；72 路由含探活；新增 `/warnings`、AI 分析 4 端点、K-2 评分历史、CHAT-1 舌诊上下文 |
| 2026-11-18 | main `254d51f` 后 | P1 收口：AI 快捷/规则+AI 评价/异步分析/任务轮询接入 `HealthAnalysis.vue`；59 已接入 / 10 仅封装 / 2 未封装 |
| 2026-11-19 | main `c577392` | DOC-2 校准：修正饮食行（明细 8/2/1，原汇总误写 7/3/1）与总计 **60 已接入 / 9 仅封装 / 2 未封装**；§2 剩余缺口对齐 FE-2 派单；实测后端 271 passed、前端 27 passed |
| 2026-11-19 | main `c3923b5` | ASYNC-1 / DB-2b / E2E-1 收口：异步任务持久化（`async_tasks` + 原子领取 + 启动恢复 + 单事务落库，迁移 `a1b2c3d4e5f6`）；DB-2b 删除 `health_articles`/`user_health_goals`（迁移 `b2c3d4e5f6a7`，模型/schema/脚本同步）；E2E 冒烟 + CI（uv/ruff）。实测后端 288 passed、前端 27 passed |
| 2026-11-19 | main `2b0de16` | AI 配置局部更新：`AIConfigUpdate` 的 provider/model 改为可选，舌诊视觉配置可单独保存并保留聊天模型；前端 `readApiError` 拍平 422 detail 数组。实测后端 289 passed、前端 31 passed |
| 2026-11-19 | main `3aa9862` | 视觉模型失败提示细分：智谱 1210（仅 text）提示模型不支持图片并建议 glm-4v-plus；401/403 鉴权、404 接口、400 模型能力分别提示；新增 3 例视觉错误测试。实测后端 292 passed、前端 31 passed |
