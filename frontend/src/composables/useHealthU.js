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
    const saved = localStorage.getItem('hk-sound')
    if (saved === '0') soundEnabled.value = false
  })

  function toggleSound() {
    soundEnabled.value = !soundEnabled.value
    localStorage.setItem('hk-sound', soundEnabled.value ? '1' : '0')
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
