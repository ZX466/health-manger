# 大学生健康管理系统

一个用于管理大学生身体健康数据的 Web 应用程序，基于 FastAPI + Vue.js 3 构建，集成中医舌诊 AI 分析。

## 项目简介

本系统旨在帮助大学生管理个人健康数据，提供健康记录、饮食管理、运动管理、AI 健康分析、中医舌诊和预警等功能。前端采用 modern-minimal 设计系统（Linear / Vercel 式：冷色中性底 + 单一蓝色强调，OKLch 令牌），响应式侧边栏 + 移动端底部 Tab 导航。

## 技术栈

### 后端
- **框架**: FastAPI + SQLAlchemy 2.0 + SQLite
- **环境管理**: uv（虚拟环境 + 依赖管理）
- **数据库迁移**: Alembic
- **认证**: JWT Token (python-jose) + SECRET_KEY 强度校验
- **密码加密**: bcrypt (12 rounds)
- **AI 对话**: 智谱 AI GLM-4.5-Air（httpx 线程本地连接池，异步任务工作线程安全）
- **AI 舌诊**: 火山引擎 ARK 豆包视觉模型 (`doubao-seed-1-6-vision-250815`)
- **测试**: pytest + pytest-asyncio + pytest-cov (109 tests)

### 前端
- **框架**: Vue.js 3（以 Options API 为主，部分组件使用 `<script setup>`）
- **构建工具**: Vite 5
- **路由**: Vue Router 4 (history mode)
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **设计系统**: modern-minimal（Linear / Vercel 式）——OKLch 设计令牌 + AppIcon 描线图标系统 + RingGauge/TrendChart 数据可视化组件，桌面 232px 侧栏 → 平板 68px 图标栏 → 移动端底部 Tab
- **交互系统**: Vue composable (toast/modal/sound/scroll-reveal/lightbox)

## 前端设计系统（modern-minimal）

- **设计令牌**: `tokens.css` 为唯一配色/字体来源——OKLch 冷色中性底 + 单一蓝色强调 `--accent`（派生 `--accent-strong/--accent-soft`），语义色 `success/warn/danger` 永远成对使用（文字色 + 浅底），中文字体栈含 PingFang SC/Microsoft YaHei 回退；禁止组件内硬编码颜色
- **图标系统**: `AppIcon.vue`（22 个 1.7px 描线 SVG 图标：home/record/diet/sport/ai/tongue/alert/check/plus/chevron/device/close 等），全站功能图标统一走它；emoji 仅限吉祥物与趣图模块
- **数据可视化**: `RingGauge.vue`（评分环，count-up 动画 + reduced-motion 降级）、`TrendChart.vue`（数据计算生成的实心面积折线图，带类别/数值标签）
- **响应式导航**: 桌面 232px 侧栏 → ≤1024px 收成 68px 图标栏 → ≤768px 隐藏侧栏、底部 Tab 栏（56px 触控目标）
- **可访问性**: 全局 `:focus-visible` 焦点环、触控目标 ≥44px、`prefers-reduced-motion` 全局降级
- **动效纪律**: 仅允许 count-up 与 hover 微上移 2px；无卡片毛玻璃（顶栏除外）、无发光、无无限循环动画

## 核心功能

### 1. 用户认证系统
- 用户注册（邀请码验证）
- 用户登录（JWT Token 认证）
- 密码安全加密（bcrypt，最大 72 字符）

### 2. 健康记录管理
- 问卷式健康数据填写（身体指标、心血管、视力、生活习惯）
- 自动计算 BMI 并分析
- **健康综合评级**（优秀/良好/中等/较差/危险 五级体系）
- 历史记录查看、单选/多选管理

### 3. 饮食管理系统
- 食物库管理（20+ 预置食物）
- 营养成分查询（热量、蛋白质、脂肪、碳水化合物）
- 饮食记录（按餐次分类）与热量摄入统计

### 4. 运动管理系统
- 运动库管理（18+ 预置运动项目）
- 运动消耗查询（kcal/小时）
- 运动记录与统计

### 5. AI 健康分析
- 基于智谱 AI GLM-4.5-Air 的智能健康顾问
- 个性化健康建议与快速评估（规则评分 + LLM 综合）
- AI 对话咨询（后端会话 API 已实现；前端聊天入口待接入）

### 6. 中医舌诊分析
- 上传舌象图片，AI 自动分析（PIL 图像有效性校验 + 10MB 大小限制）
- 舌色、苔色、苔质、舌形、润燥等多维度诊断
- 体质辨识与调理建议
- 基于 ARK 豆包视觉大模型（云端分析，不可用返回 503，失败自动清理孤儿文件与记录）

### 7. 健康预警系统
- BMI / 血压 / 心率 / 体温异常预警
- 预警级别分类（警告、危险）

> 注：原「健康知识库 / 健康提醒」页面因后端未实现对应功能（仅孤儿表），已在审计清理中移除，避免前端崩溃。

## 快速开始

### 环境要求

> **本项目使用 [uv](https://docs.astral.sh/uv/) 管理 Python 环境与依赖，请勿使用全局 Python 直接运行！**

- Python 3.9+
- [uv](https://docs.astral.sh/uv/)（Python 包与虚拟环境管理，替代 pip/venv）
- Node.js 16+（仅开发模式需要）

### 创建虚拟环境（首次运行前必做，使用 uv）

```bash
# 安装 uv（任选其一，若已安装可跳过）
#   Windows:  winget install astral-sh.uv   或   pip install uv
#   macOS/Linux: curl -LsSf https://astral.sh/uv/install.sh | sh

cd <仓库根目录>   # 例如 E:\zxdevelop\project1

# 创建虚拟环境 + 安装依赖（一步完成）
uv venv .venv
uv pip install -r requirements.txt

# 激活虚拟环境
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# 或者不激活，直接用 uv run 执行任意命令：
uv run pytest -q
```

### 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填入以下配置：
# SECRET_KEY=<至少32字符的随机强密钥>     # JWT 签名密钥（必须）
# INVITE_CODES=your-invite-codes          # 注册邀请码（逗号分隔，未配置则禁止注册）
# ZHIPU_API_KEY=your-zhipu-api-key       # 智谱 AI（健康分析/对话）
# ARK_API_KEY=your-ark-api-key           # 火山引擎 ARK（舌诊分析）
# ARK_MODEL_ID=doubao-seed-1-6-vision-250815
```

> **SECRET_KEY 安全要求**: 长度 >= 32 字符，禁止使用 `your-secret-key-here` 等弱密钥。推荐生成方式: `openssl rand -hex 32`

### 启动服务

> 前置：已按上文创建 `.venv` 并安装依赖、已配置 `.env`（至少 `SECRET_KEY`，否则启动即报错；`INVITE_CODES` 未配置则禁止注册）。

#### 方式一：生产模式（推荐，端口 8420）

```bash
# ① 构建前端（生成 static/ 产物，生产由 FastAPI 直接托管；首次运行必做）
cd frontend && npm install && npm run build && cd ..

# ② 应用数据库迁移（开发环境 create_all 会自动建表，此步可跳过）
uv run alembic upgrade head

# ③ 启动后端
uv run uvicorn main:app --port 8420
# 访问 http://localhost:8420
```

#### 方式二：开发模式（前后端分离，热更新）

```bash
# 终端 1：后端（端口 8420，--reload 热重载）
uv run uvicorn main:app --reload --port 8420

# 终端 2：前端（端口 3000，Vite 将 /api 代理到 8420）
cd frontend && npm install && npm run dev
# 访问 http://localhost:3000
```

#### 验证启动

```bash
# 后端健康检查（应返回 {"status":"healthy"}）
curl http://localhost:8420/api/health

# API 交互文档
# http://localhost:8420/docs  （Swagger UI）
# http://localhost:8420/redoc （ReDoc）
```

### 初始化数据

```bash
uv run python scripts/init_data.py          # 初始化食物/运动数据
uv run python scripts/create_test_user.py   # 创建测试用户
```

## 项目结构

```
project1/
├── main.py                    # FastAPI 应用入口（CORS、安全头、SPA fallback）
├── models.py                  # SQLAlchemy 数据库模型（users.name 唯一约束）
├── schemas.py                 # Pydantic 请求/响应模式
├── database.py                # 数据库引擎与会话配置
├── auth.py                    # JWT 认证（iat/iss/aud 声明）+ SECRET_KEY 强度校验
├── constants.py               # 医学阈值常量（中国临床标准）
├── health_rating.py           # 健康综合评级（优秀/良好/中等/较差/危险）
├── chat_session.py            # 聊天会话管理（token 感知上下文截断）
├── async_tasks.py             # 异步任务队列（TTL 定期清理 + user_id 归属校验）
├── settings.py                # 集中配置（环境变量 + 默认值）
├── requirements.txt           # Python 依赖
├── alembic.ini                # 数据库迁移配置
├── alembic/                   # Alembic 迁移脚本
├── tongue/                    # 舌诊模块包
│   ├── diagnosis.py           #   舌诊分析（云端 ARK）
│   ├── cloud_analyzer.py      #   ARK 云端舌象分析器（requests.Session 复用）
│   └── feature_mapping.py     #   舌诊数据映射
├── ai_module/                 # AI 流水线模块（factory/pipeline/metrics/exceptions）
├── backends/                  # AI 流水线后端（预处理/推理/后处理，llm_call 可注入）
├── interfaces/                # AI 流水线抽象接口（Protocol）
├── services/                  # 业务逻辑层（SQLAlchemy 2.0 select 风格）
│   ├── auth_service.py        #   邀请码校验（无内置默认码）
│   ├── health_record_service.py
│   ├── health_service.py      #   BMI/血压分析（高血压优先判定）
│   ├── food_service.py        #   含 delete_food_record
│   ├── sport_service.py       #   含 delete_sport_record
│   ├── tongue_service.py      #   PIL 魔数校验 + 失败清理孤儿文件
│   ├── llm_service.py         #   httpx 线程本地连接池
│   ├── warning_service.py
│   ├── security_service.py    #   prompt 注入防护 + 速率限制
│   └── cache_service.py       # TTL 内存缓存（LLM 响应 + 舌诊结果）
├── routers/                   # HTTP 路由层
│   ├── auth.py                #   注册（去枚举）+ 登录（IP+用户名限流）
│   ├── health.py
│   ├── food.py                #   含 DELETE /records/{id}
│   ├── sport.py               #   含 DELETE /records/{id}
│   ├── tongue.py
│   ├── chat.py
│   ├── ai_analysis.py
│   └── warning.py
├── tests/                     # pytest 测试（109 个用例，TDD）
├── frontend/                  # 前端源码（Vue 3）
│   └── src/
│       ├── views/             #   8 个页面组件（健康知识/提醒页已移除）
│       ├── components/        #   通用组件（AppSidebar, AppTopbar, AppIcon, RingGauge, TrendChart, CharacterAvatar 等）
│       ├── layouts/           #   AppShell 布局（侧边栏 + 顶栏 + 移动端底部 Tab）
│       ├── composables/       #   useHealthU（toast/modal/sound/scroll）
│       ├── styles/            #   tokens.css（OKLch 令牌）+ layout.css + components.css
│       ├── assets/            #   静态资源管理
│       ├── router/            #   路由配置（含 auth guard）
│       ├── api/               #   API 调用封装
│       └── stores/            #   Pinia 状态管理
├── static/                    # 前端构建产物（生产模式）
└── uploads/                   # 用户上传文件
```

## 邀请码

注册时需要有效的邀请码。**系统不再内置默认邀请码**——必须通过环境变量 `INVITE_CODES` 配置（逗号分隔多个），未配置则禁止注册：

```bash
# .env
INVITE_CODES=code1,code2
```

## 测试账户

- **用户名**: `testuser`
- **密码**: `test123`

## API 文档

启动后端服务后访问：

- **Swagger UI**: http://localhost:8420/docs
- **ReDoc**: http://localhost:8420/redoc

## API 端点概览

### 认证接口 (`/api/auth`)
- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `GET /me` - 获取当前用户信息

### 健康接口 (`/api/health`)
- `POST /records` - 创建健康记录
- `GET /records` - 获取健康记录列表
- `DELETE /records/{id}` - 删除健康记录（仅删除关联分析）
- `GET /analysis/latest` - 最新健康分析
- `GET /analysis/history` - 分析历史
- `GET /rating/latest` - 最新健康评级

### 饮食接口 (`/api/food`)
- `GET /foods` - 食物列表（支持搜索/分类筛选）
- `POST /foods` - 添加食物（需管理员）
- `POST /records` - 添加饮食记录
- `GET /records` - 饮食记录列表
- `GET /records/stats` - 饮食统计
- `DELETE /records/{id}` - 删除饮食记录（按用户归属校验）

### 运动接口 (`/api/sport`)
- `GET /sports` - 运动列表（支持搜索/分类筛选）
- `POST /sports` - 添加运动（需管理员）
- `POST /records` - 添加运动记录
- `GET /records` - 运动记录列表
- `GET /records/stats` - 运动统计
- `DELETE /records/{id}` - 删除运动记录（按用户归属校验）

### AI 分析接口 (`/api/ai`)
- `POST /analysis` - AI 健康分析
- `GET /analysis/history` - 分析历史
- `POST /quick-analysis` - 快速分析（30min 缓存）
- `POST /health-evaluation` - LLM 增强健康评价（规则评分 + LLM 综合）
- `POST /async-analysis` - 异步 AI 分析（返回 task_id）
- `GET /task/{task_id}` - 查询异步任务状态

### 舌诊接口 (`/api/tongue`)
- `POST /upload` - 上传舌象图片分析（10MB 限制 + PIL 魔数校验）
- `GET /list` - 舌诊记录列表
- `GET /{id}` - 舌诊详情
- `GET /latest/result` - 最新舌诊结果
- `GET /stats/summary` - 舌诊统计

### 对话接口 (`/api/chat`)
- `POST /session` - 创建对话会话
- `GET /sessions` - 会话列表
- `POST /session/{id}/message` - 发送消息（事务一致性保障）
- `DELETE /session/{id}` - 删除会话

### 预警接口 (`/api/warning`)
- `POST /check` - 检查健康预警
- `GET /list` - 预警列表
- `PUT /read/{id}` - 标记已读
- `GET /stats` - 预警统计

## 健康标准参考（中国临床标准）

### BMI 标准
| 范围 | 分类 |
|------|------|
| < 18.5 | 偏瘦 |
| 18.5 - 24 | 正常 |
| 24 - 28 | 偏胖 |
| >= 28 | 肥胖 |

### 血压标准 (mmHg)
| 收缩压 | 舒张压 | 分类 |
|--------|--------|------|
| < 90 | < 60 | 低血压 |
| 90-120 | 60-80 | 正常 |
| 120-139 | 80-89 | 偏高 |
| >= 140 | >= 90 | 高血压 |

### 健康评级体系
| 评级 | 分数 | 含义 |
|------|------|------|
| 优秀 | 95-100 | 所有指标正常 |
| 良好 | 80-94 | 大部分指标正常 |
| 中等 | 60-79 | 部分指标异常 |
| 较差 | 40-59 | 多项指标异常 |
| 危险 | 0-39 | 健康状况较差 |

## 测试

```bash
# 激活虚拟环境后运行，或用 uv run 直接执行
uv run pytest --tb=short -q                          # 运行全部测试（109 个）
uv run pytest --cov=. --cov-report=term-missing -q   # 查看覆盖率
uv run ruff check .                                  # 代码检查
make test          # 快速运行（需先激活环境）
make coverage      # 带覆盖率报告
make lint          # 代码检查
```

## 安全特性

1. **SECRET_KEY 强度校验**: 启动时强制 >= 32 字符，拒绝已知弱密钥
2. **密码加密**: bcrypt 算法 (12 rounds) 加密存储，最大 72 字符
3. **Token 认证**: JWT Token 短期有效（默认 30 分钟），含 `iat/iss/aud` 声明并在校验端验证；`sub` 缺失/异常统一返回 401
4. **CORS 配置**: 限制允许的 HTTP 方法和请求头
5. **输入验证**: Pydantic Field 约束 + Literal 枚举 + 中英文 prompt 注入防护（Unicode 归一化 + 零宽字符剥离 + 绕过变体黑名单）
6. **SQL 注入防护**: SQLAlchemy ORM 参数化查询（2.0 select 风格）
7. **路径穿越防护**: SPA 静态文件服务用 `abspath + commonpath` 校验，阻止 `..` 逃逸
8. **登录防爆破**: `/api/auth/login` 按 IP + 用户名限流（5 次/60 秒）
9. **异步任务越权防护**: 任务结果绑定 `user_id`，查询时校验归属
10. **文件上传安全**: UUID 文件名 + 扩展名白名单 + 10MB 限制 + **PIL 魔数校验**（防伪造图片）
11. **安全响应头**: CSP / X-Frame-Options / X-Content-Type-Options / Referrer-Policy 中间件
12. **用户名唯一约束**: `users.name` 唯一索引 + 注册 IntegrityError 兜底，注册统一提示防枚举
13. **线程安全**: httpx client 改线程本地存储，异步任务工作线程不共享连接池
14. **API 密钥管理**: 通过 `.env` 环境变量管理，`.env.example` 仅含占位符
15. **集中配置**: `settings.py` 统一管理可调参数，全部从环境变量读取
16. **LLM 缓存**: 相同健康数据的 AI 分析结果缓存 30 分钟，舌诊按图片 hash 缓存 1 小时

## License

本项目仅供学习和开发使用。
