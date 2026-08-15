import { createRouter, createWebHistory } from 'vue-router'

// 路由级懒加载——按需加载视图，缩小首屏 JS 体积
const Login = () => import('../views/Login.vue')
const Register = () => import('../views/Register.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const HealthRecord = () => import('../views/HealthRecord.vue')
const HealthAnalysis = () => import('../views/HealthAnalysis.vue')
const DietManagement = () => import('../views/DietManagement.vue')
const SportManagement = () => import('../views/SportManagement.vue')
const TongueDiagnosis = () => import('../views/TongueDiagnosis.vue')
const ChatView = () => import('../views/ChatView.vue')
const AISettings = () => import('../views/AISettings.vue')

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { layout: 'auth', title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: Register,
    meta: { layout: 'auth', title: '注册' }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true, title: '健康仪表盘' }
  },
  {
    path: '/health-record',
    name: 'HealthRecord',
    component: HealthRecord,
    meta: { requiresAuth: true, title: '健康记录' }
  },
  {
    path: '/health-analysis',
    name: 'HealthAnalysis',
    component: HealthAnalysis,
    meta: { requiresAuth: true, title: '健康分析' }
  },
  {
    path: '/diet-management',
    name: 'DietManagement',
    component: DietManagement,
    meta: { requiresAuth: true, title: '饮食管理' }
  },
  {
    path: '/sport-management',
    name: 'SportManagement',
    component: SportManagement,
    meta: { requiresAuth: true, title: '运动管理' }
  },
  {
    path: '/tongue-diagnosis',
    name: 'TongueDiagnosis',
    component: TongueDiagnosis,
    meta: { requiresAuth: true, title: '中医舌诊' }
  },
  {
    path: '/chat',
    name: 'ChatView',
    component: ChatView,
    meta: { requiresAuth: true, title: 'AI 对话' }
  },
  {
    path: '/ai-settings',
    name: 'AISettings',
    component: AISettings,
    meta: { requiresAuth: true, title: 'AI 设置' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/register') && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router