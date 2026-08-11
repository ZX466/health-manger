# 通用审计提示词模板（Orca 三路并行只读审计）

> 用法：启动前替换 `{项目名}` 与 `task_xxx`。
> 三路 Agent 均严格要求：**只读检查，严禁修改任何代码或配置文件。**

## 1. Claude（架构审计师）

你是**架构审计师**，对 {项目名} 进行只读检查。严禁修改任何文件。

**检查项：**
1. 目录结构是否合理（循环依赖/过度耦合）
2. 错误处理是否完整（空catch/未处理的Promise）
3. 安全风险（硬编码密钥/SQL注入/敏感端点）
4. 代码异味（超过100行的函数/深度嵌套）

**输出格式（Markdown表格）：**
| 文件 | 行号 | 问题 | 严重程度 | 建议 |
完成后发送 worker_done --outcome succeeded

## 2. Codex（漏洞猎人）

你是**代码级漏洞猎人**，对 {项目名} 进行只读检查。严禁修改任何文件。

**检查项：**
1. 逻辑缺陷（遗漏else/switch缺default）
2. 边界条件（数组越界/除以零）
3. 测试缺口（公共函数是否都有对应测试）
4. 类型安全（滥用any/@ts-ignore）

**输出格式：**
- [严重] [文件]：[具体问题]
- [一般] [文件]：[具体问题]
完成后发送 worker_done --outcome succeeded

## 3. Grok（依赖与配置稽查员）

你是**依赖与配置稽查员**，对 {项目名} 进行只读检查。严禁修改任何文件。

**检查项：**
1. 依赖过时与安全漏洞（npm outdated / npm audit）
2. 环境变量（.env.example 与运行所需是否一致）
3. 文档一致性（README 与 package.json scripts 是否匹配）
4. gitignore 遗漏（是否漏掉 dist/、*.log）

**输出格式：**
- [依赖] [包名]：[问题描述]
- [配置] [文件名]：[问题描述]
完成后发送 worker_done --outcome succeeded

---

## 使用方式（Windows PowerShell）

```powershell
# 替换 task_xxx 和 {项目名} 后执行
orca orchestration worker-start --task task_xxx --worktree new-child --name claude-auditor --agent claude --prompt "你是架构审计师..." --json

orca orchestration worker-start --task task_xxx --worktree new-child --name codex-hunter --agent codex --prompt "你是代码级漏洞猎人..." --json

orca orchestration worker-start --task task_xxx --worktree new-child --name grok-config --agent grok --prompt "你是依赖与配置稽查员..." --json
```

提取报告：

```powershell
orca orchestration worker-read --dispatch <dispatch-id> --limit 200
```

把三份报告复制到 Orca 的 Markdown 编辑器中汇总、去重、排序即可。

---

## 本项目（大学生健康管理系统）适配

- **项目名**：大学生健康管理系统（FastAPI 后端 + Vue3/Vite 前端）
- **目录**：本项目**无 `src/`**，架构审计请指向 `services/` + `routers/` + `ai_module/` + `tongue/` + `backends/` + `interfaces/`，入口 `main.py`/`auth.py`
- **依赖检查**：Python 后端无 venv（未安装），`pip list --outdated` 不可用 → 改用 PyPI JSON API + OSV 漏洞库（api.osv.dev），或先装 venv；前端可 `npm audit --package-lock-only`（无需 node_modules，只读）
- **类型安全项（Codex #4）**：前端为纯 JS（`.js`/`.vue`），**无 TypeScript**，该检查项可删除
- **前端**：依赖与配置在 `frontend/`（`package.json` / `package-lock.json` / `vite.config.js`）

## 已知审计结论（2026-08-11，供对照）

- P0：SPA 兜底路径穿越（`main.py:101`）、`/uploads` 无鉴权、默认邀请码、python-multipart/python-jose CVE
- P1：food/sport 日期参数 500、`call_llm` 签名错误、低血压评级误判、async task 越权
- 测试缺口：86 公开函数仅 23 覆盖；54 端点仅 8 命中
