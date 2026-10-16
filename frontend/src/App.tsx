import { useState } from 'react'
import { api } from './api'

type Health = { status: string }

export default function App() {
  const [result, setResult] = useState<string>('(not called yet)')

  async function pingBackend() {
    try {
      const response = await api.get<Health>('/health')
      setResult(`success: ${JSON.stringify(response.data)}`)
    } catch (error) {
      setResult(`failed: ${error instanceof Error ? error.message : String(error)}`)
    }
  }

  return (
    <main style={{ fontFamily: 'sans-serif', padding: '2rem', maxWidth: 640 }}>
      <h1>Fake Academy</h1>
      <p>Frontend container is running (Vite dev server, no nginx yet).</p>
      <button onClick={pingBackend}>GET /health</button>
      <pre style={{ background: '#f5f5f5', padding: '1rem' }}>{result}</pre>
    </main>
  )
}
