/**
 * 搭子声画素材目录。
 * 图片/音频均位于 public/assets，原型阶段就绪；这里集中管理，避免页面里散落字符串。
 */

const BASE = '/assets'

export const AUDIO_CLIPS = {
  giggle: {
    src: `${BASE}/audio/cartoon-giggle.mp3`,
    label: '轻快偷笑'
  },
  belly: {
    src: `${BASE}/audio/cartoon-belly-laugh.mp3`,
    label: '捧腹大笑'
  },
  crazy: {
    src: `${BASE}/audio/cartoon-crazy-laugh.mp3`,
    label: '魔性大笑'
  },
  pixabay: {
    src: `${BASE}/audio/pixabay-cartoon-laugh.mp3`,
    label: '欢笑连击'
  }
}

export const MEDIA_ASSETS = {
  hajimi: {
    key: 'hajimi',
    label: '哈基米',
    tagline: '高冷吐槽系猫咪，适合深夜监工与日常提醒',
    thumb: `${BASE}/images/hajimi/680bc15901f9fx7I.jpg`,
    static: [
      `${BASE}/images/hajimi/680bc15901f9fx7I.jpg`,
      `${BASE}/images/hajimi/681a46ece1cd1qft.jpeg`,
      `${BASE}/images/hajimi/68222c4cb855becx.jpeg`,
      `${BASE}/images/hajimi/68222c4df19feHWp.jpeg`,
      `${BASE}/images/hajimi/68222c4f29862DzT.jpeg`,
      `${BASE}/images/hajimi/68222c5114272wRK.jpeg`,
      `${BASE}/images/hajimi/681f86c26f89aviH.jpeg`,
      `${BASE}/images/hajimi/68222c4b783c1lFZ.jpeg`
    ],
    gif: [
      `${BASE}/images/hajimi/68222c4e5733aByW.gif`
    ]
  },
  nailong: {
    key: 'nailong',
    label: '奶龙',
    tagline: '魔性元气系动图与表情包，适合减压盲盒与加油',
    thumb: `${BASE}/images/nailong/png/png_09_6b2619b9f1b3440a84cff5a29bbf23f5.png`,
    static: [
      `${BASE}/images/nailong/png/png_09_6b2619b9f1b3440a84cff5a29bbf23f5.png`,
      `${BASE}/images/nailong/nailong_sample1.jpg`,
      `${BASE}/images/nailong/memes/bing_08_6750702430334j6k.jpg`,
      `${BASE}/images/nailong/memes/bing_11_6949a5f01b9025LH.jpeg`,
      `${BASE}/images/nailong/memes/bing_22_w700d1q75cms.jpg`,
      `${BASE}/images/nailong/memes/bing_23_6737706c14883XhG.jpg`,
      `${BASE}/images/nailong/memes/bing_24_v2-751d3f9fccb15bc9f52f6d279dbb65a5_r.jpg`,
      `${BASE}/images/nailong/memes/bing_30_6949a5f0394caQ4e.jpeg`,
      `${BASE}/images/nailong/memes/bing_36_v2-4d4d9445311930862d3c38a36d1cbd14_r.jpg`,
      `${BASE}/images/nailong/memes/bing_42_v2-6993b97ab9a240a082d72b7b4a1e2129_r.jpg`
    ],
    gif: [
      `${BASE}/images/nailong/gif/bing_20_20220303113117_3642d.thumb.400_0.gif`,
      `${BASE}/images/nailong/gif/bing_09_20210216082626_ZWCNd.gif`,
      `${BASE}/images/nailong/gif/bing_15_v2-7f2ada495b8d6e4247d0e5c317927ff5_1440w.gif`,
      `${BASE}/images/nailong/gif/bing_18_v2-c5f802c39a46f12f3bd083c00a64cb0c_1440w.gif`,
      `${BASE}/images/nailong/gif/bing_02_v2-77c7ecdd44ab5e3106ea61e738b55f8e_1440w.gif`,
      `${BASE}/images/nailong/gif/bing_19_v2-9a70cad278261b992329d7a5cf90f657_1440w.gif`
    ]
  }
}

export const COMPANION_KEYS = Object.keys(MEDIA_ASSETS)

export const BLINDBOX_CATALOG = [
  {
    id: 'bb-1',
    character: 'hajimi',
    title: '早八续命成功',
    audioKey: 'giggle',
    staticSrc: MEDIA_ASSETS.hajimi.static[0],
    gifSrc: MEDIA_ASSETS.hajimi.gif[0],
    alt: '哈基米早八续命表情'
  },
  {
    id: 'bb-2',
    character: 'nailong',
    title: '功德 +99 认证',
    audioKey: 'belly',
    staticSrc: MEDIA_ASSETS.nailong.static[2],
    gifSrc: MEDIA_ASSETS.nailong.gif[0],
    alt: '奶龙功德加满动图'
  },
  {
    id: 'bb-3',
    character: 'nailong',
    title: '热量刺客退散',
    audioKey: 'crazy',
    staticSrc: MEDIA_ASSETS.nailong.static[4],
    gifSrc: MEDIA_ASSETS.nailong.gif[1],
    alt: '奶龙热量刺客表情包'
  },
  {
    id: 'bb-4',
    character: 'hajimi',
    title: 'DDL 明天再说',
    audioKey: 'pixabay',
    staticSrc: MEDIA_ASSETS.hajimi.static[2],
    gifSrc: MEDIA_ASSETS.hajimi.gif[0],
    alt: '哈基米放松表情'
  },
  {
    id: 'bb-5',
    character: 'nailong',
    title: '允许今天当咸鱼',
    audioKey: 'giggle',
    staticSrc: MEDIA_ASSETS.nailong.static[6],
    gifSrc: MEDIA_ASSETS.nailong.gif[2],
    alt: '奶龙摸鱼动图'
  },
  {
    id: 'bb-6',
    character: 'hajimi',
    title: '熬夜监工上线',
    audioKey: 'belly',
    staticSrc: MEDIA_ASSETS.hajimi.static[3],
    gifSrc: MEDIA_ASSETS.hajimi.static[3],
    alt: '哈基米监工表情'
  },
  {
    id: 'bb-7',
    character: 'nailong',
    title: '操场溜达回血',
    audioKey: 'pixabay',
    staticSrc: MEDIA_ASSETS.nailong.static[8],
    gifSrc: MEDIA_ASSETS.nailong.gif[3],
    alt: '奶龙元气加油动图'
  },
  {
    id: 'bb-8',
    character: 'hajimi',
    title: '咖啡因精算师',
    audioKey: 'crazy',
    staticSrc: MEDIA_ASSETS.hajimi.static[5],
    gifSrc: MEDIA_ASSETS.hajimi.static[5],
    alt: '哈基米咖啡续命表情'
  }
]

export const BLINDBOX_FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'hajimi', label: '哈基米' },
  { key: 'nailong', label: '奶龙' },
  { key: 'favorites', label: '收藏' }
]

export const COMPANION_STATE_COPY = {
  night_owl: {
    pill: '修仙中',
    bubble: '再熬下去，发际线就要比你的绩点先起飞了。'
  },
  low_mood: {
    pill: '低电量',
    bubble: '允许自己今天当条咸鱼，深呼吸 3 次，天塌不下来。'
  },
  energetic: {
    pill: '自律上线',
    bubble: '自律这块被你拿捏了，今天就是朋友圈卷王本人。'
  },
  default: {
    pill: '状态在线',
    bubble: '先喝两口温水、起身溜达两分钟，体能电量稳稳在线。'
  },
  crisis: {
    pill: '先照顾你',
    bubble: '你不需要一个人扛着。先联系校心理中心，或者告诉一个信任的人。'
  }
}

export const CLINICAL_BUBBLE = '建议先补充睡眠，观察 3 天；如持续心悸或头晕，请到校医院就诊。'

export function companionPool (key = 'hajimi') {
  const asset = MEDIA_ASSETS[key] || MEDIA_ASSETS.hajimi
  return [...asset.gif, ...asset.static]
}

export function companionImage (key = 'hajimi', index = 0) {
  const pool = companionPool(key)
  if (!pool.length) return ''
  const safe = ((Number(index) || 0) % pool.length + pool.length) % pool.length
  return pool[safe]
}

/** 优先动图；系统减少动态或用户关闭动图时回退静态图。 */
export function mediaSrc (item, animated = true) {
  if (!item) return ''
  return animated && item.gifSrc ? item.gifSrc : (item.staticSrc || item.gifSrc)
}

export function buildMoodReaction ({ level, companion = 'hajimi', index = 0 } = {}) {
  const label = MEDIA_ASSETS[companion]?.label || '搭子'
  const score = Number(level) || 0
  if (score >= 4) {
    return {
      tone: 'success',
      tag: `${label}反馈 · 元气在线`,
      text: score === 5
        ? '今天松弛感拉满，继续保持这个舒服的节奏！'
        : '状态稳稳在线，今晚早点关灯就是满分收尾。',
      image: companionImage(companion, index + score),
      audio: score === 5 ? 'belly' : 'giggle'
    }
  }
  if (score === 3) {
    return {
      tone: '',
      tag: `${label}反馈 · 电量一般`,
      text: '已读乱回也没关系，先把今天的状态记下来，晚上别再硬撑了。',
      image: companionImage(companion, index + score),
      audio: ''
    }
  }
  return {
    tone: 'warn',
    tag: `${label}陪伴 · 轻声模式`,
    text: '电量见底就别勉强自己支棱起来了。倒杯温水，慢慢呼气，我在这儿陪你。',
    image: companionImage(companion, index + score),
    audio: ''
  }
}

export function buildDietReaction ({ intake = 0, goal = 2000, companion = 'hajimi', index = 0 } = {}) {
  const label = MEDIA_ASSETS[companion]?.label || '搭子'
  const total = Math.max(0, Number(intake) || 0)
  const target = Math.max(800, Number(goal) || 2000)
  const over = total > target
  return {
    tone: over ? 'warn' : 'success',
    tag: over ? `${label}餐评 · 热量刺客预警` : `${label}餐评 · 额度充足`,
    text: over
      ? `超出目标 ${(total - target).toLocaleString('zh-CN')} kcal！快乐是真快乐，晚饭后下楼绕操场走两圈消消食。`
      : `还剩 ${(target - total).toLocaleString('zh-CN')} kcal 额度，营养节奏很稳，晚饭加颗蛋就能体面收尾。`,
    image: companionImage(companion, index + (over ? 4 : 1)),
    audio: over ? 'crazy' : 'giggle'
  }
}

export function buildSportReaction ({ minutes = 0, calories = 0, count = 0, companion = 'hajimi', index = 0 } = {}) {
  const label = MEDIA_ASSETS[companion]?.label || '搭子'
  const active = Number(minutes) > 0 || Number(count) > 0
  return {
    tone: active ? 'success' : '',
    tag: active ? `${label}认证 · 今日已动起来` : `${label}加油 · 先下楼走两步`,
    text: active
      ? `今天已经活动 ${Number(minutes) || 0} 分钟、消耗 ${Number(calories) || 0} kcal，自律这块被你拿捏了，记得拉伸放松小腿。`
      : '步数设备还没接入，但你可以先手动记一次快走或拉伸。下楼溜达十分钟，也算给今天回血。',
    image: companionImage(companion, index + (active ? 5 : 3)),
    audio: active ? 'belly' : 'giggle'
  }
}
