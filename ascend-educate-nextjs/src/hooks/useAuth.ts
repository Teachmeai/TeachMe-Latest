import { useState, useEffect, useRef } from 'react'
import { User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { backend, UserSession } from '../lib/backend'

export interface AuthUser {
  user: User | null
  session: UserSession | null
  loading: boolean
  deviceId: string
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<UserSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [deviceId] = useState(() => `device-${Math.random().toString(36).substr(2, 9)}`)
  const [isLoggingOut, setIsLoggingOut] = useState(false)
  const [sessionRefreshTimer, setSessionRefreshTimer] = useState<NodeJS.Timeout | null>(null)
  const lastSignedInAtRef = useRef(0)
  const lastAccessTokenRef = useRef<string | null>(null)
  const isFetchingRef = useRef(false)
  const listenerAttachedRef = useRef(false)
  const initialFetchDoneRef = useRef(false)

  useEffect(() => {
    if (listenerAttachedRef.current) {
      return
    }
    listenerAttachedRef.current = true
    let mounted = true

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!mounted) return
      console.log('Initial session:', session?.user?.email, session?.access_token ? 'JWT present' : 'No JWT')
      setUser(session?.user ?? null)
      if (session?.user) {
        // Do an initial bootstrap fetch once
        if (!initialFetchDoneRef.current) {
          initialFetchDoneRef.current = true
          fetchUserSession()
          // Track the token used for bootstrap to dedup subsequent SIGNED_IN
          lastAccessTokenRef.current = session.access_token ?? null
          lastSignedInAtRef.current = Date.now()
        }
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (!mounted) return
        console.log('Auth state change:', event, session?.user?.email, session?.access_token ? 'JWT present' : 'No JWT')
        
        if (event === 'SIGNED_OUT') {
          console.log('User signed out, clearing state')
          setUser(null)
          setSession(null)
          setLoading(false)
          setIsLoggingOut(false)
        } else if ((event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED') && session?.user) {
          if (event === 'SIGNED_IN') {
            const token = session?.access_token || null
            // Dedup if same token as last processed
            if (token && lastAccessTokenRef.current === token) {
              console.log('Dedup SIGNED_IN by token - skipping duplicate event')
              return
            }
            lastAccessTokenRef.current = token
            const now = Date.now()
            // Extend window to 5 seconds to avoid rapid duplicates
            if (now - lastSignedInAtRef.current < 5000) {
              console.log('Dedup SIGNED_IN by time window - skipping duplicate event')
              return
            }
            lastSignedInAtRef.current = now
          }
          console.log('User signed in or token refreshed, updating state')
          setUser(session.user)
          if (event === 'SIGNED_IN') {
            // Avoid refetch if initial bootstrap just did it
            if (!initialFetchDoneRef.current) {
              initialFetchDoneRef.current = true
              setLoading(true)
              await fetchUserSession()
            } else {
              console.log('Skipping fetchUserSession on SIGNED_IN - already bootstrapped')
            }
          } else {
            console.log('Token refreshed, keeping existing session')
          }
        } else if (event === 'PASSWORD_RECOVERY') {
          console.log('Password recovery event')
        } else {
          console.log('Unhandled auth event:', event)
        }
      }
    )

    return () => {
      mounted = false
      subscription.unsubscribe()
      // Clear session refresh timer on unmount
      if (sessionRefreshTimer) {
        clearTimeout(sessionRefreshTimer)
      }
    }
  }, [])

  const setupSessionRefresh = (sessionData: UserSession) => {
    // Clear existing timer
    if (sessionRefreshTimer) {
      clearTimeout(sessionRefreshTimer)
    }

    if (sessionData.exp) {
      const now = Math.floor(Date.now() / 1000)
      const timeUntilExpiry = sessionData.exp - now
      
      console.log(`Session expires in ${timeUntilExpiry} seconds`)
      
      if (timeUntilExpiry > 0) {
        // Set timer to refresh session 2 minutes before expiry
        const refreshTime = Math.max((timeUntilExpiry - 120) * 1000, 30000) // At least 30 seconds
        
        const timer = setTimeout(() => {
          if (user && !isLoggingOut) {
            console.log('Auto-refreshing session before expiry')
            fetchUserSession()
          }
        }, refreshTime)
        
        setSessionRefreshTimer(timer)
        console.log(`Session will auto-refresh in ${refreshTime / 1000} seconds`)
      }
    }
  }

  const fetchUserSession = async () => {
    if (isLoggingOut) {
      console.log('Skipping session fetch - logout in progress')
      return
    }
    if (isFetchingRef.current) {
      console.log('Session fetch already in progress, skipping')
      return
    }
    isFetchingRef.current = true

    try {
      setLoading(true)
      console.log('Fetching user session...')
      // Ensure JWT is available; if not, wait briefly and retry once
      const current = (await supabase.auth.getSession()).data.session
      if (!current?.access_token) {
        await new Promise(res => setTimeout(res, 200))
      }
      const response = await backend.getMe(deviceId)
      if (response.ok && response.data) {
        const sessionData = response.data
        setSession(sessionData)
        setupSessionRefresh(sessionData)
        console.log('Session fetched successfully')
      } else {
        console.error('Failed to fetch session:', response.error)
        setSession(null)
        // Clear refresh timer on session failure
        if (sessionRefreshTimer) {
          clearTimeout(sessionRefreshTimer)
          setSessionRefreshTimer(null)
        }
      }
    } catch (error) {
      console.error('Error fetching session:', error)
      setSession(null)
      // Clear refresh timer on error
      if (sessionRefreshTimer) {
        clearTimeout(sessionRefreshTimer)
        setSessionRefreshTimer(null)
      }
    } finally {
      setLoading(false)
      isFetchingRef.current = false
    }
  }

  const switchRole = async (role: string, orgId?: string) => {
    const response = await backend.switchRole(role, orgId)
    if (response.ok) {
      await fetchUserSession() // Refresh session
      return true
    } else {
      console.error('Error switching role:', response.error)
      return false
    }
  }

  const logout = async () => {
    if (isLoggingOut) {
      console.log('Logout already in progress, skipping...')
      return
    }

    try {
      setIsLoggingOut(true)
      console.log('Starting logout process...')
      
      // Store user ID before clearing state
      const currentUserId = user?.id
      console.log('Current user ID for logout:', currentUserId)
      
      // Clear session refresh timer
      if (sessionRefreshTimer) {
        clearTimeout(sessionRefreshTimer)
        setSessionRefreshTimer(null)
      }
      
      // Try to call backend logout to clear session (may fail if JWT expired)
      try {
        console.log('Attempting backend logout...')
        const backendResponse = await backend.logout(deviceId)
        console.log('Backend logout response:', backendResponse)
      } catch (backendError) {
        console.log('Backend logout failed (likely JWT expired):', backendError)
        // Try force logout if we have user ID
        if (currentUserId) {
          try {
            console.log('Attempting force logout for user:', currentUserId)
            const forceLogoutResponse = await backend.forceLogout(currentUserId, deviceId)
            console.log('Force logout response:', forceLogoutResponse)
          } catch (forceLogoutError) {
            console.log('Force logout also failed:', forceLogoutError)
          }
        }
      }
      
      // Sign out from Supabase
      console.log('Signing out from Supabase...')
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('Supabase logout error:', error)
      } else {
        console.log('Supabase logout successful')
      }
      
      // Clear local state after backend operations
      setUser(null)
      setSession(null)
      setLoading(false)
      
      console.log('Logout completed successfully')
    } catch (error) {
      console.error('Logout error:', error)
      // Clear state even on error
      setUser(null)
      setSession(null)
      setLoading(false)
    } finally {
      setIsLoggingOut(false)
    }
  }

  return {
    user,
    session,
    loading,
    deviceId,
    switchRole,
    logout,
    refreshSession: fetchUserSession
  }
}
