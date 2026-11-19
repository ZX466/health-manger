import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 每次启动随机取一个四位数端口（4000–7999），避免 3000 被占用。
// 端口只在启动时决定一次；若被占用，Vite 会自动顺延到下一个可用端口。
const devPort = 4000 + Math.floor(Math.random() * 4000)

export default defineConfig({
  plugins: [vue()],
  base: '/',
  build: {
    outDir: '../static',
    assetsDir: 'assets'
  },
  server: {
    port: devPort,
    proxy: {
      '/api': {
        target: 'http://localhost:8420',
        changeOrigin: true
      }
    }
  }
})
