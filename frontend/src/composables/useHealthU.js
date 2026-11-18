import { ref, onMounted } from 'vue'

const soundEnabled = ref(true)

const AUDIO_FILES = {
  success: '/assets/mpo6l1c6-pixabay_cartoon_laugh.mp3',
  cheer: '/assets/mpo6ky8m-cartoon-belly-laugh.mp3',
  giggle: '/assets/mpo6kd2k-cartoon-giggle.mp3',
  laugh: '/assets/mpo6kd1j-cartoon-crazy-laugh.mp3'
}

export function useSound() {
  onMounted(() => {
    try {
      const saved = localStorage.getItem('hk-sound')
      if (saved === '0') soundEnabled.value = false
    } catch (e) { /* 隐私模式等场景下无法读取，保持默认开启 */ }
  })

  function toggleSound() {
    soundEnabled.value = !soundEnabled.value
    try {
      localStorage.setItem('hk-sound', soundEnabled.value ? '1' : '0')
    } catch (e) { /* ignore */ }
  }

  return { soundEnabled, toggleSound }
}

export function playSound(type) {
  if (!soundEnabled.value) return
  const src = AUDIO_FILES[type]
  if (!src) return
  try {
    const audio = new Audio(src)
    audio.volume = 0.3
    audio.play().catch(() => {})
  } catch (e) { /* ignore */ }
}

// 合成音：不依赖新增音频文件；首次点击时也尊重 localStorage 里的静音开关。
let audioContext = null

function getAudioContext () {
  if (soundEnabled.value === false) return null
  try {
    if (typeof localStorage !== 'undefined' && localStorage.getItem('hk-sound') === '0') return null
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return null
    if (!audioContext) audioContext = new AudioCtx()
    if (audioContext.state === 'suspended') audioContext.resume()
    return audioContext
  } catch (e) {
    return null
  }
}

export function playWoodfish() {
  const ctx = getAudioContext()
  if (!ctx) return
  try {
    const now = ctx.currentTime
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(520, now)
    osc.frequency.exponentialRampToValueAtTime(180, now + 0.09)
    gain.gain.setValueAtTime(0.0001, now)
    gain.gain.exponentialRampToValueAtTime(0.16, now + 0.005)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(now)
    osc.stop(now + 0.2)
  } catch (e) { /* ignore */ }
}

/** 4-7-8 呼吸训练的轻柔节拍提示音。 */
export function playBreathCue(phase = 'inhale') {
  const ctx = getAudioContext()
  if (!ctx) return
  try {
    const now = ctx.currentTime
    const freq = phase === 'inhale' ? 392 : phase === 'hold' ? 330 : 262
    const osc = ctx.createOscillator()
    const gain = ctx.createGain()
    osc.type = 'sine'
    osc.frequency.setValueAtTime(freq, now)
    gain.gain.setValueAtTime(0.0001, now)
    gain.gain.exponentialRampToValueAtTime(0.07, now + 0.04)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.42)
    osc.connect(gain)
    gain.connect(ctx.destination)
    osc.start(now)
    osc.stop(now + 0.46)
  } catch (e) { /* ignore */ }
}
