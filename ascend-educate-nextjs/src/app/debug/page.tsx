'use client'

import { useState, useEffect } from 'react'
import { supabase } from '../../lib/supabase'
import { backend } from '../../lib/backend'

type AuthState = {
  hasSession: boolean
  user?: string
  hasJWT: boolean
  jwtLength?: number
} | null

type BackendTest = {
  success: boolean
  error?: string
  data?: unknown
} | null

export default function DebugPage() {
  const [authState, setAuthState] = useState<AuthState>(null)
  const [backendTest, setBackendTest] = useState<BackendTest>(null)

  useEffect(() => {
    // Check auth state
    supabase.auth.getSession().then(({ data: { session } }) => {
      setAuthState({
        hasSession: !!session,
        user: session?.user?.email,
        hasJWT: !!session?.access_token,
        jwtLength: session?.access_token?.length
      })
    })

    // Test backend health first
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => {
        console.log('Health check:', data)
        // Then test auth endpoint
        return backend.getMe('test-device')
      })
      .then((response) => {
        setBackendTest({
          success: response.ok,
          error: response.error,
          data: response.data
        })
      })
      .catch(error => {
        setBackendTest({
          success: false,
          error: error.message,
          data: null
        })
      })
  }, [])

  const testBackend = async () => {
    const response = await backend.getMe('test-device')
    setBackendTest({
      success: response.ok,
      error: response.error,
      data: response.data
    })
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Debug Information</h1>
      
      <div className="space-y-6">
        <div className="border p-4 rounded">
          <h2 className="text-lg font-semibold mb-2">Auth State</h2>
          <pre className="bg-gray-100 p-2 rounded text-sm">
            {JSON.stringify(authState, null, 2)}
          </pre>
        </div>

        <div className="border p-4 rounded">
          <h2 className="text-lg font-semibold mb-2">Backend Test</h2>
          <button 
            onClick={testBackend}
            className="bg-blue-500 text-white px-4 py-2 rounded mb-2"
          >
            Test Backend Connection
          </button>
          <pre className="bg-gray-100 p-2 rounded text-sm">
            {JSON.stringify(backendTest, null, 2)}
          </pre>
        </div>

        <div className="border p-4 rounded">
          <h2 className="text-lg font-semibold mb-2">Environment</h2>
          <pre className="bg-gray-100 p-2 rounded text-sm">
            {JSON.stringify({
              supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL,
              backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL
            }, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  )
}
