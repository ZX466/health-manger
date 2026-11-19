<template>
  <div class="dash">
    <header class="page-head">
      <span class="folio" aria-hidden="true">01</span>
      <div class="page-head-copy">
        <p class="eyebrow">TODAY / {{ dateStamp }}</p>
        <h1>身体简报<span class="title-dot">.</span></h1>
        <p class="deck">{{ todayNarrative }}</p>
      </div>
      <div class="page-actions">
        <span class="status-chip">
          <span class="status-dot" :class="statusDotClass"></span>
          {{ statusLabel }}
        </span>
        <router-link class="btn btn-primary" to="/chat">找搭子聊聊</router-link>
      </div>
    </header>

    <section v-if="mentalSerious" class="dash-care" aria-labelledby="care-title">
      <div class="care-mark"><AppIcon name="heart" :size="20" /></div>
      <div class="care-copy">
        <h2 id="care-title">今天先照顾自己</h2>
        <p>不用一个人扛着。去心理空间看看支持资源，或联系学校心理咨询中心。如有危机想法，请立即拨打 120 或 12356。</p>
        <div class="care-lines">
          <a href="tel:120">120</a>
          <a href="tel:12356">12356</a>
          <router-link class="btn btn-ghost" to="/mental">去心理空间</router-link>
        </div>
      </div>
    </section>

    <router-link
      v-if="warningStore.stats.unread"
      class="dash-warning"
      to="/warnings"
      aria-label="查看健康预警"
    >
      <span class="dash-warning-mark"><AppIcon name="alert" :size="18" /></span>
      <span class="dash-warning-copy">
        <span class="micro">ALERTS / {{ warningStore.stats.danger ? 'ACTION NEEDED' : 'UNREAD' }}</span>
        <strong>{{ warningStore.stats.unread }} 条健康提醒待查看</strong>
        <small>
          {{
            warningStore.stats.danger
              ? `${warningStore.stats.danger} 条危险级提醒，建议优先处理。`
              : '来自最近的体检记录与量表结果。'
          }}
        </small>
      </span>
      <AppIcon name="arrow" :size="16" />
    </router-link>

    <div class="dashboard-grid">
      <section class="score-panel" aria-labelledby="score-title">
        <div class="score-panel-head">
          <span class="micro micro--inverse">HEALTH SCORE</span>
          <div class="score-ranges" role="group" aria-label="评分时间范围">
            <button
              v-for="key in rangeKeys"
              :key="key"
              type="button"
              class="score-range"
              :class="{ 'is-active': activeRange === key }"
              :aria-pressed="activeRange === key"
              @click="switchRange(key)"
            >
              {{ rangeLabels[key] }}
            </button>
          </div>
          <span class="score-delta">{{ rangeStatusText }}</span>
        </div>
        <div class="score-main">
          <div class="score-ring" aria-hidden="true">
            <svg viewBox="0 0 180 180">
              <circle class="ring-track" cx="90" cy="90" r="72" />
              <circle
                class="ring-bar"
                cx="90" cy="90" r="72"
                :stroke-dasharray="ringCircumference"
                :stroke-dashoffset="ringOffset"
              />
            </svg>
            <div class="score-number"><strong>{{ ringScore }}</strong><span>/ 100</span></div>
          </div>
          <div class="score-copy">
            <p class="micro micro--inverse" id="score-title">当前称号</p>
            <h2>{{ statusLabel }}</h2>
            <p>{{ scoreNarrative }}</p>
            <div class="score-tags">
              <span v-for="tag in scoreTags" :key="tag">{{ tag }}</span>
            </div>
          </div>
        </div>
        <div class="score-foot">
          <div><span>昨晚睡眠</span><strong>{{ todaySleepText }}</strong></div>
          <div><span>静息心率</span><strong>{{ restingHeartRate }} <small>bpm</small></strong></div>
          <div><span>7 天欠账</span><strong>{{ sleepDebtText }}</strong></div>
        </div>
      </section>

      <aside class="brief-panel" aria-labelledby="brief-title">
        <div class="panel-head">
          <span class="micro">TODAY, IN SHORT</span>
          <span class="micro">{{ briefItems.length }} / 04</span>
        </div>
        <h2 class="sr-only" id="brief-title">今日简报</h2>
        <ol class="brief-list">
          <li v-for="item in briefItems" :key="item.index">
            <span class="brief-index">{{ item.index }}</span>
            <div>
              <p class="brief-title">{{ item.title }}</p>
              <p class="brief-note">{{ item.note }}</p>
            </div>
            <span class="brief-state" :class="{ 'brief-state--warn': item.warn }">{{ item.state }}</span>
          </li>
        </ol>
        <div class="companion">
          <div class="mascot" aria-hidden="true">
            <MiniNailong :animation="reduced ? 'none' : 'float'" />
          </div>
          <div>
            <p class="micro">{{ avatarBubbleTitle }}</p>
            <p class="companion-text">{{ avatarBubble }}</p>
          </div>
        </div>
      </aside>
    </div>

    <div class="dashboard-lower">
      <section class="trend-panel" aria-labelledby="trend-title">
        <div class="panel-head">
          <span class="micro">LAST 7 DAYS</span>
          <span class="micro">睡眠 / 精神</span>
        </div>
        <div class="panel-title-row">
          <h2 id="trend-title">这一周，身体在说什么</h2>
          <span class="trend-note">{{ trendNote }}</span>
        </div>
        <div v-if="trendReady" class="chart-wrap">
          <svg class="chart chart--dashboard" viewBox="0 0 720 220" role="img" aria-label="近七天睡眠时长与精神状态趋势">
            <g class="chart-grid">
              <path d="M44 32H690M44 84H690M44 136H690M44 188H690" />
              <path d="M44 32V188M150 32V188M256 32V188M362 32V188M468 32V188M574 32V188M690 32V188" />
            </g>
            <g class="chart-axis chart-axis-y">
              <text x="32" y="36">8h</text>
              <text x="32" y="88">7h</text>
              <text x="32" y="140">6h</text>
              <text x="32" y="192">5h</text>
            </g>
            <g class="chart-axis chart-axis-x">
              <text
                v-for="label in trendLabels"
                :key="label.text"
                :x="label.x"
                y="208"
                :text-anchor="label.anchor"
              >{{ label.text }}</text>
            </g>
            <path v-if="sleepPath" class="chart-line chart-line--sleep" :d="sleepPath" />
            <path v-if="moodPath" class="chart-line chart-line--mood" :d="moodPath" />
            <g class="chart-dots chart-dots--sleep">
              <circle v-for="p in sleepPoints" :key="'s' + p.x" :cx="p.x" :cy="p.y" r="3.5" />
            </g>
            <g class="chart-dots chart-dots--mood">
              <circle v-for="p in moodPoints" :key="'m' + p.x" :cx="p.x" :cy="p.y" r="3" />
            </g>
          </svg>
        </div>
        <div v-else class="chart-empty">还没有足够的睡眠与心情记录。今晚打卡后，这里会长出第一条曲线。</div>
        <div class="legend">
          <span class="legend-item"><i class="legend-line" />睡眠时长</span>
          <span class="legend-item"><i class="legend-line legend-line--mood" />精神状态</span>
          <span class="legend-item legend-item--note">目标睡眠 8h</span>
        </div>
      </section>

      <section v-if="!mentalSerious && persona.canShare" class="persona-panel" aria-labelledby="persona-title">
        <div class="panel-head">
          <span class="micro">TODAY'S PERSONA</span>
          <span class="micro">{{ personaDate }}</span>
        </div>
        <p class="persona-kicker">今日人设</p>
        <h2 id="persona-title">{{ persona.title }}</h2>
        <p class="persona-short">{{ persona.short }}</p>
        <div class="persona-tags"><span v-for="tag in persona.tags" :key="tag">{{ tag }}</span></div>
        <p class="persona-share">{{ personaSharePreview }}</p>
        <div class="persona-actions">
          <button class="btn btn-primary" type="button" @click="copyPersona">
            <AppIcon name="copy" :size="15" />{{ copied ? '已复制' : '复制分享文案' }}
          </button>
          <router-link class="btn btn-ghost" to="/mental">去心理空间</router-link>
        </div>
      </section>
      <section v-else class="persona-panel" aria-labelledby="persona-title">
        <div class="panel-head">
          <span class="micro">TODAY'S PERSONA</span>
          <span class="micro">—</span>
        </div>
        <p class="persona-kicker">今日人设</p>
        <h2 id="persona-title">今天不玩梗</h2>
        <p class="persona-short">检测到身体或情绪指标明显异常。先把今天过稳，再谈人设。</p>
        <p v-if="!mentalSerious" class="persona-share">建议查看健康记录，必要时前往校医院或联系辅导员。</p>
        <p v-else class="persona-share">支持资源在心理空间。你不需要一个人扛。</p>
        <div class="persona-actions">
          <router-link class="btn btn-primary" to="/health-record">查看健康记录</router-link>
          <router-link class="btn btn-ghost" to="/mental">去心理空间</router-link>
        </div>
      </section>
    </div>

    <nav class="quick-row" aria-label="快捷入口">
      <router-link class="quick-link" to="/mental">
        <span class="micro">02 / MOOD</span><strong>今天心情怎么样</strong><AppIcon name="arrow" :size="16" />
      </router-link>
      <router-link class="quick-link" to="/diet-management">
        <span class="micro">03 / FOOD</span><strong>拍一张，算算热量</strong><AppIcon name="arrow" :size="16" />
      </router-link>
      <router-link class="quick-link" to="/health-record">
        <span class="micro">05 / RECORD</span><strong>体检单自动填入</strong><AppIcon name="arrow" :size="16" />
      </router-link>
      <router-link class="quick-link" to="/chat">
        <span class="micro">09 / CHAT</span><strong>身体问诊 / 心理树洞</strong><AppIcon name="arrow" :size="16" />
      </router-link>
    </nav>

    <div class="toast" :class="{ show: toastVisible }" role="status" aria-live="polite">
      <AppIcon name="check" :size="16" :stroke="2.2" />
      <span>{{ toastMsg }}</span>
    </div>
  </div>
</template>

<script>
import api from '../api'
import MemeGallery from '../components/MemeGallery.vue'
import AudioPlayer from '../components/AudioPlayer.vue'
import AppIcon from '../components/AppIcon.vue'
import MiniNailong from '../components/mascots/MiniNailong.vue'
import { buildPersonaCard, getHealthTier, moodTitle } from '../constants/copywriting'
import { formatShortDate, localDateKey } from '../utils/date'
import { summarizeRatingHistory } from '../utils/ratingHistory'
import { useWellnessStore } from '../stores/wellness'
import { useWarningStore } from '../stores/warnings'

export default {
  name: 'Dashboard',
  components: { MemeGallery, AudioPlayer, AppIcon, MiniNailong },
  setup() {
    return { warningStore: useWarningStore() }
  },
  data() {
    return {
      userName: '',
      currentDate: '',
      stats: { totalRecords: 0 },
      latestRecord: null,
      latestAnalysis: null,
      latestRating: null,
      analysisLoading: true,

      // score ring
      ringCircumference: 2 * Math.PI * 72,
      ringScore: 0,
      ringOffset: 2 * Math.PI * 96,
      ringLevel: '—',
      ringDelta: '',
      activeRange: 'today',
      rangeKeys: ['today', 'w7', 'm30'],
      rangeLabels: { today: '今日', w7: '近 7 天', m30: '近 30 天' },
      ranges: {
        today: { score: 0, level: '—', delta: '暂无评分', hasScore: false, recorded: 0, days: 1 },
        w7:    { score: 0, level: '暂无评分', delta: '近 7 天暂无评分', hasScore: false, recorded: 0, days: 7 },
        m30:   { score: 0, level: '暂无评分', delta: '近 30 天暂无评分', hasScore: false, recorded: 0, days: 30 }
      },

      // chart
      chartDays: ['周一','周二','周三','周四','周五','周六','周日'],
      chartIntake: [2180, 1950, 2260, 1830, 2070, 2450, 1680],
      chartBurn:   [420, 380, 520, 310, 460, 610, 350],
      chartGoal: 2000,
      chartMax: 2600,
      chartReal: false,

      // tasks
      tasks: [
        { name: '饮水 1500 / 2000 ml', meta: '建议全天均匀补水', icon: 'water', progress: 75, done: false },
        { name: '久坐提醒 · 已起身 3 次', meta: '每 45 分钟站立活动 1–2 分钟', icon: 'activity', progress: null, done: false },
        { name: '23:30 前放下手机', meta: '睡前 30 分钟避免屏幕光', icon: 'moon', progress: null, done: true }
      ],

      // modules
      moduleList: [
        { id: 'record', title: '健康记录', desc: '体重 · 血压 · 睡眠', path: '/health-record', icon: 'record' },
        { id: 'diet', title: '饮食管理', desc: '三餐 · 热量 · 营养', path: '/diet-management', icon: 'diet' },
        { id: 'sport', title: '运动管理', desc: '训练 · 时长 · 消耗', path: '/sport-management', icon: 'sport' },
        { id: 'ai', title: 'AI 健康分析', desc: '趋势解读 · 建议', path: '/health-analysis', icon: 'ai' },
        { id: 'mental', title: '心理空间', desc: '情绪 · 量表 · 放松', path: '/mental', icon: 'heart' },
        { id: 'tongue', title: '中医舌诊', desc: '舌象分析 · 体质调理', path: '/tongue-diagnosis', icon: 'tongue' },
        { id: 'warning', title: '健康预警', desc: '异常监测 · 风险提醒', path: '', icon: 'alert' }
      ],

      // mental
      mentalSerious: false,
      mentalSummary: null,
      mentalTrend: { dates: [], mood_score: [], sleep_hours: [] },
      trendLoaded: false,
      wellness: null,
      personaGenerated: false,
      copied: false,
      copyTimer: null,

      // fun
      funOpen: false,

      // modal
      modalOpen: false,
      modalType: 'weight',
      modalValue: '',
      modalNote: '',
      modalError: false,
      modalSaving: false,
      modalUnit: 'kg',
      modalUnits: { weight: 'kg', bp: 'mmHg', hr: 'bpm', sleep: 'h' },

      // toast
      toastVisible: false,
      toastMsg: '',
      toastTimer: null,

      // misc
      reduced: false,
      store: { get(k,d){try{var v=localStorage.getItem(k);return v===null?d:v}catch(e){return d}}, set(k,v){try{localStorage.setItem(k,v)}catch(e){}} }
    }
  },
  computed: {
    greeting() {
      const h = new Date().getHours()
      if (h < 12) return '上午好'
      if (h < 18) return '下午好'
      return '晚上好'
    },
    completedTasks() {
      return this.tasks.filter(t => t.done).length
    },
    displayMetrics() {
      const r = this.latestRecord
      const m = []
      // BMI
      if (r && r.bmi) {
        const bmi = parseFloat(r.bmi)
        const st = bmi < 18.5 ? '偏瘦' : bmi < 24 ? '正常' : bmi < 28 ? '偏胖' : '肥胖'
        m.push({ key:'bmi', label:'BMI 体质指数', value:bmi.toFixed(1), unit:'kg/m²', badgeClass: st==='正常'?'badge-ok':st==='偏瘦'?'badge-info':'badge-warn', badgeText:st, trendClass:'trend-flat', trendIcon:'', trendValue:'', trendNote:'最新记录' })
      } else {
        m.push({ key:'bmi', label:'BMI 体质指数', value:'22.4', unit:'kg/m²', badgeClass:'badge-ok', badgeText:'正常', trendClass:'trend-flat', trendIcon:'', trendValue:'', trendNote:'示例数据' })
      }
      // Blood pressure
      if (r && r.blood_pressure_systolic) {
        m.push({ key:'bp', label:'血压', value:r.blood_pressure_systolic+'/'+r.blood_pressure_diastolic, unit:'mmHg', badgeClass:'badge-ok', badgeText:'正常', trendClass:'trend-flat', trendIcon:'', trendValue:'', trendNote:'最新记录' })
      } else {
        m.push({ key:'bp', label:'血压', value:'118/76', unit:'mmHg', badgeClass:'badge-ok', badgeText:'正常', trendClass:'trend-flat', trendIcon:'', trendValue:'', trendNote:'示例数据' })
      }
      // Heart rate
      if (r && r.heart_rate) {
        m.push({ key:'hr', label:'静息心率', value:String(r.heart_rate), unit:'bpm', badgeClass:'badge-ok', badgeText:'正常', trendClass:'trend-flat', trendIcon:'', trendValue:'', trendNote:'最新记录' })
      } else {
        m.push({ key:'hr', label:'静息心率', value:'68', unit:'bpm', badgeClass:'badge-ok', badgeText:'正常', trendClass:'trend-up', trendIcon:'▼', trendValue:'3', trendNote:'示例数据' })
      }
      // Sleep
      if (r && r.sleep_hours) {
        m.push({ key:'sleep', label:'夜间睡眠', value:String(r.sleep_hours), unit:'h', badgeClass:'badge-ok', badgeText:'良好', trendClass:'trend-flat', trendIcon:'', trendValue:'', trendNote:'最新记录' })
      } else {
        m.push({ key:'sleep', label:'夜间睡眠', value:'7.2', unit:'h', badgeClass:'badge-ok', badgeText:'良好', trendClass:'trend-up', trendIcon:'▲', trendValue:'0.4', trendNote:'示例数据' })
      }
      return m
    },
    analysisItems() {
      if (!this.latestAnalysis) {
        return ['暂无分析数据，完成健康记录后查看', '保持规律作息和均衡饮食', '定期记录健康指标以获得更准确的分析']
      }
      const items = []
      if (this.latestAnalysis.bmi_advice) items.push(this.latestAnalysis.bmi_advice)
      if (this.latestAnalysis.blood_pressure_advice) items.push(this.latestAnalysis.blood_pressure_advice)
      if (this.latestAnalysis.overall_advice) items.push(this.latestAnalysis.overall_advice)
      return items.length > 0 ? items : ['暂无分析建议']
    },
    persona() {
      const w = this.wellness
      return buildPersonaCard({
        score: this.latestRating?.score,
        rating: this.latestRating?.rating,
        bedtimeHour: w?.bedtimeHour,
        moodLevel: w?.moodLevel,
        stressTags: w?.stressTags,
        sleepHours: w?.sleepHours ?? this.latestRecord?.sleep_hours,
        hasSport: w?.hasSportToday,
        isHighRisk: this.mentalSerious || !!w?.isDanger
      })
    },
    statusLabel() {
      if (this.activeRange !== 'today') {
        const range = this.ranges[this.activeRange]
        return range?.hasScore ? range.level : '暂无评分'
      }
      if (this.mentalSerious) return '先照顾自己'
      if (this.latestRating?.rating === '危险') return '重点关怀'
      return this.persona.tier.title
    },
    rangeStatusText() {
      const range = this.ranges[this.activeRange]
      if (!range) return ''
      if (!range.hasScore) {
        return this.activeRange === 'today' ? '暂无评分' : `近 ${range.days} 天暂无评分`
      }
      return range.delta
    },
    todayMoodRecord() {
      const latest = this.mentalSummary?.latest_mood
      if (!latest?.record_date) return null
      const key = String(latest.record_date).slice(0, 10)
      return key === localDateKey() ? latest : null
    },
    todayMoodLevel() {
      const level = this.todayMoodRecord?.mood_score ?? this.wellness?.moodLevel
      const value = Number(level)
      return Number.isFinite(value) ? Math.min(5, Math.max(1, value)) : null
    },
    todayMoodText() {
      if (!this.todayMoodLevel) return '还没打卡'
      if (this.mentalSerious) {
        return { 1: '很难受', 2: '有些低落', 3: '一般', 4: '尚可', 5: '稳定' }[this.todayMoodLevel]
      }
      return moodTitle(this.todayMoodLevel)
    },
    todayMoodTone() {
      if (!this.todayMoodLevel) return 'none'
      if (this.todayMoodLevel <= 2) return 'low'
      if (this.todayMoodLevel >= 4) return 'good'
      return 'mid'
    },
    todaySleepHours() {
      const value = this.todayMoodRecord?.sleep_hours
      return value == null ? null : Number(value)
    },
    todaySleepText() {
      return this.todaySleepHours == null ? '—' : `${this.todaySleepHours.toFixed(1)}h`
    },
    sleepAvgValue() {
      const value = this.mentalSummary?.sleep_avg_7d
      const number = Number(value)
      return value == null || !Number.isFinite(number) ? null : number
    },
    sleepDebtValue() {
      const value = this.mentalSummary?.sleep_debt_7d
      const number = Number(value)
      return value == null || !Number.isFinite(number) ? null : number
    },
    sleepAvgText() {
      return this.sleepAvgValue == null ? '—' : `${this.sleepAvgValue.toFixed(1)}h`
    },
    sleepDebtText() {
      return this.sleepDebtValue == null ? '—' : `${this.sleepDebtValue.toFixed(1)}h`
    },
    moodTags() {
      const tags = this.wellness?.stressTags
      return Array.isArray(tags) ? tags.filter(tag => typeof tag === 'string' && tag).slice(0, 3) : []
    },
    avatarBubble() {
      if (this.mentalSerious) {
        return '今天先不玩梗。愿意的话，去心理空间看看支持资源。'
      }
      return this.wellness?.avatarBubble || '今天也在认真照顾自己，慢一点也没关系。'
    },
    avatarBubbleTitle() {
      const state = this.wellness?.avatarState
      if (state === 'night_owl') return '修仙中'
      if (state === 'low_mood') return '电量偏低'
      if (state === 'energetic') return '状态在线'
      return '慢慢来'
    },
    todayHeadline() {
      if (this.mentalSerious) return '今天先照顾自己'
      if (this.sleepAvgValue != null && this.sleepAvgValue < 7) {
        return `近 7 天平均睡眠 ${this.sleepAvgText}，今晚早点休息`
      }
      if (this.sleepDebtValue != null && this.sleepDebtValue >= 1.5) {
        return `近 7 天睡眠欠账 ${this.sleepDebtText}，今晚补一补`
      }
      if (this.todayMoodLevel != null && this.todayMoodLevel <= 2) {
        return '情绪电量偏低，先做一件小事就好'
      }
      if (this.ringScore >= 85) return '状态在线，保持今天的节奏'
      if (this.ringScore > 0) return '状态一般，先把睡眠和情绪照顾好'
      return '从一条健康记录开始，慢慢了解自己'
    },
    todayNarrative() {
      if (this.mentalSerious) {
        return '不用一个人扛着。需要的话，去心理空间看看支持资源，或联系学校心理咨询中心。'
      }
      const parts = []
      if (this.todayMoodLevel) parts.push(`今天的心情是「${this.todayMoodText}」`)
      else parts.push('今天还没有心情打卡')
      if (this.todaySleepHours != null) parts.push(`昨晚睡了 ${this.todaySleepText}`)
      else if (this.sleepAvgValue != null) parts.push(`近 7 天平均睡眠 ${this.sleepAvgText}`)
      return `${parts.join('，')}。`
    },
    dateStamp() {
      const now = new Date()
      const pad = value => String(value).padStart(2, '0')
      return `${now.getFullYear()}.${pad(now.getMonth() + 1)}.${pad(now.getDate())}`
    },
    personaSharePreview() {
      if (!this.persona?.canShare) return ''
      const lines = String(this.persona.shareText || '').split('\n')
      return lines
        .slice(2)
        .map(line => line.replace(/^[·\s]+/, '').trim())
        .filter(Boolean)
        .join(' · ')
    },
    personaDate() {
      const now = new Date()
      return `${String(now.getMonth() + 1).padStart(2, '0')} / ${String(now.getDate()).padStart(2, '0')}`
    },
    statusDotClass() {
      if (this.mentalSerious) return 'status-dot--danger'
      if (this.persona.canShare) return 'status-dot--success'
      return 'status-dot--accent'
    },
    scoreNarrative() {
      if (this.activeRange !== 'today') {
        const range = this.ranges[this.activeRange]
        if (!range?.hasScore) {
          return `近 ${range?.days || ''} 天还没有评分记录。先记录一次体检，这里会慢慢长出趋势。`
        }
        const coverage = range.recorded === range.days
          ? `${range.days} 天都有记录`
          : `${range.days} 天里记录了 ${range.recorded} 天`
        return `近 ${range.days} 天平均 ${range.score} 分，${coverage}。`
      }
      if (this.mentalSerious) return '今天先不追求满分。把支持资源放在手边，先照顾好自己。'
      return this.todayHeadline
    },
    scoreTags() {
      if (this.activeRange !== 'today') {
        const range = this.ranges[this.activeRange]
        if (!range?.hasScore) return ['等待记录', '先做一次体检']
        return [`${range.days} 天均值`, `${range.recorded}/${range.days} 天记录`, range.level]
      }
      const tags = []
      if (this.sleepDebtValue != null) tags.push(`睡眠债 ${this.sleepDebtText}`)
      if (this.todayMoodLevel) tags.push(`心情 ${this.todayMoodText}`)
      if (this.wellness?.hasSportToday) tags.push('今日已运动')
      else tags.push('待运动')
      if (!tags.length) tags.push(`睡眠 ${this.sleepAvgText}`)
      return tags.slice(0, 3)
    },
    restingHeartRate() {
      const value = this.latestRecord?.heart_rate
      return value == null ? '—' : String(value)
    },
    briefItems() {
      const sleep = this.todaySleepHours
      const hasMood = !!this.todayMoodRecord
      const hasSport = !!this.wellness?.hasSportToday
      const recordDate = this.latestRecord?.record_date
      return [
        {
          index: '01',
          title: '睡眠',
          note: sleep == null ? '昨晚还没有睡眠记录 · 目标 8h' : `昨晚 ${this.todaySleepText} · 目标 8h`,
          state: sleep == null ? '未记录' : sleep < 7 ? '偏低' : '达标',
          warn: sleep == null || sleep < 7
        },
        {
          index: '02',
          title: '心情',
          note: hasMood ? `今天已记录「${this.todayMoodText}」` : '今天还没有打卡',
          state: hasMood ? '已记录' : '待打卡',
          warn: !hasMood
        },
        {
          index: '03',
          title: '运动',
          note: hasSport ? '今天已完成运动打卡' : '今天还没有运动记录',
          state: hasSport ? '已打卡' : '待运动',
          warn: !hasSport
        },
        {
          index: '04',
          title: '体检',
          note: recordDate ? `最近记录 ${formatShortDate(recordDate)}` : '还没有体检记录',
          state: recordDate ? '有记录' : '待记录',
          warn: !recordDate
        }
      ]
    },
    trendSeries() {
      const dates = Array.isArray(this.mentalTrend?.dates) ? this.mentalTrend.dates : []
      const moods = Array.isArray(this.mentalTrend?.mood_score) ? this.mentalTrend.mood_score : []
      const sleeps = Array.isArray(this.mentalTrend?.sleep_hours) ? this.mentalTrend.sleep_hours : []
      const xAt = index => 44 + index * (646 / 6)
      const sleepY = hours => 188 - ((Math.min(8, Math.max(5, Number(hours))) - 5) / 3) * 156
      const moodY = level => 188 - ((Math.min(5, Math.max(1, Number(level))) - 1) / 4) * 156
      const build = (values, toY) => {
        const points = []
        let path = ''
        let open = false
        values.slice(0, 7).forEach((value, index) => {
          if (value == null || !Number.isFinite(Number(value))) {
            open = false
            return
          }
          const point = { x: xAt(index), y: toY(value) }
          points.push(point)
          path += `${open ? ' L' : ' M'}${point.x.toFixed(1)} ${point.y.toFixed(1)}`
          open = true
        })
        return { points, path: path.trim() }
      }
      const sleep = build(sleeps, sleepY)
      const mood = build(moods, moodY)
      return {
        dates: dates.slice(0, 7),
        sleepPoints: sleep.points,
        moodPoints: mood.points,
        sleepPath: sleep.points.length > 1 ? sleep.path : '',
        moodPath: mood.points.length > 1 ? mood.path : '',
        recorded: dates.slice(0, 7).filter((_, index) => sleeps[index] != null || moods[index] != null).length
      }
    },
    trendReady() {
      const series = this.trendSeries
      return series.sleepPoints.length > 0 || series.moodPoints.length > 0
    },
    sleepPoints() {
      return this.trendSeries.sleepPoints
    },
    moodPoints() {
      return this.trendSeries.moodPoints
    },
    sleepPath() {
      return this.trendSeries.sleepPath
    },
    moodPath() {
      return this.trendSeries.moodPath
    },
    trendLabels() {
      const dates = this.trendSeries.dates
      return dates.map((date, index) => {
        const parsed = new Date(`${date}T00:00:00`)
        const text = Number.isNaN(parsed.getTime())
          ? String(date).slice(5).replace('-', '/')
          : `${parsed.getMonth() + 1}/${parsed.getDate()}`
        return {
          text,
          x: (44 + index * (646 / 6)).toFixed(1),
          anchor: index === 0 ? 'start' : index === dates.length - 1 ? 'end' : 'middle'
        }
      })
    },
    trendNote() {
      if (!this.trendReady) return '等待记录'
      const count = this.trendSeries.recorded
      return count >= 4 ? `已记录 ${count} 天` : `刚开始记录 · ${count} 天`
    },
    scaleSummaries() {
      const build = (key, title, item) => {
        if (!item) return { key, title, result: '还没测过', tone: 'muted', has: false }
        const score = item.score != null ? `${item.score} 分` : ''
        const label = item.label || ''
        const date = item.created_at ? ` · ${formatShortDate(item.created_at)}` : ''
        return {
          key,
          title,
          result: [score, label].filter(Boolean).join(' · ') + date || '已完成',
          tone: item.crisis_flag ? 'danger' : 'normal',
          has: true
        }
      }
      return [
        build('PHQ-9', '情绪晴雨表', this.mentalSummary?.latest_phq9),
        build('GAD-7', '焦虑自测', this.mentalSummary?.latest_gad7)
      ]
    }
  },
  async mounted() {
    this.reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    this.currentDate = new Date().toLocaleDateString('zh-CN', {
      year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
    })

    // restore persisted state
    const savedRange = this.store.get('hd:range', 'today')
    if (this.rangeLabels[savedRange]) this.activeRange = savedRange
    this.funOpen = this.store.get('hd:fun', '0') === '1'

    // load API data
    await this.loadUserInfo()
    await this.loadStats()
    await this.loadMentalSummary()
    await this.loadTrend()
    await this.loadWellness()
    this.warningStore.refreshStats(true)

    // paint ring after data is ready
    this.$nextTick(() => {
      this.paintRange(this.activeRange)
    })
  },
  methods: {
    async loadUserInfo() {
      try {
        const res = await api.getCurrentUser()
        this.userName = res.data.name || ''
      } catch (e) { /* silent */ }
    },
    async loadMentalSummary() {
      try {
        const res = await api.getMentalSummary()
        this.mentalSummary = res.data || null
        this.mentalSerious = !!res.data?.serious_mode
        if (res.data?.serious_mode) useWellnessStore().markSerious()
      } catch (e) { /* 心理摘要不可用不影响首页 */ }
    },
    async loadWellness() {
      try {
        const wellness = useWellnessStore()
        wellness.hydrateLocal()
        await wellness.load()
        this.wellness = wellness
        if (wellness.isHighRisk) this.mentalSerious = true
      } catch (e) { /* 状态源不可用时人设卡退化为评分文案 */ }
    },
    async loadTrend() {
      try {
        const res = await api.getMentalTrend({ days: 7 })
        const data = res.data || {}
        this.mentalTrend = {
          dates: Array.isArray(data.dates) ? data.dates : [],
          mood_score: Array.isArray(data.mood_score) ? data.mood_score : [],
          sleep_hours: Array.isArray(data.sleep_hours) ? data.sleep_hours : []
        }
      } catch (e) {
        this.mentalTrend = { dates: [], mood_score: [], sleep_hours: [] }
      }
      this.trendLoaded = true
    },
    generatePersona() {
      const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
      this.personaGenerated = true
      if (!reduced) {
        requestAnimationFrame(() => {
          this.$el?.querySelector('.persona-card')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
        })
      }
      this.showToast('今日人设卡已生成')
    },
    async copyPersona() {
      if (!this.persona.canShare) {
        this.showToast('今天先不分享，照顾好自己更重要')
        return
      }
      const text = this.persona.shareText
      try {
        await navigator.clipboard.writeText(text)
      } catch (e) {
        const area = document.createElement('textarea')
        area.value = text
        area.style.position = 'fixed'
        area.style.opacity = '0'
        document.body.appendChild(area)
        area.select()
        document.execCommand('copy')
        area.remove()
      }
      this.copied = true
      clearTimeout(this.copyTimer)
      this.copyTimer = setTimeout(() => { this.copied = false }, 2000)
      this.showToast('文案已复制，去发朋友圈吧')
    },
    async loadStats() {
      try {
        const recRes = await api.getHealthRecords()
        this.stats.totalRecords = recRes.data.length
        if (recRes.data.length > 0) this.latestRecord = recRes.data[0]

        // F-N2: 真实健康记录接入趋势图（每日记录次数）；无记录时保持示例并标注
        const records = recRes.data || []
        if (records.length >= 1) {
          const byDay = {}
          records.slice(0, 14).forEach(r => {
            const d = r.record_date ? new Date(r.record_date).toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' }) : '今日'
            byDay[d] = (byDay[d] || 0) + 1
          })
          const entries = Object.entries(byDay).slice(-7)
          this.chartDays = entries.map(([k]) => k)
          this.chartIntake = entries.map(([, v]) => v)
          this.chartBurn = []
          this.chartGoal = 0
          this.chartMax = Math.max(...this.chartIntake, 1) * 1.3
          this.chartReal = true
        }

        const analysisRes = await api.getLatestAnalysis()
        this.latestAnalysis = analysisRes.data
      } catch (e) { /* silent */ }
      this.analysisLoading = false

      try {
        const ratingRes = await api.getLatestRating()
        if (ratingRes.data && ratingRes.data.score != null) {
          this.latestRating = ratingRes.data
          this.ranges.today = {
            score: ratingRes.data.score,
            level: getHealthTier({
              score: ratingRes.data.score,
              rating: ratingRes.data.rating
            }).title,
            delta: '今日评分',
            hasScore: true,
            recorded: 1,
            days: 1
          }
        }
      } catch (e) { /* silent */ }

      await Promise.all([this.loadRatingHistory(7), this.loadRatingHistory(30)])

      // re-paint ring with real data
      this.$nextTick(() => {
        this.paintRange(this.activeRange)
      })
    },
    async loadRatingHistory(days) {
      const key = days === 7 ? 'w7' : 'm30'
      try {
        const res = await api.getRatingHistory(days)
        const summary = summarizeRatingHistory(res.data, days)
        this.ranges[key] = {
          score: summary.score,
          level: summary.hasScore ? getHealthTier({ score: summary.score }).title : '暂无评分',
          delta: summary.hasScore
            ? `近 ${days} 天均值 · ${summary.recorded} 天有记录`
            : `近 ${days} 天暂无评分`,
          hasScore: summary.hasScore,
          recorded: summary.recorded,
          days
        }
        if (this.activeRange === key) this.paintRange(key)
      } catch (e) {
        this.ranges[key] = {
          score: 0,
          level: '暂无评分',
          delta: `近 ${days} 天暂无评分`,
          hasScore: false,
          recorded: 0,
          days
        }
        if (this.activeRange === key) this.paintRange(key)
      }
    },

    // ---- score ring ----
    switchRange(key) {
      this.activeRange = key
      this.store.set('hd:range', key)
      this.paintRange(key)
    },
    paintRange(key) {
      const d = this.ranges[key]
      if (!d) return
      const target = d.score
      this.ringLevel = d.level
      this.ringDelta = d.delta

      if (this.reduced) {
        this.ringScore = target
        this.ringOffset = this.ringCircumference * (1 - target / 100)
        return
      }
      const from = this.ringScore
      const t0 = performance.now()
      const dur = 700
      const animate = (now) => {
        const p = Math.min(1, (now - t0) / dur)
        const eased = 1 - Math.pow(1 - p, 3)
        this.ringScore = Math.round(from + (target - from) * eased)
        this.ringOffset = this.ringCircumference * (1 - eased * target / 100)
        if (p < 1) requestAnimationFrame(animate)
      }
      // reset to start for ring fill animation
      this.ringOffset = this.ringCircumference
      requestAnimationFrame(animate)
    },

    // ---- chart ----
    renderChart() {
      const svg = this.$refs.trendChart
      if (!svg) return
      svg.innerHTML = ''
      const ns = 'http://www.w3.org/2000/svg'
      const mk = (tag, attrs) => {
        const el = document.createElementNS(ns, tag)
        for (const k in attrs) el.setAttribute(k, attrs[k])
        return el
      }
      const W=600, H=260, PL=46, PR=14, PT=16, PB=34
      const X0=PL, X1=W-PR, Y0=PT, Y1=H-PB
      const MAX=this.chartMax
      const px = i => X0 + i * (X1-X0) / (this.chartDays.length-1)
      const py = v => Y1 - (v/MAX) * (Y1-Y0)
      const linePath = arr => arr.map((v,i) => (i===0?'M':'L') + px(i).toFixed(1) + ' ' + py(v).toFixed(1)).join(' ')
      const areaPath = arr => linePath(arr) + ' L' + px(arr.length-1).toFixed(1) + ' ' + Y1 + ' L' + X0 + ' ' + Y1 + ' Z'

      // grid + y labels
      for (let g=0; g<=4; g++) {
        const yv = MAX/4*g, y = py(yv)
        svg.appendChild(mk('line', { x1:X0, y1:y, x2:X1, y2:y, stroke:'var(--border)', 'stroke-width':1 }))
        const lbl = mk('text', { x:X0-8, y:y+4, 'text-anchor':'end', 'font-size':11, fill:'var(--muted-strong)' })
        lbl.textContent = yv
        svg.appendChild(lbl)
      }
      // x labels
      this.chartDays.forEach((d, i) => {
        const t = mk('text', { x:px(i), y:H-12, 'text-anchor':'middle', 'font-size':11, fill:'var(--muted-strong)' })
        t.textContent = d
        svg.appendChild(t)
      })
      // goal line（示例模式才显示）
      if (!this.chartReal) {
        svg.appendChild(mk('line', { x1:X0, y1:py(this.chartGoal), x2:X1, y2:py(this.chartGoal), stroke:'var(--muted)', 'stroke-width':1.4, 'stroke-dasharray':'4 6', opacity:0.75 }))
      }
      // areas + lines
      svg.appendChild(mk('path', { d:areaPath(this.chartIntake), fill:'var(--warn)', opacity:0.12, 'pointer-events':'none' }))
      svg.appendChild(mk('path', { d:linePath(this.chartIntake), fill:'none', stroke:'var(--warn)', 'stroke-width':2.2, 'stroke-linecap':'round', 'pointer-events':'none' }))
      if (this.chartBurn.length) {
        svg.appendChild(mk('path', { d:areaPath(this.chartBurn), fill:'var(--success)', opacity:0.12, 'pointer-events':'none' }))
        svg.appendChild(mk('path', { d:linePath(this.chartBurn), fill:'none', stroke:'var(--success)', 'stroke-width':2.2, 'stroke-linecap':'round', 'pointer-events':'none' }))
      }
      // dots
      this.chartIntake.forEach((v,i) => svg.appendChild(mk('circle', { cx:px(i), cy:py(v), r:3.4, fill:'var(--surface)', stroke:'var(--warn)', 'stroke-width':2, 'pointer-events':'none' })))
      if (this.chartBurn.length) {
        this.chartBurn.forEach((v,i) => svg.appendChild(mk('circle', { cx:px(i), cy:py(v), r:3.4, fill:'var(--surface)', stroke:'var(--success)', 'stroke-width':2, 'pointer-events':'none' })))
      }
      // hit area + tooltip
      const hit = mk('rect', { x:X0-4, y:Y0, width:X1-X0+8, height:Y1-Y0, fill:'transparent' })
      svg.appendChild(hit)
      const tip = this.$refs.chartTip
      const chartBox = this.$refs.chartBox
      if (hit && tip) {
        hit.addEventListener('mousemove', (e) => {
          const rect = svg.getBoundingClientRect()
          const rx = (e.clientX - rect.left) * (W / rect.width)
          const idx = Math.max(0, Math.min(this.chartDays.length-1, Math.round((rx - X0) / ((X1-X0) / (this.chartDays.length-1)))))
          const cx = px(idx) * (rect.width / W)
          tip.innerHTML = this.chartReal
            ? '<div><b>记录数 ' + this.chartIntake[idx] + '</b> · ' + this.chartDays[idx] + '</div>'
            : '<div><b>摄入 ' + this.chartIntake[idx] + ' kcal</b> · 消耗 ' + (this.chartBurn[idx] || 0) + ' kcal</div><div style="opacity:.75;margin-top:2px;">' + this.chartDays[idx] + ' · 目标 ' + this.chartGoal + '</div>'
          tip.classList.add('show')
          const cw = chartBox.clientWidth
          tip.style.left = Math.min(Math.max(cx, 70), cw - 150) + 'px'
          tip.style.top = '18px'
        })
        hit.addEventListener('mouseleave', () => tip.classList.remove('show'))
      }
    },

    // ---- fun ----
    toggleFun() {
      this.funOpen = !this.funOpen
      this.store.set('hd:fun', this.funOpen ? '1' : '0')
    },

    // ---- modal ----
    openModal() {
      this.modalOpen = true
      this.modalError = false
      this.$nextTick(() => {
        if (this.$refs.modalEl) this.$refs.modalEl.focus()
      })
    },
    closeModal() {
      this.modalOpen = false
    },
    updateUnit() {
      this.modalUnit = this.modalUnits[this.modalType] || ''
    },
    async submitRecord() {
      const v = parseFloat(this.modalValue)
      const valid = this.modalValue !== '' && !isNaN(v) && v > 0
      this.modalError = !valid
      if (!valid) {
        this.$nextTick(() => { if (this.$refs.recValueInput) this.$refs.recValueInput.focus() })
        return
      }
      this.modalSaving = true
      // simulate save (replace with real API call when available)
      setTimeout(() => {
        this.modalSaving = false
        this.modalOpen = false
        this.modalValue = ''
        this.modalNote = ''
        this.showToast('已保存到健康记录（示例）')
      }, 500)
    },

    // ---- toast ----
    showToast(msg) {
      this.toastMsg = msg
      this.toastVisible = true
      clearTimeout(this.toastTimer)
      this.toastTimer = setTimeout(() => { this.toastVisible = false }, 2600)
    },

    // ---- navigation ----
    navigate(path) {
      if (!path) {
        this.showToast('该功能即将上线')
        return
      }
      this.$router.push(path)
    }
  }
}
</script>
