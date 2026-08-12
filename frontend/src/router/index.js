import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import Dashboard from '../views/Dashboard.vue'
import HealthRecord from '../views/HealthRecord.vue'
import HealthAnalysis from '../views/HealthAnalysis.vue'
import DietManagement from '../views/DietManagement.vue'
import SportManagement from '../views/SportManagement.vue'
import TongueDiagnosis from '../views/TongueDiagnosis.vue'

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
