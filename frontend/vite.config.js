import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

// 开发端口：首次启动随机取一个四位数（4000–7999）并写入 .dev-port，
// 之后每次启动都复用同一个端口，保证开发地址固定。
// 生产模式不受影响：npm run build 后由后端 8420 统一托管。
const portFile = resolve(dirname(fileURLToPath(import.meta.url)), '.dev-port')

function resolveDevPort() {
  if (existsSync(portFile)) {
    const saved = Number.parseInt(readFileSync(portFile, 'utf8').trim(), 10)
    if (Number.isInteger(saved) && saved >= 1000 && saved <= 9999) {
      return saved
    }
  }
  const port = 4000 + Math.floor(Math.random() * 4000)
  writeFileSync(portFile, `${port}\n`, 'utf8')
  return port
}

export default defineConfig({
  plugins: [vue()],
  base: '/',
  build: {
    outDir: '../static',
    assetsDir: 'assets'
  },
  server: {
    port: resolveDevPort(),
    // 端口一旦确定就固定使用；被占用时直接报错，而不是悄悄换端口。
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8420',
        changeOrigin: true
      }
    }
  }
})
