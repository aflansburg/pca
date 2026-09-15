import vue from '@vitejs/plugin-vue'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [vue()],
  // Relative asset paths so FastAPI can serve the build from any base.
  base: './',
  server: {
    // Dev: proxy API calls to the FastAPI backend.
    proxy: { '/api': 'http://127.0.0.1:8000' },
    allowedHosts: true
  },
  build: { outDir: 'dist' },
})
