/**
 * 集中式年轻化文案与随机金句。
 * 所有玩梗只作用于日常亚健康场景；危险评级与高危心理状态必须走关怀文案。
 */

export const HEALTH_TIERS = [
  {
    key: 'excellent',
    min: 95,
    max: 100,
    title: '六边形战士',
    short: '作息饮食全拉满，宿舍自律天花板',
    tone: 'success'
  },
  {
    key: 'good',
    min: 80,
    max: 94,
    title: '状态在线',
    short: '体能电量充足，继续保持这个节奏',
    tone: 'success'
  },
  {
    key: 'fair',
    min: 60,
    max: 79,
    title: '脆皮预警',
    short: '表面风平浪静，实则全靠咖啡和意志力硬撑',
    tone: 'warn'
  },
  {
    key: 'poor',
    min: 40,
    max: 59,
    title: '急需回血',
    short: '身体已亮起黄灯，今晚必须开启强制休眠模式',
    tone: 'warn'
  },
  {
    key: 'danger',
    min: 0,
    max: 39,
    title: '重点关怀',
    short: '检测到多项指标明显异常，请及时前往校医院或联系辅导员/家人',
    tone: 'danger'
  }
]

const RATING_TO_TIER = {
  优秀: 'excellent',
  良好: 'good',
  中等: 'fair',
  较差: 'poor',
  危险: 'danger'
}

export const MOOD_LEVELS = [
  { level: 5, title: '稳如老狗', face: 'calm', hint: '今天的心态很稳，适合把难事往前推一格' },
  { level: 4, title: '精神良好', face: 'good', hint: '还有余力，记得给自己留一点空白' },
  { level: 3, title: '已读乱回', face: 'neutral', hint: '有点走神也正常，先喝口水再继续' },
  { level: 2, title: '电量 5%', face: 'low', hint: '今天可以只完成最低限度的事' },
  { level: 1, title: '破防边缘', face: 'bad', hint: '先别硬撑，找个人说一句话也好' }
]

export const STRESS_TAGS = [
  '早八续命',
  '毕设 ddl',
  '期末周渡劫',
  '求职焦虑',
  '寝室社交',
  '钱包告急',
  '单纯想躺'
]

export const TIP_POOLS = {
  dietOver: [
    '捕获“热量刺客”！快乐是真快乐，今晚帕梅拉还债 30 分钟',
    '这顿碳水炸弹很顶，建议晚饭后下楼绕操场走两圈消消食',
    '好吃是好吃，就是腰带可能要申请工伤鉴定'
  ],
  sportEmpty: [
    '今日活动轨迹：床 → 拿外卖 → 床，建议下楼呼吸一口新鲜空气',
    '微信步数正在和躺平冠军争夺榜首',
    '先别急着自责，从走到楼下便利店开始也算运动'
  ],
  tongue: {
    title: '赛博把脉',
    subtitle: '拍张舌象，AI 帮你看看最近到底熬了多少夜'
  },
  aiLoading: [
    '正在翻阅《本草纲目》...',
    '正在扫描你的熬夜黑眼圈...',
    'AI 校医正在扶眼镜...',
    '正在计算昨晚欠下的睡眠债...'
  ],
  daily: [
    '今天先把水喝够，其他的事排队来',
    '久坐一小时了，站起来伸个懒腰也算赢',
    '晚饭后走十分钟，比在宿舍纠结更有用',
    '如果今天只能完成一件事，先保证睡够'
  ],
  nightOwl: [
    '再熬下去，发际线就要和期末成绩一起起飞了。',
    '凌晨的手机不会替你写论文，但黑眼圈会替你出席早八。',
    '今晚提前半小时放下手机，明天的你会回来道谢。'
  ],
  lowMood: [
    '允许自己今天当条咸鱼，深呼吸 3 次，天塌不下来。',
    '状态低的时候不用证明什么，先把今天过完。',
    '想哭就哭，眼泪不扣学分。'
  ],
  energetic: [
    '自律这块被你拿捏了，今天就是朋友圈卷王本人。',
    '这个状态很适合去操场刷两圈，顺便让室友羡慕一下。',
    '保持住，别让奶茶把你从神坛上拽下来。'
  ]
}

export const AI_LOADING_PHRASES = TIP_POOLS.aiLoading

export function pickRandom (list, fallback = '') {
  if (!Array.isArray(list) || list.length === 0) return fallback
  return list[Math.floor(Math.random() * list.length)]
}

function scoreOf (stats = {}) {
  const raw = stats.score ?? stats.healthScore
  const value = Number(raw)
  return Number.isFinite(value) ? Math.max(0, Math.min(100, value)) : null
}

export function getHealthTier (stats = {}) {
  const rating = stats.rating || stats.healthRating
  if (rating && RATING_TO_TIER[rating]) {
    return HEALTH_TIERS.find(tier => tier.key === RATING_TO_TIER[rating]) || HEALTH_TIERS[2]
  }
  const score = scoreOf(stats)
  if (score == null) return HEALTH_TIERS[2]
  return HEALTH_TIERS.find(tier => score >= tier.min && score <= tier.max) || HEALTH_TIERS[2]
}

export function isDangerousRating (stats = {}) {
  return getHealthTier(stats).key === 'danger'
}

export function moodTitle (level) {
  return MOOD_LEVELS.find(item => item.level === Number(level))?.title || '状态已记录'
}

export function bedtimeLabel (bedtimeHour) {
  const value = Number(bedtimeHour)
  if (!Number.isFinite(value)) return '未记录'
  const normalized = ((value % 24) + 24) % 24
  const hours = Math.floor(normalized)
  const minutes = Math.round((normalized - hours) * 60)
  return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}`
}

/**
 * 生成「当代大学生健康人设卡」。
 * @param {object} stats 最新健康分/评级、入睡时间、情绪等级、压力标签、今日运动、睡眠时长
 */
export function buildPersonaCard (stats = {}) {
  const tier = getHealthTier(stats)
  const score = scoreOf(stats)
  const bedtime = Number(stats.bedtimeHour)
  const mood = Number(stats.moodLevel)
  const tags = Array.isArray(stats.stressTags) ? stats.stressTags : []
  const sleepHours = Number(stats.sleepHours)
  const hasSport = !!stats.hasSport

  if (tier.key === 'danger' || stats.isHighRisk) {
    return {
      title: '【需要被认真照顾 · 先慢下来】',
      tier,
      tags: ['今天不玩梗'],
      canShare: false,
      short: '现在最重要的不是自律打卡，而是让身边的人知道你的状态。',
      shareText: '最近状态不太好，我准备先联系校医院或心理咨询中心，也告诉一个信任的人。',
      tip: '如果出现伤害自己的念头，请立刻联系 400-161-9995 / 12356，或拨打 120 / 110。'
    }
  }

  let title = '【稳中向好型 · 宿舍健康搭子】'
  let short = '没有惊天动地的自律，但每天都在认真照顾自己。'
  let toneTags = ['日常在线']

  if (bedtime >= 1.5) {
    title = '【熬夜修仙派 · 肝帝预备役】'
    short = '夜色是你的主场，但发际线已经开始写抗议书了。'
    toneTags = ['修仙中', '睡眠债']
  } else if (score != null && score >= 85 && hasSport) {
    title = '【间歇性自律 · 赛博养生选手】'
    short = '一边泡枸杞一边去操场，养生和运动都被你玩明白了。'
    toneTags = ['自律闪光', '今日有运动']
  } else if (mood && mood <= 2) {
    title = '【低电量待机 · 需要一点甜】'
    short = '今天不适合硬撑，适合热奶茶、热水澡和早点睡。'
    toneTags = ['低电量', '先照顾情绪']
  } else if (tags.includes('早八续命') || (score != null && score < 80)) {
    title = '【早八美式续命型 · 脆皮大学生】'
    short = '靠咖啡启动，靠意志力续航，建议今晚给身体补个觉。'
    toneTags = ['脆皮', '咖啡续命']
  } else if (tags.includes('毕设 ddl') || tags.includes('期末周渡劫')) {
    title = '【 ddl 特种兵 · 边赶工边养生】'
    short = '截止日期追着你跑，但你还没忘记喝水，这很了不起。'
    toneTags = ['ddl 战士', '忙里偷闲']
  } else if (tier.key === 'excellent') {
    title = '【六边形战士 · 宿舍自律天花板】'
    short = '作息、饮食、运动都在线，建议开班授课。'
    toneTags = ['满格状态', '自律天花板']
  } else if (tier.key === 'good') {
    title = '【状态在线 · 稳健型选手】'
    short = '节奏不错，继续保持，不用突然给自己加码。'
    toneTags = ['状态在线']
  }

  const tagText = [...new Set([...toneTags, ...tags.slice(0, 2)])].slice(0, 4)
  const scoreLine = score != null ? `健康分 ${score} ` : ''
  const sleepLine = Number.isFinite(sleepHours) ? `· 昨晚睡了 ${sleepHours} 小时` : ''
  const strongLine = hasSport ? '· 今天有运动打卡' : ''
  const shareText = [
    `【${title.replace(/^【|】$/g, '')}】`,
    short,
    `${scoreLine}${sleepLine} ${strongLine}`.trim(),
    `今日标签：${tagText.join(' · ')}`,
    '今天也有在认真照顾自己。'
  ].filter(Boolean).join('\n')

  return {
    title,
    tier,
    tags: tagText,
    canShare: true,
    short,
    shareText,
    tip: pickRandom(TIP_POOLS.daily)
  }
}
