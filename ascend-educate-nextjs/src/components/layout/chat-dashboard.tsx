"use client"

import { useState, useEffect, useRef } from "react"
import { 
  MessageSquare, 
  Plus, 
  LogOut, 
  User,
  Edit,
  Trash2,
  Search,
  Camera,
  PanelLeftClose,
  PanelLeft,
  Menu
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Logo } from "@/components/ui/logo"
import { ThemeToggle } from "@/components/features/theme-toggle"
import { NotificationBell } from "@/components/features/notification-bell"
import dynamic from 'next/dynamic'

// Code splitting for heavy components
const ChatInterface = dynamic(() => import("@/components/features/chat-interface").then(mod => ({ default: mod.ChatInterface })), {
  loading: () => (
    <div className="flex items-center justify-center h-32">
      <div className="loading-spinner w-6 h-6"></div>
    </div>
  )
})

const ProfileManagement = dynamic(() => import("@/components/features/profile-management").then(mod => ({ default: mod.ProfileManagement })), {
  loading: () => (
    <div className="flex items-center justify-center h-32">
      <div className="loading-spinner w-6 h-6"></div>
    </div>
  )
})
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
// Removed ResizablePanelGroup imports as we're using a mobile-first approach
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
// removed quick role switcher; role management happens inside Profile
import type { UserSession, BackendProfile, Assistant, AssistantMessage } from "../../lib/backend"
import { backend } from "../../lib/backend"

import type { UserProfile, ChatMessage } from "@/types"


interface ChatSession {
  id: string
  title: string
  lastMessage: string
  timestamp: string // ISO string for serialization
}


interface ChatDashboardProps {
  user: UserProfile
  onLogout: () => void
  onSendMessage?: () => void
  onProfileUpdate?: (profile: UserProfile) => void
  session: UserSession | null
  onSwitchRole: (role: string, orgId?: string) => Promise<boolean>
  onRefreshSession?: () => Promise<void>
}

export function ChatDashboard({ user, onLogout, onSendMessage, onProfileUpdate, session, onSwitchRole, onRefreshSession }: ChatDashboardProps) {
  // Professional sidebar width constraints
  const SIDEBAR_MIN_WIDTH = 319 // Minimum width for usability
  const SIDEBAR_MAX_WIDTH = 520 // Maximum width to prevent it being too wide
  const SIDEBAR_DEFAULT_WIDTH = 320 // Default comfortable width
  
  const [isMobile, setIsMobile] = useState(false)

  // Simple mobile detection
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768)
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile) // Default to closed on mobile
  const [sidebarAnimating, setSidebarAnimating] = useState(false)
  const [sidebarWidth, setSidebarWidth] = useState<number>(SIDEBAR_DEFAULT_WIDTH)
  const isResizingRef = useRef(false)
  const [isAtMinWidth, setIsAtMinWidth] = useState(false)
  const [isAtMaxWidth, setIsAtMaxWidth] = useState(false)
  const [activeChat, setActiveChat] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState("")
  const [userProfile, setUserProfile] = useState<UserProfile>(user)
  const [profileDialogOpen, setProfileDialogOpen] = useState(false)
  
  const [showProfileManagement, setShowProfileManagement] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  // Session and role switching are provided by parent to avoid double auth hooks

  // Bootstrap profile from backend and gate chat until complete
  useEffect(() => {
    let mounted = true
    const loadProfile = async () => {
      const resp = await backend.getProfile()
      if (!mounted || !resp.ok || !resp.data) return
      const p = resp.data as BackendProfile
      setUserProfile(prev => ({
        ...prev,
        name: p.full_name || prev.name,
        avatar: p.avatar_url || prev.avatar,
        phoneNumber: p.phone || prev.phoneNumber,
        socialMedia: {
          ...(prev.socialMedia || {}),
          linkedin: p.linkedin_url || prev.socialMedia?.linkedin,
          twitter: p.twitter_url || prev.socialMedia?.twitter,
          github: p.github_url || prev.socialMedia?.github,
          website: p.website || prev.socialMedia?.website,
        },
        isProfileComplete: (p.profile_completion_percentage ?? 0) >= 100,
        profileCompletionPercentage: p.profile_completion_percentage ?? prev.profileCompletionPercentage,
      }))
      if ((p.profile_completion_percentage ?? 0) < 100) {
        setShowProfileManagement(true)
      }
    }
    loadProfile()
    return () => { mounted = false }
  }, [])

  // Update sidebar state when mobile state changes
  useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false)
    } else {
      setSidebarOpen(true)
    }
  }, [isMobile])

  // Fetch assistants from backend
  useEffect(() => {
    let mounted = true
    const loadAssistants = async () => {
      setLoadingAssistants(true)
      try {
        const resp = await backend.getAssistants()
        if (!mounted || !resp.ok || !resp.data) {
          console.error('Failed to load assistants:', resp.error)
          return
        }
        console.log('Loaded assistants:', resp.data.assistants)
        setAssistants(resp.data.assistants)
      } catch (error) {
        console.error('Error loading assistants:', error)
      } finally {
        if (mounted) {
          setLoadingAssistants(false)
        }
      }
    }
    
    if (session?.active_role) {
      loadAssistants()
    }
    
    return () => { mounted = false }
  }, [session?.active_role, session?.active_org_id])

  // Professional sidebar resize handlers with boundary feedback
  const onResizeMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isMobile) return
    e.preventDefault()
    isResizingRef.current = true
    const startX = e.clientX
    const startWidth = sidebarWidth
    
    const onMove = (ev: MouseEvent) => {
      if (!isResizingRef.current) return
      
      const delta = ev.clientX - startX
      let newWidth = startWidth + delta
      
      // Apply constraints with smooth clamping
      newWidth = Math.min(Math.max(newWidth, SIDEBAR_MIN_WIDTH), SIDEBAR_MAX_WIDTH)
      
      // Update boundary states for visual feedback
      setIsAtMinWidth(newWidth <= SIDEBAR_MIN_WIDTH)
      setIsAtMaxWidth(newWidth >= SIDEBAR_MAX_WIDTH)
      
      setSidebarWidth(newWidth)
    }
    
    const onUp = () => {
      isResizingRef.current = false
      
      // Reset boundary states after a delay for visual feedback
      setTimeout(() => {
        setIsAtMinWidth(false)
        setIsAtMaxWidth(false)
      }, 200)
      
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }
  
  // Real assistants from OpenAI
  const [assistants, setAssistants] = useState<Assistant[]>([])
  const [activeAssistant, setActiveAssistant] = useState<Assistant | null>(null)
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const [loadingAssistants, setLoadingAssistants] = useState(false)
  
  // Keep chatSessions for backward compatibility (optional, can be removed later)
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([])

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map(n => n[0])
      .join("")
      .toUpperCase()
  }

  const handleAssistantClick = async (assistant: Assistant) => {
    console.log('Assistant clicked:', assistant.name)
    setActiveAssistant(assistant)
    setActiveChat(assistant.id)
    
    // Close sidebar on mobile after selection
    if (isMobile) {
      setSidebarOpen(false)
    }
    
    try {
      // 1. Check if thread exists for this assistant
      let threadId = activeThreadId
      if (!threadId || activeAssistant?.id !== assistant.id) {
        // Create or get thread
        const resp = await backend.createThread(assistant.id)
        if (resp.ok && resp.data) {
          threadId = resp.data.thread_id
          setActiveThreadId(threadId)
          console.log('Thread created/retrieved:', threadId)
        } else {
          console.error('Failed to create thread:', resp.error)
          return
        }
      }
      
      // 2. Load existing messages
      if (threadId) {
        const messagesResp = await backend.getMessages(threadId)
        if (messagesResp.ok && messagesResp.data) {
          const messages: ChatMessage[] = messagesResp.data.messages.map(msg => ({
            id: msg.id,
            role: msg.role,
            content: msg.content,
            created_at: msg.created_at
          }))
          setChatMessages(messages)
          console.log('Loaded messages:', messages.length)
        }
      }
    } catch (error) {
      console.error('Error handling assistant click:', error)
    }
  }
  
  const handleNewChat = () => {
    // Clear current chat to start fresh
    setActiveAssistant(null)
    setActiveThreadId(null)
    setChatMessages([])
    setActiveChat(null)
  }

  const handleDeleteChat = (chatId: string) => {
    setChatSessions(prev => prev.filter(chat => chat.id !== chatId))
    if (activeChat === chatId) {
      setActiveChat(null)
    }
  }

  const filteredChats = chatSessions.filter(chat =>
    chat.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    chat.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const formatTime = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)
    
    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    return 'Just now'
  }

  const handleAvatarChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        setUserProfile(prev => ({ ...prev, avatar: result }))
      }
      reader.readAsDataURL(file)
    }
  }

  const handleProfileUpdate = async (profile: UserProfile) => {
    setUserProfile(profile)
    if (onProfileUpdate) {
      onProfileUpdate(profile)
    }
    // Refresh from backend to get latest completion percentage without full page reload
    try {
      const resp = await backend.getProfile()
      if (resp.ok && resp.data) {
        const p = resp.data as BackendProfile
        setUserProfile(prev => ({
          ...prev,
          name: p.full_name || prev.name,
          avatar: p.avatar_url || prev.avatar,
          phoneNumber: p.phone || prev.phoneNumber,
          socialMedia: {
            ...(prev.socialMedia || {}),
            linkedin: p.linkedin_url || prev.socialMedia?.linkedin,
            twitter: p.twitter_url || prev.socialMedia?.twitter,
            github: p.github_url || prev.socialMedia?.github,
            website: p.website || prev.socialMedia?.website,
          },
          isProfileComplete: (p.profile_completion_percentage ?? 0) >= 100,
          profileCompletionPercentage: p.profile_completion_percentage ?? prev.profileCompletionPercentage,
        }))
        // Close the profile modal if completion is now 100%
        if ((p.profile_completion_percentage ?? 0) >= 100) {
          setShowProfileManagement(false)
        }
      }
    } catch {}
    setProfileDialogOpen(false)
  }

  const handleRoleSwitch = async (role: string, orgId?: string) => {
    const success = await onSwitchRole(role, orgId)
    if (success && session) {
      // Update the user profile with the new role
      const updatedProfile = {
        ...userProfile,
        role: role,
        institute: session.roles.find(r => r.role === role && r.scope === 'org')?.org_name || userProfile.institute
      }
      setUserProfile(updatedProfile)
      if (onProfileUpdate) {
        onProfileUpdate(updatedProfile)
      }
    }
    return success
  }

  const handleSidebarToggle = () => {
    if (sidebarAnimating) return
    
    setSidebarAnimating(true)
    if (sidebarOpen) {
      setSidebarOpen(false)
    } else {
      setSidebarOpen(true)
    }
    
    // Reset animation state after transition
    setTimeout(() => {
      setSidebarAnimating(false)
    }, 250)
  }

  return (
    <div className="h-screen flex bg-gradient-to-br from-background via-background to-muted/20 relative overflow-hidden">
      {/* Enhanced Background Effects */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 right-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 left-1/4 w-80 h-80 bg-accent/5 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-primary/3 rounded-full blur-2xl animate-float" style={{ animationDelay: '2s' }} />
      </div>
      
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-md lg:hidden animate-fade-in"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Mobile: Fixed overlay, Desktop: Resizable panel */}
      {sidebarOpen && (
        <div
          className={cn(
            "sidebar-panel flex flex-col sidebar-transition glass-card",
            isMobile
              ? "fixed left-0 top-0 z-50 h-full w-80 transform transition-all duration-300 animate-slide-in-left"
              : "flex-shrink-0",
            sidebarAnimating ? "sidebar-slide-in" : ""
          )}
          style={!isMobile ? { width: `${sidebarWidth}px` } : undefined}
        >
          {/* Sidebar Header */}
          <div className="p-6 border-b border-border/50 bg-gradient-to-r from-card/50 to-card/30 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <Logo size="sm" className="animate-fade-in" />
              <div className="flex items-center gap-2">
                <ThemeToggle />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSidebarToggle}
                  className="hover:bg-primary/10 transition-all duration-200 hover:scale-105"
                >
                  <PanelLeftClose className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            {/* New Chat Button */}
            <Button
              onClick={handleNewChat}
              className="w-full glass-button hover-scale text-primary-foreground border-0 shadow-lg hover:shadow-xl group"
              variant="default"
            >
              <Plus className="h-4 w-4 mr-2 transition-transform duration-200 group-hover:rotate-90" />
              New Chat
            </Button>
          </div>

          {/* Search */}
          <div className="p-4 px-6 border-b border-border/50">
            <div className="relative group">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground transition-colors duration-200 group-focus-within:text-primary" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-12 pr-4 py-2.5 bg-muted/30 border border-border/20 rounded-xl focus:bg-muted/50 transition-all duration-200 focus:ring-2 focus:ring-primary/30 focus:border-primary/50"
              />
            </div>
          </div>

          {/* Assistants List */}
          <ScrollArea className="flex-1">
            <div className="p-3 space-y-1.5">
              {loadingAssistants ? (
                <div className="flex items-center justify-center py-8">
                  <div className="loading-spinner w-6 h-6"></div>
                  <span className="ml-2 text-sm text-muted-foreground">Loading assistants...</span>
                </div>
              ) : assistants.length === 0 ? (
                <div className="text-center py-8 px-4">
                  <p className="text-sm text-muted-foreground">No assistants available</p>
                  <p className="text-xs text-muted-foreground mt-2">Contact your administrator</p>
                </div>
              ) : (
                assistants.map((assistant, index) => (
                  <div
                    key={assistant.id}
                    onClick={() => handleAssistantClick(assistant)}
                    className={cn(
                      "group flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all duration-200 hover:bg-muted/60 relative overflow-hidden",
                      activeChat === assistant.id && "bg-primary/10 border border-primary/20 shadow-md"
                  )}
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className="flex-shrink-0 w-9 h-9 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors duration-200">
                    <MessageSquare className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0 pr-2">
                    <h4 className="text-sm font-medium truncate text-foreground group-hover:text-primary transition-colors duration-200">{assistant.name}</h4>
                    {assistant.description && (
                      <p className="text-xs text-muted-foreground truncate mt-0.5 leading-relaxed">
                        {assistant.description}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground/70 mt-1 font-medium">
                      {assistant.model}
                    </p>
                  </div>
                </div>
              )))}
            </div>
          </ScrollArea>

          {/* User Profile */}
          <div className="p-4 border-t border-border/50 bg-gradient-to-r from-card/30 to-card/50 shadow-inner">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start p-2.5 h-auto hover:bg-muted/50 transition-all duration-200 rounded-lg group">
                  <Avatar className="h-9 w-9 mr-3 ring-2 ring-primary/20 group-hover:ring-primary/40 transition-all duration-200">
                    <AvatarImage src={userProfile.avatar} alt={userProfile.name} />
                    <AvatarFallback className="bg-gradient-primary text-primary-foreground text-sm font-semibold">
                      {getInitials(userProfile.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium text-foreground group-hover:text-primary transition-colors duration-200">{userProfile.name}</p>
                    <p className="text-xs text-muted-foreground capitalize">{userProfile.role}</p>
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent className="w-64" align="end" forceMount>
                <DropdownMenuLabel className="font-normal">
                  <div className="flex flex-col space-y-1">
                    <p className="text-sm font-medium leading-none">{userProfile.name}</p>
                    <p className="text-xs leading-none text-muted-foreground">
                      {userProfile.email}
                    </p>
                    <p className="text-xs leading-none text-primary font-medium capitalize">
                      {userProfile.role}
                    </p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                
                <DropdownMenuItem 
                  className="cursor-pointer"
                  onClick={() => setShowProfileManagement(true)}
                >
                  <User className="mr-2 h-4 w-4" />
                  <span>Profile</span>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="cursor-pointer text-destructive focus:text-destructive"
                  onClick={onLogout}
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  <span>Log out</span>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      )}

      {/* Desktop resize handle with boundary feedback */}
      {!isMobile && sidebarOpen && (
        <div
          onMouseDown={onResizeMouseDown}
          title={
            isAtMinWidth 
              ? `Minimum width reached (${SIDEBAR_MIN_WIDTH}px)` 
              : isAtMaxWidth 
              ? `Maximum width reached (${SIDEBAR_MAX_WIDTH}px)` 
              : "Drag to resize sidebar"
          }
          style={{ cursor: 'col-resize' }}
          className={cn(
            "group relative w-3 hover:w-4 transition-all duration-200 flex items-center justify-center",
            isAtMinWidth || isAtMaxWidth
              ? "bg-gradient-to-r from-destructive/30 via-destructive/50 to-destructive/30"
              : "bg-gradient-to-r from-border/30 via-border/50 to-border/30 hover:from-primary/20 hover:via-primary/30 hover:to-primary/20"
          )}
        >
          <div className="flex flex-col gap-1 opacity-40 group-hover:opacity-100 transition-opacity duration-200">
            <div className={cn(
              "w-0.5 h-3 rounded-full transition-all duration-200",
              isAtMinWidth || isAtMaxWidth
                ? "bg-destructive"
                : "bg-muted-foreground/50 group-hover:bg-primary"
            )}></div>
            <div className={cn(
              "w-0.5 h-3 rounded-full transition-all duration-200",
              isAtMinWidth || isAtMaxWidth
                ? "bg-destructive"
                : "bg-muted-foreground/50 group-hover:bg-primary"
            )}></div>
            <div className={cn(
              "w-0.5 h-3 rounded-full transition-all duration-200",
              isAtMinWidth || isAtMaxWidth
                ? "bg-destructive"
                : "bg-muted-foreground/50 group-hover:bg-primary"
            )}></div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className={cn(
        "flex flex-col flex-1 main-content-transition relative z-10 min-h-0",
        !sidebarOpen && "main-content-expand"
      )}>
        {/* Header */}
        <div className="border-b border-border/50 bg-gradient-to-r from-card/80 to-card/60 backdrop-blur-md shadow-md">
          <div className="flex items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              {/* Mobile Menu Button */}
              {isMobile && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSidebarToggle}
                  className="hover:bg-primary/10 transition-all duration-200 hover:scale-105"
                >
                  <Menu className="h-5 w-5" />
                </Button>
              )}
              
              {/* Desktop Sidebar Toggle */}
              {!isMobile && !sidebarOpen && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSidebarToggle}
                  className="hover:bg-primary/10 transition-all duration-200 hover:scale-105"
                >
                  <PanelLeft className="h-5 w-5" />
                </Button>
              )}
              
              <h1 className="text-xl font-bold truncate bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
                {activeAssistant ? activeAssistant.name : "TeachMe AI"}
              </h1>
            </div>

            {/* Notification Bell */}
            <div className="flex items-center gap-2">
              <NotificationBell />
            </div>
          </div>
          
          {/* Profile Completion Banner */}
          {!userProfile.isProfileComplete && (
            <div className="bg-gradient-to-r from-orange-50 to-amber-50 dark:from-orange-950/30 dark:to-amber-950/30 border-t border-orange-200/50 dark:border-orange-800/50 px-6 py-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-4 min-w-0 flex-1">
                  <div className="w-3 h-3 bg-gradient-to-r from-orange-500 to-amber-500 rounded-full animate-pulse-glow flex-shrink-0" />
                  <p className="text-sm font-medium text-orange-800 dark:text-orange-200 truncate">
                    Complete your profile to start chatting with TeachMe AI
                  </p>
                </div>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => setShowProfileManagement(true)}
                  className="text-orange-800 dark:text-orange-200 border-orange-300 dark:border-orange-700 hover:bg-orange-100 dark:hover:bg-orange-900/20 flex-shrink-0 hover-scale transition-all duration-200"
                >
                  Complete Profile
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-gradient-to-br from-background via-background to-muted/10 h-screen overflow-hidden relative">
          {showProfileManagement ? (
            <ProfileManagement
              user={userProfile}
              roles={session?.roles || []}
              activeRole={userProfile.role}
              onSwitchRole={handleRoleSwitch}
              onProfileUpdate={handleProfileUpdate}
              onRefreshSession={onRefreshSession}
              onClose={() => setShowProfileManagement(false)}
            />
          ) : !userProfile.isProfileComplete ? (
            <div className="h-full flex items-center justify-center p-4 sm:p-8 relative">
              <div className="text-center max-w-lg w-full animate-fade-in">
                <div className="w-20 h-20 sm:w-24 sm:h-24 bg-gradient-primary rounded-2xl mx-auto mb-6 sm:mb-8 flex items-center justify-center shadow-xl animate-bounce-in">
                  <User className="h-10 w-10 sm:h-12 sm:w-12 text-primary-foreground" />
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
                  Complete Your Profile
                </h2>
                <p className="text-muted-foreground mb-6 sm:mb-8 text-base sm:text-lg leading-relaxed">
                  You need to complete your profile setup before you can start chatting. 
                  This helps us personalize your TeachMe experience.
                </p>
                <div className="space-y-4">
                  <Button 
                    onClick={() => setShowProfileManagement(true)}
                    className="w-full glass-button hover-scale text-primary-foreground shadow-lg hover:shadow-xl"
                    size="lg"
                  >
                    <User className="h-5 w-5 mr-2" />
                    Complete Profile Setup
                  </Button>
                  <div className="bg-muted/50 rounded-lg p-3">
                    <p className="text-sm text-muted-foreground font-medium">
                      Profile completion: {userProfile.profileCompletionPercentage || 0}%
                    </p>
                    <div className="w-full bg-muted-foreground/20 rounded-full h-2 mt-2">
                      <div 
                        className="bg-gradient-primary h-2 rounded-full transition-all duration-500"
                        style={{ width: `${userProfile.profileCompletionPercentage || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : activeAssistant && activeThreadId ? (
            <ChatInterface
              assistantId={activeAssistant.id}
              assistantName={activeAssistant.name}
              threadId={activeThreadId}
              messages={chatMessages}
              onMessagesUpdate={setChatMessages}
              placeholder={`Chat with ${activeAssistant.name}...`}
            />
          ) : (
            <div className="h-full flex items-center justify-center p-4 sm:p-8 relative">
              <div className="text-center max-w-lg w-full animate-fade-in">
                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-primary rounded-2xl mx-auto mb-6 sm:mb-8 flex items-center justify-center shadow-xl animate-float">
                  <MessageSquare className="h-8 w-8 sm:h-10 sm:w-10 text-primary-foreground" />
                </div>
                <h2 className="text-display-lg sm:text-display-xl font-bold mb-4 sm:mb-6 bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
                  Welcome to TeachMe AI
                </h2>
                <p className="text-body-lg text-muted-foreground mb-6 sm:mb-8 leading-relaxed">
                  Select a conversation from the sidebar or start a new chat to begin learning with AI.
                </p>
                <Button 
                  onClick={handleNewChat} 
                  className="glass-button hover-scale text-primary-foreground shadow-lg hover:shadow-xl"
                  size="lg"
                >
                  <Plus className="h-5 w-5 mr-2" />
                  Start New Chat
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Profile Dialog */}
      <Dialog open={profileDialogOpen} onOpenChange={setProfileDialogOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Profile Settings</DialogTitle>
            <DialogDescription>
              Update your profile information and avatar.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="flex flex-col items-center gap-4">
              <div className="relative">
                <Avatar className="h-20 w-20">
                  <AvatarImage src={userProfile.avatar} alt={userProfile.name} />
                  <AvatarFallback className="bg-primary/10 text-primary text-lg">
                    {getInitials(userProfile.name)}
                  </AvatarFallback>
                </Avatar>
                <Button
                  size="sm"
                  variant="secondary"
                  className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full p-0"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Camera className="h-4 w-4" />
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
              </div>
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name
              </Label>
              <Input
                id="name"
                value={userProfile.name}
                onChange={(e) => setUserProfile(prev => ({ ...prev, name: e.target.value }))}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="email" className="text-right">
                Email
              </Label>
              <Input
                id="email"
                value={userProfile.email}
                onChange={(e) => setUserProfile(prev => ({ ...prev, email: e.target.value }))}
                className="col-span-3"
              />
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="role" className="text-right">
                Role
              </Label>
              <Input
                id="role"
                value={userProfile.role}
                disabled
                className="col-span-3 bg-muted"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <Button onClick={() => handleProfileUpdate(userProfile)}>
              Save Changes
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      
    </div>
  )
}
