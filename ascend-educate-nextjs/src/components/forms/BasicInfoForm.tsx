"use client"

import * as React from "react"
import { useState } from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ProfilePictureUpload } from "./ProfilePictureUpload"
import { FormData, ValidationErrors } from "@/types"
import { cn } from "@/lib/utils"
import { SPACING, PADDING, TYPOGRAPHY, BACKGROUNDS, BORDER_RADIUS } from "@/config/design-tokens"

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

  const handleSocialLinkSubmit = () => {
    if (!socialLink.trim()) return
    const platform = detectPlatform(socialLink.trim())
    onFieldChange(platform as keyof FormData, socialLink.trim())
    setSocialLink("")
  }

  return (
    <div className={cn(SPACING.form.betweenSections, className)}>
      {/* Profile Picture */}
      <div className="flex justify-center">
        <ProfilePictureUpload
          imageUrl={formData.profilePicture}
          name={formData.name}
          onImageChange={onImageChange}
        />
      </div>

      {/* Common Fields */}
      <div className={cn("grid grid-cols-1 lg:grid-cols-2", SPACING.grid.formFields)}>
        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="name" className={TYPOGRAPHY.label.default}>Full Name *</Label>
          <Input
            id="name"
            value={formData.name}
            onChange={(e) => onFieldChange('name', e.target.value)}
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size, errors.name && "border-destructive")}
            placeholder="Enter your full name"
          />
          {errors.name && (
            <p className={cn(TYPOGRAPHY.body.small, "text-destructive font-medium")}>{errors.name}</p>
          )}
        </div>

        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="email" className={TYPOGRAPHY.label.default}>Email Address</Label>
          <Input
            id="email"
            type="email"
            value={formData.email}
            onChange={(e) => onFieldChange('email', e.target.value)}
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size, "bg-muted/50", errors.email && "border-destructive")}
            placeholder="Enter your email"
            disabled
          />
          {errors.email && (
            <p className={cn(TYPOGRAPHY.body.small, "text-destructive font-medium")}>{errors.email}</p>
          )}
        </div>

        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="phoneNumber" className={TYPOGRAPHY.label.default}>Phone Number *</Label>
          <Input
            id="phoneNumber"
            type="tel"
            value={formData.phoneNumber}
            onChange={(e) => onFieldChange('phoneNumber', e.target.value)}
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size, errors.phoneNumber && "border-destructive")}
            placeholder="Enter your phone number"
          />
          {errors.phoneNumber && (
            <p className={cn(TYPOGRAPHY.body.small, "text-destructive font-medium")}>{errors.phoneNumber}</p>
          )}
          <p className={TYPOGRAPHY.body.muted}>
            Enter your phone number with country code or local format
          </p>
        </div>
      </div>

      {/* Address & Bio */}
      <div className={cn("grid grid-cols-1 lg:grid-cols-2", SPACING.grid.formFields)}>
        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="address" className={TYPOGRAPHY.label.default}>Address</Label>
          <Input
            id="address"
            value={formData.address}
            onChange={(e) => onFieldChange('address', e.target.value)}
            placeholder="Street address"
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size)}
          />
        </div>
        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="city" className={TYPOGRAPHY.label.default}>City</Label>
          <Input
            id="city"
            value={formData.city}
            onChange={(e) => onFieldChange('city', e.target.value)}
            placeholder="City"
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size)}
          />
        </div>
        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="state" className={TYPOGRAPHY.label.default}>State</Label>
          <Input
            id="state"
            value={formData.state}
            onChange={(e) => onFieldChange('state', e.target.value)}
            placeholder="State"
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size)}
          />
        </div>
        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="country" className={TYPOGRAPHY.label.default}>Country</Label>
          <Input
            id="country"
            value={formData.country}
            onChange={(e) => onFieldChange('country', e.target.value)}
            placeholder="Country"
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size)}
          />
        </div>
        <div className={SPACING.form.betweenLabelAndInput}>
          <Label htmlFor="postalCode" className={TYPOGRAPHY.label.default}>Postal Code</Label>
          <Input
            id="postalCode"
            value={formData.postalCode}
            onChange={(e) => onFieldChange('postalCode', e.target.value)}
            placeholder="Postal/ZIP code"
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size)}
          />
        </div>
        <div className={cn(SPACING.form.betweenLabelAndInput, "lg:col-span-2")}>
          <Label htmlFor="bio" className={TYPOGRAPHY.label.default}>Bio</Label>
          <Input
            id="bio"
            value={formData.bio}
            onChange={(e) => onFieldChange('bio', e.target.value)}
            placeholder="A short bio about you"
            className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size)}
          />
        </div>
      </div>

      {/* Social Media Links (Smart input) */}
      <div className={cn(SPACING.form.betweenFields, PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
        <h4 className={TYPOGRAPHY.heading.subsection}>Social Media Links</h4>
        <div className={SPACING.form.betweenFields}>
          <div className={SPACING.form.betweenLabelAndInput}>
            <Label htmlFor="social-link" className={TYPOGRAPHY.label.default}>Paste a social link</Label>
            <div className={cn("flex", SPACING.flex.tight)}>
              <Input
                id="social-link"
                type="url"
                value={socialLink}
                onChange={(e) => setSocialLink(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSocialLinkSubmit() } }}
                placeholder="Paste LinkedIn, Twitter/X, GitHub, or Website URL and press Enter"
                className={cn(TYPOGRAPHY.input.height, TYPOGRAPHY.input.size, "flex-1")}
              />
              <button
                type="button"
                className={cn("px-6 py-3 font-semibold bg-primary text-primary-foreground hover:bg-primary/90 transition-colors", BORDER_RADIUS.default, TYPOGRAPHY.input.size)}
                onClick={handleSocialLinkSubmit}
              >
                Add
              </button>
            </div>
            <p className={TYPOGRAPHY.body.muted}>We&apos;ll detect the platform and place it in the right field.</p>
          </div>

          <div className={SPACING.form.betweenLabelAndInput}>
            <Label className={TYPOGRAPHY.label.default}>Added links</Label>
            <div className={cn("flex flex-wrap", SPACING.flex.default)}>
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
                <p className={TYPOGRAPHY.body.muted}>No links added yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
