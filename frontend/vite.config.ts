// Vite's job: serve src/ to the browser, transform TSX on the fly,
// and hot-reload (HMR) on every save.
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

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
    watch: {
      // Docker on Windows: ./frontend reaches the container through a
      // FUSE-style file share that does NOT emit inotify events — Vite
      // hears nothing when files change and HMR silently dies (verified:
      // even edits made inside the container produced no watcher events).
      // Polling (reading mtimes directly) works through the share.
      // node_modules/.git stay excluded (Vite defaults) -> low CPU cost.
      usePolling: true,
    },
  },
})
