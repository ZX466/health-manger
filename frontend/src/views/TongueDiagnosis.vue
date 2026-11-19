<template>
  <div class="tongue-page">
    <PageHead
      folio="07"
      eyebrow="TONGUE / SCAN"
      title="舌诊"
      deck="自然光、舌头放平、别伸太用力。拍一张，看看中医眼里的寒热虚实。"
    >
      <template #actions>
        <span class="status-chip" :class="cameraActive || activeResult ? 'status-chip--accent' : ''">
          <span class="status-dot" :class="cameraActive || activeResult ? 'status-dot--success' : ''"></span>
          {{ cameraActive ? '实时采集中' : (store.analyzing ? '分析中' : (activeResult ? '已完成' : '待拍摄')) }}
        </span>
      </template>
    </PageHead>

    <div class="tongue-toolbar">
      <div class="tongue-tabs">
        <button :class="{ active: inputMode === 'upload' }" @click="setInputMode('upload')">
          <AppIcon name="plus" :size="14" />
          图片上传
        </button>
        <button :class="{ active: inputMode === 'camera' }" @click="setInputMode('camera')">
          <AppIcon name="camera" :size="14" />
          摄像头实时
        </button>
      </div>
      <span class="micro">{{ inputMode === 'camera' ? 'LIVE / CAMERA' : 'STILL / UPLOAD' }}</span>
    </div>

    <section v-if="tongueStats" class="v21-panel tongue-stats" aria-label="舌诊统计">
      <div class="panel-head">
        <span class="micro">TONGUE / STATS</span>
        <span class="micro">累计 {{ tongueStats.total_records || 0 }} 次</span>
      </div>
      <div class="tongue-stat-grid">
        <div>
          <span class="micro">累计分析</span>
          <strong>{{ tongueStats.total_records || 0 }}</strong>
        </div>
        <div>
          <span class="micro">已完成</span>
          <strong>{{ tongueStats.completed_records || 0 }}</strong>
        </div>
        <div>
          <span class="micro">最近证型</span>
          <strong>{{ tongueStats.latest_syndrome || '—' }}</strong>
        </div>
        <div>
          <span class="micro">最近舌象</span>
          <strong>{{ tongueStats.latest_overall_type || '—' }}</strong>
        </div>
      </div>
    </section>

    <div class="tongue-grid">
      <!-- 左侧控制栏 -->
      <div class="tongue-col">
        <section v-if="inputMode === 'upload'" class="v21-panel control-panel">
          <div class="panel-head">
            <span class="micro">INPUT</span>
            <span class="micro">JPG / PNG</span>
          </div>
          <h2>舌象照片</h2>

          <div
            class="upload-drop"
            :class="{ dragover: isDragOver }"
            role="button"
            tabindex="0"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @click="openFilePicker()"
            @keydown.enter.prevent="openFilePicker()"
            @keydown.space.prevent="openFilePicker()"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none"
            >
            <template v-if="!previewImage">
              <span class="upload-mark"><AppIcon name="camera" :size="22" /></span>
              <p>点击或拖拽图片到此处</p>
              <span class="micro">支持 JPG、PNG 格式</span>
            </template>
            <img v-else :src="previewImage" alt="舌象预览" class="upload-preview" />
          </div>

          <button
            v-if="previewImage && !store.analyzing"
            class="btn btn-primary btn-block"
            @click="startAnalysis"
          >
            开始分析
          </button>

          <button v-if="store.analyzing" class="btn btn-primary btn-block" disabled>
            <span class="spinner"></span>
            分析中…
          </button>

          <button
            v-if="previewImage && !store.analyzing"
            class="btn btn-ghost btn-block"
            @click="clearImage"
          >
            清除图片
          </button>
        </section>

        <section v-else class="v21-panel control-panel">
          <div class="panel-head">
            <span class="micro">CAMERA</span>
            <span class="camera-status-line" :class="{ active: cameraActive }">
              <span class="status-dot" :class="cameraActive ? 'status-dot--success' : ''"></span>
              {{ cameraActive ? '已开启' : '已关闭' }}
            </span>
          </div>
          <h2>摄像头控制</h2>

          <div class="camera-controls">
            <button
              v-if="!cameraActive && !cameraError"
              class="btn btn-primary btn-block"
              @click="startCamera"
            >
              开启摄像头
            </button>
            <button
              v-if="cameraActive"
              class="btn btn-ghost btn-block"
              @click="stopCamera"
            >
              关闭摄像头
            </button>
          </div>

          <div v-if="cameraError" class="camera-error">
            <AppIcon name="alert" :size="18" />
            <p>{{ cameraError }}</p>
            <button class="btn btn-ghost" @click="retryCamera">重试</button>
          </div>

          <div v-if="cameraActive" class="camera-guide">
            <span class="micro">GUIDE</span>
            <ul>
              <li>保持光线充足均匀</li>
              <li>舌头自然伸出放平</li>
              <li>对准舌头正面区域</li>
              <li>避免舌头过度伸展</li>
              <li>保持手机 / 摄像头稳定</li>
            </ul>
          </div>
        </section>

        <section class="v21-panel control-panel">
          <div class="panel-head">
            <span class="micro">SETTINGS</span>
            <span class="micro">{{ confidenceThreshold }}</span>
          </div>
          <h2>分析设置</h2>
          <label class="range-row">
            <span>置信度阈值</span>
            <input type="range" v-model="confidenceThreshold" min="0.5" max="1" step="0.05" />
          </label>
          <label v-if="inputMode === 'camera'" class="select-row">
            <span>分析频率</span>
            <select v-model="analysisInterval">
              <option value="1000">每秒 1 次</option>
              <option value="2000">每 2 秒 1 次</option>
              <option value="3000">每 3 秒 1 次</option>
              <option value="5000">每 5 秒 1 次</option>
            </select>
          </label>
        </section>

        <section class="v21-panel control-panel">
          <div class="panel-head">
            <span class="micro">COATING</span>
            <span class="micro">{{ selectedCoatingColor || '未选择' }}</span>
          </div>
          <h2>舌苔信息</h2>

          <div class="coating-block">
            <span class="coating-label">苔色</span>
            <div class="swatch-row">
              <button
                v-for="color in coatingColors"
                :key="color.name"
                class="swatch"
                :class="{ active: selectedCoatingColor === color.name }"
                :style="{ backgroundColor: color.color }"
                :title="color.name + '：' + color.desc"
                :aria-label="color.name + '：' + color.desc"
                @click="selectedCoatingColor = color.name"
              />
            </div>
            <p class="coating-hint">{{ selectedCoatingHint }}</p>
          </div>

          <div class="coating-block">
            <span class="coating-label">苔质</span>
            <div class="chip-row">
              <button
                v-for="thickness in coatingThickness"
                :key="thickness"
                class="chip"
                :class="{ active: selectedCoatingThickness === thickness }"
                @click="selectedCoatingThickness = thickness"
              >
                {{ thickness }}
              </button>
            </div>
          </div>

          <div v-if="selectedCoatingColor || selectedCoatingThickness" class="coating-actions">
            <button class="btn btn-primary" @click="applyCoatingSelection">应用选择</button>
            <button class="btn btn-ghost" @click="clearCoatingSelection">清除</button>
          </div>
        </section>

        <section class="v21-panel control-panel">
          <div class="panel-head">
            <span class="micro">SHOOTING NOTES</span>
          </div>
          <h2>拍摄提示</h2>
          <ul class="tips-list">
            <li>在自然光下拍摄效果最佳</li>
            <li>舌头自然伸出，不要用力</li>
            <li>对准舌头正面，避免遮挡</li>
            <li>拍摄前请清洁口腔</li>
          </ul>
        </section>
      </div>

      <!-- 中间图像区域 -->
      <div class="tongue-col">
        <section class="v21-panel stage-panel">
          <div class="panel-head">
            <span class="micro">SPECIMEN / VIEW</span>
            <span class="micro">{{ inputMode === 'camera' ? (cameraActive ? '● LIVE' : 'PAUSED') : 'STILL' }}</span>
          </div>

          <!-- 图片上传模式 -->
          <div v-if="inputMode === 'upload'" class="stage-frame">
            <div v-if="!previewImage" class="stage-empty">
              <span class="stage-mark"><AppIcon name="tongue" :size="30" /></span>
              <p>请上传舌象图片开始分析</p>
              <button class="btn btn-ghost" @click="openFilePicker()">选择图片</button>
            </div>

            <template v-else>
              <img :src="previewImage" alt="舌象图片" class="stage-media" />
              <div v-if="activeResult" class="overlay-stack">
                <span class="result-pill result-pill--type" :class="typeTone(activeResult.overall_type)">
                  {{ activeResult.overall_type }}
                </span>
                <span class="result-pill">{{ activeResult.tcm_syndrome }}</span>
                <span class="result-pill result-pill--muted">
                  置信度 {{ (activeResult.confidence_score * 100).toFixed(1) }}%
                </span>
              </div>
            </template>
          </div>

          <!-- 摄像头模式 -->
          <div v-else class="stage-frame stage-frame--camera">
            <div v-if="!cameraActive && !cameraError" class="stage-empty">
              <span class="stage-mark"><AppIcon name="camera" :size="30" /></span>
              <p>开启摄像头后，这里会显示实时画面</p>
            </div>

            <div v-if="cameraError" class="stage-empty">
              <span class="stage-mark stage-mark--danger"><AppIcon name="alert" :size="28" /></span>
              <h3>摄像头访问错误</h3>
              <p>{{ cameraError }}</p>
              <button class="btn btn-ghost" @click="retryCamera">重新尝试</button>
            </div>

            <template v-if="cameraActive">
              <video
                ref="videoElement"
                autoplay
                playsinline
                muted
                class="stage-media"
                style="width: 100%; min-height: 320px; background: #000;"
              ></video>
              <canvas ref="canvasElement" class="analysis-canvas"></canvas>

              <div v-if="store.realtimeResult" class="overlay-stack">
                <span class="result-pill result-pill--type" :class="typeTone(store.realtimeResult.overall_type)">
                  {{ store.realtimeResult.tcm_syndrome }}
                </span>
                <span class="result-pill result-pill--muted">
                  {{ (store.realtimeResult.confidence_score * 100).toFixed(0) }}%
                </span>
              </div>

              <div v-if="store.analyzing" class="analyzing-bar">
                <span class="spinner"></span>
                分析中…
              </div>
            </template>
          </div>

          <div v-if="inputMode === 'camera' && store.realtimeHistory.length > 0" class="realtime-strip">
            <div
              v-for="(item, idx) in store.realtimeHistory.slice(-5)"
              :key="idx"
              class="realtime-item"
              :class="{ latest: idx === store.realtimeHistory.slice(-5).length - 1 }"
            >
              <span class="micro">{{ item.time }}</span>
              <span class="realtime-syndrome">{{ item.syndrome }}</span>
              <span class="micro">{{ (item.confidence * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </section>

        <section v-if="store.historyList.length > 0" class="v21-panel history-panel">
          <div class="panel-head">
            <span class="micro">HISTORY</span>
            <span class="micro">{{ store.historyList.length }} 条</span>
          </div>
          <h2>历史记录</h2>
          <div class="history-strip">
            <div v-for="item in store.historyList" :key="item.id" class="history-item">
              <button class="history-card" @click="loadHistoryDetail(item)">
                <span class="history-thumb-wrap">
                  <img :src="protectedImageUrls[item.id] || ''" class="history-thumb" alt="" />
                </span>
                <span class="history-type">{{ item.overall_type || '分析中' }}</span>
                <span class="micro">{{ formatDate(item.created_at) }}</span>
              </button>
              <button
                class="history-delete"
                type="button"
                :aria-label="`删除 ${formatDate(item.created_at)} 的舌诊记录`"
                title="删除记录"
                @click="askDeleteHistory(item)"
              >
                <AppIcon name="trash" :size="14" />
              </button>
              <div v-if="pendingDeleteTongue === item.id" class="history-confirm" role="alert">
                <span>删除这条记录？</span>
                <button type="button" :disabled="deletingTongue === item.id" @click="deleteHistory(item)">
                  {{ deletingTongue === item.id ? '删除中' : '确认' }}
                </button>
                <button type="button" @click="pendingDeleteTongue = null">取消</button>
              </div>
            </div>
          </div>
        </section>

        <section class="v21-panel result-panel">
          <div class="panel-head">
            <span class="micro">DIAGNOSIS / RESULT</span>
            <span v-if="activeResult" class="micro">
              {{ (activeResult.confidence_score * 100).toFixed(0) }}%
            </span>
          </div>

          <div v-if="!activeResult" class="result-empty">
            <span class="stage-mark"><AppIcon name="chart" :size="26" /></span>
            <p>{{ inputMode === 'camera' ? '开启摄像头后，实时结果会出现在这里。' : '上传图片后，分析结果会出现在这里。' }}</p>
          </div>

          <template v-else>
            <div class="result-head">
              <div>
                <span class="micro">TCM SYNDROME</span>
                <h2 class="result-syndrome">{{ activeResult.tcm_syndrome || '—' }}</h2>
              </div>
              <span class="result-pill result-pill--type" :class="typeTone(activeResult.overall_type)">
                {{ activeResult.overall_type || '—' }}
              </span>
            </div>

            <div class="confidence-track">
              <span :style="{ width: confidencePercent + '%' }"></span>
            </div>

            <div class="feature-table">
              <div class="feature-row">
                <span class="feature-key">舌色</span>
                <span class="feature-val">
                  <span class="color-dot" :style="{ background: activeResult.tongue_color?.color || 'var(--muted-2)' }"></span>
                  {{ activeResult.tongue_color?.name || '—' }}
                  <em>{{ activeResult.tongue_color?.desc || '' }}</em>
                </span>
              </div>
              <div class="feature-row">
                <span class="feature-key">苔色</span>
                <span class="feature-val">
                  <span class="color-dot" :style="{ background: activeResult.coating_color?.color || 'var(--muted-2)' }"></span>
                  {{ activeResult.coating_color?.name || '—' }}
                  <em>{{ activeResult.coating_color?.desc || '' }}</em>
                </span>
              </div>
              <div class="feature-row">
                <span class="feature-key">苔质</span>
                <span class="feature-val">{{ activeResult.coating_thickness || '—' }}</span>
              </div>
              <div class="feature-row">
                <span class="feature-key">舌形</span>
                <span class="feature-val">{{ activeResult.tongue_shape || '—' }}</span>
              </div>
              <div class="feature-row">
                <span class="feature-key">润燥</span>
                <span class="feature-val">{{ activeResult.moisture_level || '—' }}</span>
              </div>
              <div class="feature-row">
                <span class="feature-key">裂纹</span>
                <span class="feature-val">{{ activeResult.has_cracks ? '有' : '无' }}</span>
              </div>
              <div class="feature-row">
                <span class="feature-key">齿痕</span>
                <span class="feature-val">{{ activeResult.has_teeth_marks ? '有' : '无' }}</span>
              </div>
            </div>

            <div class="advice-block">
              <span class="micro">COMPREHENSIVE</span>
              <p>{{ activeResult.health_advice || '暂无建议' }}</p>
            </div>
            <div class="advice-block">
              <span class="micro">DIET</span>
              <p>{{ activeResult.diet_suggestion || '暂无建议' }}</p>
            </div>
            <div class="advice-block">
              <span class="micro">LIFESTYLE</span>
              <p>{{ activeResult.lifestyle_advice || '暂无建议' }}</p>
            </div>

            <p class="result-fineprint">AI 舌象分析仅供健康管理参考，不能替代医生诊断。如有持续不适，请前往校医院。</p>

            <div v-if="inputMode === 'upload'" class="result-actions">
              <button class="btn btn-primary" @click="exportResult">导出报告</button>
              <button class="btn btn-ghost" @click="reAnalyze">重新分析</button>
            </div>
          </template>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useTongueStore } from '../stores/tongue'
import api from '../api'
import PageHead from '../components/PageHead.vue'
import AppIcon from '../components/AppIcon.vue'

const store = useTongueStore()

const fileInput = ref(null)
const videoElement = ref(null)
const canvasElement = ref(null)

const inputMode = ref('upload')
const previewImage = ref(null)
const previewImageId = ref(null)
const protectedImageUrls = ref({})
// 已删除记录的黑名单：晚到的详情/图片响应按 id 丢弃，避免删完又被写回。
const deletedTongueIds = new Set()
let detailToken = 0
const selectedFile = ref(null)
const isDragOver = ref(false)

const cameraActive = ref(false)
const cameraError = ref(null)
const videoStream = ref(null)
const analysisInterval = ref(2000)
const analysisTimer = ref(null)
const tongueStats = ref(null)
const pendingDeleteTongue = ref(null)
const deletingTongue = ref(null)

const confidenceThreshold = ref(0.75)

const coatingColors = ref([
  { name: '白苔', color: '#FFFFFF', desc: '正常或寒证' },
  { name: '黄苔', color: '#FFD700', desc: '热证，脾胃湿热' },
  { name: '灰黑苔', color: '#696969', desc: '重证，寒热错杂' },
  { name: '剥苔', color: '#FFE4B5', desc: '胃阴不足' },
  { name: '无苔', color: '#FF6347', desc: '胃气不足或阴虚' }
])
const coatingThickness = ref(['薄苔', '厚苔', '腻苔', '腐苔'])
const selectedCoatingColor = ref(null)
const selectedCoatingThickness = ref(null)

const activeResult = computed(() => store.result || store.realtimeResult)
const confidencePercent = computed(() => {
  const value = Number(activeResult.value?.confidence_score)
  return Number.isFinite(value) ? Math.max(0, Math.min(100, Math.round(value * 100))) : 0
})
const selectedCoatingHint = computed(() => {
  const item = coatingColors.value.find((color) => color.name === selectedCoatingColor.value)
  return item ? item.desc : '选择苔色后可手动修正结果'
})

function typeTone(type) {
  if (!type) return 'is-muted'
  if (type === '正常舌象') return 'is-success'
  if (['轻度异常舌象', '偏虚寒舌象', '阳虚舌象'].includes(type)) return 'is-warn'
  return 'is-danger'
}

function setInputMode(mode) {
  if (mode === 'camera' && inputMode.value === 'upload') {
    stopCamera()
  }
  if (mode === 'upload' && inputMode.value === 'camera') {
    stopCamera()
  }
  inputMode.value = mode
  store.clearResult()
}

function handleFileSelect(e) {
  const file = e.target.files[0]
  if (file) {
    processFile(file)
  }
}

function handleDrop(e) {
  isDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    processFile(file)
  }
}

function processFile(file) {
  selectedFile.value = file
  store.clearResult()
  const reader = new FileReader()
  reader.onload = (e) => {
    previewImage.value = e.target.result
  }
  reader.readAsDataURL(file)
}

function openFilePicker() {
  fileInput.value?.click()
}

function clearImage() {
  previewImage.value = null
  selectedFile.value = null
  store.clearResult()
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

async function startAnalysis() {
  if (!selectedFile.value && inputMode.value === 'upload') return
  await store.uploadAndAnalyze(selectedFile.value, 'upload', null)
  await Promise.all([loadHistoryImages(), loadStats()])
}

async function startCamera() {
  cameraError.value = null
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user'
      },
      audio: false
    })
    videoStream.value = stream
    cameraActive.value = true
    await nextTick()
    const videoEl = videoElement.value
    if (videoEl) {
      videoEl.srcObject = stream
      videoEl.play().catch(() => {})
    } else {
      cameraError.value = '视频元素未找到'
    }
    startRealtimeAnalysis()
  } catch (err) {
    if (err.name === 'NotAllowedError') {
      cameraError.value = '摄像头访问被拒绝，请在浏览器设置中允许访问摄像头'
    } else if (err.name === 'NotFoundError') {
      cameraError.value = '未检测到摄像头设备，请确保设备已正确连接'
    } else if (err.name === 'NotReadableError') {
      cameraError.value = '摄像头被其他应用占用，请关闭其他使用摄像头的程序'
    } else {
      cameraError.value = `摄像头启动失败: ${err.message}`
    }
  }
}

function stopCamera() {
  if (analysisTimer.value) {
    clearInterval(analysisTimer.value)
    analysisTimer.value = null
  }
  if (videoStream.value) {
    videoStream.value.getTracks().forEach(track => track.stop())
    videoStream.value = null
  }
  if (videoElement.value) {
    videoElement.value.srcObject = null
  }
  cameraActive.value = false
  store.clearResult()
}

function retryCamera() {
  cameraError.value = null
  startCamera()
}

function startRealtimeAnalysis() {
  if (analysisTimer.value) {
    clearInterval(analysisTimer.value)
  }
  analysisTimer.value = setInterval(() => {
    captureAndAnalyze()
  }, analysisInterval.value)
}

async function captureAndAnalyze() {
  if (!cameraActive.value || store.analyzing) return
  const video = videoElement.value
  const canvas = canvasElement.value
  if (!video || !canvas) return

  const captureFn = () => {
    return new Promise((resolve) => {
      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)
      canvas.toBlob((blob) => resolve(blob), 'image/jpeg', 0.8)
    })
  }

  await store.uploadAndAnalyze(null, 'camera', captureFn)
  await Promise.all([loadHistoryImages(), loadStats()])
}

async function loadHistoryDetail(item) {
  if (!item || !item.id) return
  const token = ++detailToken
  // 切换详情先清空预览，避免新图加载失败时仍显示上一条记录的照片。
  previewImageId.value = item.id
  previewImage.value = null
  try {
    const response = await api.getTongueDetail(item.id)
    if (token !== detailToken || deletedTongueIds.has(item.id)) return
    store.result = response.data
    const url = await loadProtectedImage(item.id)
    // 图片晚到且期间已删除或切换详情：丢弃，避免回填已删记录的预览。
    if (token !== detailToken || deletedTongueIds.has(item.id) || !url) return
    previewImage.value = url
  } catch (err) {
    if (token === detailToken) alert('加载详情失败')
  }
}

async function loadProtectedImage(id) {
  if (protectedImageUrls.value[id]) return protectedImageUrls.value[id]

  const response = await api.getTongueImage(id)
  const url = URL.createObjectURL(response.data)
  // 请求期间记录已被删除：回收 URL，不写入缓存。
  if (deletedTongueIds.has(id)) {
    URL.revokeObjectURL(url)
    return null
  }
  protectedImageUrls.value = { ...protectedImageUrls.value, [id]: url }
  return url
}

async function loadStats() {
  try {
    const { data } = await api.getTongueStats()
    tongueStats.value = data || null
  } catch {
    tongueStats.value = null
  }
}

function askDeleteHistory(item) {
  if (!item?.id) return
  pendingDeleteTongue.value = pendingDeleteTongue.value === item.id ? null : item.id
}

async function deleteHistory(item) {
  if (!item?.id || deletingTongue.value) return
  deletingTongue.value = item.id
  try {
    await api.deleteTongueRecord(item.id)
    deletedTongueIds.add(item.id)
    if (previewImageId.value === item.id) {
      previewImageId.value = null
      previewImage.value = null
      store.clearResult()
    }
    if (protectedImageUrls.value[item.id]) {
      URL.revokeObjectURL(protectedImageUrls.value[item.id])
      const next = { ...protectedImageUrls.value }
      delete next[item.id]
      protectedImageUrls.value = next
    }
    pendingDeleteTongue.value = null
    await store.loadHistory()
    await loadHistoryImages()
    await loadStats()
  } catch {
    alert('删除失败，请稍后重试')
  } finally {
    deletingTongue.value = null
  }
}

async function loadHistoryImages() {
  const visibleIds = new Set(store.historyList.map(({ id }) => id))
  if (previewImageId.value) visibleIds.add(previewImageId.value)
  const retainedUrls = Object.entries(protectedImageUrls.value).reduce((urls, [id, url]) => {
    if (visibleIds.has(Number(id))) {
      return { ...urls, [id]: url }
    }
    URL.revokeObjectURL(url)
    return urls
  }, {})
  protectedImageUrls.value = retainedUrls

  await Promise.all(store.historyList.map(async ({ id }) => {
    try {
      await loadProtectedImage(id)
    } catch {
      // A missing image should not prevent the history metadata from rendering.
    }
  }))
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
}

function exportResult() {
  if (!store.result) return
  let content = `中医舌诊分析报告\n`
  content += `================\n\n`
  content += `分析时间: ${new Date().toLocaleString()}\n\n`
  content += `【舌象特征】\n`
  content += `- 舌色: ${store.result.tongue_color?.name} (${store.result.tongue_color?.desc})\n`
  content += `- 苔色: ${store.result.coating_color?.name} (${store.result.coating_color?.desc})\n`
  content += `- 苔质: ${store.result.coating_thickness}\n`
  content += `- 舌形: ${store.result.tongue_shape}\n`
  content += `- 裂纹: ${store.result.has_cracks ? '有' : '无'}\n`
  content += `- 齿痕: ${store.result.has_teeth_marks ? '有' : '无'}\n\n`
  content += `【中医证型】\n`
  content += `- 证型: ${store.result.tcm_syndrome}\n`
  content += `- 总体: ${store.result.overall_type}\n\n`
  content += `【健康建议】\n`
  content += `${store.result.health_advice}\n\n`
  content += `【饮食建议】\n`
  content += `${store.result.diet_suggestion}\n\n`
  content += `【生活建议】\n`
  content += `${store.result.lifestyle_advice}\n`
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `舌诊报告_${new Date().toLocaleDateString()}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

function reAnalyze() {
  if (selectedFile.value) {
    startAnalysis()
  } else {
    clearImage()
  }
}

function applyCoatingSelection() {
  if (!store.result) return
  const colorInfo = coatingColors.value.find(c => c.name === selectedCoatingColor.value)
  if (colorInfo) {
    store.result = {
      ...store.result,
      coating_color: {
        name: colorInfo.name,
        color: colorInfo.color,
        desc: colorInfo.desc
      }
    }
  }
  if (selectedCoatingThickness.value) {
    store.result = {
      ...store.result,
      coating_thickness: selectedCoatingThickness.value
    }
  }
}

function clearCoatingSelection() {
  selectedCoatingColor.value = null
  selectedCoatingThickness.value = null
}

onMounted(async () => {
  await Promise.all([store.loadHistory(), loadStats()])
  await loadHistoryImages()
})

onBeforeUnmount(() => {
  stopCamera()
  Object.values(protectedImageUrls.value).forEach(URL.revokeObjectURL)
})
</script>

<style scoped>
.tongue-page {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.tongue-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.tongue-tabs {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
}

.tongue-tabs button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: background var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.tongue-tabs button.active {
  background: var(--ink);
  color: var(--surface);
}

.tongue-grid {
  display: grid;
  grid-template-columns: 292px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.tongue-col {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}

/* 宽屏：舌象舞台与诊断结果同屏左右，历史记录留在舞台下方 */
@media (min-width: 1181px) {
  .tongue-grid .tongue-col:nth-child(2) {
    display: grid;
    grid-template-columns: minmax(0, 1.12fr) minmax(0, 0.88fr);
    gap: 16px;
    align-items: start;
  }

  .tongue-grid .tongue-col:nth-child(2) > .stage-panel {
    grid-column: 1;
    grid-row: 1;
  }

  .tongue-grid .tongue-col:nth-child(2) > .history-panel {
    grid-column: 1;
    grid-row: 2;
  }

  .tongue-grid .tongue-col:nth-child(2) > .result-panel {
    grid-column: 2;
    grid-row: 1 / span 2;
    align-self: stretch;
  }
}

.control-panel h2,
.history-panel h2 {
  margin-top: 4px;
  font-family: var(--font-display);
  font-size: 21px;
  font-weight: 730;
  letter-spacing: -0.035em;
}

.btn-block {
  width: 100%;
  margin-top: 10px;
}

.camera-status-line {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted-2);
}

.camera-status-line.active {
  color: var(--success);
}

.camera-controls {
  margin-top: 12px;
}

.camera-error {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 12px;
  border-radius: var(--radius-sm);
  background: var(--danger-soft);
  color: var(--danger);
}

.camera-error p {
  font-size: 12px;
  line-height: 1.6;
}

.camera-guide {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.camera-guide ul,
.tips-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 10px;
  padding: 0;
  list-style: none;
}

.camera-guide li,
.tips-list li {
  position: relative;
  padding-left: 13px;
  font-size: 12px;
  line-height: 1.6;
  color: var(--muted);
}

.camera-guide li::before,
.tips-list li::before {
  content: "";
  position: absolute;
  left: 0;
  top: 7px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--line-strong);
}

.upload-drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  min-height: 156px;
  margin-top: 12px;
  padding: 16px;
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius-md);
  background: var(--surface-2);
  text-align: center;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), background var(--duration-fast) var(--ease-out);
}

.upload-drop:hover,
.upload-drop.dragover {
  border-color: var(--accent);
  background: var(--accent-soft);
}

.upload-drop p {
  font-size: 12.5px;
  font-weight: 600;
}

.upload-mark,
.stage-mark {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  border: 1px solid var(--line);
  background: var(--surface);
  color: var(--muted);
}

.stage-mark--danger {
  border-color: color-mix(in oklch, var(--danger) 35%, var(--line));
  color: var(--danger);
}

.upload-preview {
  width: 100%;
  height: 150px;
  border-radius: var(--radius-sm);
  object-fit: cover;
}

.range-row,
.select-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 14px;
  font-size: 12px;
  color: var(--muted);
}

.range-row input[type="range"] {
  width: 100%;
  accent-color: var(--accent);
}

.select-row select {
  width: 100%;
  min-height: 34px;
  padding: 0 8px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface);
  color: var(--fg);
  font: inherit;
  font-size: 12px;
}

.coating-block {
  margin-top: 14px;
}

.coating-block + .coating-block {
  padding-top: 12px;
  border-top: 1px solid var(--line);
}

.coating-label {
  display: block;
  margin-bottom: 8px;
  font-family: var(--font-mono);
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted-2);
}

.swatch-row {
  display: flex;
  gap: 8px;
}

.swatch {
  width: 30px;
  height: 30px;
  padding: 0;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  cursor: pointer;
  transition: transform var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);
}

.swatch:hover {
  transform: translateY(-1px);
}

.swatch.active {
  box-shadow: 0 0 0 2px var(--surface), 0 0 0 4px var(--ink);
}

.coating-hint {
  margin-top: 8px;
  font-size: 11px;
  color: var(--muted-2);
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  min-height: 28px;
  padding: 0 11px;
  border: 1px solid var(--line);
  border-radius: 999px;
  background: var(--surface);
  color: var(--muted);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}

.chip.active {
  border-color: var(--ink);
  background: var(--ink);
  color: var(--surface);
}

.coating-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.stage-panel {
  display: flex;
  flex-direction: column;
  order: 1;
}

.stage-frame {
  position: relative;
  display: grid;
  place-items: center;
  min-height: 380px;
  margin-top: 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  background: var(--surface-2);
  overflow: hidden;
}

.stage-frame--camera {
  background: var(--ink);
}

.stage-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px 20px;
  text-align: center;
  color: var(--muted);
}

.stage-empty h3 {
  font-family: var(--font-display);
  font-size: 17px;
  color: var(--fg);
}

.stage-empty p {
  max-width: 34ch;
  font-size: 12.5px;
  line-height: 1.6;
}

.stage-media {
  display: block;
  width: 100%;
  max-height: 560px;
  object-fit: contain;
}

.stage-frame--camera .stage-media {
  object-fit: cover;
}

.analysis-canvas {
  display: none;
}

.overlay-stack {
  position: absolute;
  left: 12px;
  bottom: 12px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.result-pill {
  display: inline-flex;
  align-items: center;
  min-height: 26px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(18, 18, 18, 0.82);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.01em;
  backdrop-filter: blur(4px);
}

.result-pill--type.is-success {
  background: var(--success);
}

.result-pill--type.is-warn {
  background: var(--warn);
}

.result-pill--type.is-danger {
  background: var(--danger);
}

.result-pill--type.is-muted {
  background: rgba(18, 18, 18, 0.7);
}

.result-pill--muted {
  background: rgba(255, 255, 255, 0.88);
  color: var(--fg);
}

.analyzing-bar {
  position: absolute;
  right: 12px;
  top: 12px;
  display: inline-flex;
  align-items: center;
  gap: 7px;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  font-size: 11px;
  font-weight: 600;
  color: var(--fg);
}

.realtime-strip {
  display: flex;
  flex-direction: column;
  margin-top: 12px;
  border-top: 1px solid var(--line);
}

.realtime-item {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr) auto;
  align-items: center;
  gap: 10px;
  padding: 8px 2px;
  border-bottom: 1px solid var(--line);
}

.realtime-item.latest .realtime-syndrome {
  color: var(--fg);
  font-weight: 650;
}

.realtime-syndrome {
  font-size: 12px;
  color: var(--muted);
}

.history-strip {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(92px, 1fr));
  gap: 8px;
  margin-top: 14px;
}

.history-card {
  display: flex;
  flex-direction: column;
  gap: 5px;
  width: 100%;
  padding: 6px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface);
  text-align: left;
  cursor: pointer;
  transition: border-color var(--duration-fast) var(--ease-out), transform var(--duration-fast) var(--ease-out);
}

.history-card:hover {
  border-color: var(--line-strong);
  transform: translateY(-1px);
}

.history-thumb-wrap {
  display: block;
  aspect-ratio: 4 / 3;
  border-radius: 5px;
  background: var(--surface-2);
  overflow: hidden;
}

.history-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.history-type {
  font-size: 11px;
  font-weight: 600;
  line-height: 1.35;
}

.history-card .micro {
  font-size: 8px;
}

.tongue-stats {
  padding: 14px 16px;
}

.tongue-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-top: 10px;
}

.tongue-stat-grid > div {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.tongue-stat-grid strong {
  overflow: hidden;
  font-size: 17px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-item {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.history-delete {
  position: absolute;
  top: 4px;
  right: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--muted);
  cursor: pointer;
}

.history-delete:hover {
  color: var(--danger);
}

.history-confirm {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  background: var(--surface);
  font-size: 10px;
}

.history-confirm button {
  padding: 2px 5px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: var(--surface);
  color: var(--fg);
  font-size: 10px;
  cursor: pointer;
}

.history-confirm button:first-of-type {
  color: var(--danger);
  border-color: currentColor;
}

.result-panel {
  display: flex;
  flex-direction: column;
  order: 2;
}

.result-fineprint {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 11.5px;
  line-height: 1.6;
}

.history-panel {
  order: 3;
}

.result-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 44px 18px;
  text-align: center;
  color: var(--muted);
}

.result-empty p {
  max-width: 26ch;
  font-size: 12.5px;
  line-height: 1.65;
}

.result-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-top: 14px;
}

.result-syndrome {
  margin-top: 4px;
  font-family: var(--font-display);
  font-size: 25px;
  font-weight: 750;
  line-height: 1.15;
  letter-spacing: -0.04em;
}

.confidence-track {
  height: 4px;
  margin-top: 14px;
  border-radius: 999px;
  background: var(--surface-3);
  overflow: hidden;
}

.confidence-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--accent);
  transition: width 300ms var(--ease-out);
}

.feature-table {
  display: flex;
  flex-direction: column;
  margin-top: 16px;
}

.feature-row {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 8px;
  padding: 8px 0;
  border-top: 1px solid var(--line);
  font-size: 12px;
}

.feature-key {
  color: var(--muted-2);
  font-family: var(--font-mono);
  font-size: 9px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding-top: 2px;
}

.feature-val {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  color: var(--fg);
}

.feature-val em {
  flex-basis: 100%;
  font-style: normal;
  font-size: 10.5px;
  color: var(--muted-2);
}

.color-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 1px solid var(--line-strong);
}

.advice-block {
  padding: 13px 0;
  border-top: 1px solid var(--line);
}

.advice-block p {
  margin-top: 6px;
  font-size: 12px;
  line-height: 1.75;
  color: var(--muted);
}

.result-actions {
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1180px) {
  .tongue-grid {
    grid-template-columns: 280px minmax(0, 1fr);
  }
}

@media (max-width: 820px) {
  .tongue-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  /* 手机上让「上传 → 预览 → 结果」优先，设置与提示后置 */
  .tongue-col {
    display: contents;
  }

  .tongue-col:first-child > .control-panel:nth-child(1) {
    order: 1;
  }

  .stage-panel {
    order: 2;
  }

  .result-panel {
    order: 3;
  }

  .tongue-col:first-child > .control-panel:nth-child(2) {
    order: 4;
  }

  .tongue-col:first-child > .control-panel:nth-child(3) {
    order: 5;
  }

  .tongue-col:first-child > .control-panel:nth-child(4) {
    order: 6;
  }

  .history-panel {
    order: 7;
  }

  .tongue-toolbar {
    align-items: flex-start;
  }

  .stage-frame {
    min-height: 300px;
  }
}

@media (max-width: 640px) {
  .tongue-tabs button {
    padding: 0 11px;
    font-size: 11px;
  }

  .stage-frame {
    min-height: 240px;
  }

  .result-syndrome {
    font-size: 22px;
  }

  .tongue-stat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
