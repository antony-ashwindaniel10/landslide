import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const API_TARGET = 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 43123,
    strictPort: true,
    allowedHosts: true,
    proxy: {
      '^/(predict-at|risk|elevation|place-name|rainfall|forecast-rainfall|forecast-risk|soil-wetness|heatmap|decision|reports|alerts|health|auth)': {
        target: API_TARGET,
        changeOrigin: true,
      },
    },
  },
})
