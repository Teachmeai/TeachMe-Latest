"use client"

import * as React from "react"
import { Bell, BellOff, X, Check, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useNotifications, type Notification } from "../../hooks/useNotifications"
import { cn } from "@/lib/utils"

// Demo function to add test notifications (remove in production)
export const addTestNotification = (addNotification: (notification: Omit<Notification, 'id' | 'timestamp' | 'isRead'>) => void) => {
  const testNotifications = [
    {
      type: 'learning' as const,
      title: 'Study Streak!',
      message: 'Congratulations! You\u2019ve completed 7 days in a row. Keep up the great work!',
      actionUrl: '/achievements',
      actionText: 'View Achievements'
    },
    {
      type: 'chat' as const,
      title: 'AI Response Ready',
      message: 'Your AI tutor has responded to your question about calculus derivatives.',
      actionUrl: '/chat',
      actionText: 'View Response'
    },
    {
      type: 'system' as const,
      title: 'App Update Available',
      message: 'Version 2.1.0 is now available with new features and improvements.',
      actionUrl: '/updates',
      actionText: 'Learn More'
    }
  ]
  
  const randomNotification = testNotifications[Math.floor(Math.random() * testNotifications.length)]
  addNotification(randomNotification)
}

interface NotificationItemProps {
  notification: Notification
  onMarkAsRead: (id: string) => void
  onRemove: (id: string) => void
}

function NotificationItem({ notification, onMarkAsRead, onRemove }: NotificationItemProps) {
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / (1000 * 60))
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) return `${days}d ago`
    if (hours > 0) return `${hours}h ago`
    if (minutes > 0) return `${minutes}m ago`
    return 'Just now'
  }

  const getNotificationIcon = (type: Notification['type']) => {
    switch (type) {
      case 'chat':
        return '💬'
      case 'profile':
        return '👤'
      case 'system':
        return '⚙️'
      case 'learning':
        return '📚'
      default:
        return '🔔'
    }
  }

  const getNotificationColor = (type: Notification['type']) => {
    switch (type) {
      case 'chat':
        return 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950/20'
      case 'profile':
        return 'text-orange-600 bg-orange-50 dark:text-orange-400 dark:bg-orange-950/20'
      case 'system':
        return 'text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-950/20'
      case 'learning':
        return 'text-green-600 bg-green-50 dark:text-green-400 dark:bg-green-950/20'
      default:
        return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-950/20'
    }
  }

  return (
    <div
      className={cn(
        "group p-3 rounded-lg transition-colors hover:bg-muted/50 cursor-pointer border-l-4 notification-item",
        !notification.isRead ? "border-l-primary bg-primary/5" : "border-l-transparent"
      )}
      onClick={() => !notification.isRead && onMarkAsRead(notification.id)}
    >
      <div className="flex items-start gap-3">
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm",
          getNotificationColor(notification.type)
        )}>
          {getNotificationIcon(notification.type)}
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-medium text-foreground truncate">
                {notification.title}
              </h4>
              <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                {notification.message}
              </p>
            </div>
            
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              {!notification.isRead && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 hover:bg-primary/10"
                  onClick={(e) => {
                    e.stopPropagation()
                    onMarkAsRead(notification.id)
                  }}
                >
                  <Check className="h-3 w-3" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 hover:bg-destructive/10 hover:text-destructive"
                onClick={(e) => {
                  e.stopPropagation()
                  onRemove(notification.id)
                }}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          </div>
          
          <div className="flex items-center justify-between mt-2">
            <span className="text-xs text-muted-foreground">
              {formatTime(notification.timestamp)}
            </span>
            
            {notification.actionUrl && notification.actionText && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 px-2 text-xs text-primary hover:bg-primary/10"
                onClick={(e) => {
                  e.stopPropagation()
                  // Handle navigation
                  console.log('Navigate to:', notification.actionUrl)
                }}
              >
                {notification.actionText}
                <ExternalLink className="h-3 w-3 ml-1" />
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export function NotificationBell() {
  const {
    notifications,
    isMuted,
    unreadCount,
    isLoading,
    markAsRead,
    markAllAsRead,
    toggleMute,
    removeNotification
  } = useNotifications()

  const [isOpen, setIsOpen] = React.useState(false)

  return (
    <DropdownMenu open={isOpen} onOpenChange={setIsOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-10 w-10 hover:bg-primary/10 transition-colors"
        >
          {isMuted ? (
            <BellOff className="h-5 w-5 text-muted-foreground" />
          ) : (
            <Bell className="h-5 w-5 text-muted-foreground hover:text-primary transition-colors" />
          )}
          
          {!isMuted && unreadCount > 0 && (
            <Badge 
              variant="destructive" 
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs font-medium"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      
      <DropdownMenuContent 
        className="w-80 p-0 notification-dropdown" 
        align="end"
        sideOffset={8}
      >
        {/* Header */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm">Notifications</h3>
              {unreadCount > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {unreadCount} new
                </Badge>
              )}
            </div>
            
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={toggleMute}
                className="h-8 px-2 text-xs"
              >
                {isMuted ? <Bell className="h-3 w-3 mr-1" /> : <BellOff className="h-3 w-3 mr-1" />}
                {isMuted ? 'Unmute' : 'Mute'}
              </Button>
              
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={markAllAsRead}
                  className="h-8 px-2 text-xs text-primary"
                >
                  Mark all read
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Notifications List */}
        <ScrollArea className="max-h-96">
          {isLoading ? (
            <div className="p-8 text-center">
              <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Loading notifications...</p>
            </div>
          ) : notifications.length === 0 ? (
            <div className="p-8 text-center">
              <Bell className="h-8 w-8 text-muted-foreground/50 mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">No notifications yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                We'll notify you when something important happens
              </p>
            </div>
          ) : (
            <div className="p-2">
              {notifications.map((notification, index) => (
                <React.Fragment key={notification.id}>
                  <NotificationItem
                    notification={notification}
                    onMarkAsRead={markAsRead}
                    onRemove={removeNotification}
                  />
                  {index < notifications.length - 1 && (
                    <Separator className="my-2" />
                  )}
                </React.Fragment>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Footer */}
        {notifications.length > 0 && (
          <div className="p-3 border-t border-border bg-muted/20">
            <Button
              variant="ghost"
              size="sm"
              className="w-full text-xs text-muted-foreground hover:text-foreground"
              onClick={() => {
                // Navigate to full notifications page
                console.log('View all notifications')
              }}
            >
              View all notifications
            </Button>
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
