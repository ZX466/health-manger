<template>
  <div>
    <header class="auth-topnav">
      <router-link to="/login" class="auth-topnav-logo">
        <span class="logo-icon">慧</span>
        慧康 HealthU
      </router-link>
      <div class="auth-topnav-right">
        还没有账号？ <router-link to="/register">立即注册</router-link>
      </div>
    </header>
    <main class="auth-main">
      <div class="auth-card">
        <div class="auth-header">
          <div class="auth-icon">
            <CharacterAvatar type="hajimi" :animated="true" style="width:64px;height:64px" />
          </div>
          <h1>欢迎回来</h1>
          <p>登录你的慧康账号</p>
        </div>
        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label for="login-name">姓名</label>
            <input id="login-name" v-model="name" class="form-input" type="text" placeholder="请输入姓名" autocomplete="username" />
          </div>
          <div class="form-group">
            <label for="login-password">密码</label>
            <input id="login-password" v-model="password" class="form-input" type="password" placeholder="请输入密码" autocomplete="current-password" />
          </div>
          <div v-if="error" class="error-msg">{{ error }}</div>
          <button type="submit" :disabled="loading" class="auth-submit">
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        <p class="auth-footer">
          还没有账号？ <router-link to="/register">立即注册</router-link>
        </p>
      </div>
    </main>
  </div>
</template>

<script>
import api from '../api'
import CharacterAvatar from '../components/CharacterAvatar.vue'

export default {
  name: 'Login',
  components: { CharacterAvatar },
  data() {
    return {
      name: '',
      password: '',
      loading: false,
      error: ''
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      this.error = ''
      try {
        const response = await api.login(this.name, this.password)
        localStorage.setItem('token', response.data.access_token)
        localStorage.setItem('userName', this.name)
        this.$router.push('/dashboard')
      } catch (err) {
        this.error = err.response?.data?.detail || '登录失败，请检查用户名和密码'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 4px;
}
.error-msg {
  color: var(--danger);
  font-size: 13px;
  margin-bottom: 12px;
  padding: 10px 14px;
  background: var(--danger-soft);
  border-radius: var(--radius);
  text-align: center;
}
</style>
