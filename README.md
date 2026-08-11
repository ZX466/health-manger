# 大学生健康管理系统

一个用于管理大学生身体健康数据的 Web 应用程序，基于 FastAPI + Vue.js 3 构建，集成中医舌诊 AI 分析。

## 项目简介

本系统旨在帮助大学生管理个人健康数据，提供健康记录、饮食管理、运动管理、AI 健康分析、中医舌诊和预警等功能。前端采用 glassmorphism 毛玻璃设计系统，侧边栏导航布局。

## 技术栈

### 后端
- **框架**: FastAPI + SQLAlchemy 2.0 + SQLite
- **数据库迁移**: Alembic
- **认证**: JWT Token (python-jose) + SECRET_KEY 强度校验
- **密码加密**: bcrypt (12 rounds)
- **AI 对话**: 智谱 AI GLM-4.5-Air (httpx 连接池复用)
- **AI 舌诊**: 火山引擎 ARK 豆包视觉模型 (`doubao-seed-1-6-vision-250815`)
- **测试**: pytest + pytest-asyncio + pytest-cov (34 tests)

### 前端
- **框架**: Vue.js 3 (Options API)
- **构建工具**: Vite 5
- **路由**: Vue Router 4 (history mode)
- **状态管理**: Pinia
- **HTTP 客户端**: Axios
- **设计系统**: Glassmorphism 毛玻璃风格 (CSS 变量令牌 + 侧边栏布局)
- **交互系统**: Vue composable (toast/modal/sound/scroll-reveal/lightbox)

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
- 个性化健康建议与快速评估
- AI 对话咨询（会话管理）

### 6. 中医舌诊分析
- 上传舌象图片，AI 自动分析（自动下采样至 1024px）
- 舌色、苔色、苔质、舌形、润燥等多维度诊断
- 体质辨识与调理建议
- 基于 ARK 豆包视觉大模型（云端分析，失败返回 503）

### 7. 健康预警系统
- BMI / 血压 / 心率 / 体温异常预警
- 预警级别分类（警告、危险）

### 8. 健康知识库
- 健康知识文章、食谱大全、收藏功能

## 快速开始

### 环境要求

> **本项目必须在虚拟环境中运行，请勿直接使用全局 Python！**

- Python 3.8+
- Node.js 16+（仅开发模式需要）

### 创建虚拟环境（首次运行前必做）

```bash
cd d:\aidevelop\project7

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填入以下配置：
# SECRET_KEY=<至少32字符的随机强密钥>     # JWT 签名密钥（必须）
# ZHIPU_API_KEY=your-zhipu-api-key       # 智谱 AI（健康分析/对话）
# ARK_API_KEY=your-ark-api-key           # 火山引擎 ARK（舌诊分析）
# ARK_MODEL_ID=doubao-seed-1-6-vision-250815
```

> **SECRET_KEY 安全要求**: 长度 >= 32 字符，禁止使用 `your-secret-key-here` 等弱密钥。推荐生成方式: `openssl rand -hex 32`

### 启动服务

```bash
# 方式一：生产模式（推荐）
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8001
# 访问 http://localhost:8001

# 方式二：开发模式（前后端分离）
# 终端 1：后端
uvicorn main:app --reload --port 8001
# 终端 2：前端
cd frontend && npm install && npm run dev
# 访问 http://localhost:3000
```

### 初始化数据

```bash
python init_data.py          # 初始化食物/运动数据
python create_test_user.py   # 创建测试用户
```

## 项目结构

```
project7/
├── main.py                    # FastAPI 应用入口（CORS、SPA fallback）
├── models.py                  # SQLAlchemy 数据库模型（12 个表）
├── schemas.py                 # Pydantic 请求/响应模式
├── database.py                # 数据库引擎与会话配置
├── auth.py                    # JWT 认证 + SECRET_KEY 强度校验
├── constants.py               # 医学阈值常量（中国临床标准）
├── health_rating.py           # 健康综合评级（优秀/良好/中等/较差/危险）
├── tongue_diagnosis.py        # 舌诊分析（云端 ARK，失败抛 RuntimeError）
├── cloud_tongue_analyzer.py   # ARK 云端舌象分析器（requests.Session 复用）
├── feature_mapping.py         # 舌诊数据映射
├── chat_session.py            # 聊天会话管理（token 感知上下文截断）
├── async_tasks.py             # 异步任务队列
├── settings.py                # 集中配置（环境变量 + 默认值）
├── requirements.txt           # Python 依赖
├── alembic.ini                # 数据库迁移配置
├── alembic/                   # Alembic 迁移脚本
├── services/                  # 业务逻辑层（SQLAlchemy 2.0 select 风格）
│   ├── auth_service.py
│   ├── health_record_service.py
│   ├── health_service.py
│   ├── food_service.py
│   ├── sport_service.py
│   ├── tongue_service.py
│   ├── llm_service.py         # httpx 连接池复用
│   ├── warning_service.py
│   ├── security_service.py    # 中文 prompt 注入防护 + Unicode 归一化
│   └── cache_service.py       # TTL 内存缓存（LLM 响应 + 舌诊结果）
├── routers/                   # HTTP 路由层
│   ├── auth.py
│   ├── health.py
│   ├── food.py
│   ├── sport.py
│   ├── tongue.py
│   ├── chat.py
│   ├── ai_analysis.py
│   └── warning.py
├── tests/                     # pytest 测试（34 个用例）
├── frontend/                  # 前端源码
│   └── src/
│       ├── views/             #   10 个页面组件
│       ├── components/        #   通用组件（AppSidebar, AppTopbar, CharacterAvatar 等）
│       ├── layouts/           #   AppShell 布局（侧边栏 + 顶栏）
│       ├── composables/       #   useHealthU（toast/modal/sound/scroll）
│       ├── styles/            #   tokens.css + layout.css + components.css
│       ├── assets/            #   静态资源管理
│       ├── router/            #   路由配置（含 auth guard）
│       ├── api/               #   API 调用封装
│       └── stores/            #   Pinia 状态管理
├── static/                    # 前端构建产物（生产模式）
└── uploads/                   # 用户上传文件
```

## 邀请码

注册时需要使用有效的邀请码：

| 邀请码 | 说明 |
|--------|------|
| `health2026` | 系统默认邀请码 |

## 测试账户

- **用户名**: `testuser`
- **密码**: `test123`

## API 文档

启动后端服务后访问：

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

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
- `POST /foods` - 添加食物
- `POST /records` - 添加饮食记录
- `GET /records` - 饮食记录列表
- `GET /records/stats` - 饮食统计

### 运动接口 (`/api/sport`)
- `GET /sports` - 运动列表（支持搜索/分类筛选）
- `POST /sports` - 添加运动
- `POST /records` - 添加运动记录
- `GET /records` - 运动记录列表
- `GET /records/stats` - 运动统计

### AI 分析接口 (`/api/ai`)
- `POST /analysis` - AI 健康分析
- `GET /analysis/history` - 分析历史
- `POST /quick-analysis` - 快速分析（30min 缓存）
- `POST /health-evaluation` - LLM 增强健康评价（规则评分 + LLM 综合）
- `POST /async-analysis` - 异步 AI 分析（返回 task_id）
- `GET /task/{task_id}` - 查询异步任务状态

### 舌诊接口 (`/api/tongue`)
- `POST /upload` - 上传舌象图片分析（10MB 限制，自动下采样）
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
# 激活虚拟环境后运行
pytest --tb=short -q                          # 运行全部测试
pytest --cov=. --cov-report=term-missing -q   # 查看覆盖率
make test          # 快速运行
make coverage      # 带覆盖率报告
make lint          # 代码检查
```

## 安全特性

1. **SECRET_KEY 强度校验**: 启动时强制 >= 32 字符，拒绝已知弱密钥
2. **密码加密**: bcrypt 算法 (12 rounds) 加密存储，最大 72 字符
3. **Token 认证**: JWT Token 短期有效（默认 30 分钟）
4. **CORS 配置**: 限制允许的 HTTP 方法和请求头
5. **输入验证**: Pydantic Field 约束（min/max/ge/le）+ Literal 枚举 + 中英文 prompt 注入防护（Unicode 归一化 + 零宽字符剥离）
6. **SQL 注入防护**: SQLAlchemy ORM 参数化查询（2.0 select 风格）
7. **文件上传安全**: UUID 文件名 + 扩展名白名单 + 10MB 大小限制
8. **API 密钥管理**: 通过 `.env` 环境变量管理，`.env.example` 仅含占位符
9. **集中配置**: `settings.py` 统一管理 47 项可调参数，全部从环境变量读取
10. **LLM 缓存**: 相同健康数据的 AI 分析结果缓存 30 分钟，舌诊按图片 hash 缓存 1 小时
9. **图像处理**: 自动下采样至 1024px，减少内存占用和处理时间

## License

本项目仅供学习和开发使用。
