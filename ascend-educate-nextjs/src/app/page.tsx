'use client'

import * as React from "react"
import { LoginPage } from "@/components/login-page"
import { ChatDashboard } from "@/components/chat-dashboard"
import { useToast } from "@/hooks/use-toast"
import { useHydration } from "@/hooks/use-hydration"
import { useAuth } from "../hooks/useAuth"
import { DebugInfo } from "../components/debug-info"

interface UserProfile {
  name: string
  email: string
  role: string
  avatar?: string
  institute?: string
  phoneNumber?: string
  socialMedia?: {
    linkedin?: string
    twitter?: string
    github?: string
    website?: string
  }
  roleData?: Record<string, string>
  isProfileComplete?: boolean
  profileCompletionPercentage?: number
}

export default function HomePage() {
  const { user, session, loading, logout } = useAuth()
  const isHydrated = useHydration()
  const { toast } = useToast()

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

  const handleProfileUpdate = (profile: UserProfile) => {
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

  // Show loading state during hydration or auth loading
  if (!isHydrated || loading) {
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
    return (
      <>
        <LoginPage onLogin={() => {}} />
        <DebugInfo auth={{ user, session, logout }} />
      </>
    )
  }

  // Loading state while fetching backend session
  if (user && !session && loading) {
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
      <>
        <ChatDashboard 
          user={userProfile} 
          onLogout={handleLogout}
          onSendMessage={handleChatMessage}
          onProfileUpdate={handleProfileUpdate}
        />
        <DebugInfo auth={{ user, session, logout }} />
      </>
    )
  }

  // Fallback: User is authenticated but no backend session
  if (user && !session && !loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center max-w-md">
          <div className="w-20 h-20 bg-gradient-to-br from-orange-500 to-red-500 rounded-full mx-auto mb-6 flex items-center justify-center shadow-glow">
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
              <span className="text-orange-500 font-bold">!</span>
            </div>
          </div>
          <h2 className="text-2xl font-bold mb-4">Session Setup Required</h2>
          <p className="text-muted-foreground mb-6">
            We need to set up your session. Please try refreshing the page or logging out and back in.
          </p>
          <div className="space-y-3">
            <button 
              onClick={() => window.location.reload()}
              className="w-full bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg"
            >
              Refresh Page
            </button>
            <button 
              onClick={handleLogout}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 px-4 py-2 rounded-lg"
            >
              Logout & Try Again
            </button>
          </div>
        </div>
        <DebugInfo auth={{ user, session, logout }} />
      </div>
    )
  }

  return <DebugInfo auth={{ user, session, logout }} />
}