# 大学生健康管理系统

FastAPI + Vue 3 的大学生身心健康管理 Web 应用：健康记录、饮食运动、AI 分析 / 对话、舌诊、心理空间与健康预警。

## 功能

- **认证**：邀请码注册、JWT 登录。
- **健康记录**：问卷录入、BMI / 血压 / 心率 / 体温预警、综合评级、体检报告 OCR（草稿）。
- **饮食 / 运动**：食物与运动库、记录统计、拍照识餐（草稿）。
- **AI**：健康分析、SSE 流式对话、每用户自定义聊天 / 视觉模型、中医舌诊。
- **心理空间 `/mental`**：情绪打卡、睡眠趋势、PHQ-9 / GAD-7 初筛、危机资源、呼吸环 / 木鱼 / 人设卡。
- **预警**：分级列表、标记已读。

## 示例用户

| 用户 | 情况 | 可以体验 |
|---|---|---|
| 小林 · 大一 | 连续熬夜，情绪 2/5，睡眠 5 小时 | 在 `/mental` 打卡 → 查看睡眠债 → 做 PHQ-9 → 用 4-4-6 呼吸环放松 → 去 `/chat` 聊睡眠 |
| 阿哲 · 大三 | 考研压力大，PHQ-9 第 9 题阳性 | 量表结果标记危机 → 查看 120 / 110 与学校心理中心 → 聊天切换严肃关怀 → Dashboard 显示提醒 |
| 小周 · 大二 | 健身、控制饮食 | 记录三餐和运动 → 查看热量 / 消耗统计与健康评级 → 配置 AI Key 后生成分析建议 |

示例只用于说明功能路径，不对应真实用户；实际数据由各自账号录入。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | FastAPI、SQLAlchemy 2.0、SQLite、Alembic、JWT、bcrypt |
| 前端 | Vue 3、Vite 5、Vue Router 4、Pinia、Axios |
| AI | 默认智谱 GLM-4.5-Air；舌诊默认火山 ARK 豆包视觉模型，支持用户覆盖 |
| 测试 | pytest（198 个用例）、pytest-asyncio、pytest-cov |

前端使用 modern-minimal 设计令牌、统一描线图标和响应式侧栏 / 移动端抽屉导航。

## 快速开始

### 环境要求

- Python 3.9+
- [uv](https://docs.astral.sh/uv/)
- Node.js 16+（开发模式和构建前端时需要）

### 安装依赖

```powershell
cd E:\zxdevelop\project1

# 首次运行；已有 .venv 可跳过
uv venv .venv
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt

cd frontend
npm install
cd ..

Copy-Item .env.example .env
```

macOS / Linux 将激活命令换成 `source .venv/bin/activate`，复制命令换成 `cp`。

### 配置 `.env`

至少填写 `SECRET_KEY`；需要注册时再配置 `INVITE_CODES`。

| 变量 | 必填 | 说明 |
|---|---|---|
| `SECRET_KEY` | 是 | JWT 签名密钥，至少 32 字符，禁止使用示例弱密钥 |
| `INVITE_CODES` | 注册时必填 | 逗号分隔的邀请码；未配置则禁止注册 |
| `ZHIPU_API_KEY` | 否 | 默认聊天 / 健康分析模型 |
| `ARK_API_KEY` | 否 | 舌诊视觉模型 |
| `ARK_MODEL_ID` | 否 | 舌诊模型 ID，默认 `doubao-seed-1-6-vision-250815` |
| `MENTAL_HOTLINE` / `CAMPUS_COUNSELING` | 否 | 心理危机资源，未配置不编造号码 |

生成密钥：

```powershell
uv run python -c "import secrets; print(secrets.token_hex(32))"
```

登录后也可以在「AI 设置」页按用户配置聊天 / 视觉模型；用户配置优先于 `.env`。

### 启动

**生产模式（端口 8420，FastAPI 同时托管前端）**

```powershell
cd frontend
npm run build
cd ..

uv run alembic upgrade head
uv run uvicorn main:app --port 8420
```

访问 <http://localhost:8420>。

**开发模式（前后端热更新）**

```powershell
# 终端 1：后端
uv run uvicorn main:app --reload --port 8420

# 终端 2：前端
cd frontend
npm run dev
```

访问 <http://localhost:3000>。Vite 会把 `/api` 代理到 8420。

SQLite 首次启动会自动建表；`alembic upgrade head` 用于确保数据库结构是最新的。

### 初始化数据

```powershell
uv run python scripts/init_data.py          # 食物 / 运动基础数据
uv run python scripts/create_test_user.py   # 测试用户：testuser / test123
```

### 验证

```powershell
curl http://localhost:8420/api/health
# 应返回 {"status":"healthy"}

# 接口文档
# http://localhost:8420/docs
# http://localhost:8420/redoc
```

## 心理安全

- PHQ-9 Q9 > 0 或总分 ≥ 20、GAD-7 ≥ 15 时标记 `crisis_flag`；前端始终展示危机资源，不隐藏。
- 高风险 / 危机时聊天强制严肃关怀 Prompt，隐藏木鱼和玩梗人设，但不阻止求助。
- 危机资源来自 `MENTAL_HOTLINE` / `CAMPUS_COUNSELING`；未配置时固定展示 120 / 110 + 学校心理咨询中心，不编造号码。

## API

完整参数与响应见 `/docs`（Swagger UI）或 `/redoc`。

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
tests/                    pytest 测试（198 个）
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
