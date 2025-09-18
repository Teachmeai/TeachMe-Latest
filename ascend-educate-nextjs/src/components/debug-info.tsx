'use client'

import { useEffect, useRef } from 'react'
import type { User } from '@supabase/supabase-js'
import type { UserSession } from '../lib/backend'
import { useNotifications } from '../hooks/useNotifications'
import { addTestNotification } from '../app/components/notification-bell'

type DebugInfoProps = {
  auth: {
    user: User | null
    session: UserSession | null
    logout: () => Promise<void>
  }
}

export function DebugInfo({ auth }: DebugInfoProps) {
  const renderCount = useRef(0)
  const apiCallCount = useRef(0)
  const { logout, user, session } = auth
  const { addNotification } = useNotifications()

  useEffect(() => {
    renderCount.current += 1
    console.log(`🔄 Component rendered ${renderCount.current} times`)
  })

  useEffect(() => {
    const originalFetch = window.fetch
    window.fetch = function(...args) {
      apiCallCount.current += 1
      console.log(`🌐 API call #${apiCallCount.current}:`, args[0])
      return originalFetch.apply(this, args)
    }

    return () => {
      window.fetch = originalFetch
    }
  }, [])

  const testLogout = async () => {
    console.log('🧪 Manual logout test triggered')
    await logout()
  }

  const testNotification = () => {
    console.log('🔔 Adding test notification')
    addTestNotification(addNotification)
  }

  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 bg-black/80 text-white p-2 rounded text-xs z-50 space-y-1">
      <div>Renders: {renderCount.current}</div>
      <div>API Calls: {apiCallCount.current}</div>
      <div>User: {user ? 'Logged in' : 'Not logged in'}</div>
      <div>Session: {session ? 'Active' : 'None'}</div>
      {user && (
        <div className="space-y-1">
          <button 
            onClick={testNotification}
            className="bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-xs block w-full"
          >
            Test Notification
          </button>
          <button 
            onClick={testLogout}
            className="bg-red-600 hover:bg-red-700 px-2 py-1 rounded text-xs block w-full"
          >
            Test Logout
          </button>
        </div>
      )}
    </div>
  )
}
