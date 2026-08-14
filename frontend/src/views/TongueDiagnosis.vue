<template>
  <div class="tongue-diagnosis">

    <div class="page-header">
      <h1> 中医舌诊分析</h1>
      <p>上传舌象照片或使用摄像头实时分析</p>
      <div class="mascot-companion mascot-nailong-companion">
        <MiniNailong />
      </div>
    </div>

    <div class="mode-tabs">
      <button :class="['mode-tab', { active: inputMode === 'upload' }]" @click="setInputMode('upload')">
         图片上传
      </button>
      <button :class="['mode-tab', { active: inputMode === 'camera' }]" @click="setInputMode('camera')">
         摄像头实时
      </button>
    </div>

    <div class="diagnosis-container">
      <!-- 左侧配置面板 -->
      <div class="left-panel">
        <!-- 图片上传模式 -->
        <div v-if="inputMode === 'upload'" class="panel-section">
          <h3> 图片上传</h3>
          <div
            class="upload-area"
            :class="{ 'dragover': isDragOver }"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragOver = true"
            @dragleave.prevent="isDragOver = false"
            @click="$refs.fileInput.click()"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              @change="handleFileSelect"
              style="display: none"
            >
            <div v-if="!previewImage" class="upload-placeholder">
              <span class="upload-icon"></span>
              <p>点击或拖拽图片到此处</p>
              <span class="upload-hint">支持 JPG、PNG 格式</span>
            </div>
            <img v-else :src="previewImage" alt="舌象预览" class="preview-image" />
          </div>

          <button
            v-if="previewImage && !store.analyzing"
            @click="startAnalysis"
            class="analyze-btn primary"
          >
             开始分析
          </button>

          <button v-if="store.analyzing" class="analyze-btn analyzing" disabled>
            <span class="spinner"></span> 分析中...
          </button>

          <div v-if="previewImage && !store.analyzing" class="clear-btn" @click="clearImage">
            清除图片
          </div>
        </div>

        <!-- 摄像头模式 -->
        <div v-if="inputMode === 'camera'" class="panel-section camera-panel">
          <h3> 摄像头控制</h3>

          <div class="camera-status">
            <div class="status-indicator" :class="{ active: cameraActive }"></div>
            <span>{{ cameraActive ? '摄像头已开启' : '摄像头已关闭' }}</span>
          </div>

          <div class="camera-controls">
            <button
              v-if="!cameraActive && !cameraError"
              @click="startCamera"
              class="camera-btn start"
            >
              ▶ 开启摄像头
            </button>
            <button
              v-if="cameraActive"
              @click="stopCamera"
              class="camera-btn stop"
            >
              ⏹ 关闭摄像头
            </button>
          </div>

          <div v-if="cameraError" class="camera-error">
            <span class="error-icon"></span>
            <p>{{ cameraError }}</p>
            <button @click="retryCamera" class="retry-btn">重试</button>
          </div>

          <div class="camera-guide" v-if="cameraActive">
            <h4> 拍摄指南</h4>
            <ul>
              <li>保持光线充足均匀</li>
              <li>舌头自然伸出放平</li>
              <li>对准舌头正面区域</li>
              <li>避免舌头过度伸展</li>
              <li>保持手机/摄像头稳定</li>
            </ul>
          </div>
        </div>

        <div class="panel-section">
          <h3> 分析设置</h3>
          <div class="setting-item">
            <label>置信度阈值</label>
            <input type="range" v-model="confidenceThreshold" min="0.5" max="1" step="0.05" />
            <span>{{ confidenceThreshold }}</span>
          </div>
          <div class="setting-item" v-if="inputMode === 'camera'">
            <label>分析频率</label>
            <select v-model="analysisInterval">
              <option value="1000">每秒1次</option>
              <option value="2000">每2秒1次</option>
              <option value="3000">每3秒1次</option>
              <option value="5000">每5秒1次</option>
            </select>
          </div>
        </div>

        <div class="panel-section tongue-coating">
          <h3> 舌苔信息</h3>
          <div class="coating-grid">
            <div class="coating-item">
              <label>苔色</label>
              <div class="color-options">
                <button
                  v-for="color in coatingColors"
                  :key="color.name"
                  :class="['color-btn', { active: selectedCoatingColor === color.name }]"
                  :style="{ backgroundColor: color.color }"
                  :title="color.name + ': ' + color.desc"
                  @click="selectedCoatingColor = color.name"
                >
                  <span v-if="selectedCoatingColor === color.name" class="check-mark"></span>
                </button>
              </div>
              <span class="coating-label">{{ selectedCoatingColor || '请选择' }}</span>
            </div>
            <div class="coating-item">
              <label>苔质</label>
              <div class="thickness-options">
                <button
                  v-for="thickness in coatingThickness"
                  :key="thickness"
                  :class="['thickness-btn', { active: selectedCoatingThickness === thickness }]"
                  @click="selectedCoatingThickness = thickness"
                >
                  {{ thickness }}
                </button>
              </div>
            </div>
          </div>
          <div class="coating-actions" v-if="selectedCoatingColor || selectedCoatingThickness">
            <button class="apply-btn" @click="applyCoatingSelection">
              应用选择
            </button>
            <button class="clear-btn-small" @click="clearCoatingSelection">
              清除
            </button>
          </div>
        </div>

        <div class="panel-section tips">
          <h3> 拍摄提示</h3>
          <ul>
            <li>在自然光下拍摄效果最佳</li>
            <li>舌头自然伸出，不要用力</li>
            <li>对准舌头正面，避免遮挡</li>
            <li>拍摄前请清洁口腔</li>
          </ul>
        </div>
      </div>

      <!-- 中间图像区域 -->
      <div class="center-panel">
        <!-- 图片上传模式显示 -->
        <div v-if="inputMode === 'upload'" class="image-display">
          <div v-if="!store.result && !previewImage" class="empty-state">
            <span class="empty-icon"></span>
            <p>请上传舌象图片开始分析</p>
          </div>

          <div v-if="previewImage" class="image-wrapper">
            <img :src="previewImage" alt="舌象图片" class="main-image" />

            <div v-if="store.result" class="analysis-overlay">
              <div class="overlay-badge type-badge" :style="{ background: getTypeColor(store.result.overall_type) }">
                {{ store.result.overall_type }}
              </div>
              <div class="overlay-badge syndrome-badge">
                {{ store.result.tcm_syndrome }}
              </div>
              <div class="confidence-badge">
                置信度: {{ (store.result.confidence_score * 100).toFixed(1) }}%
              </div>
            </div>
          </div>
        </div>

        <!-- 摄像头模式显示 -->
        <div v-if="inputMode === 'camera'" class="camera-display">
          <div v-if="!cameraActive && !cameraError" class="camera-placeholder">
            <span class="camera-placeholder-icon"></span>
            <p>点击左侧"开启摄像头"开始实时分析</p>
          </div>

          <div v-if="cameraError" class="camera-error-display">
            <span class="error-icon-large"></span>
            <h3>摄像头访问错误</h3>
            <p>{{ cameraError }}</p>
            <button @click="retryCamera" class="retry-btn-large">重新尝试</button>
          </div>

          <div v-if="cameraActive" class="video-wrapper">
            <video
              ref="videoElement"
              autoplay
              playsinline
              muted
              class="camera-video"
              style="width: 100%; min-height: 320px; background: #000;"
            ></video>
            <canvas ref="canvasElement" class="analysis-canvas"></canvas>

            <div v-if="store.realtimeResult" class="realtime-overlay">
              <div class="realtime-badge syndrome" :style="{ background: getTypeColor(store.realtimeResult.overall_type) }">
                {{ store.realtimeResult.tcm_syndrome }}
              </div>
              <div class="realtime-badge confidence">
                {{ (store.realtimeResult.confidence_score * 100).toFixed(0) }}%
              </div>
            </div>

            <div v-if="store.analyzing" class="analyzing-indicator">
              <span class="spinner-large"></span>
              <span>分析中...</span>
            </div>
          </div>

          <!-- 实时分析结果条 -->
          <div v-if="store.realtimeHistory.length > 0" class="realtime-results-bar">
            <div
              v-for="(item, idx) in store.realtimeHistory.slice(-5)"
              :key="idx"
              class="realtime-result-item"
              :class="{ latest: idx === store.realtimeHistory.slice(-5).length - 1 }"
            >
              <span class="result-time">{{ item.time }}</span>
              <span class="result-syndrome" :style="{ color: getTypeColor(item.overall_type) }">
                {{ item.tcm_syndrome }}
              </span>
              <span class="result-confidence">{{ (item.confidence * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>

        <!-- 历史记录列表 -->
        <div class="history-section" v-if="store.historyList.length > 0">
          <h4> 历史记录 ({{ store.historyList.length }})</h4>
          <div class="history-list">
            <div
              v-for="item in store.historyList"
              :key="item.id"
              class="history-item"
              @click="loadHistoryDetail(item)"
            >
              <img :src="protectedImageUrls[item.id] || ''" class="history-thumb" />
              <div class="history-info">
                <span class="history-type">{{ item.overall_type || '分析中' }}</span>
                <span class="history-date">{{ formatDate(item.created_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧结果面板 -->
      <div class="right-panel">
        <div v-if="!store.result && !store.realtimeResult" class="no-result">
          <span class="no-result-icon"></span>
          <p>{{ inputMode === 'camera' ? '开启摄像头后开始实时分析...' : '等待分析结果...' }}</p>
        </div>

        <div v-if="store.result || store.realtimeResult" class="result-panel">
          <h3> {{ inputMode === 'camera' ? '实时' : '' }}分析结果</h3>
          <div class="result-source" v-if="inputMode === 'camera'">
            <span class="source-badge" :class="{ live: cameraActive }">
              {{ cameraActive ? '● LIVE' : 'PAUSED' }}
            </span>
          </div>

          <div class="result-table">
            <table>
              <thead>
                <tr>
                  <th>特征项</th>
                  <th>检测结果</th>
                  <th>说明</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><span class="feature-dot tongue"></span>舌色</td>
                  <td>
                    <span
                      class="color-badge"
                      :style="{ background: (store.result || store.realtimeResult)?.tongue_color?.color || 'var(--muted)' }"
                    >
                      {{ (store.result || store.realtimeResult)?.tongue_color?.name || '-' }}
                    </span>
                  </td>
                  <td class="desc">{{ (store.result || store.realtimeResult)?.tongue_color?.desc || '-' }}</td>
                </tr>
                <tr>
                  <td><span class="feature-dot coating"></span>苔色</td>
                  <td>
                    <span
                      class="color-badge"
                      :style="{ background: (store.result || store.realtimeResult)?.coating_color?.color || 'var(--muted)' }"
                    >
                      {{ (store.result || store.realtimeResult)?.coating_color?.name || '-' }}
                    </span>
                  </td>
                  <td class="desc">{{ (store.result || store.realtimeResult)?.coating_color?.desc || '-' }}</td>
                </tr>
                <tr>
                  <td><span class="feature-dot thickness"></span>苔质</td>
                  <td>{{ (store.result || store.realtimeResult)?.coating_thickness || '-' }}</td>
                  <td>-</td>
                </tr>
                <tr>
                  <td><span class="feature-dot shape"></span>舌形</td>
                  <td>{{ (store.result || store.realtimeResult)?.tongue_shape || '-' }}</td>
                  <td>-</td>
                </tr>
                <tr>
                  <td><span class="feature-dot moisture"></span>润燥</td>
                  <td>{{ (store.result || store.realtimeResult)?.moisture_level || '-' }}</td>
                  <td>-</td>
                </tr>
                <tr>
                  <td><span class="feature-dot crack"></span>裂纹</td>
                  <td>{{ (store.result || store.realtimeResult)?.has_cracks ? '有' : '无' }}</td>
                  <td>-</td>
                </tr>
                <tr>
                  <td><span class="feature-dot teeth"></span>齿痕</td>
                  <td>{{ (store.result || store.realtimeResult)?.has_teeth_marks ? '有' : '无' }}</td>
                  <td>-</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="syndrome-card">
            <h4> 中医证型判断</h4>
            <div class="syndrome-result">
              <span class="syndrome-name">{{ (store.result || store.realtimeResult)?.tcm_syndrome || '-' }}</span>
              <span class="overall-type" :style="{ color: getTypeColor((store.result || store.realtimeResult)?.overall_type) }">
                {{ (store.result || store.realtimeResult)?.overall_type || '-' }}
              </span>
            </div>
          </div>

          <div class="advice-section">
            <h4> 健康建议</h4>
            <div class="advice-card health">
              <h5>综合评估</h5>
              <p>{{ (store.result || store.realtimeResult)?.health_advice || '暂无建议' }}</p>
            </div>

            <div class="advice-card diet">
              <h5> 饮食建议</h5>
              <p>{{ (store.result || store.realtimeResult)?.diet_suggestion || '暂无建议' }}</p>
            </div>

            <div class="advice-card lifestyle">
              <h5> 生活建议</h5>
              <p>{{ (store.result || store.realtimeResult)?.lifestyle_advice || '暂无建议' }}</p>
            </div>
          </div>

          <div class="action-buttons" v-if="inputMode === 'upload'">
            <button @click="exportResult" class="action-btn export">
               导出报告
            </button>
            <button @click="reAnalyze" class="action-btn retry">
               重新分析
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useTongueStore } from '../stores/tongue'
import api from '../api'
import MiniNailong from '../components/mascots/MiniNailong.vue'

const store = useTongueStore()

const fileInput = ref(null)
const videoElement = ref(null)
const canvasElement = ref(null)

const inputMode = ref('upload')
const previewImage = ref(null)
const previewImageId = ref(null)
const protectedImageUrls = ref({})
const selectedFile = ref(null)
const isDragOver = ref(false)

const cameraActive = ref(false)
const cameraError = ref(null)
const videoStream = ref(null)
const analysisInterval = ref(2000)
const analysisTimer = ref(null)

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
  await loadHistoryImages()
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
  await loadHistoryImages()
}

async function loadHistoryDetail(item) {
  if (!item || !item.id) return
  try {
    const response = await api.getTongueDetail(item.id)
    store.result = response.data
    previewImageId.value = item.id
    previewImage.value = await loadProtectedImage(item.id)
  } catch (err) {
    alert('加载详情失败')
  }
}

async function loadProtectedImage(id) {
  if (protectedImageUrls.value[id]) return protectedImageUrls.value[id]

  const response = await api.getTongueImage(id)
  const url = URL.createObjectURL(response.data)
  protectedImageUrls.value = { ...protectedImageUrls.value, [id]: url }
  return url
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
  return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${String(date.getMinutes()).padStart(2,'0')}`
}

function getTypeColor(type) {
  const colors = {
    '正常舌象': '#52c41a',
    '轻度异常舌象': '#faad14',
    '偏虚寒舌象': '#1890ff',
    '偏实热舌象': '#ff4d4f',
    '痰湿舌象': '#722ed1',
    '湿热舌象': '#fa8c16',
    '血瘀舌象': '#eb2f96',
    '阳虚舌象': '#13c2c2',
    '异常舌象': '#f5222d'
  }
  return colors[type] || 'var(--muted)'
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
  await store.loadHistory()
  await loadHistoryImages()
})

onBeforeUnmount(() => {
  stopCamera()
  Object.values(protectedImageUrls.value).forEach(URL.revokeObjectURL)
})
</script>


<style scoped>
.tongue-diagnosis {
  min-height: 100vh;
  background: var(--accent);
}

.page-header {
  text-align: center;
  padding: 30px 20px;
  color: white;
}
.page-header h1 {
  font-size: 28px;
  margin-bottom: 8px;
}
.page-header p {
  opacity: 0.9;
  font-size: 15px;
}

.mode-tabs {
  display: flex;
  justify-content: center;
  gap: 16px;
  padding: 0 20px;
  margin-top: -15px;
  margin-bottom: 20px;
}

.mode-tab {
  padding: 12px 32px;
  border: none;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.mode-tab.active {
  background: white;
  color: var(--accent-strong);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}

.mode-tab:hover:not(.active) {
  background: rgba(255, 255, 255, 0.3);
}

.diagnosis-container {
  max-width: 1400px;
  margin: 0 auto 40px;
  display: grid;
  grid-template-columns: 280px 1fr 380px;
  gap: 20px;
  padding: 0 20px;
}

/* 左侧面板 */
.left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel-section {
  background: white;
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.panel-section h3 {
  font-size: 16px;
  margin-bottom: 16px;
  color: var(--fg);
}

.camera-panel .camera-status {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 10px;
  background: var(--warn-soft);
  border-radius: var(--radius);
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--muted);
}

.status-indicator.active {
  background: var(--success);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.camera-controls {
  display: flex;
  gap: 10px;
}

.camera-btn {
  flex: 1;
  padding: 12px;
  border: none;
  border-radius: var(--radius);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.camera-btn.start {
  background: var(--success);
  color: white;
}

.camera-btn.start:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(82, 196, 26, 0.4);
}

.camera-btn.stop {
  background: var(--danger);
  color: white;
}

.camera-btn.stop:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 77, 79, 0.4);
}

.camera-error {
  text-align: center;
  padding: 16px;
  background: var(--danger-soft);
  border-radius: var(--radius);
  margin-top: 12px;
}

.error-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
}

.camera-error p {
  color: var(--muted);
  font-size: 13px;
  margin-bottom: 12px;
}

.retry-btn {
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: var(--accent);
  color: white;
  cursor: pointer;
  font-size: 13px;
}

.camera-guide {
  margin-top: 16px;
  padding: 12px;
  background: var(--warn-soft);
  border-radius: var(--radius);
}

.camera-guide h4 {
  font-size: 13px;
  margin-bottom: 8px;
  color: var(--fg);
}

.camera-guide ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.camera-guide li {
  font-size: 12px;
  color: var(--muted);
  padding: 4px 0;
  position: relative;
  padding-left: 16px;
}

.camera-guide li::before {
  content: "";
  position: absolute;
  left: 0;
  color: var(--success);
  font-size: 10px;
}

.upload-area {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  background: var(--warn-soft);
}
.upload-area:hover, .upload-area.dragover {
  border-color: var(--accent-strong);
  background: var(--warn-soft);
}
.upload-placeholder .upload-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 10px;
}
.upload-placeholder p {
  color: var(--muted);
  margin-bottom: 8px;
}
.upload-hint {
  font-size: 12px;
  color: var(--muted);
}
.preview-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 6px;
  object-fit: contain;
}

.analyze-btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 16px;
  transition: all 0.3s;
}
.analyze-btn.primary {
  background: var(--accent);
  color: white;
}
.analyze-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(255,155,113,0.4);
}
.analyze-btn.analyzing {
  background: var(--warn-soft);
  color: var(--muted);
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-top-color: var(--accent-strong);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
  vertical-align: middle;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.clear-btn {
  text-align: center;
  color: var(--muted);
  cursor: pointer;
  padding: 8px;
  font-size: 13px;
  margin-top: 8px;
}
.clear-btn:hover { color: var(--danger); }

.setting-item {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.setting-item label {
  flex: 1;
  font-size: 14px;
  color: var(--muted);
}
.setting-item input[type="range"] {
  flex: 2;
}
.setting-item span, .setting-item select {
  width: auto;
  min-width: 60px;
  text-align: right;
  font-weight: 600;
  color: var(--accent-strong);
}

.tongue-coating {
  background: var(--warn-soft);
}

.coating-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 12px;
}

.coating-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.coating-item label {
  font-size: 13px;
  color: var(--muted);
  font-weight: 500;
}

.color-options {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-btn {
  width: 36px;
  height: 36px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.color-btn:hover {
  transform: scale(1.1);
  border-color: var(--accent-strong);
}

.color-btn.active {
  border-color: var(--accent-strong);
  box-shadow: 0 0 0 2px var(--accent-soft);
}

.check-mark {
  color: white;
  font-weight: bold;
}

.coating-label {
  font-size: 12px;
  color: var(--muted);
}

.thickness-options {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.thickness-btn {
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  background: white;
  font-size: 12px;
  color: var(--muted);
  cursor: pointer;
  transition: all 0.2s;
}

.thickness-btn:hover {
  border-color: var(--accent-strong);
  color: var(--accent-strong);
}

.thickness-btn.active {
  background: var(--accent);
  color: white;
  border-color: transparent;
}

.coating-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.apply-btn {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 6px;
  background: var(--accent);
  color: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.apply-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 155, 113, 0.3);
}

.clear-btn-small {
  padding: 8px 16px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: white;
  color: var(--muted);
  font-size: 13px;
  cursor: pointer;
}

.clear-btn-small:hover {
  border-color: var(--danger);
  color: var(--danger);
}

.tips ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.tips li {
  padding: 6px 0;
  font-size: 13px;
  color: var(--muted);
  position: relative;
  padding-left: 16px;
}
.tips li::before {
  content: "";
  position: absolute;
  left: 0;
  color: var(--success);
  font-weight: bold;
}

/* 中间面板 */
.center-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-display, .camera-display {
  background: white;
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  min-height: 450px;
  display: flex;
  flex-direction: column;
}

.empty-state, .camera-placeholder {
  text-align: center;
  padding: 100px 20px;
  color: var(--muted);
}
.empty-state .empty-icon, .camera-placeholder-icon {
  font-size: 80px;
  display: block;
  margin-bottom: 16px;
}

.camera-error-display {
  text-align: center;
  padding: 60px 20px;
}
.error-icon-large {
  font-size: 64px;
  display: block;
  margin-bottom: 16px;
}
.camera-error-display h3 {
  color: var(--fg);
  margin-bottom: 12px;
}
.camera-error-display p {
  color: var(--muted);
  margin-bottom: 20px;
}
.retry-btn-large {
  padding: 12px 32px;
  border: none;
  border-radius: var(--radius);
  background: var(--accent);
  color: white;
  font-size: 15px;
  cursor: pointer;
}

.video-wrapper {
  position: relative;
  width: 100%;
  min-height: 400px;
  border-radius: var(--radius);
  overflow: hidden;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.camera-video {
  width: 100%;
  height: auto;
  max-height: 400px;
  display: block;
  object-fit: cover;
}

.analysis-canvas {
  display: none;
}

.realtime-overlay {
  position: absolute;
  top: 10px;
  right: 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.realtime-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  color: white;
  font-weight: 600;
  text-align: center;
}

.realtime-badge.syndrome {
  font-size: 14px;
  padding: 6px 14px;
}

.analyzing-indicator {
  position: absolute;
  bottom: 10px;
  left: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
}

.spinner-large {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.realtime-results-bar {
  display: flex;
  gap: 8px;
  margin-top: 12px;
  padding: 10px;
  background: var(--warn-soft);
  border-radius: var(--radius);
  overflow-x: auto;
}

.realtime-result-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  min-width: 80px;
  font-size: 11px;
}

.realtime-result-item.latest {
  background: var(--accent);
  color: white;
}

.realtime-result-item.latest .result-syndrome,
.realtime-result-item.latest .result-confidence {
  color: white;
}

.result-time {
  color: var(--muted);
  margin-bottom: 4px;
}

.result-syndrome {
  font-weight: 600;
  font-size: 12px;
}

.result-confidence {
  color: var(--muted);
}

.history-section {
  background: white;
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.history-section h4 {
  margin-bottom: 12px;
  color: var(--fg);
  font-size: 14px;
}
.history-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}
.history-item {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.history-item:hover {
  border-color: var(--accent-strong);
  box-shadow: 0 2px 8px rgba(255,155,113,0.2);
}
.history-thumb {
  width: 100%;
  height: 60px;
  object-fit: cover;
  border-radius: 4px;
  margin-bottom: 6px;
}
.history-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.history-type {
  font-size: 12px;
  font-weight: 600;
  color: var(--fg);
}
.history-date {
  font-size: 11px;
  color: var(--muted);
}

/* 右侧结果面板 */
.right-panel {
  background: white;
  border-radius: var(--radius);
  padding: 20px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

.no-result {
  text-align: center;
  padding: 60px 20px;
  color: var(--muted);
}
.no-result-icon {
  font-size: 60px;
  display: block;
  margin-bottom: 16px;
}

.result-panel h3 {
  font-size: 18px;
  margin-bottom: 12px;
  color: var(--fg);
}

.result-source {
  margin-bottom: 16px;
}

.source-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  background: var(--warn-soft);
  color: var(--muted);
}

.source-badge.live {
  background: var(--danger-soft);
  color: var(--danger);
}

@keyframes pulseBadge {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.result-table {
  margin-bottom: 20px;
}
.result-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.result-table th {
  background: var(--accent);
  color: white;
  padding: 10px 8px;
  text-align: left;
  font-weight: 500;
}
.result-table th:first-child { border-radius: 6px 0 0 0; }
.result-table th:last-child { border-radius: 0 6px 0 0; }
.result-table td {
  padding: 10px 8px;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}
.result-table tr:last-child td:first-child { border-radius: 0 0 0 6px; }
.result-table tr:last-child td:last-child { border-radius: 0 0 6px 0; }

.feature-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}
.feature-dot.tongue { background: #FF69B4; }
.feature-dot.coating { background: #FFFFFF; border: 1px solid var(--border); }
.feature-dot.thickness { background: #90EE90; }
.feature-dot.shape { background: #87CEEB; }
.feature-dot.moisture { background: #DDA0DD; }
.feature-dot.crack { background: #FFD700; }
.feature-dot.teeth { background: #F0E68C; }

.color-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: var(--radius);
  color: var(--fg);
  font-size: 12px;
  font-weight: 600;
  border: 1px solid rgba(0,0,0,0.1);
}
.desc {
  color: var(--muted);
  font-size: 12px;
}

.syndrome-card {
  background: linear-gradient(135deg, var(--warn-soft) 0%, var(--border) 100%);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}
.syndrome-card h4 {
  margin-bottom: 12px;
  color: var(--fg);
  font-size: 14px;
}
.syndrome-result {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.syndrome-name {
  font-size: 22px;
  font-weight: bold;
  color: var(--fg);
}
.overall-type {
  font-size: 14px;
  font-weight: 600;
  padding: 4px 12px;
  background: white;
  border-radius: 20px;
}

.advice-section h4 {
  margin-bottom: 12px;
  color: var(--fg);
  font-size: 14px;
}
.advice-card {
  background: var(--warn-soft);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 12px;
  border-left: 3px solid var(--accent);
}
.advice-card h5 {
  margin-bottom: 8px;
  color: var(--fg);
  font-size: 13px;
}
.advice-card p {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
  margin: 0;
}
.advice-card.diet { border-left-color: var(--success); }
.advice-card.lifestyle { border-left-color: var(--info); }

.action-buttons {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}
.action-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.action-btn:hover {
  border-color: var(--accent-strong);
  color: var(--accent-strong);
}
.action-btn.export:hover { border-color: var(--success); color: var(--success); }
.action-btn.retry:hover { border-color: var(--info); color: var(--info); }

@media (max-width: 1200px) {
  .diagnosis-container {
    grid-template-columns: 1fr;
  }
  .right-panel {
    max-height: none;
  }
}
/* page-header mascot positioning */
.page-header { display: flex; align-items: center; flex-wrap: wrap; }
.page-header .mascot-companion {
  position: relative; top: auto; transform: none;
  margin-right: 8px; flex-shrink: 0;
}

</style>
