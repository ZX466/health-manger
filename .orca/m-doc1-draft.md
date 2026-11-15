# M-DOC1 文档骨架（草稿 · 未定稿）

> 状态：已认领（2026-11-15 16:55，见 talking.txt accept）。本文件是 README / .env.example / CLAUDE.md / AGENTS.md 的合并前骨架。
> 口径：M 系列全部完成并合并 main 后按本骨架定稿，**最终数字必须实测**；合并前 README 不写未实现功能。
> 负责人：cline（依赖/配置/文档）；评审：Claude。定稿后本草稿可删。

## 1. 依赖核对（2026-11-15 已完成）

- 方法：main + 5 工作树逐一 `git diff main -- requirements.txt frontend/package.json` 与 `git status --short`（同路径）。
- 结果：**全部零差异 → 零新增第三方依赖**（后端 19 项、前端 4 deps + 2 devDeps 均未变）。
- Pillow 已在 `requirements.txt`（`pillow>=10.0.0`），图片管线（M-PERF2）复用即可。
- 结论：**PASS**。后续任何合并若引入新依赖，立即在本板 `blocked`。

## 2. 基线实测（2026-11-15 17:05，main b9a033a，本工作树 ZX466/cline）

- 后端：`uv run python -m pytest -q` → **112 passed, 1 warning（30.04s）**；Python 3.11.15 + pytest 9.2.0。
- 前端：`npm ci && npm run build` → **通过（vite build 1.19s，产物输出 ../static/，git 无产物扰动）**。
- 当前规模（M 系列前基线）：10 views / 8 routers / 5 Alembic revisions / 13 services。
- 环境踩坑（重要）：uv 默认选最新 Python（本机 3.13/3.15），pydantic-core 2.14.6 无 3.13 wheel 会源码构建失败；
  必须 `uv venv --python 3.11 --clear`（uv 0.12.3 替换已有 venv 必须 --clear），再 `uv pip install -r requirements.txt`（清华镜像可用）。
  `uv run` 只同步 pyproject 的 dev 组（pip-audit），不装 requirements.txt。

## 3. 待 Claude 裁决的口径分叉（定稿前必须收敛）

1. `persona_style` 取值：派单与 Codex M-SEC1 契约 = `humorous | clinical`；kilo `.orca/contracts/api-v2.md` §5 = `humorous | warm | professional | concise`。文档跟随最终实现，需统一。
2. SSE `safety.level`：kilo 契约 §4 = `normal | caution | crisis`；Codex `RiskState.level` = `normal | elevated | high`。同上需统一。

## 4. README.md 增补骨架（合并后落笔）

### 4.1 核心功能新增「心理健康」（依赖 M-DB1/M-LOGIC1/M-SEC1/M-FE1）
- 10 秒打卡：情绪 1–5 分 + 压力标签（≤5 项、每项 ≤12 字）+ 睡眠时长 `sleep_hours`（0–16，只记时长不记入睡/起床时间）；每人每天一条，同日重复提交 = 更新。
- 睡眠债：近 7 个有记录日 `Σ max(0, 8 − hours)`；覆盖 <4 天显示「数据不足」。
- PHQ-9 / GAD-7 初筛：题目后端下发（`scale_scoring.SCALES`），0–3 计分；分级 minimal/mild/moderate/moderately_severe/severe（GAD-7 无 moderately_severe）；每类每天限 3 次。
- 危机标记：PHQ-9 Q9>0 或总分 ≥20、GAD-7 ≥15 → `crisis_flag=true`，后端强制，前端必须展示危机资源、不得隐藏。
- 危机资源：只读环境变量 `MENTAL_HOTLINE` / `CAMPUS_COUNSELING`（默认空，不编造号码）；紧急文案只写 120/110 + 学校心理咨询中心。
- 双模式聊天人设：`persona_style` 默认 humorous；高风险/危机后端强制严肃关怀 Prompt，前端同步隐藏玩梗文案。
- 前端减压模块（M-FE1 落地后按实际写）：呼吸训练 / 电子木鱼 / 烦恼粉碎机 / 人设卡。
- 免责声明：初筛不构成诊断，AI 不能替代医生。

### 4.2 核心功能新增「拍照识餐」「体检报告 OCR」（依赖 M-PERF2/M-API1）
- 只返回草稿（`needs_confirm: true`），不写库；识餐确认后 `POST /api/food/custom` 创建 `Food`（`description` 前缀 `[AI估算]`）再走现有餐记录接口；OCR 确认后复用现有健康记录表单。
- 图片管线：最长边 1024、JPEG 质量 85、剥离 EXIF/GPS；≤10MB，jpg/png/webp，PIL 魔数校验。

### 4.3 「流式对话」（依赖 M-PERF1）
- `POST /api/chat/session/{id}/stream`，`text/event-stream`；事件 `safety → delta* → done|error`；头 `Cache-Control: no-cache`、`X-Accel-Buffering: no`。
- 用户消息先落库；assistant 仅 `done` 后落库；断开即中止上游、丢弃半截回复。

### 4.4 环境变量表新增（与 .env.example 同步）
`MENTAL_HOTLINE`、`CAMPUS_COUNSELING`（默认空）、`IMAGE_MAX_EDGE=1024`、`IMAGE_JPEG_QUALITY=85`、`PERSONA_STYLE_DEFAULT=humorous`。

### 4.5 结构/迁移/API 表更新
- 迁移链：补 M-DB1 新 revision（`down_revision = 8e4f5a6b7c8d`，以 opencode 实测为准）。
- 项目结构：补 `routers/mental.py`、`services/{mental,safety,image,vision,food_recognition,report_ocr}_service.py`、新 views/components（以合并后实测为准）。
- API 表补：`/api/mental/*`（mood/trend/scales/scales/{t}/submit/scales/history/summary）、`/api/food/recognize`、`/api/food/custom`、`/api/health/reports/ocr`、`/api/chat/session/{id}/stream`。
- 技术栈/测试节：更新实测测试数；明确「M 系列零新增第三方依赖」。

## 5. .env.example 增补骨架（合并后落笔，不写真实号码）

```dotenv
# ========== 心理健康（M 系列） ==========
# 心理支持热线（可选，默认空；为空时仅显示通用求助文案，不编造号码）
MENTAL_HOTLINE=
# 学校心理咨询中心联系方式（可选，默认空）
CAMPUS_COUNSELING=

# ========== 图片管线（识餐 / 体检 OCR / 舌诊共用） ==========
# 压缩后最长边像素 / JPEG 质量；输出剥离 EXIF/GPS
IMAGE_MAX_EDGE=1024
IMAGE_JPEG_QUALITY=85

# AI 聊天人设默认风格（取值以最终实现为准，见草稿 §3.1）
PERSONA_STYLE_DEFAULT=humorous
```

## 6. CLAUDE.md / AGENTS.md 更新计划（保留现有协作规则）

- 项目速览补「身心双维」一句；测试数改实测；补视图数 / 路由数 / 模块结构（合并后统计）。
- 常用命令补 `uv run python -m pytest -q` 口径说明（`uv run pytest` 有 sys.path 问题）。
- 其余协作规则不动。

## 7. 定稿检查单

- [ ] M-DB1/M-API1/M-SEC1/M-PERF1/M-PERF2/M-LOGIC1/M-FE1 全部合并 main
- [ ] `git merge --ff-only main`（或 rebase）同步本工作树
- [ ] §3 两处分叉已由 Claude 收敛
- [ ] `uv run python -m pytest -q` 实测数字写入 README/CLAUDE/AGENTS
- [ ] `cd frontend && npm run build` 通过
- [ ] 依赖复核仍零新增（否则 blocked）
- [ ] README 无未实现功能；无真实热线号码
- [ ] `git diff --stat` 记录；提交；回 `complete M-DOC1: <hash> / 测试与构建结果`；不合并 main