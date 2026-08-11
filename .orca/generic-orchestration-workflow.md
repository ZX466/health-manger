# Orca 多 Agent 协作 · 通用工作流

> 用途：**跨项目复用**。把本项目（`.orca/generic-orchestration-workflow.md`）拷到任意新项目根目录（连同 `.orca/` 目录），在 main 分支打开 Claude Code，粘贴第 4 节的「启动语」即可驱动 claude/codex/grok（及未来更多 agent）按能力域协作、互审、合并 main。
> 版本：v1.3（2026-08-11；v1.3 运维手册补充：GitHub 代理推送、修复通道降级策略、setup 失败不阻塞、task-create 抖动重试；启动语预检核实修正 task-list 说明）

---

## 1. 核心模型

```
         ┌──────────── 协调者（主工作树 / main）────────────┐
         │  Claude Code：分派任务 · 汇总 · 仲裁 · 合并       │
         └───────┬──────────────────┬──────────────────────┘
                 │  Orca 总线（send / reply / ask / check / worker_done）
          ┌──────▼─────┐ ┌──────▼──────┐ ┌──────▼───────┐
          │ 角色 A     │ │ 角色 B      │ │ 角色 C      │ ... 更多
          │ 独立工作树  │ │ 独立工作树  │ │ 独立工作树   │
          │ 分支 A      │ │ 分支 B      │ │ 分支 C      │
          └────────────┘ └─────────────┘ └──────────────┘
               ▲   互审：B 审 A → C 审 B → A 审 C（经 Orca 消息）
               └── 全部通过 + 用户验收 → 合并进 main
```

**三条铁律**
1. **消息都走 Orca**：agent 之间不直接互访工作树，只通过 `orca orchestration send/reply/ask/check` 交流。
2. **各司其职**：每个 agent 有固定能力域，按能力域匹配分派任务。
3. **审核后进 main**：任何产出必须经另一 agent 审过 + 用户验收，才允许合并 main。

## 2. 角色注册表（可扩展架构）

> **核心扩展原则：分派按「能力域」匹配，不写死 agent 名。** 阶段 A→D 与协议本体不变，新 agent 加入 = 注册表加一行 + 环境配置好。添加 agent 类型、新能力域、新任务类型都不需要改流程代码。

| Agent | Orca `--agent` 值 | 能力域 | 默认任务类型 | 评审偏好 |
|---|---|---|---|---|
| **claude** | `claude` | 架构 / 安全 / 整体质量 | 架构审计、安全审查、高价值修复 | 审代码级改动 |
| **codex** | `codex` | 逻辑 / 边界 / 测试 | 逻辑修复（TDD）、测试缺口补测 | 审架构与安全 |
| **grok** | `grok` | 依赖 / 配置 / 文档 / 环境 | 依赖 CVE、.env 一致性、README 稽查 | 审依赖与配置 |

> **本表只列实际在用的 agent，不预设任何范例**。新 agent 由你自行提供，按下方「接入新 Agent 契约（5 步）」登记即可；Orca 的 `--agent` 类型与群地址以 `orca skills get orchestration` 为准。

### 接入新 Agent 契约（5 步，不改协议）

1. **确认 Orca 支持**：该 agent 是否在 `orca skills get orchestration` 的可用类型 / 群地址（`@<agent>`）里。
2. **配置环境**：本机该 agent 的登录 / 供应商 / 模型可用（参考运维手册「供应商 400」坑，先确保能正常启动）。
3. **登记注册表**：加一行，填 `--agent` 值、能力域、默认任务类型、评审偏好。
4. **验证通道**：先给它派一个**只读小任务**跑通一次 `worker_done`（验证消息通道与 pane 归属，规避 `--from` 坑）。
5. **纳入互审池**：之后跨能力域互审会自动把它纳入评审人集合。

### 扩展点清单（哪些能扩展、扩展在哪）

| 要扩展什么 | 改哪里 | 协议要不要改 |
|---|---|---|
| 新 Agent 类型 | 注册表加一行 + 环境配置 | 不改 |
| 新能力域 | 注册表新增一行或给现有 agent 补能力域 | 不改 |
| 新任务类型（如迁移/联调） | 用任务 Spec 模板描述即可 | 不改 |
| 自定义模型 / 推理强度 | `worker-start --model <id> --effort <level>` | 不改 |

## 3. 工作协议（阶段 A→D）

| 阶段 | 动作 | 执行者 | 产出 |
|---|---|---|---|
| **A 分派** | `run-create` → 按能力域 `task-create` → `worker-start` | 协调者 | 各 agent 独立工作树 + 分支 |
| **B 执行** | 按能力域匹配的 agent 干活（只读审计 或 代码修复） | 能力域匹配的 agent | 报告 或 分支上的代码改动 |
| **C 互审** | 评审派给**能力域不同**的 agent（避免自我评审），审对方分支 diff/报告 → verdict | 跨能力域 agent | pass / 修改意见 |
| **D 合并** | 全通过 → 协调者合并进 main → **用户验收**；不通过 → 打回原 agent | 协调者 | main 更新 |

**分派规则**
- **B 执行**：按「能力域」匹配最合适的 agent（注册表决定），支持任意数量 agent 并行。
- **C 互审**：评审人 = 能力域不同的 agent（由注册表「评审偏好」列决定，不预设固定配对）。
- **并行上限**：同一阶段可并行启动多个独立任务（互不依赖的 agent 同时跑）。

**任务分类**
- **只读任务**（审计/评审）：agent 严禁修改任何文件；`worker-start` 加 `--setup skip`（理由：避免 setup 副作用，保护只读语义）。
- **修复任务**：agent 只能在**自己分支**上改，必须 **TDD**（先写失败测试 → 最小实现），`worker_done` 带 `--files-modified`。

## 4. 启动语（复制粘贴进主分支的 Claude Code）

````text
# Orca 多 Agent 协作工作流 — 启动规则

你现在是本项目的「协调者」。严格按以下规则执行：先规划再行动；需要我决策时用 AskUserQuestion 提问；未经我确认不得合并 main。

## 目标
用 Orca 作为唯一编排总线，驱动 claude / codex / grok（及以后更多 agent）各自扮演角色协作完成任务，产物互相审核，审核通过后合并到 main 分支。

## 铁律
- 消息全部经 Orca（orca orchestration send/reply/ask/check），agent 之间不直接互访工作树。
- 每个 agent 一个独立工作树 + 分支（隔离、可审、可弃）。
- 任何代码改动必须 TDD + 互审 + 我（用户）验收后才允许合并 main。
- 只读任务严禁 agent 修改任何文件；修复任务只在各自分支上改。

## 启动前（每次）
- 运行 `orca status --json` 确认 Orca 在线；运行 `orca skills get orchestration` 读取本版本指南（不要凭记忆猜命令）。
- 运行 `orca orchestration run-list --json` 检查遗留运行空间（`task-list` 需先有绑定 Run，全新环境会报 `run_required`，属正常，先 run-create 即可）；有遗留先问我是否 `reset --all`。
- 若我是换新项目复用：先读 `.orca/generic-orchestration-workflow.md` 的**角色注册表**与协议（按能力域匹配 agent；新 agent 加一行即可接入），并用 AskUserQuestion 让我确认：①目标 ②任务拆分（哪个能力域接哪个任务）③只读还是修复模式。

## 标准流程（阶段 A→D）
1. A 分派：`run-create --objective <目标>` → 按能力域 `task-create --spec <完整任务说明>`（spec 即注入给 worker 的提示词）→ 每任务 `worker-start --task <id> --worktree new-child --name <agent名> --agent <能力域匹配的agent>`（只读任务加 `--setup skip` 并说明理由）。
2. B 执行：worker 在分支产出（报告 或 TDD 修复）。
3. C 互审：修复类任务，把评审任务派给**能力域不同**的 agent（注册表评审偏好列决定），审对方分支 diff → verdict。
4. D 合并：全通过后合并进 main；**合并前必须等我确认**。

## 等待与结算
- 用 `orca orchestration check --wait --types worker_done,escalation,question --timeout-ms 600000` 滚动等待；超时是检查点不是失败，`worker-show` 确认存活后继续等。
- 每条 worker_done 处理后 `worker-release --dispatch <id>`（除非要复用同一终端给下一任务 → `worker-start --task <next> --terminal <handle>`）。
- 处理完整个 delivery 后 `orca orchestration check --ack <delivery_id> --wait ...`。

## 已知坑（务必遵守）
- worker 发 worker_done 时绝不传 `--from`（会被 pane 校验拒绝）。
- exact 已存在工作树启动：`worker-start --worktree <精确id> --agent <角色>`，不要带 `--setup/--name`（仅 new-child/new-top-level 允许）。
- 任务连续失败变 `blocked` 后：先 `task-update --id <task> --status ready` 再重试。
- Orca 运行时若重启：后台 `check --wait` 可能挂掉，重新发起滚动等待；用 `worker-show` 判断 worker 存活。
- agent（尤其 codex）供应商/model 配置错误是环境问题：先用 `worker-show` 看终端报错，不要盲目重启。

## 汇总与交付
- 多路报告按角色汇总去重，标注「几路独立确认」。
- 给出优先级排序（P0/P1/P2/P3）与可执行修复顺序。
- 每次执行前先向我确认关键决策（分派对象、修复范围、合并闸门）。
````

## 5. 任务 Spec 模板

**审计类（只读）**
````text
你是<能力域匹配的agent>，对「<项目名>」（<技术栈>，仓库 <路径>）进行只读检查。严禁修改任何代码或配置文件，严禁创建/写入文件。
检查项：<按注册表能力域列 3-5 项>
输出格式：<Markdown 表格 或 [严重] 清单>
最后给 Top N 优先项。完成后发送 worker_done（--outcome succeeded）。
````

**修复类（TDD）**
````text
你是<能力域匹配的agent>，修复「<项目名>」的 <Bug 描述 + 文件:行号>。
要求：TDD（先写失败测试 → 最小实现）；只能在你的分支上改；不引入无关重构。
完成后提交到你的分支，发送 worker_done（--outcome succeeded，--files-modified <改动的文件>）。
````

**评审类（互审）**
````text
你是<能力域匹配的agent>，评审 <分支名> 上的改动（<改动概述>）。用只读方式检查：逻辑正确性、边界、测试是否覆盖、是否引入新问题。
输出 verdict：PASS 或 FAIL+修改意见（具体到行）。完成后发送 worker_done（--outcome succeeded）。
````

## 6. 运维手册（踩坑记录）

| 现象 | 根因 | 处置 |
|---|---|---|
| worker_done 被拒 `The caller is not the Dispatch pane` | worker 误传 `--from <协调者句柄>` | 重发时省略 --from；报告内容仍在消息体里，可人工结清 |
| 任务 `blocked` 但报告已产出 | dispatch 未正规落定（被拒/被停） | `task-update --status completed`（明确恢复场景）+ `worker-stop`/`worker-abandon` 清理 |
| `worker-release` 报 `dispatch_inactive/ready` | 只允许对 succeeded/failed 的 dispatch release | 先 `worker-stop`（关闭终端）或 `worker-abandon` |
| `worker-stop` 返回 `stop_unknown` | 进程已退出、无终端可关 | `worker-abandon` 结清（资源可能残留，警告可忽略） |
| 后台 `check --wait` 意外 exit 1 | Orca 运行时重启 | 重新发起滚动等待；`worker-show` 确认存活 |
| exact 工作树 `worker-start` 报 `Creation and setup options apply only to new-child...` | exact 工作树不允许 --setup/--name | 去掉这两个选项重试 |
| Codex 启动即崩 `cc_switch_upstream_error / upstream_status:400` | 本机 codex config.toml 的供应商/model 配置错误 | 环境问题，先修配置；不是 Orca 问题，勿盲目重启 |
| GitHub 推送失败 `Failed to connect to github.com:443`（Gitee 正常） | 大陆网络对 github.com 直连被阻断 | 检查本地代理端口（Clash/Mihomo 常见 7897/7890/10809）：`(echo > /dev/tcp/127.0.0.1/7897)`；一次性推送不污染全局配置：`git -c http.proxy=http://127.0.0.1:7897 -c https.proxy=http://127.0.0.1:7897 push <remote> <branch>` |
| 修复类 worker 停滞/死亡（codex 停在 TUI 空闲提示符、claude 静默退出或停在空壳提示符 `P>`） | 本机 Orca 运行时多次重启后，新 worker 的注入任务未激活（input_accepted 但 agent 无动作） | 降级：协调者在主工作树 TDD 修复 + 严格自查替代互审（附完整测试证据）；Orca 互审等运行时稳定后再补。勿反复重启烧时间 |
| setup 钩子失败（`setupState: failed`） | 新工作树 setup 命令失败（如依赖安装失败） | start-immediately 策略下不阻塞 agent：`worker-show` 确认 worker 存活即可继续 |
| 长 spec 的 `task-create` 偶发静默无输出（无 JSON、无报错） | Orca 运行时抖动 | 幂等重试；可用最小 spec 冒烟验证 task-create 可用（先清掉冒烟任务） |

## 7. 协调者检查清单（每轮必查）

- [ ] `orca status --json` OK，`orca skills get orchestration` 已读
- [ ] Run 已建、任务按能力域建好、worker 独立工作树+分支
- [ ] 只读任务加了 `--setup skip` 且说明理由
- [ ] `check --wait` 滚动；每条 worker_done 后处理→release（或复用）→ack
- [ ] 报告按角色汇总、去重、标注确认源、按 P0-P3 排序
- [ ] 修复类：TDD 已验证、互审 verdict 收集、合并 main 前用户确认
