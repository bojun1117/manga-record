import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

const BACKEND_PREFIXES = ['/auth', '/manga', '/collections', '/health']

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
