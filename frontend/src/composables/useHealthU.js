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

// 木鱼合成音：不依赖新增音频文件；首次点击时也尊重 localStorage 里的静音开关。
let audioContext = null

export function playWoodfish() {
  if (!soundEnabled.value) return
  try {
    if (typeof localStorage !== 'undefined' && localStorage.getItem('hk-sound') === '0') return
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return
    if (!audioContext) audioContext = new AudioCtx()
    if (audioContext.state === 'suspended') audioContext.resume()

    const now = audioContext.currentTime
    const osc = audioContext.createOscillator()
    const gain = audioContext.createGain()
    osc.type = 'triangle'
    osc.frequency.setValueAtTime(520, now)
    osc.frequency.exponentialRampToValueAtTime(180, now + 0.09)
    gain.gain.setValueAtTime(0.0001, now)
    gain.gain.exponentialRampToValueAtTime(0.16, now + 0.005)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.18)
    osc.connect(gain)
    gain.connect(audioContext.destination)
    osc.start(now)
    osc.stop(now + 0.2)
  } catch (e) { /* ignore */ }
}
