import { ref, onMounted, onUnmounted, nextTick } from 'vue'

const toastContainer = ref(null)
const soundEnabled = ref(true)

const AUDIO_FILES = {
  success: '/assets/mpo6l1c6-pixabay_cartoon_laugh.mp3',
  cheer: '/assets/mpo6ky8m-cartoon-belly-laugh.mp3',
  giggle: '/assets/mpo6kd2k-cartoon-giggle.mp3',
  laugh: '/assets/mpo6kd1j-cartoon-crazy-laugh.mp3'
}

function ensureToastContainer() {
  if (!toastContainer.value) {
    const el = document.createElement('div')
    el.className = 'toast-container'
    document.body.appendChild(el)
    toastContainer.value = el
  }
  return toastContainer.value
}

export function useToast() {
  function showToast(message, type = 'info', duration = 3000) {
    const container = ensureToastContainer()
    const toast = document.createElement('div')
    toast.className = 'toast' + (type === 'success' ? ' toast-success' : type === 'error' ? ' toast-error' : '')
    toast.textContent = message
    container.appendChild(toast)
    requestAnimationFrame(() => toast.classList.add('show'))
    setTimeout(() => {
      toast.classList.remove('show')
      setTimeout(() => toast.remove(), 300)
    }, duration)

    if (soundEnabled.value) {
      if (type === 'success') playSound('giggle')
      else if (type === 'error') playSound('laugh')
    }
  }
  return { showToast }
}

export function useModal() {
  function openModal(id) {
    const el = document.getElementById(id)
    if (el) { el.classList.add('show'); document.body.style.overflow = 'hidden' }
  }
  function closeModal(id) {
    const el = document.getElementById(id)
    if (el) { el.classList.remove('show'); document.body.style.overflow = '' }
  }
  return { openModal, closeModal }
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

function playSound(type) {
  if (!soundEnabled.value) return
  const src = AUDIO_FILES[type]
  if (!src) return
  try {
    const audio = new Audio(src)
    audio.volume = 0.3
    audio.play().catch(() => {})
  } catch (e) { /* ignore */ }
}

export function useScrollReveal() {
  let observer = null

  onMounted(() => {
    nextTick(() => {
      const els = document.querySelectorAll('.animate-in')
      if (!els.length) return
      els.forEach(el => el.classList.add('prepare'))
      observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.remove('prepare')
            entry.target.classList.add('visible')
            observer.unobserve(entry.target)
          }
        })
      }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' })
      els.forEach(el => observer.observe(el))
      setTimeout(() => {
        document.querySelectorAll('.animate-in.prepare:not(.visible)').forEach(el => {
          el.classList.remove('prepare')
          el.classList.add('visible')
        })
      }, 800)
    })
  })

  onUnmounted(() => {
    if (observer) observer.disconnect()
  })
}

export function useCountUp() {
  function animateNumber(el, target, duration = 800) {
    const isFloat = String(target).includes('.')
    const start = 0
    const startTime = performance.now()
    function update(currentTime) {
      const elapsed = currentTime - startTime
      const progress = Math.min(elapsed / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      const current = start + (target - start) * eased
      el.textContent = isFloat ? current.toFixed(1) : Math.round(current)
      if (progress < 1) requestAnimationFrame(update)
    }
    requestAnimationFrame(update)
  }

  let observer = null

  onMounted(() => {
    nextTick(() => {
      const counters = document.querySelectorAll('[data-count-to]')
      if (!counters.length) return
      observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const target = parseFloat(entry.target.dataset.countTo)
            animateNumber(entry.target, target)
            observer.unobserve(entry.target)
          }
        })
      }, { threshold: 0.3 })
      counters.forEach(el => observer.observe(el))
    })
  })

  onUnmounted(() => {
    if (observer) observer.disconnect()
  })

  return { animateNumber }
}

export function useScrollProgress() {
  let ticking = false

  function onScroll() {
    if (!ticking) {
      requestAnimationFrame(() => {
        const bar = document.querySelector('.scroll-progress')
        if (bar) {
          const scrollTop = document.documentElement.scrollTop || document.body.scrollTop
          const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight
          const progress = scrollHeight > 0 ? scrollTop / scrollHeight : 0
          bar.style.transform = `scaleX(${progress})`
        }
        ticking = false
      })
      ticking = true
    }
  }

  onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
  onUnmounted(() => window.removeEventListener('scroll', onScroll))
}

export function useLightbox() {
  let overlay = null
  let gallery = []
  let index = 0

  function createLightbox() {
    if (overlay) return
    overlay = document.createElement('div')
    overlay.className = 'lightbox-overlay'
    overlay.innerHTML = `
      <button class="lightbox-nav lightbox-prev" style="position:absolute;top:50%;left:16px;width:44px;height:44px;border-radius:50%;background:rgba(0,0,0,0.4);color:white;border:none;cursor:pointer;display:grid;place-items:center;transform:translateY(-50%);backdrop-filter:blur(8px)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><polyline points="15 18 9 12 15 6"/></svg></button>
      <div class="lightbox-content">
        <img src="" alt="" />
        <button class="lightbox-close"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
      </div>
      <button class="lightbox-nav lightbox-next" style="position:absolute;top:50%;right:16px;width:44px;height:44px;border-radius:50%;background:rgba(0,0,0,0.4);color:white;border:none;cursor:pointer;display:grid;place-items:center;transform:translateY(-50%);backdrop-filter:blur(8px)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20"><polyline points="9 18 15 12 9 6"/></svg></button>
    `
    document.body.appendChild(overlay)
    overlay.querySelector('.lightbox-close').addEventListener('click', closeLightbox)
    overlay.addEventListener('click', e => { if (e.target === overlay) closeLightbox() })
    overlay.querySelector('.lightbox-prev').addEventListener('click', () => navigate(-1))
    overlay.querySelector('.lightbox-next').addEventListener('click', () => navigate(1))
    document.addEventListener('keydown', e => {
      if (!overlay.classList.contains('show')) return
      if (e.key === 'Escape') closeLightbox()
      if (e.key === 'ArrowLeft') navigate(-1)
      if (e.key === 'ArrowRight') navigate(1)
    })
  }

  function openLightbox(src, caption, galleryItems, idx) {
    createLightbox()
    gallery = galleryItems || []
    index = idx || 0
    const img = overlay.querySelector('.lightbox-content img')
    img.src = src
    img.alt = caption || ''
    overlay.classList.add('show')
    document.body.style.overflow = 'hidden'
  }

  function closeLightbox() {
    if (!overlay) return
    overlay.classList.remove('show')
    document.body.style.overflow = ''
  }

  function navigate(dir) {
    if (gallery.length <= 1) return
    index = (index + dir + gallery.length) % gallery.length
    const item = gallery[index]
    const img = overlay.querySelector('.lightbox-content img')
    img.style.opacity = '0'
    setTimeout(() => {
      img.src = item.src
      img.alt = item.caption || ''
      img.style.opacity = '1'
    }, 150)
    img.style.transition = 'opacity 0.15s ease'
  }

  return { openLightbox, closeLightbox }
}
