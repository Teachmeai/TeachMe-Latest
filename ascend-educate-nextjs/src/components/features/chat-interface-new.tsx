"use client"

import * as React from "react"
import { Send, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: number
}

interface ChatInterfaceProps {
  className?: string
  placeholder?: string
  assistantId?: string
  assistantName?: string
  threadId?: string
  messages?: ChatMessage[]
  onMessagesUpdate?: (messages: ChatMessage[]) => void
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

// Enhanced loading message component
function LoadingMessage() {
  return (
    <div className="flex items-center gap-3 text-sm text-muted-foreground py-2 animate-fade-in">
      <div className="loading-dots">
        <div></div>
        <div></div>
        <div></div>
      </div>
      <span className="animate-pulse font-medium">AI is thinking...</span>
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
        // Customize code block styling
        code: ({ inline, className, children, ...props }: any) => {
          return inline ? (
            <code className="bg-muted px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
              {children}
            </code>
          ) : (
            <code className="block bg-muted p-3 rounded-lg text-xs font-mono overflow-x-auto my-2" {...props}>
              {children}
            </code>
          )
        },
        // Customize link styling
        a: ({ children, href }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            {children}
          </a>
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
  assistantId,
  assistantName,
  threadId,
  messages = [],
  onMessagesUpdate,
  onSendMessage 
}: ChatInterfaceProps) {
  const [message, setMessage] = React.useState("")
  const [sending, setSending] = React.useState(false)
  
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!message.trim()) return
    if (sending) return
    if (!assistantId || !threadId) {
      console.error('Cannot send message: missing assistantId or threadId')
      return
    }
    
    const text = message.trim()
    setSending(true)
    setMessage("")
    
    // Optimistically add user message
    const userMessage: ChatMessage = {
      id: `temp-user-${Date.now()}`,
      role: 'user',
      content: text,
      created_at: Date.now() / 1000
    }
    const updatedMessages = [...messages, userMessage]
    onMessagesUpdate?.(updatedMessages)
    
    try {
      // Import backend here to avoid circular dependencies
      const { backend } = await import('../../lib/backend')
      
      console.log('Sending message to assistant:', assistantId, 'thread:', threadId)
      const resp = await backend.sendMessage(threadId, assistantId, text)
      
      if (resp.ok && resp.data) {
        // Add assistant response
        const assistantMessage: ChatMessage = {
          id: resp.data.assistant_response.id,
          role: 'assistant',
          content: resp.data.assistant_response.content,
          created_at: resp.data.assistant_response.created_at
        }
        onMessagesUpdate?.([...updatedMessages, assistantMessage])
        console.log('Assistant response received')
      } else {
        console.error('Failed to get response:', resp.error)
        // Show error message
        const errorMessage: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'I apologize, but I encountered an error. Please try again.',
          created_at: Date.now() / 1000
        }
        onMessagesUpdate?.([...updatedMessages, errorMessage])
      }
    } catch (error) {
      console.error('Chat error:', error)
      // Show error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error. Please try again.',
        created_at: Date.now() / 1000
      }
      onMessagesUpdate?.([...updatedMessages, errorMessage])
    } finally {
      setSending(false)
    }
    
    onSendMessage?.()
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages Area */}
      <div className="flex-1 overflow-hidden">
        <ScrollArea className="h-full px-4 sm:px-6">
          <div className="max-w-4xl mx-auto py-6 space-y-6" ref={scrollAreaRef}>
            {messages.length === 0 ? (
              <div className="text-center py-12">
                <p className="text-muted-foreground">
                  {assistantName ? `Start chatting with ${assistantName}` : 'Start a conversation'}
                </p>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex gap-3",
                    msg.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] rounded-2xl px-4 py-3",
                      msg.role === 'user'
                        ? "bg-primary text-primary-foreground ml-auto"
                        : "bg-muted"
                    )}
                  >
                    <MarkdownRenderer content={msg.content} />
                  </div>
                </div>
              ))
            )}
            {sending && <LoadingMessage />}
          </div>
        </ScrollArea>
      </div>

      {/* Input Area */}
      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-4">
          <div className="flex gap-2">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={placeholder}
              disabled={sending}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={!message.trim() || sending}
              size="icon"
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
    </div>
  )
}
