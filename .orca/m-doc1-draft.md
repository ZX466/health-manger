# M-DOC1 文档骨架（草稿 · 未定稿）

> 状态：已认领（2026-11-15 16:55）；第三轮对齐完成——已按 M-API2/M-PERF3/M-SEC1 最新口径更新（只改文档，不依赖合并）。
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
- 合并后复测（2026-11-15 19:20，含 M-DB1/M-API1/M-PERF1/2/M-LOGIC1）：**131 passed**（40.34s）；前端自基线无变更，构建结论沿用。迁移链 head 现为 `9f1a2b3c4d5e`（M-DB1）。
- 最新基线（各方实测，定稿时以本树复测为准）：main **137 passed**（A01 修复后）；Codex 收尾树（main 6397764 + M-SEC1）**198 passed**（60.89s，安全 61/61）；Pi 合并树（main 6397764 + M-PERF3/be3bd61）**137 passed**（35.38s，cline 复测）。
- 环境踩坑（重要）：uv 默认选最新 Python（本机 3.13/3.15），pydantic-core 2.14.6 无 3.13 wheel 会源码构建失败；
  必须 `uv venv --python 3.11 --clear`（uv 0.12.3 替换已有 venv 必须 --clear），再 `uv pip install -r requirements.txt`（清华镜像可用）。
  `uv run` 只同步 pyproject 的 dev 组（pip-audit），不装 requirements.txt。

## 3. 已裁决口径 + 三任务最新契约（第三轮对齐）

**统一裁决（2026-11-15 20:30）**
1. `persona_style` 仅 `humorous | clinical`，默认 `humorous`；高风险/危机后端强制严肃关怀，前端同步隐藏玩梗。
2. SSE `safety.level` 仅 `normal | elevated | high`（Codex `RiskState`）；`caution/crisis` 作废。
3. 危机资源为对象列表，消费方按字段格式化，禁止 `join(dict)`。

**M-SEC1（Codex `6c77022`，cline 评审 pass；收尾 `243433c` 全量 198 passed，待合 main）**
4. `RiskState(level, reasons, crisis)` frozen；`assess_user_risk` 近 30 天每类最新（时间 desc + id desc tie-break、排除未来记录、按 user_id 隔离）；Q9 三重兜底（crisis_flag OR 严格 answers 校验 Q9>0 OR 总分≥20）；GAD-7 ≥15 high / 10–14 elevated；评级危险 high+crisis、较差 elevated；未读 danger elevated；无数据 normal；reasons 固定中文短句、不含用户原文、不读心理笔记。
5. `build_system_prompt`：high 或 crisis → **完全丢弃 base** 返回严肃关怀 Prompt（禁调侃/非诊断/学校心理咨询中心+精神卫生中心/120/110/不追问自伤细节/不承诺绝对保密）；正常 → base + 医疗边界 + 人设；未知人设安全降级 clinical。
6. `crisis_resources()` 仅调用时读 `MENTAL_HOTLINE`/`CAMPUS_COUNSELING`；热线 fullmatch 格式校验（拒 URL/文本/超长，宁拒勿截断）；校园说明剥离 Unicode C 类字符 + 300 字上限；未配置返回通用求助对象（无 phone、全文无数字）；每次返回新对象。

**M-API2（kilo，已合并 main `55184dd`；api-v2.md 为唯一权威口径）**
7. `CrisisResource = {name: str, phone: str|null, description: str}`；服务层未配置时省略 phone 键，API 序列化为 `phone: null`。
8. `ScaleSubmitResponse.resources`：`crisis_flag=false` → `[]`；true → `crisis_resources()`；安全模块缺失 → `[]` 降级（**当前 main 状态**）。`resources=[]` 或 `phone=null` 时前端**仍展示 120/110 + 学校心理咨询中心固定文案**，不因缺配置编造号码。
9. 识餐/OCR 路由已改 `await arecognize_meal/aextract_report`（不阻塞事件循环）；`persona_style` 已接线（`save_config` 透传、缺省不覆盖已存值；GET/PUT 读写；非法值 422；v1 客户端不传行为不变）。
10. `summary.serious_mode` 为保守展示策略：最新 PHQ-9 ≥15 / GAD-7 ≥10 / 评级危险 / crisis_flag 任一（比 safety 的 high 更宽，两口径并存，文档分别表述）。

**M-PERF3（Pi `a4bc6ba`，cline 评审 pass，可连同 `be3bd61` 合并）**
11. 显示文本清洗 `services/text_cleaning.py`（clean_output_text/list）：ANSI OSC/CSI/ESC **整段**抹除、零宽/bidi/C0/C1 剥离、空白折叠、截断；识餐 name ≤50 字、OCR abnormal ≤10 条 ×100 字；与 `sanitize_for_prompt`（输入侧）互补。
12. 非有限数收敛：识餐 NaN/±Inf/非数值 → 默认值（confidence → 0.5）；OCR → null；`json.dumps(allow_nan=False)` 安全。
13. 图片解码顺序修复（`be3bd61`）：格式/像素校验前移到解码前（size 取自文件头），DecompressionBomb 归为「图片尺寸过大」。

## 4. README.md 增补骨架（合并后落笔）

### 4.1 核心功能新增「心理健康」（依赖 M-DB1/M-LOGIC1/M-SEC1/M-FE1）
- 10 秒打卡：情绪 1–5 分 + 压力标签（≤5 项、每项 ≤12 字）+ 睡眠时长 `sleep_hours`（0–16，只记时长不记入睡/起床时间）；每人每天一条，同日重复提交 = 更新。
- 睡眠债：近 7 个有记录日 `Σ max(0, 8 − hours)`；覆盖 <4 天显示「数据不足」。
- PHQ-9 / GAD-7 初筛：题目后端下发（`scale_scoring.SCALES`），0–3 计分；分级 minimal/mild/moderate/moderately_severe/severe（GAD-7 无 moderately_severe）；每类每天限 3 次。
- 危机标记：PHQ-9 Q9>0 或总分 ≥20、GAD-7 ≥15 → `crisis_flag=true`，后端强制，前端必须展示危机资源、不得隐藏。
- 危机资源：只读环境变量 `MENTAL_HOTLINE` / `CAMPUS_COUNSELING`（默认空，不编造号码）；热线格式校验宁拒勿截断、校园说明 ≤300 字去控制字符；**未配置或 phone=null 时前端仍展示 120/110 + 学校心理咨询中心固定文案**。
- 风险评估与严肃模式：后端 `assess_user_risk`（近 30 天每类最新、Q9 三重兜底）输出 normal/elevated/high；high/crisis 强制严肃关怀 Prompt（完全覆盖原人设）；`summary.serious_mode` 为保守展示策略（PHQ-9 ≥15 / GAD-7 ≥10 / 评级危险 / crisis_flag 任一）。
- 双模式聊天人设：`persona_style` = humorous（轻松懂梗）/ clinical（专业克制），默认 humorous；高风险/危机后端强制严肃关怀 Prompt，前端同步隐藏玩梗文案。
- 前端减压模块（M-FE1 落地后按实际写）：呼吸训练 / 电子木鱼 / 烦恼粉碎机 / 人设卡。
- 免责声明：初筛不构成诊断，AI 不能替代医生。

### 4.2 核心功能新增「拍照识餐」「体检报告 OCR」（依赖 M-PERF2/3/M-API1/2）
- 只返回草稿（`needs_confirm: true`），不写库；识餐确认后 `POST /api/food/custom` 创建 `Food`（`description` 前缀 `[AI估算]`）再走现有餐记录接口；OCR 确认后复用现有健康记录表单。
- 图片管线：最长边 1024、JPEG 质量 85、剥离 EXIF/GPS；≤10MB，jpg/png/webp，PIL 魔数校验；格式/像素校验前置于解码（解压炸弹防护）。
- 输出边界加固（M-PERF3）：显示文本统一清洗（ANSI 转义/零宽/bidi/控制字符去除、空白折叠、截断）；NaN/±Inf 等非有限数收敛为默认值/null，保证响应为合法 JSON。
- 字段口径：识餐 items ≤10、name ≤50 字、grams 0–5000、calories 0–10000、protein/fat/carbs 0–1000、confidence 0–1 默认 0.5、match_food_id 精确→LIKE；OCR 8 字段恒存在（未识别/越界/非有限 → null）、abnormal ≤10 条 ×100 字、confidence 默认 0.5。
- 路由为异步包装（`await`，M-API2），识别请求不阻塞其他请求。

### 4.3 「流式对话」（依赖 M-PERF1/4）
- `POST /api/chat/session/{id}/stream`，`text/event-stream`；事件 `safety → delta* → done|error`；头 `Cache-Control: no-cache`、`X-Accel-Buffering: no`。
- safety 首帧 `{level: normal|elevated|high, crisis: bool, resources: CrisisResource[]}`（M-PERF4 接入后生效；`resources=[]` 或 `phone=null` 时前端仍展示 120/110 + 学校心理咨询中心固定文案）。
- 用户消息先落库；assistant 仅 `done` 后落库；断开即中止上游、丢弃半截回复。

### 4.4 环境变量表新增（与 .env.example 同步）
`MENTAL_HOTLINE`（格式校验：可选 + 前缀，数字/空格/括号/连字符，3–41 字符；非法整体拒绝）、`CAMPUS_COUNSELING`（≤300 字、自动去控制字符），均默认空；`IMAGE_MAX_EDGE=1024`、`IMAGE_JPEG_QUALITY=85`、`PERSONA_STYLE_DEFAULT=humorous`。

### 4.5 结构/迁移/API 表更新
- 迁移链：补 M-DB1 新 revision `9f1a2b3c4d5e`（`down_revision = 8e4f5a6b7c8d`，已实测对称可逆）。
- 项目结构：补 `routers/mental.py`、`routers/_uploads.py`、`services/{mental,safety,image,vision,food_recognition,report_ocr}_service.py`、`services/text_cleaning.py`、新 views/components（以合并后实测为准）。
- API 表补：`/api/mental/*`（mood/trend/scales/scales/{t}/submit/scales/history/summary）、`/api/food/recognize`、`/api/food/custom`、`/api/health/reports/ocr`、`/api/chat/session/{id}/stream`；注明 `ScaleSubmitResponse.resources` 为对象列表（CrisisResource）、AI 配置 GET/PUT 含 `persona_style`。
- 技术栈/测试节：更新实测测试数；明确「M 系列零新增第三方依赖」。

### 4.6 安全特性节增补（合并后落笔）
- 心理危机干预：风险分级（normal/elevated/high）+ 高风险强制严肃 Prompt + 危机资源（环境变量驱动、不编造号码、固定兜底文案）。
- AI 输出边界：显示文本清洗（ANSI/Trojan Source/零宽字符）+ 非有限数收敛 + 识别类草稿需人工确认后才写库。
- 心理数据隐私：风险 reasons 不含用户原文、不读心理笔记；图片 EXIF/GPS 剥离；保留期限/删除流程待产品决定（审计 A05）——**README 不写未实现的合规承诺**。

## 5. .env.example 增补骨架（合并后落笔，不写真实号码）

```dotenv
# ========== 心理健康（M 系列） ==========
# 心理支持热线（可选，默认空；格式：可选 + 前缀 + 数字/空格/括号/连字符，3–41 字符；
# 非法格式整体拒绝不展示；为空时仅显示通用求助文案，不编造号码）
MENTAL_HOTLINE=
# 学校心理咨询中心联系方式（可选，默认空；≤300 字，控制字符自动剥离）
CAMPUS_COUNSELING=

# ========== 图片管线（识餐 / 体检 OCR / 舌诊共用） ==========
# 压缩后最长边像素 / JPEG 质量；输出剥离 EXIF/GPS
IMAGE_MAX_EDGE=1024
IMAGE_JPEG_QUALITY=85

# AI 聊天人设默认风格（humorous | clinical）
PERSONA_STYLE_DEFAULT=humorous
```

## 6. CLAUDE.md / AGENTS.md 更新计划（保留现有协作规则）

- 项目速览补「身心双维」一句；测试数改实测；补视图数 / 路由数 / 模块结构（合并后统计）。
- 常用命令补 `uv run python -m pytest -q` 口径说明（`uv run pytest` 有 sys.path 问题）。
- 其余协作规则不动。

## 7. 定稿检查单

- [ ] M 系列全部合并 main（已合：M-DB1/M-API1/**M-API2**/M-PERF1/2/M-LOGIC1+A01；待合：**M-SEC1**〔Codex complete `243433c`，198 passed，等 Claude/用户集成〕、**M-PERF3+be3bd61**〔cline pass〕、**M-PERF4**〔blocked 等 M-SEC1 合入〕、**M-FE1**〔Claude 未开始〕）
- [ ] `git merge main` 同步本工作树（本轮只改文档不依赖合并；定稿前同步 + 实测）
- [x] §3 口径已裁决并对齐 M-API2/M-PERF3/M-SEC1 最新契约（第三轮）
- [ ] `uv run python -m pytest -q` 实测数字写入 README/CLAUDE/AGENTS
- [ ] `cd frontend && npm run build` 通过
- [ ] 依赖复核仍零新增（否则 blocked）
- [ ] README 无未实现功能；无真实热线号码
- [ ] `git diff --stat` 记录；提交；回 `complete M-DOC1: <hash> / 测试与构建结果`；不合并 main