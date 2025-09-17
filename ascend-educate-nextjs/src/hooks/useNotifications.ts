import { useState, useEffect, useCallback } from 'react'

export interface Notification {
  id: string
  type: 'chat' | 'profile' | 'system' | 'learning'
  title: string
  message: string
  timestamp: string
  isRead: boolean
  actionUrl?: string
  actionText?: string
}

interface NotificationState {
  notifications: Notification[]
  isMuted: boolean
  unreadCount: number
  isLoading: boolean
}

const STORAGE_KEY = 'teachme-notifications'
const MUTE_KEY = 'teachme-notifications-muted'

export function useNotifications() {
  const [state, setState] = useState<NotificationState>({
    notifications: [],
    isMuted: false,
    unreadCount: 0,
    isLoading: false
  })

  // Load initial state from localStorage
  useEffect(() => {
    const savedNotifications = localStorage.getItem(STORAGE_KEY)
    const savedMuteState = localStorage.getItem(MUTE_KEY)
    
    if (savedNotifications) {
      try {
        const parsed = JSON.parse(savedNotifications)
        setState(prev => ({
          ...prev,
          notifications: parsed,
          unreadCount: parsed.filter((n: Notification) => !n.isRead).length
        }))
      } catch (error) {
        console.error('Error parsing saved notifications:', error)
      }
    }

    if (savedMuteState) {
      try {
        setState(prev => ({
          ...prev,
          isMuted: JSON.parse(savedMuteState)
        }))
      } catch (error) {
        console.error('Error parsing saved mute state:', error)
      }
    }
  }, [])

  // Save to localStorage whenever state changes
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state.notifications))
  }, [state.notifications])

  useEffect(() => {
    localStorage.setItem(MUTE_KEY, JSON.stringify(state.isMuted))
  }, [state.isMuted])

  // Generate mock notifications for demo
  const generateMockNotifications = useCallback((): Notification[] => {
    const now = new Date()
    return [
      {
        id: '1',
        type: 'chat',
        title: 'New Message',
        message: 'You have a new message in your AI learning session',
        timestamp: new Date(now.getTime() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
        isRead: false,
        actionUrl: '/chat',
        actionText: 'View Chat'
      },
      {
        id: '2',
        type: 'profile',
        title: 'Complete Your Profile',
        message: 'Add your profile picture and bio to get personalized recommendations',
        timestamp: new Date(now.getTime() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
        isRead: false,
        actionUrl: '/profile',
        actionText: 'Complete Profile'
      },
      {
        id: '3',
        type: 'system',
        title: 'Welcome to TeachMe AI!',
        message: 'Your account has been successfully created. Start your learning journey today!',
        timestamp: new Date(now.getTime() - 1000 * 60 * 60 * 2).toISOString(), // 2 hours ago
        isRead: true
      },
      {
        id: '4',
        type: 'learning',
        title: 'Study Reminder',
        message: 'You have 3 pending lessons. Keep up with your learning streak!',
        timestamp: new Date(now.getTime() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
        isRead: true,
        actionUrl: '/lessons',
        actionText: 'View Lessons'
      }
    ]
  }, [])

  // Initialize with mock data if no notifications exist
  useEffect(() => {
    if (state.notifications.length === 0 && !state.isLoading) {
      setState(prev => ({
        ...prev,
        isLoading: true
      }))
      
      // Simulate API call delay
      setTimeout(() => {
        const mockNotifications = generateMockNotifications()
        setState(prev => ({
          ...prev,
          notifications: mockNotifications,
          unreadCount: mockNotifications.filter(n => !n.isRead).length,
          isLoading: false
        }))
      }, 500)
    }
  }, [state.notifications.length, state.isLoading, generateMockNotifications])

  const markAsRead = useCallback((id: string) => {
    setState(prev => ({
      ...prev,
      notifications: prev.notifications.map(n =>
        n.id === id ? { ...n, isRead: true } : n
      ),
      unreadCount: prev.notifications.filter(n => n.id !== id && !n.isRead).length
    }))
  }, [])

  const markAllAsRead = useCallback(() => {
    setState(prev => ({
      ...prev,
      notifications: prev.notifications.map(n => ({ ...n, isRead: true })),
      unreadCount: 0
    }))
  }, [])

  const toggleMute = useCallback(() => {
    setState(prev => ({
      ...prev,
      isMuted: !prev.isMuted
    }))
  }, [])

  const addNotification = useCallback((notification: Omit<Notification, 'id' | 'timestamp' | 'isRead'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
      isRead: false
    }

    setState(prev => ({
      ...prev,
      notifications: [newNotification, ...prev.notifications].slice(0, 20), // Keep last 20
      unreadCount: prev.unreadCount + 1
    }))
  }, [])

  const removeNotification = useCallback((id: string) => {
    setState(prev => {
      const notification = prev.notifications.find(n => n.id === id)
      return {
        ...prev,
        notifications: prev.notifications.filter(n => n.id !== id),
        unreadCount: notification && !notification.isRead 
          ? prev.unreadCount - 1 
          : prev.unreadCount
      }
    })
  }, [])

  return {
    notifications: state.notifications,
    isMuted: state.isMuted,
    unreadCount: state.unreadCount,
    isLoading: state.isLoading,
    markAsRead,
    markAllAsRead,
    toggleMute,
    addNotification,
    removeNotification
  }
}
