// Entry point: mount the React app into the #root div from index.html.
//
// Providers wrap <App/> so every component below can use them:
//   StrictMode          — double-invokes effects in dev to surface bugs
//   QueryClientProvider — TanStack Query: fetching/caching server data
//                         (ready to use, not consumed anywhere yet)
//   BrowserRouter       — client-side routing: URL ↔ component mapping
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import App from './App'

// The bundler handles CSS imports at runtime; TypeScript has no declaration for this file.
// @ts-expect-error CSS side-effect import
import './styles/global.css'

// One client for the whole app, created ONCE outside the component
// (a new client per render would wipe the cache every navigation).
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000, // data considered fresh for 30s -> fewer refetches
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
