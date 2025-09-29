'use client'

import { useState, useEffect } from "react"
import { LoginPage } from "@/components/features/login-page"
import { ChatDashboard } from "@/components/layout/chat-dashboard"
import { useToast } from "@/hooks/use-toast"
import { useAuth } from "../hooks/useAuth"

import type { UserProfile } from "@/types"

export default function HomePage() {
  const { user, session, loading, logout, switchRole, refreshSession } = useAuth()
  const [isHydrated, setIsHydrated] = useState(false)
  const { toast } = useToast()
  const [sessionGrace, setSessionGrace] = useState(false)

  // Simple hydration check
  useEffect(() => {
    setIsHydrated(true)
  }, [])

  // Brief grace window after user becomes available to avoid flashing the
  // "Session Setup Required" fallback while /auth/me runs in background
  useEffect(() => {
    if (user && !session) {
      setSessionGrace(true)
      const t = setTimeout(() => setSessionGrace(false), 1500)
      return () => clearTimeout(t)
    } else {
      setSessionGrace(false)
    }
  }, [user, session])

  // Convert backend session to frontend user profile
  const userProfile: UserProfile | null = user && session ? {
    name: user.user_metadata?.full_name || user.email?.split('@')[0] || "",
    email: user.email || "",
    role: session.active_role || "",
    avatar: user.user_metadata?.avatar_url,
    institute: session.roles.find(r => r.scope === 'org' && r.role === session.active_role)?.org_name || "",
    phoneNumber: "",
    socialMedia: {},
    roleData: {},
    isProfileComplete: session.active_role !== "",
    profileCompletionPercentage: session.active_role ? 100 : 0
  } : null

  const handleProfileUpdate = (_profile: UserProfile) => {
    toast({
      title: "Profile Updated",
      description: "Your profile has been updated successfully.",
    })
  }

  const handleLogout = async () => {
    try {
      await logout()
      toast({
        title: "Logged Out",
        description: "You have been successfully logged out.",
      })
    } catch (error) {
      console.error('Logout error:', error)
      toast({
        title: "Logout Error",
        description: "There was an issue logging out. Please try again.",
        variant: "destructive"
      })
    }
  }

  const handleChatMessage = () => {
    // Handle chat message - integrate with backend API
    toast({
      title: "Message Sent",
      description: "Your message has been sent to TeachMe AI.",
    })
  }

  // Show loading only during hydration or initial auth loading BEFORE user exists
  if (!isHydrated || (loading && !user)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto mb-4 flex items-center justify-center">
            <div className="w-8 h-8 bg-primary/20 rounded animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Loading...</h1>
          <p className="text-muted-foreground">Please wait while we prepare your experience</p>
        </div>
      </div>
    )
  }

  // Login State
  if (!user) {
    return <LoginPage onLogin={() => {}} />
  }

  // Loading state while fetching backend session
  if (user && !session && (loading || sessionGrace)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <div className="w-16 h-16 bg-primary/10 rounded-full mx-auto mb-4 flex items-center justify-center">
            <div className="w-8 h-8 bg-primary/20 rounded animate-pulse" />
          </div>
          <h1 className="text-2xl font-bold mb-2">Setting up your session...</h1>
          <p className="text-muted-foreground">Please wait while we prepare your experience</p>
        </div>
      </div>
    )
  }

  // Dashboard State - ChatGPT/Grok Style
  if (userProfile) {
    return (
      <ChatDashboard 
        user={userProfile} 
        onLogout={handleLogout}
        onSendMessage={handleChatMessage}
        onProfileUpdate={handleProfileUpdate}
        session={session}
        onSwitchRole={switchRole}
        onRefreshSession={refreshSession}
      />
    )
  }

  // No explicit fallback; background retries will continue until session arrives
  return null
}