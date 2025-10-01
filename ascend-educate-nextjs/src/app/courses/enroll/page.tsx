'use client'

import { useEffect, useRef, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useAuth } from '../../../hooks/useAuth'
import { backend } from '../../../lib/backend'
import { Button } from '../../../components/ui/button'
import { supabase } from '../../../lib/supabase'

export default function CourseEnrollPage() {
  const search = useSearchParams()
  const router = useRouter()
  const token = search.get('token') || ''
  const { user, refreshSession } = useAuth()
  const [status, setStatus] = useState<'idle' | 'enrolling' | 'success' | 'already' | 'error'>('idle')
  const [error, setError] = useState<string | null>(null)
  const signInStartedRef = useRef(false)
  const enrollStartedRef = useRef(false)

  useEffect(() => {
    const run = async () => {
      if (!token) {
        setError('Missing token')
        return
      }
      // Trigger sign-in only once
      if (!user) {
        if (signInStartedRef.current) return
        signInStartedRef.current = true
        const next = encodeURIComponent(`/courses/enroll?token=${token}`)
        const redirectTo = `${window.location.origin}/auth/callback?next=${next}`
        await supabase.auth.signInWithOAuth({ provider: 'google', options: { redirectTo } })
        return
      }
      // Enroll only once
      if (enrollStartedRef.current || status !== 'idle') return
      enrollStartedRef.current = true
      setStatus('enrolling')
      const resp = await backend.enrollByToken(token)
      if (resp.ok && resp.data) {
        if ((resp.data as any).already) {
          setStatus('already')
        } else {
          setStatus('success')
        }
        // refresh session in background; do not re-trigger enroll because of refs
        await refreshSession(true)
      } else {
        setStatus('error')
        setError(resp.error || 'Enrollment failed')
      }
    }
    run()
  }, [token, user, status, refreshSession])

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-lg w-full space-y-4 text-center">
        {status === 'idle' && <div>Preparing enrollment…</div>}
        {status === 'enrolling' && <div>Enrolling you in the course…</div>}
        {status === 'success' && <div className="text-green-600">You have been enrolled successfully.</div>}
        {status === 'already' && <div className="text-blue-600">You are already enrolled in this course.</div>}
        {status === 'error' && <div className="text-red-600">{error}</div>}
        <div>
          <Button onClick={() => router.push('/')}>Go to Home</Button>
        </div>
      </div>
    </div>
  )
}


