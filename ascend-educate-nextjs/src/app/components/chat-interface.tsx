"use client"

import * as React from "react"
import { Send, Paperclip, X, File } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

interface Message {
  id: string
  type: "user" | "ai"
  content: string
  timestamp: string // ISO string for serialization
  files?: FileAttachment[]
}

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
  const [messages, setMessages] = React.useState<Message[]>([
    {
      id: "1",
      type: "ai",
      content: "Hello! I'm TeachMe AI, your personalized learning assistant. How can I help you today?",
      timestamp: new Date().toISOString(),
    }
  ])

  const fileInputRef = React.useRef<HTMLInputElement>(null)

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

  const handleSend = () => {
    if (!message.trim() && files.length === 0) return

    const newMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: message,
      timestamp: new Date().toISOString(),
      files: files.length > 0 ? files : undefined,
    }

    setMessages(prev => [...prev, newMessage])
    onSendMessage?.()
    setMessage("")
    setFiles([])

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: "ai",
        content: "I understand your question. Let me help you with that...",
        timestamp: new Date().toISOString(),
      }
      setMessages(prev => [...prev, aiResponse])
    }, 1000)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-2 sm:p-4 scroll-area">
        <div className="space-y-4 sm:space-y-6 max-w-4xl mx-auto">
          {messages.map((msg, index) => (
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
                <p className="text-sm sm:text-sm leading-relaxed">{msg.content}</p>
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

      {/* Input Area */}
      <div className="chat-input-container p-3 sm:p-4">
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
            disabled={!message.trim() && files.length === 0}
            className="chat-send-button h-10 w-10 sm:h-12 sm:w-12 flex-shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}
