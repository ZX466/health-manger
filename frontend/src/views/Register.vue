<template>
  <div class="auth-container">
    <div class="auth-box">
      <div class="cat-mascot cat-blink cat-wobble">
        <div class="cat-ear left"></div>
        <div class="cat-ear right"></div>
        <div class="cat-eyes">
          <div class="cat-eye"></div>
          <div class="cat-eye"></div>
        </div>
        <div class="cat-mouth"></div>
        <div class="cat-blush left"></div>
        <div class="cat-blush right"></div>
      </div>
      <h1 class="title">大学生健康系统</h1>
      <h2 class="subtitle">用户注册</h2>
      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="form-group">
          <label for="reg-name">姓名</label>
          <input id="reg-name" v-model="name" type="text" required placeholder="请输入姓名" autocomplete="username" />
        </div>
        <div class="form-group">
          <label for="reg-password">密码</label>
          <input id="reg-password" v-model="password" type="password" required placeholder="请输入密码" autocomplete="new-password" />
        </div>
        <div class="form-group">
          <label for="reg-invite">邀请码</label>
          <input id="reg-invite" v-model="inviteCode" type="text" required placeholder="请输入邀请码" />
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <div v-if="success" class="success-message">{{ success }}</div>
        <button type="submit" :disabled="loading" class="submit-btn" :class="{ loading: loading }">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      <p class="auth-link">
        已有账号？ <router-link to="/login">立即登录</router-link>
      </p>
    </div>
  </div>
</template>

<script>
import api from '../api'

export default {
  name: 'Register',
  data() {
    return {
      name: '',
      password: '',
      inviteCode: '',
      loading: false,
      error: '',
      success: ''
    }
  },
  methods: {
    async handleRegister() {
      this.loading = true
      this.error = ''
      this.success = ''
      try {
        await api.register({
          name: this.name,
          password: this.password,
          invite_code: this.inviteCode
        })
        this.success = '注册成功！正在跳转到登录页面...'
        setTimeout(() => {
          this.$router.push('/login')
        }, 1500)
      } catch (err) {
        this.error = err.response?.data?.detail || '注册失败，请检查信息'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  background: radial-gradient(circle at 30% 70%, rgba(255, 181, 194, 0.15) 0%, transparent 50%),
              radial-gradient(circle at 70% 30%, rgba(255, 229, 160, 0.15) 0%, transparent 50%);
}
.auth-box {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: var(--shadow-md);
  border: 1px solid rgba(0,0,0,0.05);
  text-align: center;
}
.cat-mascot {
  position: relative;
  width: 80px;
  height: 72px;
  margin: 0 auto 16px;
  transform: scale(0.7);
}
.title {
  text-align: center;
  color: var(--accent-hover);
  font-size: 26px;
  margin-bottom: 8px;
  font-weight: 700;
}
.subtitle {
  text-align: center;
  color: var(--muted);
  font-size: 16px;
  margin-bottom: 28px;
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  text-align: left;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-group label {
  font-weight: 600;
  color: var(--fg);
  font-size: 14px;
}
.form-group input {
  padding: 14px 18px;
  border: 1px solid rgba(0,0,0,0.05);
  border-radius: var(--radius);
  font-size: 14px;
  transition: var(--transition);
  font-family: var(--font-body);
  background: var(--bg);
}
.form-group input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(255, 181, 194, 0.2);
}
.error-message {
  color: var(--danger);
  font-size: 14px;
  text-align: center;
  padding: 12px;
  background: #fff0f0;
  border-radius: var(--radius);
  border: 1px solid #ffd6d6;
}
.success-message {
  color: var(--success);
  font-size: 14px;
  text-align: center;
  padding: 12px;
  background: #f0fff4;
  border-radius: var(--radius);
  border: 1px solid #c6f6d5;
}
.submit-btn {
  padding: 14px;
  background: linear-gradient(135deg, var(--accent) 0%, var(--accent) 100%);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  font-family: var(--font-body);
  box-shadow: var(--shadow-md);
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}
.submit-btn.loading {
  animation: bounce-laugh 0.6s ease-in-out infinite;
}
.auth-link {
  text-align: center;
  margin-top: 20px;
  color: var(--muted);
  font-size: 14px;
}
.auth-link a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 600;
}
.auth-link a:hover {
  color: var(--accent);
}
</style>
