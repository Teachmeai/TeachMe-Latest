'use client'

import { useEffect, useRef, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { backend } from '../../lib/backend'
import { useAuth } from '../../hooks/useAuth'
import { Button } from '../../components/ui/button'
import { supabase } from '../../lib/supabase'

export default function InvitesPage() {
  const search = useSearchParams()
  const router = useRouter()
  const inviteId = search.get('invite_id') || ''
  const { user, refreshSession } = useAuth()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [invite, setInvite] = useState<any | null>(null)
  const [accepting, setAccepting] = useState(false)
  const [accepted, setAccepted] = useState(false)
  const attemptedAutoRef = useRef(false)

  useEffect(() => {
    const load = async () => {
      if (!inviteId) {
        setError('Missing invite_id')
        setLoading(false)
        return
      }
      console.log('InvitesPage: loading invite', { inviteId })
      const resp = await backend.getInvite(inviteId)
      if (!resp.ok || !resp.data) {
        console.error('InvitesPage: getInvite failed', resp.error)
        setError('Invite not found')
        setLoading(false)
        return
      }
      const inv = (resp.data as any).invite || resp.data
      console.log('InvitesPage: invite loaded', inv)
      setInvite(inv)
      setLoading(false)
    }
    load()
  }, [inviteId])

  // Auto-accept when user returns signed-in and invite is pending
  useEffect(() => {
    const autoAccept = async () => {
      if (attemptedAutoRef.current) return
      if (!user || !invite || accepted) return
      if (invite.status && invite.status !== 'pending') return
      attemptedAutoRef.current = true
      console.log('InvitesPage: auto-accepting invite after login', { inviteId })
      try {
        const resp = await backend.acceptInviteById(inviteId)
        if (resp.ok) {
          console.log('InvitesPage: auto-accept success', resp.data)
          setAccepted(true)
          await refreshSession(true)
        } else {
          console.error('InvitesPage: auto-accept failed', resp.error)
          setError('Failed to accept invite')
        }
      } catch (e) {
        console.error('InvitesPage: auto-accept threw', e)
        setError('Failed to accept invite')
      }
    }
    autoAccept()
  }, [user, invite, inviteId, accepted, refreshSession])

  const handleAccept = async () => {
    if (!invite) return
    if (!user) {
      // Trigger Supabase OAuth login and return here automatically
      const next = encodeURIComponent(`/invites?invite_id=${inviteId}`)
      const redirectTo = `${window.location.origin}/auth/callback?next=${next}`
      console.log('InvitesPage: triggering OAuth sign-in', { redirectTo })
      await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: { redirectTo }
      })
      return
    }
    setAccepting(true)
    setError(null)
    console.log('Accepting invite via backend.acceptInviteById', { inviteId })
    const resp = await backend.acceptInviteById(inviteId)
    const ok = resp.ok
    setAccepting(false)
    if (ok) {
      console.log('Invite accepted successfully', resp.data)
      setAccepted(true)
      await refreshSession(true)
    } else {
      console.error('Accept invite failed', resp.error)
      setError('Failed to accept invite')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div>Loading invite…</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-600">{error}</div>
      </div>
    )
  }

  if (!invite) return null

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-lg w-full space-y-4">
        <h1 className="text-2xl font-semibold">Organization Invitation</h1>
        <div className="text-sm text-muted-foreground">
          You are invited to join organization: <span className="font-medium">{invite.org_id}</span>
        </div>
        <div className="text-sm">Role: <span className="font-medium">{invite.role}</span></div>
        {accepted ? (
          <div className="text-green-600">Invitation accepted. You can now switch to this organization role.</div>
        ) : (
          <div className="flex gap-3">
            <Button disabled={accepting} onClick={handleAccept}>
              {accepting ? 'Accepting…' : 'Accept Invitation'}
            </Button>
          </div>
        )}
        {!!error && (
          <div className="text-sm text-red-600">{error}</div>
        )}
      </div>
    </div>
  )
}


