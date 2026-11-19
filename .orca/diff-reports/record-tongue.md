# 设计原型 vs 真实前端差异报告：体检 / 舌诊

原型：`E:\zxdevelop\opendesign\8d699fa3-6b49-4dbf-b40b-29c55c1d6429`（index.html / styles.css / app.js）
前端：`E:\zxdevelop\project1\frontend\src\views\HealthRecord.vue`、`TongueDiagnosis.vue`、`styles\v21.css`、`styles\tokens.css`、`stores\tongue.js`

## 体检

差异项 | 原型 | 当前前端 | 类型 | 优先级 | 工作量
---|---|---|---|---|---
信息架构 | index.html:432-472 左 OCR 面板、右最近记录、趋势通栏 | HealthRecord.vue:62-321 表单 1.4fr 左、历史列表 1fr 右，OCR 仅为表单内一条 bar | 结构 | P0 | M
页面头文案 | index.html:425-427 eyebrow `RECORD / OCR`、标题“体检档案.”、deck“拍一张体检单…” | HealthRecord.vue:4-8 `RECORD / CHECKUP`、“健康记录”、deck“把体检数字留在这里…” | 文案 | P2 | S
主 CTA | index.html:429 “拍体检单” | HealthRecord.vue:11-25 顶部只有单选/多选切换，无拍照入口 | 结构 | P2 | S
上传区形态 | index.html:437-443 156px 虚线大上传区 + “开始识别”；styles.css:1061-1085 | HealthRecord.vue:69-92 隐藏 input + 小按钮“拍体检单自动填”+ 说明/置信度 | 视觉/交互 | P1 | M
OCR 确认 | index.html:655-671 弹窗预览 6 字段后“填入表单”；app.js:1001-1017、488-514 | HealthRecord.vue:552-590 识别后直接回填 8 字段，无逐项核对 | 交互 | P2 | M
表单模型 | index.html:446-460 “最近一次体检”8 个预填数值（含血糖）+“保存档案” | HealthRecord.vue:64-207 空白问卷 4 组、11 字段（含体温/运动/睡眠/饮食）、“提交并查看评级”；无血糖字段（grep 0） | 结构 | P1 | L
字段视觉 | index.html:449-458 扁平两列、单位内联；styles.css:1087-1088 | HealthRecord.vue:97-200 survey-group 警示色底 + input-hint 后缀块；1087-1128 | 视觉 | P2 | M
异常提示 | index.html:459 固定 abnormal-box（轻度近视/睡眠不足） | HealthRecord.vue:88-90 仅 OCR 后 ocrAbnormal chips | 结构/文案 | P2 | S
历史 | index.html:464-471 “体检趋势/近 3 次”三行；styles.css:877-891 | HealthRecord.vue:210-318 卡片含 BMI、评级徽章、6 指标、详情/导出/删除、多选批量 | 结构 | P1 | L
免责声明 | index.html:460“数据仅用于健康管理，不替代诊断。” | HealthRecord.vue 全文无（grep 不替代/仅供 0） | 文案 | P1 | S
卡片视觉 | styles.css:1059-1090 平边卡片、无阴影 | HealthRecord.vue:1207-1219、1295、1413 白卡 + `rgba(255,155,113,…)` 橙色光晕；与 v21.css:19 蓝色 accent 及 tokens.css:50“阴影仅限弹层与下拉”冲突 | 视觉 | P1 | M
面板头 | index.html:434/447/465 micro+h2 三段式 | HealthRecord.vue:64-67/211-212 仅 h2 + 一行 hint | 视觉 | P2 | S

## 舌诊

差异项 | 原型 | 当前前端 | 类型 | 优先级 | 工作量
---|---|---|---|---|---
页面头 | index.html:479-481 “赛博把脉.”/deck“拍张舌象…熬了多少夜” | TongueDiagnosis.vue:4-7 “舌诊”/deck“自然光、舌头放平…” | 文案 | P2 | S
信息架构 | index.html:486-520 左右等分：取景区 | 结果卡 | TongueDiagnosis.vue:56-447 292px 控制栏 + 舞台/结果/历史堆叠 | 结构 | P1 | M
输入区 | index.html:490-505 SVG 舌象示意图、四角取景标、上传/分析并排、3 条提示 | TongueDiagnosis.vue:59-113 拖拽上传/预览 + 全宽“开始分析”+清除；另有摄像头 tabs:17-29、115-158 | 视觉/结构 | P2 | M
结果卡 | index.html:508-519 静态示例：舌象句标题、摘要句、3 行、建议卡、免责 | TongueDiagnosis.vue:360-445 空态→证型标题 + 置信度条 + 7 行特征表 + 3 建议块 + 导出/重算 | 结构 | P1 | M
免责声明 | index.html:518 | TongueDiagnosis.vue 无（grep 0） | 文案 | P1 | S
建议块视觉 | styles.css:1117-1122 accent-soft 卡 | TongueDiagnosis.vue:1515-1525 普通分隔块 | 视觉 | P2 | S
加载文案 | index.html:504“正在看舌象...” | TongueDiagnosis.vue:101-104“分析中…” | 文案 | P2 | S
响应式 | styles.css:1425-1427 两栅格 1024 折一列 | HealthRecord.vue:1191-1195 1100 折；TongueDiagnosis.vue:1552-1596 820 折 + `display:contents` 重排 | 交互 | P2 | S

## 原型有、前端缺

- 体检上传大区块 + 顶部拍照 CTA（index.html:429、437-443）
- OCR 识别结果逐项预览/核对再填入（index.html:663-668）
- 空腹血糖字段（index.html:455、666；后端字段需另评估，不是纯样式）
- “LATEST RECORD / 更新于”（447）、趋势简表（464-471）
- 舌象取景框示意与四角标（490-499）
- 结果摘要句（511）、齿痕专门提示（515）
- 两页免责声明（460、518）；“咖啡/有色食物等 30 分钟”（505）

## 前端有、原型没有（勿回退）

- OCR 真实上传、10MB/类型校验、置信度、异常 chips（HealthRecord.vue:69-92、533-590）
- 健康评级横幅与提交后评级弹层（30-60）
- 记录卡详情/导出/删除/批量/多选（210-345、737-789）
- 空态吉祥物、操作日志（227-235、421-434）
- 舌诊摄像头实时分析、置信度阈值、分析频率、舌苔手动修正（17-29、115-224）
- 统计面板、历史缩略图（受保护 blob）、详情、删除确认、导出报告/重算（31-54、325-358、653-783）

## 落地建议

1. 体检页做“OCR 升格”：保留创建/评级/列表真实能力，把 ocr-bar 扩为原型式上传面板 + 复用现有回填做核对层，补免责声明；同时去掉橙色光晕白卡，改 v21 边框面板与蓝色 accent（P0/P1，M）。
2. 舌诊页只调阅读顺序：保留控制栏、摄像头、历史，把舞台与结果改为原型式同屏左右（或结果紧贴舞台），补免责与摘要句；顺手修 realtime-strip 键名错位——`TongueDiagnosis.vue:319` 读 `item.tcm_syndrome`，而 `stores\tongue.js:45` 写入 `syndrome`，当前直播证型为空（S-M）。
3. mock 不作为需求：原型“保存档案/更新于刚刚”“示例结果”、预填数值均不移植；只移植信息层级、取景框与文案语气（S）。
