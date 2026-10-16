import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite's job: serve src/ to the browser, transform TSX on the fly,
// and hot-reload (HMR) on every save.
export default defineConfig({
  // The React plugin enables the JSX transform + Fast Refresh
  // (swap a component's code without losing its state).
  plugins: [react()],
  server: {
    // host: true = listen on ALL network interfaces, not just
    // 127.0.0.1. REQUIRED inside Docker
    host: true,
    port: 5173,
    // fail loudly if 5173 is taken
    strictPort: true,
  },
})
