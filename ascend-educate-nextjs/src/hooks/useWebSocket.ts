import { useState, useEffect, useRef, useCallback } from 'react'
import { supabase } from '../lib/supabase'

export interface ChatMessage {
  id: string
  type: 'user' | 'ai' | 'system' | 'error'
  message: string
  timestamp: string
}

export interface WebSocketState {
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  messages: ChatMessage[]
}

export function useWebSocket() {
  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    messages: []
  })
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const maxReconnectAttempts = 5

  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }
    
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      console.log('WebSocket already connecting')
      return
    }

    setState(prev => ({ ...prev, isConnecting: true, error: null }))

    try {
      // Get JWT token from Supabase
      const { data: { session } } = await supabase.auth.getSession()
      if (!session?.access_token) {
        throw new Error('No authentication token available')
      }

      // Create WebSocket URL with token
      const wsUrl = `${BACKEND_URL.replace('http', 'ws')}/chat/ws?token=${session.access_token}`
      console.log('Connecting to WebSocket:', wsUrl)

      wsRef.current = new WebSocket(wsUrl)

      wsRef.current.onopen = () => {
        console.log('WebSocket connected')
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null
        }))
        reconnectAttemptsRef.current = 0
      }

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('WebSocket message received:', data)
          
          const message: ChatMessage = {
            id: `${Date.now()}-${Math.random()}`,
            type: data.type,
            message: data.message,
            timestamp: data.timestamp
          }
          
          setState(prev => {
            // Check for duplicate messages (same type and message within 1 second)
            const isDuplicate = prev.messages.some(msg => 
              msg.type === message.type && 
              msg.message === message.message && 
              Math.abs(new Date(msg.timestamp).getTime() - new Date(message.timestamp).getTime()) < 1000
            )
            
            if (isDuplicate) {
              console.log('Duplicate message detected, skipping:', message.message)
              return prev
            }
            
            return {
              ...prev,
              messages: [...prev.messages, message]
            }
          })
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason)
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false
        }))

        // Attempt to reconnect if not a manual close
        if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000)
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, delay)
        }
      }

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error)
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error',
          isConnecting: false
        }))
      }

    } catch (error) {
      console.error('Error connecting to WebSocket:', error)
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Connection failed',
        isConnecting: false
      }))
    }
  }, [BACKEND_URL])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect')
      wsRef.current = null
    }
    
    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: null
    }))
  }, [])

  const sendMessage = useCallback((message: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected')
      setState(prev => ({ ...prev, error: 'Not connected to chat' }))
      return false
    }

    try {
      const messageData = {
        message: message,
        timestamp: new Date().toISOString()
      }
      
      wsRef.current.send(JSON.stringify(messageData))
      
      // Add user message to local state immediately
      const userMessage: ChatMessage = {
        id: `${Date.now()}-${Math.random()}`,
        type: 'user',
        message: message,
        timestamp: new Date().toISOString()
      }
      
      setState(prev => ({
        ...prev,
        messages: [...prev.messages, userMessage]
      }))
      
      return true
    } catch (error) {
      console.error('Error sending message:', error)
      setState(prev => ({ ...prev, error: 'Failed to send message' }))
      return false
    }
  }, [])

  const clearMessages = useCallback(() => {
    setState(prev => ({ ...prev, messages: [] }))
  }, [])

  // Auto-connect on mount
  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, []) // Remove dependencies to prevent re-connection on every render

  return {
    ...state,
    connect,
    disconnect,
    sendMessage,
    clearMessages
  }
}
