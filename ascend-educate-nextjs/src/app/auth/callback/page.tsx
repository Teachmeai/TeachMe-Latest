'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '../../../lib/supabase'

export default function AuthCallback() {
  const router = useRouter()

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Handle the OAuth callback
        const { data, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Auth callback error:', error)
          router.push('/?error=' + encodeURIComponent(error.message))
          return
        }

        if (data.session) {
          console.log('Auth callback success:', data.session.user.email)
          // Successfully authenticated, redirect to home
          router.push('/')
        } else {
          console.log('No session found, redirecting to login')
          // No session, redirect to home (which will show login)
          router.push('/')
        }
      } catch (error) {
        console.error('Unexpected error:', error)
        router.push('/?error=unexpected_error')
      }
    }

    // Small delay to ensure auth state is properly set
    const timer = setTimeout(handleAuthCallback, 100)
    return () => clearTimeout(timer)
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center">
        <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto mb-4 flex items-center justify-center">
          <div className="w-8 h-8 bg-primary/20 rounded animate-pulse" />
        </div>
        <h2 className="text-2xl font-bold mb-2">Completing sign in...</h2>
        <p className="text-muted-foreground">Please wait while we redirect you.</p>
      </div>
    </div>
  )
}
