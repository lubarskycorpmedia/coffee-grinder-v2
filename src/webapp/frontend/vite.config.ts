import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: '/news/',
  server: {
    host: '0.0.0.0',
    port: 3005,
    hmr: true,
    watch: {
      usePolling: true
    },
    allowedHosts: ['b2bc.tech', 'localhost', '127.0.0.1']
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
}) 