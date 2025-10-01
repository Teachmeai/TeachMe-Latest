"use client"

import * as React from "react"
import { Camera } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import { SPACING, TYPOGRAPHY } from "@/config/design-tokens"

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
    <div className={cn("flex flex-col items-center", SPACING.flex.default, className)}>
      <div className="relative">
        <Avatar className="h-24 w-24 ring-2 ring-border/20">
          <AvatarImage src={imageUrl} alt="Profile" />
          <AvatarFallback className="bg-primary/10 text-primary text-xl">
            {getInitials(name || 'U')}
          </AvatarFallback>
        </Avatar>
        <Button
          size="sm"
          variant="secondary"
          className="absolute -bottom-2 -right-2 h-8 w-8 rounded-full p-0 shadow-sm"
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
      <p className={cn(TYPOGRAPHY.body.muted)}>Click to upload profile picture</p>
    </div>
  )
}
