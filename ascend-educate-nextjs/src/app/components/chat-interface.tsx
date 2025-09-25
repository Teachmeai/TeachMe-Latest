"use client"

import * as React from "react"
import { Send, Paperclip, X, File, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { getUserIdFromToken } from "../../utils/jwt"
import { useAuth } from "../../hooks/useAuth"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
// HTTP mode: no WebSocket

// Note: message shape is defined inline where used to keep types minimal

interface FileAttachment {
  id: string
  name: string
  size: number
  type: string
}

interface ChatInterfaceProps {
  className?: string
  placeholder?: string
  onSendMessage?: () => void
}

// Helper function to detect if content has markdown formatting
function hasMarkdownFormatting(content: string): boolean {
  const markdownPatterns = [
    /\*\*.*?\*\*/, // Bold text
    /\*.*?\*/, // Italic text
    /^\d+\.\s/, // Numbered lists
    /^[-*+]\s/, // Bullet lists
    /^#{1,6}\s/, // Headers
    /```[\s\S]*?```/, // Code blocks
    /`[^`]+`/, // Inline code
  ]
  return markdownPatterns.some(pattern => pattern.test(content))
}

// Loading message component
function LoadingMessage() {
  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground py-2">
      <Loader2 className="h-4 w-4 animate-spin text-primary" />
      <span className="animate-pulse">AI is thinking...</span>
    </div>
  )
}

// Custom markdown renderer component
function MarkdownRenderer({ content }: { content: string }) {
  // If no markdown formatting detected, render as plain text
  if (!hasMarkdownFormatting(content)) {
    return <p className="text-sm leading-relaxed">{content}</p>
  }

  return (
    <div className="prose prose-sm max-w-none dark:prose-invert prose-headings:text-foreground prose-p:text-foreground prose-strong:text-foreground prose-li:text-foreground">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
        // Customize list styling
        ul: ({ children }) => (
          <ul className="list-disc pl-6 space-y-1 my-2">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal pl-6 space-y-1 my-2">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="text-sm leading-relaxed">
            {children}
          </li>
        ),
        // Customize heading styling
        h1: ({ children }) => (
          <h1 className="text-lg font-bold mt-4 mb-2 first:mt-0">
            {children}
          </h1>
        ),
        h2: ({ children }) => (
          <h2 className="text-base font-semibold mt-3 mb-2 first:mt-0">
            {children}
          </h2>
        ),
        h3: ({ children }) => (
          <h3 className="text-sm font-medium mt-2 mb-1 first:mt-0">
            {children}
          </h3>
        ),
        // Customize paragraph styling
        p: ({ children }) => (
          <p className="text-sm leading-relaxed my-2 first:mt-0 last:mb-0">
            {children}
          </p>
        ),
        // Customize bold text
        strong: ({ children }) => (
          <strong className="font-semibold text-foreground">
            {children}
          </strong>
        ),
        // Customize code blocks
        code: ({ children, className }) => {
          const isInline = !className
          if (isInline) {
            return (
              <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">
                {children}
              </code>
            )
          }
          return (
            <code className="block bg-muted p-3 rounded-md text-xs font-mono overflow-x-auto my-2">
              {children}
            </code>
          )
        },
        // Customize blockquotes
        blockquote: ({ children }) => (
          <blockquote className="border-l-4 border-muted-foreground/30 pl-4 my-2 italic">
            {children}
          </blockquote>
        ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}

export function ChatInterface({ 
  className, 
  placeholder = "Ask TeachMe AI anything...",
  onSendMessage 
}: ChatInterfaceProps) {
  const [message, setMessage] = React.useState("")
  const [files, setFiles] = React.useState<FileAttachment[]>([])
  
  // Local messages state (user and AI)
  const [wsMessages, setWsMessages] = React.useState<Array<{ id: string; type: "user" | "ai"; message: string; timestamp: string; files?: FileAttachment[]; isLoading?: boolean }>>([])
  const [sending, setSending] = React.useState(false)
  
  // Thread management for conversation context
  const [threadId, setThreadId] = React.useState<string | null>(null)
  
  // Get user session for fallback user ID
  const { session } = useAuth()

  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [wsMessages])

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (sending) return // Prevent file uploads during sending
    
    const selectedFiles = Array.from(event.target.files || [])
    const newFiles: FileAttachment[] = selectedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type,
    }))
    setFiles(prev => [...prev, ...newFiles])
  }

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const handleSend = async () => {
    if (!message.trim() && files.length === 0) return
    if (sending) return // Prevent multiple sends
    
    const text = message.trim()
    const userMsg = {
      id: `${Date.now()}-${Math.random()}`,
      type: "user" as const,
      message: text,
      timestamp: new Date().toISOString(),
      files: files.length ? files : undefined,
    }
    setWsMessages(prev => [...prev, userMsg])
    setMessage("")
    setFiles([])
    setSending(true)

    // Add loading message
    const loadingMsg = {
      id: `loading-${Date.now()}`,
      type: "ai" as const,
      message: "",
      timestamp: new Date().toISOString(),
      isLoading: true
    }
    setWsMessages(prev => [...prev, loadingMsg])

    try {
      const token2 = typeof window !== 'undefined' ? window.localStorage.getItem('token2') : null
      
      // Extract user ID from token or session
      let userId: string | null = null
      if (token2) {
        userId = getUserIdFromToken(token2)
        console.log('User ID extracted from token:', userId)
      }
      
      // Fallback to session user_id if token extraction fails
      if (!userId && session?.user_id) {
        userId = session.user_id
        console.log('User ID extracted from session:', userId)
      }
      
      if (!userId) {
        throw new Error('Unable to extract user ID from token or session')
      }
      
      const resp = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token2 ? { Authorization: `Bearer ${token2}` } : {}),
        },
        body: JSON.stringify({
          message: text,
          user_id: userId, // Extract from JWT token
          thread_id: threadId, // null for first message, then use returned thread_id
          assistant_id: "asst_aqIKBfxBLoKVRTo1la5T8FwX", // null to use Super-Admin Agent
          context: {}
        }),
      })
      if (!resp.ok) {
        const errText = await resp.text()
        throw new Error(errText || `HTTP ${resp.status}`)
      }
      const data = await resp.json().catch(() => ({}))
      
      // Extract response data from the new API format
      const aiText = data?.message || 'Hello World! I am responding over HTTP.'
      const responseThreadId = data?.thread_id
      const messageId = data?.message_id
      const responseTimestamp = data?.timestamp
      const metadata = data?.metadata || {}
      
      // Update thread_id for subsequent messages
      if (responseThreadId && responseThreadId !== threadId) {
        setThreadId(responseThreadId)
      }
      
      const aiMsg = {
        id: messageId || `${Date.now()}-${Math.random()}`,
        type: "ai" as const,
        message: aiText,
        timestamp: responseTimestamp || new Date().toISOString(),
        isLoading: false
      }
      
      // Replace loading message with actual response
      setWsMessages(prev => prev.map(msg => 
        msg.isLoading ? aiMsg : msg
      ))
      onSendMessage?.()
    } catch (e: any) {
      const aiMsg = {
        id: `${Date.now()}-${Math.random()}`,
        type: "ai" as const,
        message: `Request failed: ${e?.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
        isLoading: false
      }
      
      // Replace loading message with error message
      setWsMessages(prev => prev.map(msg => 
        msg.isLoading ? aiMsg : msg
      ))
    } finally {
      setSending(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className={cn("flex flex-col h-screen overflow-hidden", className)}>
      {/* Messages Area */}
      <ScrollArea ref={scrollAreaRef} className="p-2 sm:p-4 scroll-area h-[34rem] ">
        <div className="space-y-4 sm:space-y-6 max-w-4xl mx-auto">
          {wsMessages.map((msg, index) => (
            <div
              key={msg.id}
              className={cn(
                "flex",
                msg.type === "user" ? "justify-end" : "justify-start"
              )}
            >
              <div
                className={cn(
                  "max-w-[85%] sm:max-w-[80%] rounded-2xl px-3 py-2 sm:px-4 sm:py-3 shadow-sm transition-all duration-200 hover:shadow-md message-enter",
                  msg.type === "user" 
                    ? "chat-message-user" 
                    : "chat-message-ai"
                )}
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                {msg.type === "ai" ? (
                  msg.isLoading ? (
                    <LoadingMessage />
                  ) : (
                    <MarkdownRenderer content={msg.message} />
                  )
                ) : (
                  <p className="text-sm sm:text-sm leading-relaxed">{msg.message}</p>
                )}
                {msg.files && msg.files.length > 0 && (
                  <div className="mt-2 sm:mt-3 space-y-1 sm:space-y-2">
                    {msg.files.map((file) => (
                      <div key={file.id} className="flex items-center gap-2 text-xs opacity-75 bg-black/10 rounded-md px-2 py-1">
                        <File className="h-3 w-3 flex-shrink-0" />
                        <span className="truncate min-w-0">{file.name}</span>
                        <span className="text-xs opacity-60 flex-shrink-0">({formatFileSize(file.size)})</span>
                      </div>
                    ))}
                  </div>
                )}
                {!msg.isLoading && (
                  <div className="text-xs opacity-60 mt-1 sm:mt-2 text-right">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </ScrollArea>

      {/* File Attachments */}
      {files.length > 0 && (
        <div className="px-3 sm:px-6 pb-2 sm:pb-3">
          <div className="flex flex-wrap gap-2 max-w-4xl mx-auto">
            {files.map((file) => (
              <div
                key={file.id}
                className="flex items-center gap-2 bg-muted/60 rounded-lg px-2 sm:px-3 py-1 sm:py-2 text-xs border border-border hover:bg-muted/80 transition-colors max-w-full"
              >
                <File className="h-3 w-3 text-primary flex-shrink-0" />
                <span className="truncate min-w-0 max-w-24 sm:max-w-32">{file.name}</span>
                <span className="text-muted-foreground text-xs flex-shrink-0">({formatFileSize(file.size)})</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-5 w-5 p-0 hover:bg-destructive/20 rounded-full flex-shrink-0"
                  onClick={() => removeFile(file.id)}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Connection Status removed for HTTP mode */}

      {/* Input Area */}
      <div className="chat-input-container p-3 sm:p-4 flex-shrink-0">
        <div className="flex items-end gap-2 sm:gap-3 max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder={sending ? "AI is responding..." : placeholder}
              className="chat-input pr-12 h-10 sm:h-12 text-sm resize-none"
              onKeyPress={(e) => e.key === "Enter" && !sending && handleSend()}
              disabled={sending}
            />
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileUpload}
            accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.mp3,.mp4"
          />
          
          <Button
            variant="ghost"
            size="icon"
            onClick={() => fileInputRef.current?.click()}
            disabled={sending}
            className="h-10 w-10 sm:h-12 sm:w-12 hover:bg-primary/10 transition-colors flex-shrink-0 disabled:opacity-50"
          >
            <Paperclip className="h-4 w-4" />
          </Button>
          
          <Button
            variant="default"
            size="icon"
            onClick={handleSend}
            disabled={(!message.trim() && files.length === 0) || sending}
            className="chat-send-button h-10 w-10 sm:h-12 sm:w-12 flex-shrink-0"
          >
            {sending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}
