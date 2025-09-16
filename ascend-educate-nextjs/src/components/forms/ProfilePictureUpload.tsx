"use client"

import * as React from "react"
import { Camera } from "lucide-react"
import { Button } from "../../app/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "../../app/components/ui/avatar"
import { cn } from "../../app/lib/utils"

interface ProfilePictureUploadProps {
  imageUrl?: string
  name: string
  onImageChange: (imageUrl: string) => void
  className?: string
}

export function ProfilePictureUpload({ 
  imageUrl, 
  name, 
  onImageChange, 
  className 
}: ProfilePictureUploadProps) {
  const fileInputRef = React.useRef<HTMLInputElement>(null)

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map(n => n[0])
      .join("")
      .toUpperCase()
  }

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        onImageChange(result)
      }
      reader.readAsDataURL(file)
    }
  }

  return (
    <div className={cn("flex flex-col items-center space-y-4", className)}>
      <div className="relative">
        <Avatar className="h-24 w-24">
          <AvatarImage src={imageUrl} alt="Profile" />
          <AvatarFallback className="bg-primary/10 text-primary text-xl">
            {getInitials(name || 'U')}
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
          onChange={handleImageChange}
          className="hidden"
        />
      </div>
      <p className="text-sm text-muted-foreground">Click to upload profile picture</p>
    </div>
  )
}
