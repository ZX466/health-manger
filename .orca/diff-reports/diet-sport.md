# 原型 vs 前端逐页差异：饮食 / 运动

参考文件（绝对路径）：
- 原型：`E:\zxdevelop\opendesign\8d699fa3-6b49-4dbf-b40b-29c55c1d6429\index.html`、`styles.css`、`app.js`
- 前端：`E:\zxdevelop\project1\frontend\src\views\DietManagement.vue`、`SportManagement.vue`、`styles\v21.css`、`api\food.js`、`api\index.js`
- 后端：`E:\zxdevelop\project1\models.py`、`services\food_service.py`、`services\sport_service.py`
- 说明：原型为无鉴权 mock（识别是 `app.js:974-988` 的定时器假结果，确认入库仅 `app.js:450-478` 追加 DOM），不得当作需求；真实 API 链路必须保留。

## 一、饮食账本差异

| 差异项 | 原型（带行号） | 当前前端（带行号） | 类型 | 优先级 | 工作量 |
|---|---|---|---|---|---|
| 页面信息架构 | `index.html:309-335` 顶部 diet-grid 双栏（摄入面板+餐单）；`:337-357` 下方周趋势+便签；单视图 | `DietManagement.vue:23-56` 全宽摘要 + `:58-71` 三 Tab（记录/食物库/统计），`:132-221` 食物库与统计 | 结构 | P1 | L（不建议照搬单视图） |
| 今日摄入宏量营养 | `index.html:317-321` 蛋白质/脂肪/碳水三条 macro bar；`styles.css:981-985` | `DietManagement.vue:48-55` 仅有各餐次热量 chips；`services\food_service.py:172-183` stats 只聚合总热量与餐次 | 视觉/结构 | P2 | M-L（需扩 stats 或前端按 Food 宏量字段聚合 `models.py:83-95`） |
| 餐单行信息 | `index.html:328-331` 时间+餐次+菜名+热量；`styles.css:989-993` | `DietManagement.vue:97-111` 餐次 pill+食物名+克数·kcal+删除，无时间；后端 `record_date` 已有（`services\food_service.py:119-120`） | 视觉/文案 | P1 | S |
| 餐单底部引导 | `index.html:333` fineprint“今天的蛋白质还差一点…”+“再记一餐” | `DietManagement.vue:91-94` 仅有识别成功 scanNotice，无 footer | 交互/文案 | P2 | S |
| 周摄入趋势 | `index.html:338-350` “本周摄入”7 日柱状图+日均；`styles.css:996-1001` | 饮食页无周图；统计 Tab 仅当日各餐分布（`DietManagement.vue:196-203`） | 结构/视觉 | P1 | M |
| 餐数口径 | `index.html:325` “4 餐” | `DietManagement.vue:87` “{{ foodRecords.length }} 条” | 文案 | P2 | S |
| 识别触发/重识 | `index.html:642` 手动“开始识别”，`:650` “重新识别”；`app.js:974-988` | `DietManagement.vue:624-639` 选图即自动识别，`:253` 仅“重拍/换一张” | 交互 | P2 | S（保留自动，可补“重新识别”） |
| 克数→热量联动 | `app.js:372-386` 改克数按 per100 自动重算 kcal | `DietManagement.vue:282-291` 克数与热量两个独立输入，互不联动 | 交互 | P1 | S |
| 识别结果字段 | `index.html:646-651` 名称只读+克数+热量+移除；`app.js:361-407` | `DietManagement.vue:276-293` 名称可编辑、显示置信度、可移除；`:689-703` 逐项创建自定义食物+记录 | 交互（前端更强） | P2 | 勿回退 |
| 餐次选择时机 | `index.html:640` 识别前选餐次 | `DietManagement.vue:264-273` 识别结果出现后选餐次 | 交互 | P2 | S |
| 识餐提示文案 | `index.html:641` “识别建议…把餐盘放平” | `DietManagement.vue:229` scan-sub、`:295` scan-note，语义等价 | 文案 | P2 | S |
| 顶部操作 | `index.html:306` 仅“拍照识餐” | `DietManagement.vue:12-19` 另有“添加记录” | 交互（前端多） | — | 勿回退 |
| 日期与视图切换 | 原型无 | `DietManagement.vue:58-80` Tab + 日期选择器 | 交互（前端多） | — | 勿回退 |

## 二、运动记录差异

| 差异项 | 原型（带行号） | 当前前端（带行号） | 类型 | 优先级 | 工作量 |
|---|---|---|---|---|---|
| Hero 主题 | `styles.css:1008-1023` 深色 `--ink` 底、白字、进度条反色 | `v21.css:2399-2404` 沿用浅色 v21-panel（`v21.css:1292-1297`） | 视觉 | P1 | S |
| Hero 主指标 | `index.html:371-377` 步数 6,840/8,000+进度条 | `SportManagement.vue:21-31` 消耗 kcal/400（`:320`）；`models.py:129-141` 无步数字段 | 结构/数据 | P2 | L（需建模） |
| Hero 统计布局 | `index.html:378-382` 右侧三列，label 上数字下；`styles.css:1024-1027` | `SportManagement.vue:33-49` 右栏纵向三行 label-value；`v21.css:2458-2490` | 视觉 | P1 | S-M |
| 统计指标 | `index.html:379-381` 活动消耗/活跃时长/今日运动次数 | `SportManagement.vue:34-48` 活跃时长/运动次数/平均每次 | 结构/文案 | P2 | S |
| 周趋势 | `index.html:386-398` “本周步数”+周均步数 | `SportManagement.vue:69-87` “近 7 天消耗”+周均 kcal；`:355-373` 真实 7 天聚合 | 文案/数据 | P1 | M（依赖步数） |
| 快捷添加 | `index.html:402-406` 固定快走/慢跑/宿舍力量，一步补记；`app.js:516-543` | `SportManagement.vue:89-108` 取运动库前 3、统一 20 分钟、kcal 估算；`:342-354`；`:554-560` 打开预填弹窗待确认 | 交互 | P2 | M（可加一键直记） |
| 活动行 | `index.html:414-415` 名称+时间·距离·时长+“+步数” | `SportManagement.vue:118-128` 名称+时间·时长·备注+kcal+删除；`:561-567` recordMeta | 视觉/数据 | P2 | M（距离需建模） |
| 页头状态 | `index.html:368` 静态“今日已打卡”chip | `SportManagement.vue:10-17` 动态打卡 chip + “添加记录”按钮 | 交互（前端多） | — | 勿回退 |

响应式：原型 `styles.css:1428-1435`（diet-grid/diet-lower 单列）、`:1461-1462`（sport-hero 单列、stats 改上边框）；真实 `v21.css:1990/1997`（饮食断点）、`:2974-3030`（运动断点，≤820px facts 转三列）。两侧均具备收窄方案，无实质差异，无需动作。

## 三、原型有、前端缺

饮食：
1. 本周摄入 7 日柱状图（`index.html:338-350`）。
2. 蛋白质/脂肪/碳水三条进度条（`index.html:317-321`）。
3. 餐单时间列（`index.html:328-331`）。
4. 餐单底部 fineprint + “再记一餐”（`index.html:333`）。
5. 识餐“开始识别/重新识别”手动步骤（`index.html:642,650`，前端自动识别更优，不建议搬）。

运动：
1. 步数及 8,000 步目标、Hero 进度（`index.html:374-376`）；距离字段（`:414-415`）——均无后端字段（`models.py:129-141`）。
2. Hero 深色主题（`styles.css:1016-1023`）。
3. 三列 Hero 统计块（`styles.css:1024-1027`）。
4. 快捷添加一步即记（`app.js:516-543`）。
5. 活动行“+步数”文案（`index.html:414-415`）。

## 四、前端有、原型没有（勿回退）

饮食：
- 三 Tab、日期筛选（`DietManagement.vue:58-80`）；食物库搜索与管理员增删改（`:132-175`、`:519-583`）。
- 统计 Tab 各餐次分布（`:177-207`）；记录删除（`:103-111`）。
- 真实 `/food/recognize` 识别、置信度、名称可编辑、逐项自定义食物入库（`:640-703`；`api\food.js:40-51`）。
- 识别成功 notice 与错误态（`:91-94`、`:261`、`:709-710`）。

运动：
- 运动记录/运动库/统计分析三 Tab（`SportManagement.vue:52-65`）；运动库搜索与管理员 CRUD（`:136-178`、`:476-537`）。
- 备注字段、记录删除、动态打卡 chip、添加记录按钮（`:223-253`、`:125-127`、`:10-17`）。
- 近 7 天真实聚合与柱状图 tooltip（`:75-86`、`:355-373`）。
- 快捷添加的预填弹窗（可编辑时长/备注，`:554-560`）与真实 API persistence（`api\index.js:49-58`）。

事实校正：实际读取未见饮食/运动列表的分页或加载骨架；列表请求失败仅 `console.error`（`DietManagement.vue:474-496`、`SportManagement.vue:419-460`），写入失败用 `alert`（`DietManagement.vue:507-518`）。制定计划时不要把“已有分页/加载态”当作现状。

## 五、落地建议

饮食：
1. 先做三个 S 级对齐：餐单行显示时间（直接用 `record_date`）、克数改动自动重算热量（保留热量可手改）、补餐单底部“再记一餐”，均无需改后端。
2. 复用现有 `bar-chart` 视觉补“本周摄入”7 日图；前端拉 6 天额外 `getFoodRecords` 聚合即可（stats 接口已支持 start/end_date，`services\food_service.py:172-183`）。宏量条放 P2，需扩 stats 聚合，禁止用 mock 值。
3. 保留 Tab、管理员 CRUD 与真实识别入库链路；不照搬原型单视图和“内存追加餐行”。

运动：
1. 纯 CSS 将 Hero 改深色 ink（复用 `--ink`/反色文字）并把右侧统计改三列，可低成本贴近原型视觉。
2. 步数/距离需扩 `UserSportRecord`（`models.py:129-141`），建议单独立项；落地前周图继续用 kcal，并把文案统一为“近 7 天消耗”。
3. 快捷添加可增加“直接补记 20 分钟”路径（复用 `createSportRecord`），同时保留预填弹窗供编辑备注。
