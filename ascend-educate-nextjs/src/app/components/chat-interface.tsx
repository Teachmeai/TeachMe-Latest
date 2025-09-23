"use client"

import * as React from "react"
import { Send, Paperclip, X, File } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
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

export function ChatInterface({ 
  className, 
  placeholder = "Ask TeachMe AI anything...",
  onSendMessage 
}: ChatInterfaceProps) {
  const [message, setMessage] = React.useState("")
  const [files, setFiles] = React.useState<FileAttachment[]>([])
  
  // Local messages state (user and AI)
  const [wsMessages, setWsMessages] = React.useState<Array<{ id: string; type: "user" | "ai"; message: string; timestamp: string; files?: FileAttachment[] }>>([])
  const [sending, setSending] = React.useState(false)

  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const scrollAreaRef = React.useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  React.useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [wsMessages])

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
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

    try {
      const token2 = typeof window !== 'undefined' ? window.localStorage.getItem('token2') : null
      const resp = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: token2, message: text })
      })
      if (!resp.ok) {
        const errText = await resp.text()
        throw new Error(errText || `HTTP ${resp.status}`)
      }
      const data = await resp.json().catch(() => ({}))
      const aiText = data?.message || data?.reply || data?.response || 'Hello World! I am responding over HTTP.'
      const aiMsg = {
        id: `${Date.now()}-${Math.random()}`,
        type: "ai" as const,
        message: aiText,
        timestamp: new Date().toISOString(),
      }
      setWsMessages(prev => [...prev, aiMsg])
      onSendMessage?.()
    } catch (e: any) {
      const aiMsg = {
        id: `${Date.now()}-${Math.random()}`,
        type: "ai" as const,
        message: `Request failed: ${e?.message || 'Unknown error'}`,
        timestamp: new Date().toISOString(),
      }
      setWsMessages(prev => [...prev, aiMsg])
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
                <p className="text-sm sm:text-sm leading-relaxed">{msg.message}</p>
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
                <div className="text-xs opacity-60 mt-1 sm:mt-2 text-right">
                  {new Date(msg.timestamp).toLocaleTimeString()}
                </div>
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
              placeholder={placeholder}
              className="chat-input pr-12 h-10 sm:h-12 text-sm resize-none"
              onKeyPress={(e) => e.key === "Enter" && handleSend()}
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
            className="h-10 w-10 sm:h-12 sm:w-12 hover:bg-primary/10 transition-colors flex-shrink-0"
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
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
