# 功能覆盖矩阵（feature-coverage）

> 基线：main `ef6c68f`（内容对齐至 `a967496`），2026-11-18 C-1 首轮。
> 端点数为 FastAPI 路由表实测 **71**（含 `GET /api/health` 探活；派单口径 70 不含探活）。
> 状态口径：**已接入** = 前端有 UI 调用链（证据到视图/组件/store）；**仅封装** = `frontend/src/api` 已封装但无 UI 调用；**未封装** = 前端无对应方法。
> P0/P1/P2 为本轮派单优先级；P0（W-1/A-1/K-1）合并后本文档二次校准。

## 1. 模块总览

| 模块 | 路由文件 | 端点数 | 已接入 | 仅封装 | 未封装 | 前端入口 |
|---|---|---|---|---|---|---|
| 认证 | [routers/auth.py](../routers/auth.py) | 3 | 3 | 0 | 0 | `Login.vue` / `Register.vue` |
| 健康数据 | [routers/health.py](../routers/health.py) | 8 | 7 | 1 | 0 | `/health-record`、`/health-analysis`、Dashboard |
| 饮食 | [routers/food.py](../routers/food.py) | 11 | 7 | 3 | 1 | `/diet-management` |
| 运动 | [routers/sport.py](../routers/sport.py) | 9 | 6 | 2 | 1 | `/sport-management` |
| AI 分析与配置 | [routers/ai_analysis.py](../routers/ai_analysis.py) | 12 | 4 | 8 | 0 | `/ai-settings`（配置）；**分析无 UI（A-1）** |
| 健康预警 | [routers/warning.py](../routers/warning.py) | 6 | 0 | 6 | 0 | **无页面（W-1）** |
| 舌诊 | [routers/tongue.py](../routers/tongue.py) | 7 | 5 | 2 | 0 | `/tongue-diagnosis` |
| 聊天 | [routers/chat.py](../routers/chat.py) | 7 | 4 | 3 | 0 | `/chat` |
| 心理 | [routers/mental.py](../routers/mental.py) | 7 | 7 | 0 | 0 | `/mental` |
| 探活 | [main.py](../main.py) | 1 | — | — | — | 运维 `GET /api/health` |
| **合计** | 9 个路由文件 + main.py | **71** | **43** | **25** | **2** | 11 个视图 |

前端视图 11 个（[frontend/src/router/index.js](../frontend/src/router/index.js)）：Login、Register、Dashboard、HealthRecord、HealthAnalysis、DietManagement、SportManagement、TongueDiagnosis、MentalView、ChatView、AISettings。无 `/warnings` 路由。

## 2. P0 / P1 缺口（本轮任务映射）

| 缺口 | 端点 | 现状证据 | 任务 | 优先级 |
|---|---|---|---|---|
| 预警前端闭环缺失 | `/api/warning/*` 全部 6 个 | 方法已封装（[api/index.js:83-99](../frontend/src/api/index.js)）但全仓库无 UI 调用；router 无 `/warnings` | W-1 | P0 |
| AI 分析生成入口缺失 | `/api/ai/analysis`、`/analysis/history`、`/analysis/{id}` GET/DELETE、`/quick-analysis`、`/health-evaluation`、`/async-analysis`、`/task/{id}` 共 8 个 | 方法已封装（[api/index.js:58-79](../frontend/src/api/index.js)）但无 UI 调用；`HealthAnalysis.vue` 只读规则分析 `/health/analysis/*` | A-1（前端）、K-3（契约测试） | P0 / P1 |
| 记录/量表提交后不自动触发预警 | `POST /health/records`、`POST /mental/scales/{type}/submit` | 两个路由提交后未调用 `check_health_warnings`；预警只能手动 `POST /warning/check`（也无 UI） | K-1 | P0 |
| Dashboard 7/30 天评分为演示数据 | 需新端点 `GET /health/rating/history`（**尚未实现**） | Dashboard w7/m30 硬编码示例分数 | K-2 → DASH-1 | P1 |
| 聊天引用舌诊无按钮 | `POST /chat/session/{id}/tongue-context` | `addTongueContext` 已封装（[api/chat.js:20-22](../frontend/src/api/chat.js)）无 UI 调用 | CHAT-1 | P2 |
| 会话删除无入口 | `DELETE /chat/session/{id}` | `deleteChatSession` 已封装（[api/chat.js:24-26](../frontend/src/api/chat.js)）无 UI 调用 | 未派单（建议并入 W-1 后的前端收尾） | P2 |

## 3. 逐端点矩阵

### 3.1 认证（3/3 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/auth/register | [auth.py:24](../routers/auth.py) | index.js `register` | Register.vue | 已接入 |
| POST /api/auth/login | [auth.py:45](../routers/auth.py) | index.js `login` | Login.vue | 已接入 |
| GET /api/auth/me | [auth.py:72](../routers/auth.py) | index.js `getCurrentUser` | Dashboard / Diet / Sport | 已接入 |

### 3.2 健康数据（7/8 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/health/records | [health.py:26](../routers/health.py) | health.js `createHealthRecord` | HealthRecord.vue（含 OCR 草稿确认入库） | 已接入；K-1 补自动预警 |
| GET /api/health/records | [health.py:35](../routers/health.py) | health.js `getHealthRecords` | Dashboard.vue:713 / HealthRecord.vue | 已接入 |
| GET /api/health/records/{id} | [health.py:43](../routers/health.py) | health.js `getHealthRecord` | 无 | 仅封装（P2） |
| DELETE /api/health/records/{id} | [health.py:52](../routers/health.py) | health.js `deleteHealthRecord` | HealthRecord.vue | 已接入 |
| GET /api/health/analysis/latest | [health.py:61](../routers/health.py) | health.js `getLatestAnalysis` | Dashboard / HealthAnalysis.vue | 已接入 |
| GET /api/health/analysis/history | [health.py:69](../routers/health.py) | health.js `getAnalysisHistory` | HealthAnalysis.vue | 已接入 |
| GET /api/health/rating/latest | [health.py:77](../routers/health.py) | health.js `getLatestRating` | wellness.js / Dashboard / HealthRecord | 已接入 |
| POST /api/health/reports/ocr | [health.py:99](../routers/health.py) | health.js `ocrHealthReport` | HealthRecord.vue | 已接入（草稿→确认入库） |

注：`GET /health/rating/history`（7/30 天）为 K-2 待新增端点，当前不存在。

### 3.3 饮食（7/11 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/food/foods | [food.py:30](../routers/food.py) | food.js `createFood` | DietManagement.vue | 已接入 |
| GET /api/food/foods | [food.py:39](../routers/food.py) | food.js `getFoods` | DietManagement.vue | 已接入 |
| GET /api/food/foods/{id} | [food.py:49](../routers/food.py) | food.js `getFood` | 无 | 仅封装（P2） |
| PUT /api/food/foods/{id} | [food.py:58](../routers/food.py) | food.js `updateFood` | 无 | 仅封装（P2） |
| DELETE /api/food/foods/{id} | [food.py:68](../routers/food.py) | 无 | 无 | 未封装（P2，自定义食物删除） |
| POST /api/food/records | [food.py:77](../routers/food.py) | food.js `createFoodRecord` | DietManagement.vue | 已接入 |
| GET /api/food/records | [food.py:86](../routers/food.py) | food.js `getFoodRecords` | DietManagement.vue | 已接入 |
| GET /api/food/records/stats | [food.py:96](../routers/food.py) | food.js `getFoodStats` | DietManagement.vue | 已接入 |
| DELETE /api/food/records/{id} | [food.py:106](../routers/food.py) | food.js `deleteFoodRecord` | DietManagement.vue:527 | 已接入 |
| POST /api/food/recognize | [food.py:115](../routers/food.py) | food.js `recognizeFoodImage` | DietManagement.vue | 已接入（草稿→确认入库） |
| POST /api/food/custom | [food.py:133](../routers/food.py) | food.js `createCustomFood` | DietManagement.vue | 已接入 |

### 3.4 运动（6/9 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/sport/sports | [sport.py:25](../routers/sport.py) | index.js `createSport` | SportManagement.vue | 已接入 |
| GET /api/sport/sports | [sport.py:34](../routers/sport.py) | index.js `getSports` | SportManagement.vue | 已接入 |
| GET /api/sport/sports/{id} | [sport.py:44](../routers/sport.py) | index.js `getSport` | 无 | 仅封装（P2） |
| PUT /api/sport/sports/{id} | [sport.py:53](../routers/sport.py) | index.js `updateSport` | 无 | 仅封装（P2） |
| DELETE /api/sport/sports/{id} | [sport.py:63](../routers/sport.py) | 无 | 无 | 未封装（P2，自定义运动删除） |
| POST /api/sport/records | [sport.py:72](../routers/sport.py) | index.js `createSportRecord` | SportManagement.vue | 已接入 |
| GET /api/sport/records | [sport.py:81](../routers/sport.py) | index.js `getSportRecords` | wellness.js / SportManagement.vue | 已接入 |
| GET /api/sport/records/stats | [sport.py:91](../routers/sport.py) | index.js `getSportStats` | SportManagement.vue | 已接入 |
| DELETE /api/sport/records/{id} | [sport.py:101](../routers/sport.py) | index.js `deleteSportRecord` | SportManagement.vue | 已接入 |

### 3.5 AI 分析与配置（4/12 已接入；分析 8 个仅封装 → A-1）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/ai/analysis | [ai_analysis.py:61](../routers/ai_analysis.py) | index.js `createAIAnalysis` | 无 | 仅封装（**P0 A-1**） |
| GET /api/ai/analysis/history | [ai_analysis.py:110](../routers/ai_analysis.py) | index.js `getAIAnalysisHistory` | 无 | 仅封装（**P0 A-1**） |
| GET /api/ai/analysis/{id} | [ai_analysis.py:127](../routers/ai_analysis.py) | index.js `getAIAnalysis` | 无 | 仅封装（**P0 A-1**） |
| DELETE /api/ai/analysis/{id} | [ai_analysis.py:145](../routers/ai_analysis.py) | index.js `deleteAIAnalysis` | 无 | 仅封装（**P0 A-1**） |
| POST /api/ai/quick-analysis | [ai_analysis.py:166](../routers/ai_analysis.py) | index.js `quickHealthAnalysis` | 无 | 仅封装（P1） |
| POST /api/ai/health-evaluation | [ai_analysis.py:216](../routers/ai_analysis.py) | index.js `getHealthEvaluation` | 无 | 仅封装（P1） |
| POST /api/ai/async-analysis | [ai_analysis.py:303](../routers/ai_analysis.py) | index.js `asyncAIAnalysis` | 无 | 仅封装（P1） |
| GET /api/ai/task/{id} | [ai_analysis.py:343](../routers/ai_analysis.py) | index.js `getTaskStatus` | 无 | 仅封装（P1） |
| GET /api/ai/config | [ai_analysis.py:360](../routers/ai_analysis.py) | index.js `getAiConfig` | AISettings / PersonaCard.vue | 已接入 |
| PUT /api/ai/config | [ai_analysis.py:394](../routers/ai_analysis.py) | index.js `saveAiConfig` | AISettings / PersonaCard.vue | 已接入 |
| DELETE /api/ai/config | [ai_analysis.py:435](../routers/ai_analysis.py) | index.js `deleteAiConfig` | AISettings.vue | 已接入 |
| POST /api/ai/config/test | [ai_analysis.py:445](../routers/ai_analysis.py) | index.js `testAiConfig` | AISettings.vue | 已接入 |

注：AI 分析 8 端点的契约/测试由 K-3 保障；`HealthAnalysis.vue` 当前展示的是规则引擎分析（`/health/analysis/*`），不是 LLM 分析。

### 3.6 健康预警（0/6 已接入 → W-1）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/warning/check | [warning.py:15](../routers/warning.py) | index.js `checkWarnings` | 无 | 仅封装（**P0 W-1**；K-1 后由提交自动触发） |
| GET /api/warning/list | [warning.py:24](../routers/warning.py) | index.js `getWarnings` | 无 | 仅封装（**P0 W-1**） |
| PUT /api/warning/read/{id} | [warning.py:40](../routers/warning.py) | index.js `markWarningAsRead` | 无 | 仅封装（**P0 W-1**） |
| PUT /api/warning/read-all | [warning.py:65](../routers/warning.py) | index.js `markAllWarningsAsRead` | 无 | 仅封装（**P0 W-1**） |
| DELETE /api/warning/{id} | [warning.py:77](../routers/warning.py) | index.js `deleteWarning` | 无 | 仅封装（**P0 W-1**） |
| GET /api/warning/stats | [warning.py:100](../routers/warning.py) | index.js `getWarningStats` | 无 | 仅封装（**P0 W-1**，未读徽标） |

注：后端预警闭环完整（含心理交叉预警，M-LOGIC1），缺口纯在前端；W-1 不改后端。

### 3.7 舌诊（5/7 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/tongue/upload | [tongue.py:23](../routers/tongue.py) | index.js `uploadTongueImage` | stores/tongue.js → TongueDiagnosis.vue | 已接入 |
| GET /api/tongue/list | [tongue.py:32](../routers/tongue.py) | index.js `getTongueList` | stores/tongue.js | 已接入 |
| GET /api/tongue/latest/result | [tongue.py:42](../routers/tongue.py) | index.js `getLatestTongueResult` | stores/tongue.js | 已接入 |
| GET /api/tongue/stats/summary | [tongue.py:75](../routers/tongue.py) | index.js `getTongueStats` | 无 | 仅封装（P2） |
| GET /api/tongue/image/{id} | [tongue.py:83](../routers/tongue.py) | index.js `getTongueImage` | TongueDiagnosis.vue | 已接入 |
| GET /api/tongue/{id} | [tongue.py:93](../routers/tongue.py) | index.js `getTongueDetail` | TongueDiagnosis.vue | 已接入 |
| DELETE /api/tongue/{id} | [tongue.py:102](../routers/tongue.py) | index.js `deleteTongueRecord` | 无 | 仅封装（P2） |

### 3.8 聊天（4/7 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/chat/session | [chat.py:94](../routers/chat.py) | chat.js `createChatSession` | ChatView.vue | 已接入 |
| GET /api/chat/sessions | [chat.py:117](../routers/chat.py) | chat.js `getChatSessions` | ChatView.vue | 已接入 |
| GET /api/chat/session/{id}/messages | [chat.py:138](../routers/chat.py) | chat.js `getChatMessages` | ChatView.vue | 已接入 |
| POST /api/chat/session/{id}/message | [chat.py:156](../routers/chat.py) | chat.js `sendChatMessage` | 无（v1 遗留封装，前端只走流式） | 仅封装（P2） |
| POST /api/chat/session/{id}/stream | [chat.py:207](../routers/chat.py) | stream.js `streamChatMessage` | ChatView.vue（主路径，safety→delta*→done\|error） | 已接入 |
| POST /api/chat/session/{id}/tongue-context | [chat.py:296](../routers/chat.py) | chat.js `addTongueContext` | 无 | 仅封装（**P2 CHAT-1**） |
| DELETE /api/chat/session/{id} | [chat.py:337](../routers/chat.py) | chat.js `deleteChatSession` | 无 | 仅封装（P2，未派单） |

### 3.9 心理（7/7 已接入）

| 端点 | 路由证据 | 前端封装 | UI 调用 | 状态 |
|---|---|---|---|---|
| POST /api/mental/mood | [mental.py:39](../routers/mental.py) | mental.js `createMentalRecord` | MoodCheckIn.vue | 已接入（每日一条 upsert） |
| GET /api/mental/mood | [mental.py:56](../routers/mental.py) | mental.js `getMentalRecords`（别名 `getMentalMood`） | wellness.js / MentalView.vue | 已接入 |
| GET /api/mental/trend | [mental.py:65](../routers/mental.py) | mental.js `getMentalTrend` | Dashboard / MentalView.vue | 已接入 |
| GET /api/mental/scales | [mental.py:74](../routers/mental.py) | mental.js `getMentalScales` | MentalView.vue | 已接入 |
| GET /api/mental/scales/history | [mental.py:80](../routers/mental.py) | mental.js `getMentalAssessments`（别名 `getMentalScaleHistory`） | MentalView.vue | 已接入 |
| POST /api/mental/scales/{type}/submit | [mental.py:92](../routers/mental.py) | mental.js `createMentalAssessment`（别名 `submitMentalScale`） | ScaleRunner.vue | 已接入；K-1 补自动预警 |
| GET /api/mental/summary | [mental.py:121](../routers/mental.py) | mental.js `getMentalSummary` | wellness.js / MentalView / ChatView / Dashboard / AISettings | 已接入 |

### 3.10 探活

| 端点 | 证据 | 用途 |
|---|---|---|
| GET /api/health | [main.py](../main.py)（`health_check`） | 部署验证（README「5. 验证」使用） |

## 4. 复核方法（可复现）

1. 后端路由表：`uv run python -c "from main import app; ..."` 枚举 `app.routes`（需设 `SECRET_KEY`），共 71 个 `/api` 路由。
2. 前端封装：`frontend/src/api/*.js` 中 `http.get/post/put/delete` 调用逐一对照。
3. UI 调用链：在 `frontend/src`（排除 `api/`）grep `api.<方法名>` 与别名（mental.js 尾部有 v1 别名导出）。
4. 本文档只描述已实现功能；「待补」均对应本轮派单任务或明确标注未派单。

## 5. 校准记录

| 日期 | 基线 | 说明 |
|---|---|---|
| 2026-11-18 | main `ef6c68f`（对齐 `a967496`） | C-1 首轮：43 已接入 / 25 仅封装 / 2 未封装 / 1 探活 |
| 待补 | P0（W-1/A-1/K-1）合并后 | 二次校准：更新预警/AI 分析状态、K-2 新端点、README 功能段 |