import { computed, reactive, ref } from 'vue'
import { COMPANION_KEYS, MEDIA_ASSETS } from '../constants/media'

const STORAGE_KEY = 'hk-prefs-v1'
const SOUND_KEY = 'hk-sound'

const prefersReduced = typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

function readStore () {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const parsed = JSON.parse(raw)
    return parsed && typeof parsed === 'object' ? parsed : {}
  } catch (e) {
    return {}
  }
}

function writeStore (value) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(value))
  } catch (e) { /* 隐私模式忽略 */ }
}

const saved = readStore()

const theme = ref(saved.theme === 'dark' ? 'dark' : 'light')
const companion = ref(COMPANION_KEYS.includes(saved.companion) ? saved.companion : 'hajimi')
const animated = ref(saved.animated == null ? !prefersReduced : Boolean(saved.animated))
const goals = reactive({
  sleep: clampNumber(saved.goals?.sleep, 8, 4, 12),
  steps: clampNumber(saved.goals?.steps, 8000, 1000, 50000),
  calories: clampNumber(saved.goals?.calories, 2000, 800, 6000)
})
const reminders = reactive({
  morning: saved.reminders?.morning !== false,
  water: saved.reminders?.water !== false,
  breath: Boolean(saved.reminders?.breath)
})
const favoriteIds = ref(Array.isArray(saved.blindbox?.favorites) ? [...saved.blindbox.favorites] : ['bb-1', 'bb-5'])
const captions = reactive(
  saved.blindbox?.captions && typeof saved.blindbox.captions === 'object'
    ? { ...saved.blindbox.captions }
    : {}
)

let initialized = false

function clampNumber (value, fallback, min, max) {
  const number = Number(value)
  if (!Number.isFinite(number)) return fallback
  return Math.min(max, Math.max(min, number))
}

function persist () {
  writeStore({
    theme: theme.value,
    companion: companion.value,
    animated: animated.value,
    goals: { ...goals },
    reminders: { ...reminders },
    blindbox: {
      favorites: favoriteIds.value,
      captions: { ...captions }
    }
  })
}

export function applyTheme (next = theme.value) {
  if (typeof document === 'undefined') return
  const value = next === 'dark' ? 'dark' : 'light'
  document.documentElement.dataset.theme = value
  document.documentElement.style.colorScheme = value
}

export function initPreferences () {
  appliedTheme() // 首次进入即同步 html[data-theme]
  if (initialized) return
  initialized = true
  try {
    if (localStorage.getItem(SOUND_KEY) === '0') {
      // 音效状态由 useHealthU 统一维护，这里只负责首屏主题。
    }
  } catch (e) { /* ignore */ }
}

function appliedTheme () {
  applyTheme(theme.value)
}

export function usePreferences () {
  const companionMeta = computed(() => MEDIA_ASSETS[companion.value] || MEDIA_ASSETS.hajimi)

  function setTheme (value) {
    theme.value = value === 'dark' ? 'dark' : 'light'
    applyTheme(theme.value)
    persist()
  }

  function toggleTheme () {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  function setCompanion (value) {
    if (!COMPANION_KEYS.includes(value)) return
    companion.value = value
    persist()
  }

  function setAnimated (value) {
    animated.value = Boolean(value)
    persist()
  }

  function saveGoals (next = {}) {
    goals.sleep = clampNumber(next.sleep, goals.sleep, 4, 12)
    goals.steps = clampNumber(next.steps, goals.steps, 1000, 50000)
    goals.calories = clampNumber(next.calories, goals.calories, 800, 6000)
    persist()
  }

  function saveReminders (next = {}) {
    reminders.morning = Boolean(next.morning)
    reminders.water = Boolean(next.water)
    reminders.breath = Boolean(next.breath)
    persist()
  }

  function isFavorite (id) {
    return favoriteIds.value.includes(id)
  }

  function toggleFavorite (id) {
    if (favoriteIds.value.includes(id)) {
      favoriteIds.value = favoriteIds.value.filter(item => item !== id)
      persist()
      return false
    }
    favoriteIds.value = [...favoriteIds.value, id]
    persist()
    return true
  }

  function captionFor (item) {
    const custom = captions[item.id]
    return typeof custom === 'string' && custom.trim() ? custom.trim() : item.title
  }

  function setCaption (id, text, fallback) {
    const value = String(text || '').trim()
    if (!value || value === fallback) delete captions[id]
    else captions[id] = value
    persist()
  }

  function resetCaption (id) {
    delete captions[id]
    persist()
  }

  return {
    theme,
    companion,
    companionMeta,
    animated,
    goals,
    reminders,
    favoriteIds,
    captions,
    setTheme,
    toggleTheme,
    setCompanion,
    setAnimated,
    saveGoals,
    saveReminders,
    isFavorite,
    toggleFavorite,
    captionFor,
    setCaption,
    resetCaption
  }
}
