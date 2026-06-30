import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/napcore-helpdesk/',
  server: {
    port: 5173,
    fs: {
      allow: ['..'],
    },
  },
})
