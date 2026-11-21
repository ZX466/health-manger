import { ref } from 'vue'
import { AUDIO_CLIPS } from '../constants/media'

const SOUND_KEY = 'hk-sound'

function readSoundSetting () {
  try {
    return localStorage.getItem(SOUND_KEY) !== '0'
  } catch (e) {
    return true
  }
}

const soundEnabled = ref(readSoundSetting())
const suppressed = ref(false)
const playingClipId = ref('')

let activeAudio = null
let activeTimer = null

/** 关怀模式由 AppShell 统一注入；一旦开启，全局音效立即停止并拒绝播放。 */
export function setAudioSuppressed (value) {
  suppressed.value = Boolean(value)
  if (suppressed.value) stopAllAudio()
}

export function isAudioAvailable () {
  return soundEnabled.value && !suppressed.value
}

export function useSound () {
  function toggleSound () {
    setSoundEnabled(!soundEnabled.value)
  }

  function setSoundEnabled (value) {
    soundEnabled.value = Boolean(value)
    if (!soundEnabled.value) stopAllAudio()
    try {
      localStorage.setItem(SOUND_KEY, soundEnabled.value ? '1' : '0')
    } catch (e) { /* ignore */ }
  }

  return { soundEnabled, suppressed, toggleSound, setSoundEnabled, isAudioAvailable }
}

export function stopAllAudio () {
  if (activeTimer) {
    clearTimeout(activeTimer)
    activeTimer = null
  }
  if (activeAudio) {
    try {
      activeAudio.pause()
      activeAudio.currentTime = 0
    } catch (e) { /* ignore */ }
    activeAudio = null
  }
  playingClipId.value = ''
}

/**
 * 播放真实配音片段。
 * @returns {boolean} 是否成功开始播放（静音/关怀模式/音频错误时为 false）。
 */
export function playClip (key, options = {}) {
  if (!isAudioAvailable()) return false
  const clip = AUDIO_CLIPS[key]
  if (!clip?.src) return false
  const sameClip = options.clipId && playingClipId.value === options.clipId
  stopAllAudio()
  if (sameClip) return false
  try {
    const audio = new Audio(clip.src)
    audio.volume = options.volume ?? 0.72
    activeAudio = audio
    playingClipId.value = options.clipId || key
    audio.addEventListener('ended', () => {
      if (activeAudio === audio) stopAllAudio()
    })
    audio.addEventListener('error', () => {
      if (activeAudio === audio) stopAllAudio()
    })
    const promise = audio.play()
    if (promise?.catch) {
      promise.catch(() => {
        if (activeAudio === audio) stopAllAudio()
      })
    }
    const maxMs = options.maxMs || (key === 'pixabay' ? 6000 : 10000)
    activeTimer = setTimeout(() => {
      if (activeAudio === audio) stopAllAudio()
    }, maxMs)
    return true
  } catch (e) {
    stopAllAudio()
    return false
  }
}

export function playSound (type) {
  const map = {
    success: 'pixabay',
    cheer: 'belly',
    giggle: 'giggle',
    laugh: 'crazy'
  }
  const key = map[type]
  if (!key) return false
  if (!isAudioAvailable()) return false
  try {
    const clip = AUDIO_CLIPS[key]
    const audio = new Audio(clip.src)
    audio.volume = 0.3
    audio.play().catch(() => {})
    return true
  } catch (e) {
    return false
  }
}

// 合成音：不依赖新增音频文件；静音与关怀模式都会直接关闭。
let audioContext = null

function getAudioContext () {
  if (!isAudioAvailable()) return null
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext
    if (!AudioCtx) return null
    if (!audioContext) audioContext = new AudioCtx()
    if (audioContext.state === 'suspended') audioContext.resume()
    return audioContext
  } catch (e) {
    return null
  }
}

export function playWoodfish () {
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
export function playBreathCue (phase = 'inhale') {
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

export { soundEnabled, suppressed, playingClipId }
