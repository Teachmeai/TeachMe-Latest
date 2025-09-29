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
    <div className={cn("space-y-8", className)}>
      {/* Profile Picture */}
      <ProfilePictureUpload
        imageUrl={formData.profilePicture}
        name={formData.name}
        onImageChange={onImageChange}
      />

      {/* Common Fields */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="name">Full Name *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => onFieldChange('name', e.target.value)}
            className={cn(errors.name && "border-destructive")}
            placeholder="Enter your full name"
          />
          {errors.name && (
            <p className="text-sm text-destructive">{errors.name}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email Address</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => onFieldChange('email', e.target.value)}
            className={cn(errors.email && "border-destructive")}
            placeholder="Enter your email"
            disabled
          />
          {errors.email && (
            <p className="text-sm text-destructive">{errors.email}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="phoneNumber">Phone Number *</Label>
          <Input
            id="phoneNumber"
            type="tel"
            value={formData.phoneNumber}
            onChange={(e) => onFieldChange('phoneNumber', e.target.value)}
            className={cn(errors.phoneNumber && "border-destructive")}
            placeholder="Enter your phone number"
          />
          {errors.phoneNumber && (
            <p className="text-sm text-destructive">{errors.phoneNumber}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Enter your phone number with country code or local format
          </p>
        </div>
      </div>

      {/* Address & Bio */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-2">
          <Label htmlFor="address">Address</Label>
          <Input
            id="address"
            value={formData.address}
            onChange={(e) => onFieldChange('address', e.target.value)}
            placeholder="Street address"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="city">City</Label>
          <Input
            id="city"
            value={formData.city}
            onChange={(e) => onFieldChange('city', e.target.value)}
            placeholder="City"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="state">State</Label>
          <Input
            id="state"
            value={formData.state}
            onChange={(e) => onFieldChange('state', e.target.value)}
            placeholder="State"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="country">Country</Label>
          <Input
            id="country"
            value={formData.country}
            onChange={(e) => onFieldChange('country', e.target.value)}
            placeholder="Country"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="postalCode">Postal Code</Label>
          <Input
            id="postalCode"
            value={formData.postalCode}
            onChange={(e) => onFieldChange('postalCode', e.target.value)}
            placeholder="Postal/ZIP code"
          />
        </div>
        <div className="space-y-2 lg:col-span-2">
          <Label htmlFor="bio">Bio</Label>
          <Input
            id="bio"
            value={formData.bio}
            onChange={(e) => onFieldChange('bio', e.target.value)}
            placeholder="A short bio about you"
          />
        </div>
      </div>

      {/* Social Media Links (Smart input) */}
      <div className="space-y-4">
        <h4 className="text-lg font-semibold">Social Media Links</h4>
        <div className="space-y-2">
          <Label htmlFor="social-link">Paste a social link</Label>
          <div className="flex gap-2">
            <Input
              id="social-link"
              type="url"
              value={socialLink}
              onChange={(e) => setSocialLink(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSocialLinkSubmit() } }}
              placeholder="Paste LinkedIn, Twitter/X, GitHub, or Website URL and press Enter"
            />
            <button
              type="button"
              className="px-3 py-2 text-sm rounded-md bg-primary text-white hover:bg-primary/90"
              onClick={handleSocialLinkSubmit}
            >
              Add
            </button>
          </div>
          <p className="text-xs text-muted-foreground">We'll detect the platform and place it in the right field.</p>
        </div>

        <div className="space-y-2">
          <Label>Added links</Label>
          <div className="flex flex-wrap gap-2">
            {formData.linkedin && <Badge variant="secondary">LinkedIn added</Badge>}
            {formData.twitter && <Badge variant="secondary">Twitter/X added</Badge>}
            {formData.github && <Badge variant="secondary">GitHub added</Badge>}
            {formData.website && <Badge variant="secondary">Website added</Badge>}
            {!formData.linkedin && !formData.twitter && !formData.github && !formData.website && (
              <p className="text-sm text-muted-foreground">No links added yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
