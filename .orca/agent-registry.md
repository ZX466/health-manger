# Agent 注册表

每个能力域只指定一个推荐 Agent，不重复分配；未覆盖能力保持空白，后续按需补充（不要随意更改，由用户决定）。

| 能力域 | 推荐 Agent | 评审 Agent |
|---|---|---|
| 架构 / 代码质量 / 逻辑 / 测试 | Claude | Codex |
| 依赖 / 配置 / 文档 | cline | Claude |
| 安全 / 合规 / 风险 | Codex | cline |
| 性能 | Pi | cline |
| 数据 / 数据库 | opencode | Codex |
| 接口 / 兼容性 | kilo | Claude |
| 前端 / 体验 / 发布 / 运维 | Claude | codex |

> 协作规则与任务流转详见 `.orca/workflow`。
