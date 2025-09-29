"use client"

import * as React from "react"
import { useState, useMemo } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ProfilePictureUpload } from "./ProfilePictureUpload"
import { FormData, ValidationErrors } from "@/types"
import { cn } from "@/lib/utils"

interface BasicInfoFormProps {
  formData: FormData
  errors: ValidationErrors
  onFieldChange: (field: keyof FormData, value: string) => void
  onImageChange: (imageUrl: string) => void
  className?: string
}

export function BasicInfoForm({
  formData,
  errors,
  onFieldChange,
  onImageChange,
  className
}: BasicInfoFormProps) {
  const [socialLink, setSocialLink] = useState("")

  const detectPlatform = (url: string): keyof Pick<FormData, 'linkedin' | 'twitter' | 'github' | 'website'> => {
    const lower = url.toLowerCase()
    try {
      const u = new URL(lower)
      const host = u.hostname.replace("www.", "")
      if (host.includes("linkedin.com")) return 'linkedin'
      if (host.includes("twitter.com") || host.includes("x.com")) return 'twitter'
      if (host.includes("github.com")) return 'github'
      return 'website'
    } catch {
      // not a full URL; naive detection
      if (lower.includes("linkedin")) return 'linkedin'
      if (lower.includes("twitter") || lower.includes("x.com")) return 'twitter'
      if (lower.includes("github")) return 'github'
      return 'website'
    }
  }

  const currentLinks = useMemo(() => [
    { label: 'LinkedIn', key: 'linkedin', value: formData.linkedin },
    { label: 'Twitter', key: 'twitter', value: formData.twitter },
    { label: 'GitHub', key: 'github', value: formData.github },
    { label: 'Website', key: 'website', value: formData.website },
  ], [formData.linkedin, formData.twitter, formData.github, formData.website])

  const handleSocialLinkSubmit = () => {
    if (!socialLink.trim()) return
    const platform = detectPlatform(socialLink.trim())
    onFieldChange(platform as keyof FormData, socialLink.trim())
    setSocialLink("")
  }

  return (
    <div className={cn("space-y-10", className)}>
      {/* Profile Picture */}
      <div className="flex justify-center">
        <ProfilePictureUpload
          imageUrl={formData.profilePicture}
          name={formData.name}
          onImageChange={onImageChange}
        />
      </div>

      {/* Common Fields */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-3">
          <Label htmlFor="name" className="text-base font-semibold">Full Name *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => onFieldChange('name', e.target.value)}
            className={cn("h-12 text-base", errors.name && "border-destructive")}
            placeholder="Enter your full name"
          />
          {errors.name && (
            <p className="text-sm text-destructive font-medium">{errors.name}</p>
          )}
        </div>

        <div className="space-y-3">
          <Label htmlFor="email" className="text-base font-semibold">Email Address</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => onFieldChange('email', e.target.value)}
            className={cn("h-12 text-base bg-muted/50", errors.email && "border-destructive")}
            placeholder="Enter your email"
            disabled
          />
          {errors.email && (
            <p className="text-sm text-destructive font-medium">{errors.email}</p>
          )}
        </div>

        <div className="space-y-3">
          <Label htmlFor="phoneNumber" className="text-base font-semibold">Phone Number *</Label>
          <Input
            id="phoneNumber"
            type="tel"
            value={formData.phoneNumber}
            onChange={(e) => onFieldChange('phoneNumber', e.target.value)}
            className={cn("h-12 text-base", errors.phoneNumber && "border-destructive")}
            placeholder="Enter your phone number"
          />
          {errors.phoneNumber && (
            <p className="text-sm text-destructive font-medium">{errors.phoneNumber}</p>
          )}
          <p className="text-sm text-muted-foreground">
            Enter your phone number with country code or local format
          </p>
        </div>
      </div>

      {/* Address & Bio */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-3">
          <Label htmlFor="address" className="text-base font-semibold">Address</Label>
          <Input
            id="address"
            value={formData.address}
            onChange={(e) => onFieldChange('address', e.target.value)}
            placeholder="Street address"
            className="h-12 text-base"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="city" className="text-base font-semibold">City</Label>
          <Input
            id="city"
            value={formData.city}
            onChange={(e) => onFieldChange('city', e.target.value)}
            placeholder="City"
            className="h-12 text-base"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="state" className="text-base font-semibold">State</Label>
          <Input
            id="state"
            value={formData.state}
            onChange={(e) => onFieldChange('state', e.target.value)}
            placeholder="State"
            className="h-12 text-base"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="country" className="text-base font-semibold">Country</Label>
          <Input
            id="country"
            value={formData.country}
            onChange={(e) => onFieldChange('country', e.target.value)}
            placeholder="Country"
            className="h-12 text-base"
          />
        </div>
        <div className="space-y-3">
          <Label htmlFor="postalCode" className="text-base font-semibold">Postal Code</Label>
          <Input
            id="postalCode"
            value={formData.postalCode}
            onChange={(e) => onFieldChange('postalCode', e.target.value)}
            placeholder="Postal/ZIP code"
            className="h-12 text-base"
          />
        </div>
        <div className="space-y-3 lg:col-span-2">
          <Label htmlFor="bio" className="text-base font-semibold">Bio</Label>
          <Input
            id="bio"
            value={formData.bio}
            onChange={(e) => onFieldChange('bio', e.target.value)}
            placeholder="A short bio about you"
            className="h-12 text-base"
          />
        </div>
      </div>

      {/* Social Media Links (Smart input) */}
      <div className="space-y-6 p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
        <h4 className="text-xl font-bold text-foreground">Social Media Links</h4>
        <div className="space-y-4">
          <div className="space-y-3">
            <Label htmlFor="social-link" className="text-base font-semibold">Paste a social link</Label>
            <div className="flex gap-3">
              <Input
                id="social-link"
                type="url"
                value={socialLink}
                onChange={(e) => setSocialLink(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSocialLinkSubmit() } }}
                placeholder="Paste LinkedIn, Twitter/X, GitHub, or Website URL and press Enter"
                className="h-12 text-base flex-1"
              />
              <button
                type="button"
                className="px-6 py-3 text-base font-semibold rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 hover:scale-105"
                onClick={handleSocialLinkSubmit}
              >
                Add
              </button>
            </div>
            <p className="text-sm text-muted-foreground">We'll detect the platform and place it in the right field.</p>
          </div>

          <div className="space-y-3">
            <Label className="text-base font-semibold">Added links</Label>
            <div className="flex flex-wrap gap-3">
              {formData.linkedin && (
                <Badge variant="secondary" className="px-3 py-1 text-sm font-medium bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300">
                  LinkedIn added
                </Badge>
              )}
              {formData.twitter && (
                <Badge variant="secondary" className="px-3 py-1 text-sm font-medium bg-sky-50 dark:bg-sky-950/20 text-sky-700 dark:text-sky-300">
                  Twitter/X added
                </Badge>
              )}
              {formData.github && (
                <Badge variant="secondary" className="px-3 py-1 text-sm font-medium bg-gray-50 dark:bg-gray-950/20 text-gray-700 dark:text-gray-300">
                  GitHub added
                </Badge>
              )}
              {formData.website && (
                <Badge variant="secondary" className="px-3 py-1 text-sm font-medium bg-primary/10 text-primary">
                  Website added
                </Badge>
              )}
              {!formData.linkedin && !formData.twitter && !formData.github && !formData.website && (
                <p className="text-sm text-muted-foreground">No links added yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
