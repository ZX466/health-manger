<template>
  <div class="dash">
    <!-- ===== Hero ===== -->
    <section class="hero" data-od-id="hero">
      <div class="hero-left">
        <p class="eyebrow">Dashboard · 今日概览</p>
        <h1>{{ greeting }}{{ userName ? '，' + userName : '' }}</h1>
        <p class="hero-date">{{ currentDate }}</p>
      </div>
      <div class="hero-right">
        <span class="mascot" role="img" aria-label="吉祥物小猫">
          <svg width="34" height="34" viewBox="0 0 36 36" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <path d="M18 27c-7 0-11.5-4.4-11.5-10S11 7 18 7s11.5 4.4 11.5 10S25 27 18 27z"/>
            <path d="M9.5 10.5 12 13M26.5 10.5 24 13M6.8 12 3.5 9.5M29.2 12 32.5 9.5"/>
            <circle cx="14.5" cy="15.5" r="1.1" fill="currentColor" stroke="none"/>
            <circle cx="21.5" cy="15.5" r="1.1" fill="currentColor" stroke="none"/>
            <path d="M14.5 20c2.3 1.8 4.7 1.8 7 0"/>
          </svg>
        </span>
        <span class="status-chip" v-if="latestRating">
          <AppIcon name="check" :size="14" :stroke="2" />
          {{ latestRating.rating || '今日状态良好' }}
        </span>
        <button class="btn btn-primary hero-record-btn" @click="openModal">
          <AppIcon name="plus" :size="16" :stroke="2" />
          快捷记录
        </button>
      </div>
    </section>

    <!-- ===== Overview: Score Ring + Metrics/Chart ===== -->
    <section class="overview" data-od-id="overview">
      <div class="card score-card" data-od-id="score-card">
        <div class="card-head">
          <h2 class="card-title">今日健康评分</h2>
          <span class="card-sub">综合五维指标{{ hasRealRating ? '' : ' · 示例' }}</span>
        </div>
        <div class="score-body">
          <div class="ring-wrap" ref="ringWrap">
            <svg class="ring-svg" width="220" height="220" viewBox="0 0 220 220" aria-hidden="true">
              <circle class="ring-track" cx="110" cy="110" r="96" stroke-width="14"></circle>
              <circle class="ring-bar" cx="110" cy="110" r="96" stroke-width="14"
                :stroke-dasharray="ringCircumference" :stroke-dashoffset="ringOffset"></circle>
            </svg>
            <div class="ring-center">
              <span class="ring-score">{{ ringScore }}</span>
              <span class="ring-level">{{ ringLevel }}</span>
              <span class="ring-delta">{{ ringDelta }}</span>
            </div>
          </div>
          <div class="seg" role="group" aria-label="评分区间">
            <button v-for="key in rangeKeys" :key="key"
              class="seg-btn" :class="{ active: activeRange === key }"
              @click="switchRange(key)">{{ rangeLabels[key] }}</button>
          </div>
        </div>
      </div>

      <div class="right-stack">
        <div class="metrics" data-od-id="metrics">
          <div class="metric" v-for="m in displayMetrics" :key="m.key" :data-od-id="'metric-' + m.key">
            <div class="metric-top">
              <span class="metric-label">{{ m.label }}</span>
              <span class="badge" :class="m.badgeClass">{{ m.badgeText }}</span>
            </div>
            <div class="metric-value">{{ m.value }}<span class="metric-unit" v-if="m.unit">{{ m.unit }}</span></div>
            <div class="metric-foot">
              <span v-if="m.trendIcon" :class="m.trendClass">{{ m.trendIcon }} {{ m.trendValue }}</span>
              <span class="trend-flat">{{ m.trendNote }}</span>
            </div>
          </div>
        </div>

        <div class="card" data-od-id="trend-card">
          <div class="card-head">
            <h2 class="card-title">{{ chartReal ? '近 7 天健康记录趋势' : '近 7 天热量趋势' }}</h2>
            <span class="card-sub">{{ chartReal ? '每日记录次数 · 真实数据' : '摄入 vs 运动消耗 · 示例数据' }}</span>
          </div>
          <div class="chart-box" ref="chartBox">
            <div class="chart-legend" aria-hidden="true">
              <span class="legend-item"><span class="legend-dot" style="background:var(--warn);"></span>{{ chartReal ? '每日记录数' : '热量摄入 kcal' }}</span>
              <span v-if="!chartReal" class="legend-item"><span class="legend-dot" style="background:var(--success);"></span>运动消耗 kcal</span>
              <span v-if="!chartReal" class="legend-item"><span class="legend-dot line" style="background:var(--muted);border-radius:2px;"></span>目标 2000</span>
            </div>
            <svg class="chart-svg" ref="trendChart" viewBox="0 0 600 260" role="img" :aria-label="chartReal ? '近7天健康记录趋势图，真实数据' : '近7天热量趋势图，数据为示例'"></svg>
            <div class="chart-tip" ref="chartTip"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== Today Habits ===== -->
    <section class="card" data-od-id="tasks-card">
      <div class="card-head">
        <h2 class="card-title">今日习惯</h2>
        <span class="card-sub">完成度 {{ completedTasks }}/{{ tasks.length }} · 示例数据</span>
      </div>
      <div class="tasks">
        <label class="task" v-for="(task, i) in tasks" :key="i">
          <input type="checkbox" class="sr-only" v-model="task.done" />
          <span class="task-check" aria-hidden="true">
            <AppIcon name="check" :size="13" :stroke="3" />
          </span>
          <span class="task-icon" aria-hidden="true"><AppIcon :name="task.icon" :size="18" /></span>
          <span class="task-body">
            <span class="task-name">{{ task.name }}</span>
            <span class="task-meta">{{ task.meta }}</span>
            <span class="task-progress" v-if="task.progress">
              <span class="task-progress-bar" :style="{ width: task.progress + '%' }"></span>
            </span>
          </span>
        </label>
      </div>
    </section>

    <!-- ===== Module Entries ===== -->
    <section class="card" data-od-id="modules-card">
      <div class="card-head">
        <h2 class="card-title">功能模块</h2>
        <span class="card-sub">全流程入口</span>
      </div>
      <div class="modules">
        <button v-for="mod in moduleList" :key="mod.id"
          class="module" :data-od-id="'module-' + mod.id"
          @click="navigate(mod.path)">
          <span class="module-icon" aria-hidden="true"><AppIcon :name="mod.icon" :size="20" /></span>
          <span class="module-title">{{ mod.title }}</span>
          <span class="module-desc">{{ mod.desc }}</span>
        </button>
      </div>
    </section>

    <!-- ===== AI Health Analysis ===== -->
    <section class="card" data-od-id="analysis-card" :aria-busy="analysisLoading">
      <div class="card-head">
        <h2 class="card-title">AI 健康分析</h2>
        <span class="card-sub">{{ analysisLoading ? '加载中…' : '基于最新记录的自动解读' }}</span>
      </div>
      <div v-if="analysisLoading" class="analysis-skeleton">
        <div class="skeleton sk-line" style="width:88%;"></div>
        <div class="skeleton sk-line" style="width:64%;"></div>
        <div class="skeleton sk-block"></div>
      </div>
      <div v-else class="analysis-body">
        <ul class="analysis-list">
          <li v-for="(item, i) in analysisItems" :key="i" class="analysis-line">
            <AppIcon name="check" :size="18" :stroke="1.9" />
            <span>{{ item }}</span>
          </li>
        </ul>
        <a class="link-more" href="#" @click.prevent="navigate('/health-analysis')">
          查看完整分析
          <AppIcon name="arrow" :size="15" :stroke="2" />
        </a>
        <div class="device-note">
          <AppIcon name="device" :size="18" :stroke="1.7" />
          <span>心率实时趋势需连接佩戴设备后启用。当前展示为示例数据。</span>
        </div>
      </div>
    </section>

    <!-- ===== Fun Section ===== -->
    <section data-od-id="fun-card">
      <button class="fun-toggle" @click="toggleFun" :aria-expanded="funOpen" aria-controls="funPanel">
        <span class="btn-w-icon">
          <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="8.5"/><path d="M8.5 14.5c1 1.4 2.3 2 3.5 2s2.5-.6 3.5-2"/><path d="M9 10h.01M15 10h.01"/></svg>
          趣图乐一乐 · 今日份放松
        </span>
        <AppIcon class="chev" name="chevron" :size="18" :stroke="1.8" />
      </button>
      <div class="fun-panel" v-show="funOpen" id="funPanel">
        <div class="fun-inner">
          <MemeGallery source="memes" title="奶龙表情包" :count="3" :cols="3" />
          <AudioPlayer />
        </div>
      </div>
    </section>

    <!-- ===== Quick Record Modal ===== -->
    <div class="modal-backdrop" v-show="modalOpen" @click.self="closeModal">
      <div class="modal" role="dialog" aria-modal="true" aria-labelledby="modalTitle" tabindex="-1" ref="modalEl" @keydown.esc.prevent="closeModal">
        <div class="modal-head">
          <div>
            <h2 class="modal-title" id="modalTitle">快捷记录</h2>
            <p class="modal-sub">保存后将出现在今日记录中</p>
          </div>
          <button class="icon-btn" @click="closeModal" aria-label="关闭">
            <AppIcon name="close" :size="18" :stroke="1.8" />
          </button>
        </div>
        <form @submit.prevent="submitRecord" novalidate>
          <div class="field">
            <label class="field-label" for="recType">记录类型</label>
            <select class="field-select" id="recType" v-model="modalType" @change="updateUnit">
              <option value="weight">体重</option>
              <option value="bp">血压</option>
              <option value="hr">心率</option>
              <option value="sleep">睡眠时长</option>
            </select>
          </div>
          <div class="field" :class="{ 'field-error': modalError }">
            <label class="field-label" for="recValue">数值<span class="field-note">{{ modalUnit }}</span></label>
            <div class="unit-suffix" :data-unit="modalUnit">
              <input class="field-input" id="recValue" type="number" inputmode="decimal" step="0.1" min="0" v-model="modalValue" placeholder="输入数值" ref="recValueInput" />
            </div>
            <p class="error-msg">请输入有效的数值</p>
          </div>
          <div class="field">
            <label class="field-label" for="recNote">备注（可选）</label>
            <textarea class="field-area" id="recNote" v-model="modalNote" placeholder="如：晨起空腹测量"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn btn-ghost" @click="closeModal">取消</button>
            <button type="submit" class="btn btn-primary" :disabled="modalSaving">
              <span v-if="modalSaving" class="spinner" aria-hidden="true"></span>
              {{ modalSaving ? '保存中' : '保存记录' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ===== Toast ===== -->
    <div class="toast" :class="{ show: toastVisible }" role="status" aria-live="polite">
      <AppIcon name="check" :size="16" :stroke="2.2" />
      <span>{{ toastMsg }}</span>
    </div>

    <!-- ===== Mobile Tab Bar ===== -->
    <nav class="tabbar" aria-label="移动端导航" data-od-id="tabbar">
      <div class="tabbar-inner">
        <button v-for="tab in tabList" :key="tab.id"
          class="tab" :class="{ active: activeTab === tab.id }"
          @click="onTabClick(tab)">
          <AppIcon :name="tab.icon" :size="20" aria-hidden="true" />
          {{ tab.label }}
        </button>
      </div>
    </nav>
  </div>
</template>

<script>
import api from '../api'
import MemeGallery from '../components/MemeGallery.vue'
import AudioPlayer from '../components/AudioPlayer.vue'
import AppIcon from '../components/AppIcon.vue'

export default {
  name: 'Dashboard',
  components: { MemeGallery, AudioPlayer, AppIcon },
  data() {
    return {
      userName: '',
      currentDate: '',
      stats: { totalRecords: 0 },
      latestRecord: null,
      latestAnalysis: null,
      latestRating: null,
      analysisLoading: true,
      hasRealRating: false,

      // score ring
      ringCircumference: 2 * Math.PI * 96,
      ringScore: 0,
      ringOffset: 2 * Math.PI * 96,
      ringLevel: '—',
      ringDelta: '',
      activeRange: 'today',
      rangeKeys: ['today', 'w7', 'm30'],
      rangeLabels: { today: '今日', w7: '近 7 天', m30: '近 30 天' },
      ranges: {
        today: { score: 0, level: '—', delta: '暂无评分' },
        w7:    { score: 82, level: '良好', delta: '近 7 天均值 · 示例' },
        m30:   { score: 78, level: '良好', delta: '近 30 天均值 · 示例' }
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
        { id: 'tongue', title: '中医舌诊', desc: '舌象分析 · 体质调理', path: '/tongue-diagnosis', icon: 'tongue' },
        { id: 'warning', title: '健康预警', desc: '异常监测 · 风险提醒', path: '', icon: 'alert' }
      ],

      // tab bar
      activeTab: 'home',
      tabList: [
        { id: 'home', label: '首页', path: '/dashboard', icon: 'home' },
        { id: 'record', label: '记录', path: '/health-record', icon: 'record' },
        { id: 'sport', label: '运动', path: '/sport-management', icon: 'sport' },
        { id: 'tongue', label: '舌诊', path: '/tongue-diagnosis', icon: 'tongue' },
        { id: 'mine', label: '我的', path: '', icon: 'user' }
      ],

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
    this.activeTab = this.store.get('hd:tab', 'home')

    // load API data
    await this.loadUserInfo()
    await this.loadStats()

    // render chart and paint ring after data is ready
    this.$nextTick(() => {
      this.renderChart()
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
        if (ratingRes.data && ratingRes.data.score) {
          this.latestRating = ratingRes.data
          this.hasRealRating = true
          this.ranges.today = {
            score: ratingRes.data.score,
            level: ratingRes.data.rating || '—',
            delta: '今日评分'
          }
        }
      } catch (e) { /* silent */ }

      // re-paint ring with real data
      this.$nextTick(() => {
        if (this.activeRange === 'today') this.paintRange('today')
      })
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

    // ---- tab bar ----
    onTabClick(tab) {
      this.activeTab = tab.id
      this.store.set('hd:tab', tab.id)
      if (tab.path) {
        this.navigate(tab.path)
      } else if (tab.id === 'mine') {
        this.showToast('个人中心即将上线')
      }
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

<style scoped>
.sr-only { position: absolute; width: 1px; height: 1px; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }

/* ===== root layout ===== */
.dash { display: flex; flex-direction: column; gap: 20px; }
@keyframes page-in { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: none; } }
.dash > * { animation: page-in 0.28s ease both; }
.dash > *:nth-child(2) { animation-delay: 0.04s; }
.dash > *:nth-child(3) { animation-delay: 0.08s; }

/* ===== hero ===== */
.hero { display: flex; align-items: center; justify-content: space-between; gap: 20px; padding: 24px 4px 8px; }
.eyebrow { font-size: 11px; font-weight: 600; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; }
.hero h1 { font-family: var(--font-display); font-size: 26px; font-weight: 700; line-height: 1.3; margin-top: 2px; }
.hero-date { font-size: 12.5px; color: var(--muted-strong); margin-top: 2px; }
.hero-right { display: flex; align-items: center; gap: 14px; }
.mascot { width: 52px; height: 52px; border-radius: 50%; background: var(--surface); border: 1px solid var(--border); display: grid; place-items: center; }
.status-chip { display: inline-flex; align-items: center; gap: 6px; padding: 7px 12px; border-radius: 999px; background: var(--success-soft); color: var(--success); font-size: 12.5px; font-weight: 600; }
.hero-record-btn { min-height: 40px; padding: 0 16px; font-size: 13px; }

/* ===== overview grid ===== */
.overview { display: grid; grid-template-columns: 5fr 7fr; gap: 20px; align-items: stretch; }
.right-stack { display: flex; flex-direction: column; gap: 20px; min-width: 0; }

/* ===== card overrides ===== */
.card { padding: 20px; }
.card-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 16px; }
.card-title { font-size: 15px; font-weight: 650; letter-spacing: -0.01em; }
.card-sub { font-size: 12px; color: var(--muted-strong); }

/* ===== score ring ===== */
.score-body { display: flex; flex-direction: column; align-items: center; padding: 8px 0 4px; }
.ring-wrap { position: relative; width: 220px; height: 220px; }
.ring-svg { transform: rotate(-90deg); }
.ring-track { fill: none; stroke: var(--border); }
.ring-bar { fill: none; stroke: var(--accent); stroke-linecap: round; transition: stroke-dashoffset 0.9s cubic-bezier(0.22,0.8,0.3,1); }
.ring-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.ring-score { font-size: 52px; font-weight: 700; line-height: 1; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
.ring-level { font-size: 13px; font-weight: 600; color: var(--muted-strong); margin-top: 6px; }
.ring-delta { font-size: 12px; color: var(--muted-strong); margin-top: 2px; }
.seg { display: flex; gap: 6px; margin-top: 18px; }
.seg-btn { padding: 6px 14px; border-radius: 999px; border: 1px solid var(--border); font-size: 12.5px; font-weight: 500; color: var(--muted-strong); transition: background 0.15s, color 0.15s, border-color 0.15s; min-height: 36px; }
.seg-btn:hover { color: var(--fg); background: var(--hover); }
.seg-btn.active { background: var(--fg); color: var(--bg); border-color: var(--fg); font-weight: 600; }

/* ===== metrics ===== */
.metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.metric { border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); padding: 16px 18px; display: flex; flex-direction: column; gap: 6px; transition: background 0.15s; }
.metric:hover { background: var(--hover); }
.metric-top { display: flex; align-items: center; justify-content: space-between; }
.metric-label { font-size: 12.5px; color: var(--muted-strong); font-weight: 500; }
.metric-value { font-size: 26px; font-weight: 700; line-height: 1.15; font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.metric-unit { font-size: 13px; color: var(--muted-strong); font-weight: 500; margin-left: 2px; }
.metric-foot { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--muted-strong); }
.trend-up { color: var(--success); display: inline-flex; align-items: center; gap: 2px; font-weight: 600; }
.trend-flat { color: var(--muted-strong); }
.badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; }
.badge-ok { background: var(--success-soft); color: var(--success); }
.badge-warn { background: var(--warn-soft); color: var(--warn); }
.badge-info { background: var(--info-soft); color: var(--info); }

/* ===== chart ===== */
.chart-box { position: relative; min-width: 0; }
.chart-legend { display: flex; gap: 16px; margin-bottom: 12px; flex-wrap: wrap; }
.legend-item { display: inline-flex; align-items: center; gap: 6px; font-size: 12px; color: var(--muted-strong); }
.legend-dot { width: 9px; height: 9px; border-radius: 3px; }
.legend-dot.line { height: 3px; border-radius: 2px; }
.chart-svg { width: 100%; height: auto; }
.chart-tip { position: absolute; pointer-events: none; z-index: 5; background: var(--fg); color: var(--bg); border-radius: 8px; padding: 8px 10px; font-size: 12px; line-height: 1.6; opacity: 0; transform: translateY(4px); transition: opacity 0.15s, transform 0.15s; box-shadow: 0 8px 20px rgba(26, 26, 46, 0.2); box-shadow: 0 8px 20px oklch(22% 0.02 250 / 0.2); white-space: nowrap; }
.chart-tip.show { opacity: 1; transform: translateY(0); }

/* ===== modules ===== */
.modules { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 14px; }
.module { display: flex; flex-direction: column; align-items: flex-start; gap: 10px; padding: 16px 14px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--surface); transition: background 0.15s, border-color 0.15s; text-align: left; }
.module:hover { background: var(--hover); border-color: #e6e6f0; border-color: oklch(88% 0.006 250); }
.module:active { transform: translateY(1px); }
.module-icon { width: 40px; height: 40px; border-radius: 11px; background: var(--bg); border: 1px solid var(--border); display: grid; place-items: center; color: var(--fg); }
.module-icon svg { width: 20px; height: 20px; }
.module-title { font-size: 13.5px; font-weight: 600; }
.module-desc { font-size: 11.5px; color: var(--muted-strong); line-height: 1.55; }

/* ===== tasks ===== */
.tasks { display: flex; flex-direction: column; gap: 4px; }
.task { display: flex; align-items: center; gap: 12px; padding: 12px 10px; border-radius: var(--radius-sm); cursor: pointer; transition: background 0.15s; min-height: 52px; }
.task:hover { background: var(--hover); }
.task-check { width: 22px; height: 22px; border-radius: 7px; flex: 0 0 22px; border: 1.5px solid var(--border); color: transparent; display: grid; place-items: center; transition: background 0.15s, border-color 0.15s, color 0.15s; }
.task input:checked ~ .task-check { background: var(--success); border-color: var(--success); color: #fff; }
.task-body { flex: 1; min-width: 0; display: flex; flex-direction: column; transition: color 0.15s; }
.task-name { font-size: 13.5px; font-weight: 550; }
.task-meta { font-size: 12px; color: var(--muted-strong); }
.task input:checked ~ .task-body { color: var(--muted); }
.task input:checked ~ .task-body .task-name { text-decoration: line-through; text-decoration-color: var(--muted); }
.task-icon { color: var(--muted-strong); flex: 0 0 22px; }
.task-icon svg { width: 20px; height: 20px; }
.task-progress { width: 100%; height: 5px; border-radius: 999px; background: var(--border); margin-top: 8px; overflow: hidden; }
.task-progress-bar { height: 100%; border-radius: 999px; background: var(--success); }

/* ===== analysis ===== */
.analysis-body { display: flex; flex-direction: column; gap: 14px; }
.analysis-list { list-style: none; display: flex; flex-direction: column; gap: 12px; padding: 0; }
.analysis-line { display: flex; gap: 10px; align-items: flex-start; color: var(--fg); font-size: 13.5px; line-height: 1.7; }
.analysis-line svg { flex: 0 0 18px; color: var(--success); margin-top: 3px; }
.link-more { display: inline-flex; align-items: center; gap: 6px; font-size: 13px; font-weight: 600; color: var(--fg); min-height: 40px; padding: 0 4px; border-radius: 8px; text-decoration: underline; text-underline-offset: 3px; text-decoration-color: var(--border); }
.link-more:hover { text-decoration-color: var(--fg); }
.link-more svg { transition: transform 0.15s; }
.link-more:hover svg { transform: translateX(2px); }
.device-note { display: flex; gap: 10px; align-items: flex-start; padding: 12px 14px; border-radius: var(--radius-sm); background: var(--bg); border: 1px dashed var(--border); font-size: 12.5px; color: var(--muted-strong); }

/* ===== skeleton ===== */
.sk-line { height: 13px; margin-bottom: 10px; }
.sk-block { height: 120px; }

/* ===== fun ===== */
.fun-toggle { width: 100%; display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); font-size: 14px; font-weight: 600; text-align: left; transition: background 0.15s; min-height: 56px; }
.fun-toggle:hover { background: var(--hover); }
.btn-w-icon { display: inline-flex; align-items: center; gap: 8px; }
.fun-toggle .chev { transition: transform 0.2s; color: var(--muted); }
.fun-toggle[aria-expanded="true"] .chev { transform: rotate(180deg); }
.fun-panel { border: 1px solid var(--border); border-top: 0; border-radius: 0 0 var(--radius) var(--radius); background: var(--surface); }
.fun-inner { padding: 20px; }

/* ===== modal ===== */
.modal-backdrop { position: fixed; inset: 0; z-index: 100; background: rgba(26, 26, 46, 0.42); background: oklch(16% 0.012 250 / 0.42); display: flex; align-items: center; justify-content: center; padding: 20px; }
.modal { width: 100%; max-width: 460px; max-height: calc(100vh - 48px); overflow: auto; background: var(--surface); border-radius: 16px; border: 1px solid var(--border); box-shadow: var(--shadow-modal); padding: 24px; }
.modal-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 20px; }
.modal-title { font-size: 17px; font-weight: 700; letter-spacing: -0.01em; line-height: 1.35; }
.modal-sub { font-size: 12.5px; color: var(--muted-strong); margin-top: 2px; }
.icon-btn { width: 40px; height: 40px; border-radius: 10px; display: grid; place-items: center; color: var(--muted-strong); transition: background 0.15s, color 0.15s; }
.icon-btn:hover { background: var(--hover); color: var(--fg); }
.field { margin-bottom: 16px; }
.field-label { display: block; font-size: 12.5px; font-weight: 600; margin-bottom: 6px; }
.field-note { font-size: 11.5px; color: var(--muted); margin-left: 6px; font-weight: 400; }
.field-input, .field-select, .field-area { width: 100%; min-height: 44px; border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); padding: 0 14px; font-size: 14px; transition: border-color 0.15s; }
.field-area { padding: 10px 14px; min-height: 84px; resize: vertical; line-height: 1.6; }
.field-input:focus, .field-select:focus, .field-area:focus { border-color: var(--accent); outline: none; }
.field-error .field-input { border-color: var(--danger); }
.error-msg { display: none; font-size: 12px; color: var(--danger); margin-top: 6px; }
.field-error .error-msg { display: block; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 8px; }
.unit-suffix { position: relative; }
.unit-suffix .field-input { padding-right: 56px; }
.unit-suffix::after { content: attr(data-unit); position: absolute; right: 14px; top: 50%; transform: translateY(-50%); font-size: 12.5px; color: var(--muted-strong); }
.spinner { width: 15px; height: 15px; border-radius: 50%; border: 2px solid rgba(255, 255, 255, 0.45); border: 2px solid color-mix(in oklch, #fff 45%, transparent); border-top-color: #fff; animation: spin 0.7s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ===== toast ===== */
.toast { position: fixed; left: 50%; bottom: 28px; transform: translate(-50%, 8px); z-index: 150; display: flex; align-items: center; gap: 9px; background: var(--fg); color: var(--bg); border-radius: 999px; padding: 12px 18px; font-size: 13px; font-weight: 550; opacity: 0; pointer-events: none; transition: opacity 0.2s, transform 0.2s; box-shadow: 0 14px 34px rgba(26, 26, 46, 0.3); box-shadow: 0 14px 34px oklch(22% 0.02 250 / 0.3); max-width: calc(100vw - 32px); }
.toast.show { opacity: 1; transform: translate(-50%, 0); }
.toast svg { color: #4ade80; color: oklch(78% 0.11 155); flex: 0 0 17px; }

/* ===== tab bar ===== */
.tabbar { display: none; position: fixed; bottom: 0; left: 0; right: 0; z-index: 60; background: rgba(255, 255, 255, 0.9); background: color-mix(in oklch, var(--surface) 90%, transparent); border-top: 1px solid var(--border); padding: 6px 8px calc(6px + env(safe-area-inset-bottom)); }
.tabbar-inner { display: flex; max-width: 560px; margin: 0 auto; }
.tab { flex: 1; min-height: 56px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; color: var(--muted); font-size: 11px; font-weight: 500; border-radius: 12px; transition: color 0.15s, background 0.15s; }
.tab:hover { background: var(--hover); color: var(--muted-strong); }
.tab.active { color: var(--fg-strong); font-weight: 650; }
.tab svg { width: 21px; height: 21px; }

/* ===== responsive ===== */
@media (max-width: 1100px) { .modules { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 820px) { .overview { grid-template-columns: 1fr; } }
@media (max-width: 767px) {
  .dash { padding-bottom: 74px; }
  .tabbar { display: block; }
  .hero { padding: 16px 0 4px; align-items: flex-start; flex-direction: column; gap: 12px; }
  .hero h1 { font-size: 22px; }
  .mascot { width: 44px; height: 44px; }
  .overview { gap: 16px; }
  .right-stack { gap: 16px; }
  .metrics { grid-template-columns: 1fr 1fr; gap: 10px; }
  .modules { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .module { padding: 14px 12px; }
  .card { padding: 16px; }
  .ring-wrap { width: 200px; height: 200px; }
}

/* ===== reduced motion ===== */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
  .dash > * { animation: none; }
}
</style>
