# M-SEC1 心理安全服务与合规审计

日期：2026-11-15。执行：Codex；评审：cline；协调：Claude。
依据：本工作树 `.orca/talking.txt` 的 M-SEC1 已确认方案、对外契约与文件所有权。

## 实施计划

**目标**：提供可审计的风险分级、危机时强制严肃的系统 Prompt，以及不编造号码的求助资源。
**架构**：独立 `services/safety_service.py`；只读 SQLAlchemy 查询、冻结的 `RiskState`、纯 Prompt 构造；资源每次从环境变量读取。调用接线由 Pi/kilo/Claude 完成。
**技术**：Python 3.11、SQLAlchemy 2.0、pytest；只使用既有依赖与标准库。

约束：只修改指定安全服务、回归测试和本文；不改模型、路由、LLM 服务与前端；不合并 main、不推 Agent 分支。计划与执行记录放在授权的审计文档内，避免另建跨域文档或配置。

复核重点：跨用户数据混用；30 天过期/未来记录；同时间戳的最新记录；旧危机被新低风险记录替换；不一致的 Q9/flag；原 Prompt 与危机指令冲突；未配置或恶意控制字符资源。

### 任务 1：风险分级

产出：冻结的 `RiskState(level, reasons, crisis)`；`assess_user_risk(db: Session, user_id: int) -> RiskState`。

- [x] RED：`test_no_data_is_normal`，无数据时为 normal、空 reasons、非 crisis。
- [x] GREEN：先提供最小无数据实现。
- [x] RED：真实内存 SQLite 覆盖 PHQ-9 10/20、GAD-7 10/15、Q9 阳性、危险/较差评级、未读 danger；加入时间窗口、最新记录和用户隔离用例。
- [x] GREEN：每个量表与健康分析只取近 30 天最新记录，时间相同按 id 倒序；未读 danger 只判断存在，不读取内容；风险取最高级。
- [x] 验证：风险查询 42 例通过。

### 任务 2：Prompt 与求助资源

产出：`build_system_prompt(base: str, persona_style: str, risk: RiskState) -> str`；`crisis_resources() -> list[dict[str, str]]`。

- [x] RED：正常 humorous 保留人设、clinical 专业、未知人设安全降级；high 或 crisis 强制严肃并提供求助建议；冲突的 base 不进入危机 Prompt。
- [x] RED：无配置资源仍有通用求助信息但无号码；号码只来自 MENTAL_HOTLINE，校园说明只来自 CAMPUS_COUNSELING；去控制字符、校验电话格式；返回对象互不共享。
- [x] GREEN：静态安全边界 + 正常人设；危机 Prompt 完全覆写；环境变量按文本使用，不作为指令。
- [x] 验证：安全测试 61 passed；完整回归 191 passed / 1 failed（跨域适配缺陷 A01，未隐藏）。

### 任务 3：审计、评审与交付

- [x] 只读复核 Q9、免责声明、隐私/保留、EXIF/GPS、上传鉴权/大小、OCR/识餐注入、限流与诊断边界；每项列出现状、风险、整改建议与负责任务。
- [x] 按注册表只读评审 M-DB1 与 M-LOGIC1；问题只在本工作树 talking.txt 留言。
- [x] 验证：全量 pytest、ruff、编译/import main、依赖增量与敏感信息检查、diff 复核；安全后端变更不调用浏览器。全量失败已逐项报告，不伪报 PASS。
- [x] 本地约定式提交 `6c77022`；talking.txt 留交付结果、待评审点与跨域整改项；更新本工作树 memory.md。
- [ ] 跨域适配完成后全量回归通过、cline 独立评审完成，再回 complete；当前按 blocked 留交接，不伪报任务验收完成。

## 执行记录

- 已读工作流、注册表、完整本地派单并 accept；Codex 已是独立 worktree。
- 已 rebase main；仅本地 talking.txt 冲突，保留双方全部留言后解决。
- 使用 uv 创建 Python 3.11 环境并安装 requirements.txt；未增加项目依赖。命令设置 UV_NO_SYNC=1，避免 uv 根据仅含开发组的 pyproject 改写环境。
- 基线：131 passed，1 条既有 SQLAlchemy 事务警告（tests/conftest.py:49）。
- 实现裁定：以模型 `_utcnow` 对齐 UTC 时间，查询范围为 [当前时刻 - 30 天, 当前时刻]；不读取心理笔记，不把用户原文写入 reasons。
- 实现裁定：PHQ-9 的合法 Q9 阳性答案独立兜底，防止历史 flag 不一致漏报；高风险 Prompt 丢弃 base，避免继承旧人设。
- 实现裁定：clinical 为显式专业人设；未知人设安全降级为 clinical；不新增人设数据库字段。
- TDD 证据：模块缺失时无数据测试 1 failed → 最小实现 1 passed；增加风险场景后 18 failed / 24 passed → 查询实现 42 passed；新增 Prompt/资源用例 19 failed → 完整实现 61 passed。
- 测试夹具修正：环境变量不能包含 NUL；控制字符用例改用操作系统允许的 SOH/ESC/bidi 等输入，重新确认因资源功能缺失而失败后才实现。
- 只读评审：M-DB1 `68583e2` pass（模型/迁移）；M-LOGIC1 `90c69f9` changes_requested（A01）。未修改他人工作树或代码。
- 自检依据 `requesting-code-review` 模板；独立评审继续按注册表交给 cline，通过本工作树 talking.txt 请求，不另开 Agent 或终端。

## 审计结果

审计基线：main `5eddc66` + 本次 M-SEC1。**安全服务已实现，但当前整体不能合并/发布：A01 适配仍阻断全量回归，A02 聊天接线尚缺。** 以下区分已实现的服务能力、已复现的问题和需负责人验收的发布条件；不把 Prompt 单测当作真实模型安全效果证明。

| 项目 | 现状 / 证据 | 风险 | 整改建议 | 负责任务 |
|---|---|---|---|---|
| A01 Q9 阳性与危机资源链路 | `scale_scoring.score:153` 强制计算 Q9/分数危机标记；安全服务也对合法 Q9 阳性兜底。`warning_service._crisis_hint:184` 仍 join 对象；`schemas.ScaleSubmitResponse:515` 仍 list[str]。默认空配置下分别实测 TypeError、ValidationError。 | **P1：危机预警/量表响应会失败**；清空资源会掩盖错误并丢失求助信息。 | 按 `{name,phone?,description}` 格式化预警，响应模型接收对象列表；测试 Q9 阳性且无热线仍显示通用资源。 | Claude M-LOGIC1；kilo M-API1；Codex 复核 |
| A02 危机文案与强制人设 | `build_system_prompt` 在 high 或 crisis 时完全丢弃 base，固定严肃关怀、专业求助、120/110、非诊断治疗、不追问方式细节、不承诺绝对保密。`routers/chat.py:135/195` 仍直接使用 CHAT_SYSTEM_PROMPT；流式 206 行只有 TODO。 | **P1：安全函数存在但两个聊天路径尚未使用**；首个 safety 事件缺失，前端无法可靠切换。 | 两条路径均在上游调用前查询风险、构造 system Prompt；SSE 首个事件输出 level/crisis/resources；新增隔离数据库的端点回归。summary/UI 应覆盖健康评级危险等所有 high 来源，可保留既有更保守的 PHQ-9 15–19 展示策略。 | Pi M-PERF1；Claude M-LOGIC1/M-FE1/测试 |
| A03 求助资源与配置 | `crisis_resources` 只从 MENTAL_HOTLINE / CAMPUS_COUNSELING 读值，每次返回新对象；无配置返回学校心理咨询中心/当地精神卫生中心，不含任何号码。电话仅接受有界 ASCII 电话格式，拒绝超长值而不截断成另一个号码；校园说明过滤控制字符、上限 300 字。 | 语法校验不能证明号码归属、服务地区与开放时间；配置描述也可能包含误导内容。 | 部署方核验联系人与服务范围；仅作为普通文本展示，不能当 HTML 或模型指令。号码不进入默认 Prompt，紧急固定文案按派单执行。 | Codex M-SEC1 已落地；cline M-DOC1；Claude 发布验收 |
| A04 量表免责声明 | 量表名称标为初筛，评分模块文档说明非诊断；API 以分数/风险/标记返回数据。前端提示及危机资源不可隐藏需 M-FE1 验收。 | 用户可能把初筛标签理解为确诊，或以低分推断绝对安全。 | 作答前及结果页说明初筛用途、局限与求助方式；normal 只表示规则未命中，不表示临床安全结论；Q9 阳性及时连接专业支持。 | Claude M-FE1；cline M-DOC1；Codex 复核 |
| A05 心理数据隐私与保留 | 模型以 SQLite TEXT/数值保存 note、answers、score；mental 路由要求 get_current_user，各查询按 user_id 过滤。安全 reasons 只含固定中文短句；不读取心理 note、不日志输出答案、不提交事务、不触发调用方 autoflush。当前心理路由未提供删除/导出/保留清理入口。 | **发布前需闭环**：数据库/备份暴露、过度保存、用途与第三方模型传输不透明；API Key 的 Fernet 保护不等于心理数据已加密。 | 明确用途/必要性、适用处理依据及告知/单独同意、可撤回与删除流程；确定最短必要保留期限并覆盖备份；限制库文件权限、部署磁盘/备份加密；只向模型提供必要摘要，不上传身份/原始答案。期限由产品/数据负责人决定，本任务不臆定天数或新增表。 | Claude 产品/发布；cline 告知文档；opencode 后续数据任务；Codex 复核 |
| A06 图片 EXIF/GPS 与解码 | `prepare_image:37` 在方向纠正后重新编码 JPEG；以合成 Orientation+GPS 输入实测输出无 EXIF/GPS、方向正确。主线 56 行先 copy 解码、64 行后查像素；Pi 留言已说明后续前移修复，尚不在本审计基线。 | 大图在拒绝前造成内存尖峰；若未来路径跳过重编码，元数据可能外泄。 | Claude 纳入 Pi 已回报的检查前移修复；保持舌诊/识餐/OCR 都经过 prepare_image，补像素边界与元数据回归。原图不持久化、不发送上游。 | Pi M-PERF2；Claude 集成 |
| A07 上传鉴权与大小 | 识餐/OCR 依赖 get_current_user；`routers/_uploads.py:10` 校验 MIME/后缀、读取至 10 MiB+1、PIL verify；服务再验证真实格式/像素；草稿路径不写业务记录。 | 路由限制不等同于代理层请求体限制；并发大图可能耗尽解码资源。 | 保留双层验证，部署层设置请求体/超时/并发上限；拒绝伪造类型及超限文件，上传原文不得进异常日志。 | kilo M-API1；Pi M-PERF2；Claude 运维 |
| A08 OCR/识餐 Prompt 注入及输出 | 只解析 JSON、白名单字段、限制项目数、确认后才写库，未执行模型输出。`_clean_name:50` / `_clean_abnormal:64` 仅 strip/截断，实测 ESC/bidi 保留；识餐 `_clamp:42` 对 NaN 实测仍返回非有限数。 | **P1：草稿可能显示误导控制字符或因 NaN 导致 JSON 响应失败**；图片内指令仍可影响识别内容，单靠 Prompt 不能保证隔离。 | 对所有显示文本去 C0/C1/Cf 控制与双向覆盖字符，限制长度；数值先验证 math.isfinite；固定服务指令与图片数据隔离，后端字段校验/授权/人工确认持续独立于模型，前端文本渲染、不使用 v-html。补离线恶意输出用例。 | Pi M-PERF2；Claude M-FE1/测试；Codex 复核 |
| A09 限流与每日上限 | 聊天及视觉路由有限流，量表每用户每类 3 次/86400 秒；`security_service.RateLimiter:62` 为进程内内存。 | **P1：重启或多 worker 可绕过量表每日 3 次约定**；滚动 86400 秒也不等于自然日。 | 量表以既有 ScaleAssessment 表的用户/类型/日期计数作权威限制并处理并发；统一校园自然日与 UTC 存储边界。部署临时单 worker 只能降低多进程绕过，不满足持久限额。请求级速率与日提交数分别校验。 | kilo M-API1；Claude 逻辑/测试；opencode 数据评审支持 |
| A10 AI 结论不得替代诊断 | 正常与危机 Prompt 都限制诊断、治疗、给药；OCR/识餐输出为 needs_confirm 草稿。此次不调用真实模型或浏览器。 | 模型可能违背提示或生成不准确营养/体检信息；格式正确不证明医学正确。 | UI 保留 AI 估算/人工确认/非诊断提示；真实模型验收用合成、去标识样例，覆盖危机、玩梗诱导、注入和错误数字；不得把风险状态自动用于纪律/医疗决策。 | Claude M-FE1/验收；Pi M-PERF1/2；Codex 复核 |
| A11 跨模块契约 | 派单 `RiskState.level` = normal/elevated/high，资源为对象列表；当前 api-v2 §4 仍 normal/caution/crisis + 字符串数组，§5 人设枚举也与 clinical 口径分叉。服务只对 humorous 启用轻松风格，其余安全降级为 clinical。 | 消费者误判等级或无法读取资源；前后端人设显示与实际不一致。 | 以派单契约统一 schemas、api-v2、SSE 与前端映射；后端决策优先于 persona_style。不要为兼容旧类型而更改危机标记或清空资源。 | kilo M-API1；Pi M-PERF1；Claude M-FE1 |

## 验证与评审状态

| 检查 | 实测结果 |
|---|---|
| `uv run python -m pytest tests/test_safety_service.py -q` | **PASS：61 passed** |
| `uv run python -m pytest -q` | **FAIL：191 passed / 1 failed / 1 warning**；唯一失败 `tests/test_mental_service.py::test_cross_warning_for_serious_scale_without_health_record`，原因见 A01 |
| 既有 warning | `tests/conftest.py:49` SAWarning transaction already deassociated，基线也存在 |
| `uv run ruff check .` / 安全规则 `--select S` | PASS；只扫描当前代码，不据此宣称全部历史依赖零漏洞 |
| `ruff format --check` / `compileall` / `git diff --cached --check` | PASS；最终两份 Python 文件格式正确且可编译，暂存 diff 无空白错误；未新增依赖或真实凭据 |
| `uv run python -c "import main"` | PASS；SECRET_KEY 仅为该验证进程生成，不读取/打印真实凭据，不启动服务 |
| M-DB1 独立临时 SQLite | PASS：upgrade → downgrade -1 → upgrade；唯一约束/索引/FK声明/persona 非空默认值符合派单；临时目录限定在本树审计目录，连接关闭后清理 |
| 合成图片 EXIF/GPS/方向 | PASS；未使用用户图片 |
| 联调最小复现 | 默认资源对象 → ScaleSubmitResponse ValidationError；warning join TypeError；输出文本控制字符残留；识餐 NaN 非有限 |
| 真实模型 / 浏览器 | 未运行；未向外部模型发送心理数据或图片 |

结论：M-SEC1 指定文件的功能与安全回归已完成，**集成验收受 A01/A02 阻断，待 cline 独立评审**。所有跨域整改仅在本树 talking.txt 留言；不修改他人文件、不自行合并 main。

## 外部依据（2026-11-15 核对）

- 心理健康数据应按敏感信息审慎处理；用途告知、必要保留与权利流程按适用情形落实，不能由一个加密字段推定整套系统合规。参考《个人信息保护法》第 17、19、28–30、47 条：[工信部公布文本](https://www.miit.gov.cn/zwgk/zcwj/flfg/art/2022/art_04a0f1fb5df244e39688fd5372623a8d.html)。本报告为源码风险审计，部署主体还需结合实际处理活动确认适用要求。
- 阳性初筛需要专业人员进一步评估；本产品阈值是派单规定的支持策略，不是诊断或完整临床风险评估。参考 [NIMH 成人门诊简短安全评估指引](https://www.nimh.nih.gov/research/research-conducted-at-nimh/asq-toolkit-materials/adult-outpatient/adult-outpatient-brief-suicide-safety-assessment-guide)。该指引用于专业人员，本应用不复制其中的方法细节询问。
- 上传需要同时验证身份、权限、类型与资源限额：[OWASP File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)。
- 提示词不是权限或数据边界；模型输出需按下游用途独立校验：[OWASP LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)。
