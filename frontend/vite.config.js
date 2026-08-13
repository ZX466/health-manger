import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/',
  build: {
    outDir: '../static',
    assetsDir: 'assets'
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8420',
        changeOrigin: true
      }
    }
  }
})
