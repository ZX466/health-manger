# 今日一件小事（Daily Action）实施方案

> 2026-11-21 立项。基于健康周报之后的“日常闭环”缺口，先做规则驱动的每日微行动，不做自由生成式 AI。
> 状态：已上线（2026-11-21）。实现后已完成只读评审，修复 UTC/本地日边界、安全行动展示、空响应防御、并发完成与迁移索引问题；已同步 README / feature-coverage。

## 1. 背景与目标

健康周报解决“一周回看”，但学生每天打开系统时仍缺少一个明确的下一步。调研显示：

- 大学生数字健康干预总体有效，但依从性是瓶颈；8–16 周、个性化、提醒/监测类功能效果更好。
- 学生更看重自助追踪与个性化，而不是更多科普内容。
- 校园场景（食堂、校园跑、校医院、心理中心）是差异化来源，但不能做医疗诊断。

因此新增「今日一件小事」：每天只给 1 条规则生成的小行动，完成后可回看近 7 天完成天数，并与健康周报形成闭环。

## 2. 范围

### 做

- 每个用户每天 1 条行动，首次打开时生成并持久化；当天重复打开不变。
- 行动由现有健康/心理/饮食/运动数据规则生成，不调用 AI，不新增外部依赖。
- 支持标记完成；近 7 天完成天数统计。
- 高危/危机状态返回安全行动，不显示“完成打卡”；Dashboard 严肃模式复用求助横幅，非严肃模式展示安全关怀卡，避免安全信号被完全吞掉。
- Dashboard 顶部展示卡片，移动端可用。

### 不做（本期）

- 不做推送通知、连续打卡惩罚、排行榜、虚拟宠物、组队 PK。
- 不做 AI 生成文案；后续可在规则结果上做措辞润色。
- 不做校园食堂/校园跑真实数据对接。
- 不修改健康评分算法、周报算法。

## 3. 数据模型

新增 `DailyAction`（`models.py`）：

| 字段 | 类型 | 说明 |
|---|---|---|
| id | int PK | |
| user_id | FK users.id, not null | |
| action_date | Date, not null | 自然日 |
| action_key | String(32), not null | checkin/sleep/move/meal/breathe/rest/care |
| kind | String(16), default `action` | action / rest / safety |
| title | String(80), not null | |
| description | String(240), not null | |
| reason | String(240), not null | 数据依据 |
| cta_label | String(40), not null | |
| cta_path | String(120), not null | 前端路由 |
| can_complete | Boolean, default True | 安全行动为 False |
| completed_at | DateTime, nullable | |
| created_at | DateTime, default UTC | |

约束与索引：

- `UniqueConstraint("user_id", "action_date", name="uq_daily_action_user_date")`
- `Index("ix_daily_action_user_date", "user_id", "action_date")`

迁移：`alembic/versions/c3d4e5f6a7b8_add_daily_actions.py`，`down_revision = "b2c3d4e5f6a7"`。upgrade 建表（先 inspect，已存在则跳过），downgrade 删表。

## 4. API 契约

前缀：`/api/daily-action`，全部需要登录。

### GET `/api/daily-action/today`

首次调用生成当天行动；之后返回同一条。

```json
{
  "id": 1,
  "action_date": "2026-11-21",
  "action_key": "sleep",
  "kind": "action",
  "title": "今晚 23:30 前放下手机",
  "description": "不用一次改很多，今晚比昨晚早 30 分钟就够。",
  "reason": "最近一次睡眠 5.0h，离 7h 还差一点",
  "cta_label": "去记睡眠",
  "cta_path": "/health-record",
  "can_complete": true,
  "completed": false,
  "completed_at": null,
  "week_completed": 2
}
```

### POST `/api/daily-action/{id}/complete`

- 只能完成自己的行动；他人/不存在 → 404。
- `can_complete=False`（安全行动）→ 400 `"该行动不需要打卡"`。
- 已完成后重复调用 → 200，返回同一结果（幂等）。
- 返回结构与 GET 相同，`completed=true`，`completed_at` 为 ISO 时间。

### 错误

- 未登录：401（现有鉴权）。
- 行动不存在/越权：404 `"行动不存在"`。
- 安全行动：400。

## 5. 规则（按优先级，第一个命中即返回）

| 优先级 | 条件 | action_key | title | description | cta |
|---|---|---|---|---|---|
| 1 | 最近 7 天存在 `ScaleAssessment.crisis_flag=True` | care | 先联系学校心理咨询中心 | 这一周先把自己照顾好。需要时联系学校心理咨询中心；如有危机想法，请拨打 120 或 12356。 | `/mental`，`kind=safety`，`can_complete=false` |
| 2 | 今天没有 HealthRecord 且没有 MentalRecord | checkin | 花 1 分钟，给今天的状态打个分 | 不用写很多，一个心情分或一次睡眠记录就够。 | `/mental` |
| 3 | 最近 2 天最新睡眠 < 7h | sleep | 今晚 23:30 前放下手机 | 不用一次改很多，今晚比昨晚早 30 分钟就够。 | `/health-record` |
| 4 | 近 7 天运动总时长 < 150 分钟 | move | 课间快走 20 分钟 | 不用换衣服去健身房，绕教学楼快走一圈也算。 | `/sport-management` |
| 5 | 近 7 天饮食记录天数 < 4 | meal | 拍一餐，记录今天的饮食 | 只拍一餐也行，先让饮食有迹可循。 | `/diet-management` |
| 6 | 近 7 天心情均值 < 3（有打卡） | breathe | 做一轮 1 分钟呼吸 | 先停 60 秒，把注意力放回呼吸上。 | `/mental` |
| 7 | 以上都不命中 | rest | 给自己留 10 分钟不赶任务的空白 | 这周记录得不错，恢复也是健康的一部分。 | `/weekly-report`，`kind=rest` |

规则说明：

- 睡眠取最近 2 天内最新的 HealthRecord.sleep_hours，缺失时用 MentalRecord.sleep_hours；同一天优先体检。
- 运动/饮食/心情都按包含今天的近 7 天统计。
- 高危优先，不再生成“打卡”类行动；Dashboard 进入严肃模式时整卡不挂载，由求助横幅承担；非严肃模式（如近期危机但最新量表正常）仍渲染安全关怀卡，避免既无行动卡也无横幅。
- `week_completed`：近 7 天 `completed_at` 非空的 `action_date` 去重计数（0–7）。

## 6. 后端文件

- `models.py`：新增 `DailyAction`。
- `alembic/versions/c3d4e5f6a7b8_add_daily_actions.py`。
- `services/daily_action_service.py`：
  - `generate_daily_action(db, user_id, *, today: date | None = None) -> dict`
  - `complete_daily_action(db, user_id, action_id: int) -> dict`
  - 内部 `_pick_action(...)` 便于单测；返回纯 dict，不依赖 FastAPI。
- `schemas.py`：`DailyActionResponse`。
- `routers/daily_action.py`：GET/POST，`Depends(get_current_user)`。
- `main.py`：include router。
- `tests/test_daily_action.py`：至少覆盖空数据、低睡眠、低运动、危机、幂等、越权、周完成计数。
- 不改 `services/weekly_report_service.py`；后续可在周报增加“完成 X 天”字段，另立任务。

## 7. 前端文件

- `frontend/src/api/dailyAction.js`：
  - `getTodayAction()` → GET `/daily-action/today`
  - `completeDailyAction(id)` → POST `/daily-action/${id}/complete`
- `frontend/src/components/DailyActionCard.vue`：
  - 自取数据；失败静默隐藏，不阻塞 Dashboard。
  - `kind=safety`：Dashboard 严肃模式下整卡不挂载；否则渲染安全关怀卡（红色态、无完成按钮、保留 `/mental` CTA）。
  - 标题、描述、reason、CTA、完成按钮；完成后显示“已完成”与近 7 天完成天数。
  - 图标：checkin=calendar, sleep=moon, move=activity, meal=meal, breathe=heart, rest=sparkles。
  - 使用 v21 设计令牌；移动端 390px 不横向溢出。
- `frontend/src/views/Dashboard.vue`：
  - import/注册组件；在 warning 链接之后、dashboard-grid 之前放 `<DailyActionCard v-if="!mentalSerious" />`。
  - 不改动现有 CompanionCard / Persona / 周报入口等未提交改动。

## 8. 验收

- 后端：`uv run python -m pytest tests/test_daily_action.py -q`；全量 `uv run python -m pytest -q`。
- 前端：`cd frontend && npm test`、`npm run build`。
- lint：`uv run ruff check .`。
- 手工：空数据用户、低睡眠用户、危机用户三种 Dashboard；GET 两次同一天返回同一 id；完成后刷新仍为已完成；周完成天数正确。
- 文档：README 功能与测试数、`docs/feature-coverage.md` 模块/端点/校准记录同步。

## 9. Agent 分工

- **Agent A（backend）**：模型、迁移、service、schema、router、main、测试；只改后端与测试。
- **Agent B（frontend）**：API、DailyActionCard、Dashboard 接入；只改前端。
- **Agent C（reviewer）**：A/B 完成后只读评审 + 跑全量测试/构建，输出问题清单，不直接改代码。
- 主会话：合并、修复 review 问题、文档、记忆、最终验证。

## 10. 风险

- 并发首次 GET 可能撞唯一约束：service 捕获 `IntegrityError` 后 rollback 并重新查询当天记录。
- 日期使用本地自然日，与周报一致；不要用 UTC 日期切日。
- 危机判断只看近 7 天，可能重复返回安全行动；这是有意为之，优先安全。
- 不能把“完成行动”做成惩罚性 streak；本期只展示近 7 天完成天数。
