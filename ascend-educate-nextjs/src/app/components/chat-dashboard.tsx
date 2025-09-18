"use client"

import * as React from "react"
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
import { ThemeToggle } from "@/components/theme-toggle"
import { ChatInterface } from "@/components/chat-interface"
import { ProfileManagement } from "@/components/profile-management"
import { NotificationBell } from "@/components/notification-bell"
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
import { useIsMobile } from "@/hooks/use-mobile"
// removed quick role switcher; role management happens inside Profile
import type { UserSession } from "../../lib/backend"

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
}

export function ChatDashboard({ user, onLogout, onSendMessage, onProfileUpdate, session, onSwitchRole }: ChatDashboardProps) {
  const isMobile = useIsMobile()
  const [sidebarOpen, setSidebarOpen] = React.useState(!isMobile) // Default to closed on mobile
  const [sidebarAnimating, setSidebarAnimating] = React.useState(false)
  const [sidebarWidth, setSidebarWidth] = React.useState<number>(320)
  const isResizingRef = React.useRef(false)
  const [activeChat, setActiveChat] = React.useState<string | null>(null)
  const [searchQuery, setSearchQuery] = React.useState("")
  const [userProfile, setUserProfile] = React.useState<UserProfile>(user)
  const [profileDialogOpen, setProfileDialogOpen] = React.useState(false)
  
  const [showProfileManagement, setShowProfileManagement] = React.useState(false)
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  
  // Session and role switching are provided by parent to avoid double auth hooks

  // Update sidebar state when mobile state changes
  React.useEffect(() => {
    if (isMobile) {
      setSidebarOpen(false)
    } else {
      setSidebarOpen(true)
    }
  }, [isMobile])

  // Sidebar resize handlers (desktop only)
  const onResizeMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isMobile) return
    e.preventDefault()
    isResizingRef.current = true
    const startX = e.clientX
    const startWidth = sidebarWidth
    const onMove = (ev: MouseEvent) => {
      if (!isResizingRef.current) return
      const delta = ev.clientX - startX
      const next = Math.min(Math.max(startWidth + delta, 240), 520)
      setSidebarWidth(next)
    }
    const onUp = () => {
      isResizingRef.current = false
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }
  
  // Mock chat sessions
  const [chatSessions, setChatSessions] = React.useState<ChatSession[]>([
    {
      id: "1",
      title: "Getting Started with AI Learning",
      lastMessage: "How can I improve my study habits?",
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 mins ago
    },
    {
      id: "2", 
      title: "Math Problem Solving",
      lastMessage: "Can you help me with calculus?",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
    },
    {
      id: "3",
      title: "Essay Writing Tips",
      lastMessage: "How to structure an academic essay?",
      timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
    },
  ])

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map(n => n[0])
      .join("")
      .toUpperCase()
  }

  const handleNewChat = () => {
    const newChat: ChatSession = {
      id: Date.now().toString(),
      title: "New Chat",
      lastMessage: "",
      timestamp: new Date().toISOString(),
    }
    setChatSessions(prev => [newChat, ...prev])
    setActiveChat(newChat.id)
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

  const handleProfileUpdate = (profile: UserProfile) => {
    setUserProfile(profile)
    if (onProfileUpdate) {
      onProfileUpdate(profile)
    }
    setProfileDialogOpen(false)
    setShowProfileManagement(false)
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
    <div className="h-screen flex bg-background relative">
      {/* Mobile Overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar - Mobile: Fixed overlay, Desktop: Resizable panel */}
      {sidebarOpen && (
        <div
          className={cn(
            "sidebar-panel flex flex-col sidebar-transition",
            isMobile
              ? "fixed left-0 top-0 z-50 h-full w-80 transform transition-transform duration-300"
              : "flex-shrink-0",
            sidebarAnimating ? "sidebar-slide-in" : ""
          )}
          style={!isMobile ? { width: `${sidebarWidth}px` } : undefined}
        >
          {/* Sidebar Header */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between mb-4">
              <Logo size="sm" />
              <div className="flex items-center gap-2">
                <ThemeToggle />
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSidebarToggle}
                  className="hover:bg-primary/10 transition-colors"
                >
                  <PanelLeftClose className="h-4 w-4" />
                </Button>
              </div>
            </div>
            
            {/* New Chat Button */}
            <Button
              onClick={handleNewChat}
              className="w-full bg-primary/10 hover:bg-primary/20 text-primary border-0"
              variant="outline"
            >
              <Plus className="h-4 w-4 mr-2" />
              New Chat
            </Button>
          </div>

          {/* Search */}
          <div className="p-4 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-muted/50 border-0"
              />
            </div>
          </div>

          {/* Chat History */}
          <ScrollArea className="flex-1">
            <div className="p-2">
              {filteredChats.map((chat) => (
                <div
                  key={chat.id}
                  className={cn(
                    "group flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors hover:bg-muted/50 relative",
                    activeChat === chat.id && "bg-muted"
                  )}
                  onClick={() => {
                    setActiveChat(chat.id)
                    // Close sidebar on mobile when chat is selected
                    if (isMobile) {
                      setSidebarOpen(false)
                    }
                  }}
                >
                  <MessageSquare className="h-4 w-4 mt-1 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-medium truncate">{chat.title}</h4>
                    {chat.lastMessage && (
                      <p className="text-xs text-muted-foreground truncate mt-1">
                        {chat.lastMessage}
                      </p>
                    )}
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatTime(chat.timestamp)}
                    </p>
                  </div>
                  
                  {/* Chat Actions - Hidden on mobile for cleaner UI */}
                  <div className={cn(
                    "transition-opacity flex gap-1",
                    isMobile ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                  )}>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 hover:bg-muted"
                      onClick={(e) => {
                        e.stopPropagation()
                        // Edit chat title functionality
                      }}
                    >
                      <Edit className="h-3 w-3" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 hover:bg-destructive/20 hover:text-destructive"
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDeleteChat(chat.id)
                      }}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>

          {/* User Profile */}
          <div className="p-4 border-t border-border">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="w-full justify-start p-2 h-auto">
                  <Avatar className="h-8 w-8 mr-3">
                    <AvatarImage src={userProfile.avatar} alt={userProfile.name} />
                    <AvatarFallback className="bg-primary/10 text-primary text-sm">
                      {getInitials(userProfile.name)}
                    </AvatarFallback>
                  </Avatar>
                  <div className="flex-1 text-left">
                    <p className="text-sm font-medium">{userProfile.name}</p>
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

      {/* Desktop resize handle */}
      {!isMobile && sidebarOpen && (
        <div
          onMouseDown={onResizeMouseDown}
          title="Drag to resize"
          style={{ cursor: 'col-resize' }}
          className="w-1 hover:w-2 transition-[width] duration-150 bg-border/60 dark:bg-border/40"
        />
      )}

      {/* Main Content */}
      <div className={cn(
        "flex flex-col flex-1 main-content-transition",
        !sidebarOpen && "main-content-expand"
      )}>
        {/* Header */}
        <div className="border-b border-border bg-card/50 backdrop-blur-sm">
          <div className="flex items-center justify-between px-4 py-3">
            <div className="flex items-center gap-3">
              {/* Mobile Menu Button */}
              {isMobile && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSidebarToggle}
                  className="hover:bg-primary/10 transition-colors"
                >
                  <Menu className="h-4 w-4" />
                </Button>
              )}
              
              {/* Desktop Sidebar Toggle */}
              {!isMobile && !sidebarOpen && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSidebarToggle}
                  className="hover:bg-primary/10 transition-colors"
                >
                  <PanelLeft className="h-4 w-4" />
                </Button>
              )}
              
              <h1 className="text-lg font-semibold truncate">
                {activeChat ? 
                  chatSessions.find(c => c.id === activeChat)?.title || "TeachMe AI" 
                  : "TeachMe AI"
                }
              </h1>
            </div>

            {/* Notification Bell */}
            <div className="flex items-center gap-2">
              <NotificationBell />
            </div>
          </div>
          
          {/* Profile Completion Banner */}
          {!userProfile.isProfileComplete && (
            <div className="bg-orange-50 dark:bg-orange-950/20 border-t border-orange-200 dark:border-orange-800 px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="w-2 h-2 bg-orange-500 rounded-full animate-pulse flex-shrink-0" />
                  <p className="text-sm text-orange-800 dark:text-orange-200 truncate">
                    Complete your profile to start chatting with TeachMe AI
                  </p>
                </div>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => setShowProfileManagement(true)}
                  className="text-orange-800 dark:text-orange-200 border-orange-300 dark:border-orange-700 hover:bg-orange-100 dark:hover:bg-orange-900/20 flex-shrink-0"
                >
                  Complete Profile
                </Button>
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        <div className="flex-1 bg-background">
          {showProfileManagement ? (
            <ProfileManagement
              user={userProfile}
              roles={session?.roles || []}
              activeRole={userProfile.role}
              activeOrgId={session?.roles.find(r => r.scope === 'org' && r.role === userProfile.role)?.org_id}
              onSwitchRole={handleRoleSwitch}
              onProfileUpdate={handleProfileUpdate}
              onClose={() => setShowProfileManagement(false)}
            />
          ) : !userProfile.isProfileComplete ? (
            <div className="h-full flex items-center justify-center p-4 sm:p-8">
              <div className="text-center max-w-md w-full">
                <div className="w-16 h-16 sm:w-20 sm:h-20 bg-gradient-to-br from-orange-500 to-red-500 rounded-full mx-auto mb-4 sm:mb-6 flex items-center justify-center shadow-glow">
                  <User className="h-8 w-8 sm:h-10 sm:w-10 text-white" />
                </div>
                <h2 className="text-xl sm:text-2xl font-bold mb-3 sm:mb-4">Complete Your Profile</h2>
                <p className="text-muted-foreground mb-4 sm:mb-6 text-sm sm:text-base">
                  You need to complete your profile setup before you can start chatting. 
                  This helps us personalize your TeachMe experience.
                </p>
                <div className="space-y-3">
                  <Button 
                    onClick={() => setShowProfileManagement(true)}
                    className="w-full bg-primary hover:bg-primary/90"
                  >
                    <User className="h-4 w-4 mr-2" />
                    Complete Profile Setup
                  </Button>
                  <p className="text-xs text-muted-foreground">
                    Profile completion: {userProfile.profileCompletionPercentage || 0}%
                  </p>
                </div>
              </div>
            </div>
          ) : activeChat || chatSessions.length === 0 ? (
            <ChatInterface
              onSendMessage={onSendMessage}
              placeholder={`Ask TeachMe AI anything about ${userProfile.role === "student" ? "learning" : userProfile.role === "teacher" ? "teaching" : "administration"}...`}
            />
          ) : (
            <div className="h-full flex items-center justify-center p-4 sm:p-8">
              <div className="text-center max-w-md w-full">
                <MessageSquare className="h-12 w-12 sm:h-16 sm:w-16 mx-auto mb-3 sm:mb-4 text-muted-foreground/50" />
                <h2 className="text-lg sm:text-xl font-semibold mb-2">Welcome to TeachMe AI</h2>
                <p className="text-muted-foreground mb-4 sm:mb-6 text-sm sm:text-base">
                  Select a conversation from the sidebar or start a new chat to begin learning with AI.
                </p>
                <Button onClick={handleNewChat} className="bg-primary hover:bg-primary/90">
                  <Plus className="h-4 w-4 mr-2" />
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
