"use client"

import * as React from "react"
import { Input } from "../../app/components/ui/input"
import { Label } from "../../app/components/ui/label"
import { ProfilePictureUpload } from "./ProfilePictureUpload"
import { FormData, ValidationErrors } from "../../types"
import { cn } from "../../app/lib/utils"

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

      {/* Social Media Links */}
      <div className="space-y-6">
        <h4 className="text-lg font-semibold">Social Media Links</h4>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="linkedin">LinkedIn</Label>
            <Input
              id="linkedin"
              type="url"
              value={formData.linkedin}
              onChange={(e) => onFieldChange('linkedin', e.target.value)}
              className={cn(errors.linkedin && "border-destructive")}
              placeholder="https://linkedin.com/in/yourprofile"
            />
            {errors.linkedin && (
              <p className="text-sm text-destructive">{errors.linkedin}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="twitter">Twitter</Label>
            <Input
              id="twitter"
              type="url"
              value={formData.twitter}
              onChange={(e) => onFieldChange('twitter', e.target.value)}
              className={cn(errors.twitter && "border-destructive")}
              placeholder="https://twitter.com/yourprofile"
            />
            {errors.twitter && (
              <p className="text-sm text-destructive">{errors.twitter}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="github">GitHub</Label>
            <Input
              id="github"
              type="url"
              value={formData.github}
              onChange={(e) => onFieldChange('github', e.target.value)}
              className={cn(errors.github && "border-destructive")}
              placeholder="https://github.com/yourprofile"
            />
            {errors.github && (
              <p className="text-sm text-destructive">{errors.github}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="website">Website</Label>
            <Input
              id="website"
              type="url"
              value={formData.website}
              onChange={(e) => onFieldChange('website', e.target.value)}
              className={cn(errors.website && "border-destructive")}
              placeholder="https://yourwebsite.com"
            />
            {errors.website && (
              <p className="text-sm text-destructive">{errors.website}</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
