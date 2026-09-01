import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// dev server 把後端路由轉發到 :8000，讓瀏覽器視角是同源 —— 不用碰 CORS，
// 行為也比較貼近之後 EC2 上「前後端同一個 domain」的部署方式。
// 後端新增 router prefix 記得同步加在這裡。
const BACKEND_PREFIXES = ['/auth', '/manga', '/collections', '/health']

// 部署到 GitHub Pages 時 URL 是 https://<user>.github.io/<repo>/
// 所以 production build 的 base 要設成 /<repo>/
// 本機 dev 時還是用 /（localhost:5173/）
// 透過環境變數 VITE_BASE_PATH 切換，給 GitHub Actions build 時注入
export default defineConfig(({ command }) => ({
  plugins: [vue()],
  base: command === 'build' ? (process.env.VITE_BASE_PATH ?? '/manga-record/') : '/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: Object.fromEntries(
      BACKEND_PREFIXES.map((prefix) => [
        prefix,
        { target: 'http://localhost:8000', changeOrigin: true },
      ]),
    ),
  },
}))
