/// <reference types="vite/client" />

// Vite exposes ONLY variables prefixed with VITE_ to the browser via
// import.meta.env (defined in frontend/.env). This augmentation adds
// typing + IntelliSense for ours. Everything in the ROOT .env
// (JWT_SECRET, DB passwords, S3 keys...) stays server-side by design.
interface ImportMetaEnv {
  /** Base URL the browser uses to reach the FastAPI backend. */
  readonly VITE_FASTAPI_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
