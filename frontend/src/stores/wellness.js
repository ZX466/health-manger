import { defineStore } from 'pinia'
import api from '../api'
import { localDateKey } from '../utils/date'
import {
  buildPersonaCard,
  getHealthTier,
  isDangerousRating,
  moodTitle,
  pickRandom,
  TIP_POOLS
} from '../constants/copywriting'

const BEDTIME_KEY = 'hw:bedtime'

function readBedtime (dateKey) {
  try {
    const raw = localStorage.getItem(`${BEDTIME_KEY}:${dateKey}`)
    if (!raw) return null
    const value = Number(raw)
    return Number.isFinite(value) ? value : null
  } catch (e) {
    return null
  }
}

function writeBedtime (dateKey, value) {
  try {
    if (value == null || value === '') localStorage.removeItem(`${BEDTIME_KEY}:${dateKey}`)
    else localStorage.setItem(`${BEDTIME_KEY}:${dateKey}`, String(value))
  } catch (e) { /* ignore */ }
}

/** "23:30" → 23.5；"01:10" → 1.17（用于判断凌晨入睡） */
export function timeToHour (text) {
  if (!text) return null
  const [hour, minute] = String(text).split(':').map(Number)
  if (!Number.isFinite(hour)) return null
  return hour + (Number.isFinite(minute) ? minute / 60 : 0)
}

export function hourToTime (value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return ''
  const normalized = ((number % 24) + 24) % 24
  const hour = Math.floor(normalized)
  const minute = Math.round((normalized - hour) * 60)
  return `${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`
}

export const useWellnessStore = defineStore('wellness', {
  state: () => ({
    loaded: false,
    loading: false,
    error: '',
    dateKey: localDateKey(),
    healthScore: null,
    healthRating: '',
    moodLevel: null,
    sleepHours: null,
    bedtimeHour: null,
    stressTags: [],
    hasSportToday: false,
    seriousMode: false,
    isHighRisk: false
  }),

  getters: {
    healthTier (state) {
      return getHealthTier({ score: state.healthScore, rating: state.healthRating })
    },
    isDanger (state) {
      return state.seriousMode || state.isHighRisk || isDangerousRating({ score: state.healthScore, rating: state.healthRating })
    },
    moodTitle (state) {
      return state.moodLevel ? moodTitle(state.moodLevel) : ''
    },
    avatarState (state) {
      if (this.isDanger) return 'crisis'
      if (Number(state.bedtimeHour) >= 1.5) return 'night_owl'
      if (state.moodLevel && Number(state.moodLevel) <= 2) return 'low_mood'
      if (state.hasSportToday && Number(state.healthScore) >= 85) return 'energetic'
      return 'default'
    },
    avatarBubble (state) {
      if (this.avatarState === 'crisis') {
        return '今天先不玩梗。你不需要一个人扛，愿意的话，去心理空间看看支持资源。'
      }
      if (this.avatarState === 'night_owl') return pickRandom(TIP_POOLS.nightOwl)
      if (this.avatarState === 'low_mood') return pickRandom(TIP_POOLS.lowMood)
      if (this.avatarState === 'energetic') return pickRandom(TIP_POOLS.energetic)
      return pickRandom(TIP_POOLS.daily)
    },
    personaCard (state) {
      return buildPersonaCard({
        score: state.healthScore,
        rating: state.healthRating,
        bedtimeHour: state.bedtimeHour,
        moodLevel: state.moodLevel,
        stressTags: state.stressTags,
        sleepHours: state.sleepHours,
        hasSport: state.hasSportToday,
        isHighRisk: this.isDanger
      })
    }
  },

  actions: {
    hydrateLocal () {
      this.dateKey = localDateKey()
      this.bedtimeHour = readBedtime(this.dateKey)
    },

    setBedtime (value) {
      const numeric = typeof value === 'string' ? timeToHour(value) : (Number.isFinite(Number(value)) ? Number(value) : null)
      this.bedtimeHour = numeric
      writeBedtime(localDateKey(), numeric)
    },

    applyMood ({ level, tags, sleepHours, bedtimeHour } = {}) {
      if (level != null) this.moodLevel = Number(level)
      if (Array.isArray(tags)) this.stressTags = [...tags]
      if (sleepHours != null) this.sleepHours = Number(sleepHours)
      if (bedtimeHour != null) this.setBedtime(bedtimeHour)
    },

    async load (force = false) {
      if (this.loading) return
      if (this.loaded && !force) return
      this.loading = true
      this.error = ''
      this.hydrateLocal()

      const today = localDateKey()
      const results = await Promise.allSettled([
        api.getLatestRating(),
        api.getMentalSummary(),
        api.getMentalMood({ days: 1 }),
        api.getSportRecords({ start_date: today, end_date: today })
      ])
      const [ratingRes, summaryRes, moodRes, sportRes] = results

      if (ratingRes.status === 'fulfilled') {
        const data = ratingRes.value?.data
        if (data && data.score != null) {
          this.healthScore = Number(data.score)
          this.healthRating = data.rating || ''
        }
      }

      if (summaryRes.status === 'fulfilled') {
        const data = summaryRes.value?.data
        if (data) {
          this.seriousMode = !!data.serious_mode
          this.isHighRisk = !!data.serious_mode
          if (data.sleep_avg_7d != null) this.sleepHours = Number(data.sleep_avg_7d)
          const latest = data.latest_mood
          if (latest && this.isToday(latest.record_date)) {
            this.moodLevel = latest.mood_score ?? null
            this.sleepHours = latest.sleep_hours ?? this.sleepHours
            this.stressTags = Array.isArray(latest.stress_tags) ? latest.stress_tags : []
          }
          const crisisScale = [data.latest_phq9, data.latest_gad7].some(item => item?.crisis_flag)
          if (crisisScale) this.isHighRisk = true
        }
      }

      if (moodRes.status === 'fulfilled') {
        const records = Array.isArray(moodRes.value?.data) ? moodRes.value.data : []
        const todayRecord = records.find(item => this.isToday(item.record_date))
        if (todayRecord) {
          this.moodLevel = todayRecord.mood_score ?? this.moodLevel
          this.sleepHours = todayRecord.sleep_hours ?? this.sleepHours
          this.stressTags = Array.isArray(todayRecord.stress_tags) ? todayRecord.stress_tags : this.stressTags
        }
      }

      if (sportRes.status === 'fulfilled') {
        const records = Array.isArray(sportRes.value?.data) ? sportRes.value.data : []
        this.hasSportToday = records.some(item => this.isToday(item.record_date))
      }

      const failed = results.filter(item => item.status === 'rejected')
      if (failed.length === results.length) this.error = '健康状态暂时没加载出来'
      this.loaded = true
      this.loading = false
    },

    isToday (value) {
      if (!value) return false
      const text = String(value)
      return text.slice(0, 10) === localDateKey()
    }
  }
})
