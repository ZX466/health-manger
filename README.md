# 大学生健康管理系统

FastAPI + Vue 3 的大学生身心健康管理 Web 应用：健康记录、饮食运动、AI 分析 / 对话、舌诊、心理空间与健康预警。

## 功能

- **认证**：邀请码注册、JWT 登录。
- **健康记录**：问卷录入、BMI / 血压 / 心率 / 体温预警、综合评级；体检单拍照识别后先进入核对面板，逐项确认再填入表单（OCR 只出草稿，不直接提交）。
- **饮食 / 运动**：食物与运动库、记录统计、近 7 天摄入 / 消耗图、拍照识餐（草稿，人工确认后入库）。
- **AI**：每用户自定义聊天 / 视觉模型、SSE 流式对话（含安全首帧）、中医舌诊；健康分析页支持深度解读、快速分析、规则 + AI 综合评价与后台异步分析，可查看 / 删除历史，并区分缺 Key、无数据、限流与超时；身体问诊可一键引用最近舌诊。首页评分支持今日 / 近 7 天 / 近 30 天真实切换。
- **心理空间 `/mental`**：情绪打卡、睡眠趋势、PHQ-9 / GAD-7 初筛、危机资源、呼吸环 / 木鱼 / 人设卡；高压时自动进入关怀模式并隐藏玩梗工具。
- **设置 `/ai-settings`**：每用户 AI 模型与聊天人设；「偏好与提醒 / 数据隐私」目前为视觉占位（标注即将上线，控件禁用）。
- **预警 `/warnings`**：保存健康记录或提交量表后自动检查（也可手动重新检查）；分级列表、未读徽标、标记已读 / 全部已读 / 删除，覆盖血压 / BMI / 心率异常、量表危机、睡眠债、情绪低落。总览页与顶栏同步未读入口。

## 示例用户

| 用户 | 情况 | 可以体验 |
|---|---|---|
| 小林 · 大一 | 连续熬夜，情绪 2/5，睡眠 5 小时 | 在 `/mental` 打卡 → 查看睡眠债 → 做 PHQ-9 → 用 4-4-6 呼吸环放松 → 去 `/chat` 聊睡眠 |
| 阿哲 · 大三 | 考研压力大，PHQ-9 第 9 题阳性 | 量表结果标记危机 → 查看 120 / 110 与学校心理中心 → 聊天切换严肃关怀 → Dashboard 显示提醒 |
| 小周 · 大二 | 健身、控制饮食 | 记录三餐和运动 → 查看热量 / 消耗统计与健康评级 → 配置 AI Key 后在 `/chat` 获取建议，或在 `/health-analysis` 生成 AI 解读 |

示例只用于说明功能路径，不对应真实用户；实际数据由各自账号录入。

运行 `uv run python scripts/seed_demo_users.py` 可创建这三位演示用户（密码均为 `demo1234`）及对应健康、饮食、运动和心理数据。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI、SQLAlchemy 2.0、SQLite、Alembic、JWT、bcrypt |
| 前端 | Vue 3、Vite 5、Vue Router 4、Pinia、Axios |
| AI | 默认智谱 GLM-4.5-Air；舌诊默认火山 ARK 豆包视觉模型，支持用户覆盖 |
| 测试 | pytest（292 个用例）、pytest-asyncio、pytest-cov；前端 node:test（31 个） |

前端采用「临床编辑部」视觉：冷白纸面、墨黑大字、单一电光蓝强调色、细分隔线与等宽数据标签（`v21.css` 设计令牌）。断点覆盖 1024 / 768 / 560：桌面为编号侧栏，≤1024px 收为图标轨，≤768px 改用底部 Tab + 「更多」抽屉，≤560px 进一步压缩排版；舌诊在 ≥1181px 为控制 / 预览 / 结果三栏同屏。

## 快速开始

### 环境要求

- Python 3.11+（CI 与 ruff 目标版本均为 3.11）
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+（CI 使用 20；构建或开发前端时需要）

### 1. 安装依赖（首次）

```powershell
cd E:\zxdevelop\project1

uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt

cd frontend
npm install
cd ..
```

macOS / Linux 将激活命令换成 `source .venv/bin/activate`。

### 2. 配置 `.env`（首次）

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

至少填写 `SECRET_KEY`；需要注册时再配置 `INVITE_CODES`。

| 变量 | 必填 | 说明 |
|---|---|---|
| `SECRET_KEY` | 是 | JWT 签名密钥，至少 32 字符，禁止使用示例弱密钥 |
| `INVITE_CODES` | 注册时必填 | 逗号分隔的邀请码；未配置则禁止注册 |
| `MENTAL_HOTLINE` / `CAMPUS_COUNSELING` | 否 | 心理危机资源，未配置不编造号码 |
| `FRONTEND_URL` | 否 | CORS 主白名单（默认 `http://localhost:3000`）；开发时本机任意端口已由 `allow_origin_regex` 放行 |
| `PORT` | 否 | 后端端口示例值（默认 8420），实际以 `uvicorn --port` 为准 |

生成密钥：

```powershell
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

AI 模型（供应商 / Base URL / 模型 ID / API Key）在登录后的「AI 设置」页按用户配置，不写入 `.env`。自定义 Base URL 必须同时配置该服务的独立 API Key；服务级 `ZHIPU_API_KEY` 只用于默认智谱地址，不会发送到自定义主机。

### 3. 初始化数据库（首次）

```powershell
uv run alembic upgrade head
uv run python scripts/init_data.py

# 可选：三位演示用户（小林 / 阿哲 / 小周，密码均为 demo1234）
uv run python scripts/seed_demo_users.py
```

SQLite 数据库会自动创建；迁移用于确保表结构最新。

### 4. 启动

**生产模式（端口 8420，FastAPI 同时托管前端）**

```powershell
cd frontend
npm run build
cd ..

uv run uvicorn main:app --port 8420
```

访问 <http://localhost:8420>。首次运行或前端改动后需要重新执行 `npm run build`。

**开发模式（前后端热更新）**

```powershell
# 终端 1：后端
uv run uvicorn main:app --reload --port 8420

# 终端 2：前端
cd frontend
npm run dev
```

启动后终端会打印本次的随机四位数端口（4000–7999），访问 `http://localhost:<端口>`。Vite 会把 `/api` 代理到 8420。需要固定端口时用 `npm run dev -- --port 5173`（后端 CORS 已放行本机任意端口）。

### 5. 验证

```powershell
Invoke-RestMethod http://localhost:8420/api/health
# 应返回 status = healthy
```

接口文档：<http://localhost:8420/docs> 或 <http://localhost:8420/redoc>。

## 心理安全

- PHQ-9 Q9 > 0 或总分 ≥ 20、GAD-7 ≥ 15 时标记 `crisis_flag`；前端始终展示危机资源，不隐藏。
- 高风险 / 危机时聊天强制严肃关怀 Prompt，隐藏木鱼和玩梗人设，但不阻止求助。
- 危机资源来自 `MENTAL_HOTLINE` / `CAMPUS_COUNSELING`；未配置时固定展示 120 / 110 + 学校心理咨询中心，不编造号码。

## API

完整参数与响应见 `/docs`（Swagger UI）或 `/redoc`。71 个业务端点的前后端覆盖矩阵与缺口见 [docs/feature-coverage.md](docs/feature-coverage.md)。

| 前缀 | 功能 |
|---|---|
| `/api/auth` | 注册、登录、当前用户 |
| `/api/health` | 健康记录、分析、评级、体检报告 OCR |
| `/api/food` | 食物库、饮食记录、拍照识餐 |
| `/api/sport` | 运动库、运动记录与统计 |
| `/api/ai` | AI 分析、异步任务、用户 AI 配置 |
| `/api/tongue` | 舌象上传、记录、图片访问 |
| `/api/chat` | 会话、消息、SSE 流式对话 |
| `/api/mental` | 情绪打卡、趋势、量表、心理摘要 |
| `/api/warning` | 预警检查、列表、已读、统计 |

## 项目结构

```text
main.py                   FastAPI 入口
models.py / schemas.py    ORM 模型 / Pydantic 模式
auth.py / settings.py     认证 / 集中配置
routers/                  HTTP 路由
services/                 业务逻辑（健康、心理、AI、安全等）
alembic/                  数据库迁移
scripts/                  初始化数据 / 测试用户
tests/                    pytest 测试（292 个）
frontend/src/             Vue 页面、组件、路由、API、样式
static/                   前端构建产物
uploads/                  用户上传文件
```

## 测试

```powershell
uv run python -m pytest -q
uv run python -m pytest --cov=. --cov-report=term-missing -q
uv run ruff check .
```

> 使用 `uv run python -m pytest`，不要直接用 `uv run pytest`，避免 `sys.path` 问题。

## 安全要点

- `SECRET_KEY` 启动时校验长度和弱密钥；密码 bcrypt 加密，JWT 含 `iat/iss/aud`，登录按 IP + 用户名限流。
- 请求参数使用 Pydantic 校验，数据库访问使用 SQLAlchemy 参数化查询；含 prompt 注入清洗。
- 上传文件限制 10MB，UUID 文件名 + 扩展名白名单 + PIL 魔数校验，重新编码并剥离 EXIF/GPS。
- 每用户 AI Key 使用 Fernet 加密存储，接口只返回掩码；`.env` 不入库。
- 识餐 / OCR 只返回草稿，人工确认后才写库；心理风险数据按用户隔离并最小化。

## 健康标准

| 项目 | 标准 |
|---|---|
| BMI | < 18.5 偏瘦；18.5–24 正常；24–28 偏胖；≥ 28 肥胖 |
| 血压（mmHg） | 正常 90–120 / 60–80；偏高 120–139 / 80–89；高血压 ≥ 140 / 90 |
| 综合评级 | 优秀 95–100；良好 80–94；中等 60–79；较差 40–59；危险 0–39 |

## License

本项目仅供学习和开发使用。
