"use client"

import * as React from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
// lightweight props; avoid external type deps
import { useProfileForm } from "@/hooks/useProfileForm"
import { BasicInfoForm } from "@/components/forms/BasicInfoForm"
import { RoleManagementForm } from "@/components/forms/RoleManagementForm"
import { FormActions } from "@/components/forms/FormActions"
// Removed ProfileCompletion import - progress bar functionality removed
import { getRoleById } from "@/config/roles"
import { cn } from "@/lib/utils"
import { RoleSwitcher } from "@/components/features/role-switcher"
import { useEffect, useState } from "react"
import { backend } from "@/lib/backend"
import type { UserProfile } from "@/types"
import type { BackendProfile } from "@/lib/backend"
import { useTabState } from "@/hooks/useTabState"
import { SPACING, PADDING, TYPOGRAPHY, BACKGROUNDS, BORDERS, BORDER_RADIUS } from "@/config/design-tokens"

export function ProfileManagement({ 
  user, 
  onProfileUpdate, 
  onClose, 
  className,
  roles,
  activeRole,
  onSwitchRole,
  onRefreshSession
}: {
  user: UserProfile
  onProfileUpdate?: (u: UserProfile) => void
  onClose?: () => void
  className?: string
  roles?: Array<{ scope: 'global' | 'org'; role: string; org_id?: string; org_name?: string }>
  activeRole?: string
  onSwitchRole?: (role: string, orgId?: string) => Promise<boolean>
  onRefreshSession?: () => Promise<void>
}) {
  const [profile, setProfile] = useState<BackendProfile | null>(null)
  const [activeTab, setActiveTab] = useTabState("profile-management-tab", "basic-info")

  useEffect(() => {
    let mounted = true
    const load = async () => {
      const resp = await backend.getProfile()
      if (mounted && resp.ok && resp.data) {
        setProfile(resp.data)
      }
    }
    load()
    return () => { mounted = false }
  }, [])

  const {
    isEditing,
    isSaving,
    saveSuccess,
    formData,
    selectedRole,
    roleData,
    basicErrors,
    roleErrors,
    handleEdit,
    handleCancel,
    handleSaveBasic,
    handleSaveRole,
    handleFieldChange,
    handleRoleFieldChange
  } = useProfileForm({ 
    initialUser: user, 
    onProfileUpdate, 
    activeRole, 
    initialProfile: profile ? {
      full_name: profile.full_name,
      avatar_url: profile.avatar_url,
      phone: profile.phone,
      address: profile.address,
      city: profile.city,
      state: profile.state,
      country: profile.country,
      postal_code: profile.postal_code,
      bio: profile.bio,
      website: profile.website,
      linkedin_url: profile.linkedin_url,
      twitter_url: profile.twitter_url,
      github_url: profile.github_url,
    } : undefined 
  })

  const currentRole = getRoleById(selectedRole)

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map(n => n[0])
      .join("")
      .toUpperCase()
  }

  const renderBasicInfo = () => (
    <div className={SPACING.form.betweenSections}>
      <div className="space-y-4">
        <div className="pb-4 border-b border-border/20">
          <div className="flex items-center gap-3 mb-1">
            <h3 className={cn(TYPOGRAPHY.heading.section, "text-foreground")}>
              Basic Information
            </h3>
            {isEditing && (
              <span className={cn("text-primary font-medium bg-primary/10 px-2.5 py-1", BORDER_RADIUS.full, TYPOGRAPHY.body.small)}>
                Editing
              </span>
            )}
          </div>
          <p className={TYPOGRAPHY.body.muted}>Manage your personal details and contact information</p>
        </div>
        <FormActions
          isEditing={isEditing}
          isSaving={isSaving}
          saveSuccess={saveSuccess}
          errors={basicErrors}
          onEdit={handleEdit}
          onCancel={handleCancel}
          onSave={handleSaveBasic}
        />
      </div>

      {isEditing ? (
        <BasicInfoForm
          formData={formData}
          errors={basicErrors}
          onFieldChange={handleFieldChange}
          onImageChange={(imageUrl) => handleFieldChange('profilePicture', imageUrl)}
        />
      ) : (
        <div className={SPACING.form.betweenFields}>
          <div className={cn("flex items-center gap-6", PADDING.container.medium, BACKGROUNDS.card.subtle, BORDER_RADIUS.default, BORDERS.default)}>
            <Avatar className="h-20 w-20 ring-2 ring-primary/20 shadow-sm">
              <AvatarImage src={profile?.avatar_url || user.avatar} alt={user.name} />
              <AvatarFallback className="bg-gradient-primary text-primary-foreground text-xl font-bold">
                {getInitials(user.name)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <h4 className="text-xl font-bold text-foreground">{profile?.full_name || user.name}</h4>
              <p className={cn(TYPOGRAPHY.body.default, "text-muted-foreground")}>{user.email}</p>
              <div className={cn("flex items-center mt-2", SPACING.flex.tight)}>
                <div className="w-2 h-2 bg-primary rounded-full"></div>
                <span className={cn(TYPOGRAPHY.body.small, "text-muted-foreground capitalize font-medium")}>{user.role}</span>
              </div>
            </div>
          </div>

          <div className={cn("grid grid-cols-1 md:grid-cols-2", SPACING.grid.cards)}>
            <div className={cn(PADDING.card, BACKGROUNDS.muted.light, BORDER_RADIUS.default, BORDERS.default)}>
              <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-2")}>Address</p>
              <p className={cn(TYPOGRAPHY.body.default, "leading-relaxed break-words")}>{profile ? [profile.address, profile.city, profile.state, profile.country].filter(Boolean).join(", ") : 'Not specified'}</p>  
            </div>
            <div className={cn(PADDING.card, BACKGROUNDS.muted.light, BORDER_RADIUS.default, BORDERS.default)}>
              <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-2")}>Phone</p>
              <p className={cn(TYPOGRAPHY.body.default, "leading-relaxed")}>{profile?.phone || 'Not specified'}</p>
            </div>
          </div>

          {(profile?.linkedin_url || profile?.twitter_url || profile?.github_url || profile?.website) && (
            <div className={cn(PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
              <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Social Media</p>
              <div className={cn("flex flex-wrap", SPACING.flex.tight)}>
                {profile?.linkedin_url && (
                  <a 
                    href={profile.linkedin_url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={cn("inline-flex items-center px-4 py-2 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-950/30 transition-colors", BORDER_RADIUS.default, SPACING.flex.tight)}
                  >
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    LinkedIn
                  </a>
                )}
                {profile?.twitter_url && (
                  <a 
                    href={profile.twitter_url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={cn("inline-flex items-center px-4 py-2 bg-sky-50 dark:bg-sky-950/20 text-sky-700 dark:text-sky-300 hover:bg-sky-100 dark:hover:bg-sky-950/30 transition-colors", BORDER_RADIUS.default, SPACING.flex.tight)}
                  >
                    <div className="w-2 h-2 bg-sky-500 rounded-full"></div>
                    Twitter
                  </a>
                )}
                {profile?.github_url && (
                  <a 
                    href={profile.github_url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={cn("inline-flex items-center px-4 py-2 bg-gray-50 dark:bg-gray-950/20 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-950/30 transition-colors", BORDER_RADIUS.default, SPACING.flex.tight)}
                  >
                    <div className="w-2 h-2 bg-gray-500 rounded-full"></div>
                    GitHub
                  </a>
                )}
                {profile?.website && (
                  <a 
                    href={profile.website} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className={cn("inline-flex items-center px-4 py-2 bg-primary/10 text-primary hover:bg-primary/20 transition-colors", BORDER_RADIUS.default, SPACING.flex.tight)}
                  >
                    <div className="w-2 h-2 bg-primary rounded-full"></div>
                    Website
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )

  const renderRoleManagement = () => (
    <div className={SPACING.form.betweenSections}>
      <div className="space-y-4">
        <div className="pb-4 border-b border-border/20">
          <div className="flex items-center gap-3 mb-1">
            <h3 className={cn(TYPOGRAPHY.heading.section, "text-foreground")}>
              Role Management
            </h3>
            {isEditing && (
              <span className={cn("text-primary font-medium bg-primary/10 px-2.5 py-1", BORDER_RADIUS.full, TYPOGRAPHY.body.small)}>
                Editing
              </span>
            )}
          </div>
          <p className={TYPOGRAPHY.body.muted}>Configure your roles and permissions within the platform</p>
        </div>
        <FormActions
          isEditing={isEditing}
          isSaving={isSaving}
          saveSuccess={saveSuccess}
          errors={roleErrors}
          onEdit={handleEdit}
          onCancel={handleCancel}
          onSave={handleSaveRole}
        />
      </div>

      {isEditing ? (
        <RoleManagementForm
          selectedRole={selectedRole}
          roleData={roleData}
          errors={roleErrors}
          onRoleFieldChange={handleRoleFieldChange}
          hasGlobalRole={roles?.some(r => r.scope === 'global')}
          userRoles={roles}
          onRoleAssigned={async () => {
            // Refresh the session to get updated roles
            if (onRefreshSession) {
              await onRefreshSession()
            }
            // Also trigger a profile update if available
            if (onProfileUpdate) {
              onProfileUpdate({ ...user, role: activeRole })
            }
          }}
        />
      ) : (
        <div className={SPACING.form.betweenFields}>
            <div className={cn(PADDING.container.medium, BACKGROUNDS.card.subtle, BORDER_RADIUS.default, BORDERS.default)}>
              <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Current Role</p>
              <div className="flex items-center gap-4">
              {user.role && currentRole && (
                <>
                  <div className={cn("w-12 h-12 bg-primary/10 flex items-center justify-center", BORDER_RADIUS.default)}>
                    <currentRole.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <h4 className="text-lg font-bold text-foreground leading-tight">{currentRole.title}</h4>
                    {currentRole && (
                      <p className={cn(TYPOGRAPHY.body.muted, "mt-1.5 leading-relaxed")}>{currentRole.description}</p>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Role-specific fields (display only) */}
          {(() => {
            const roleName = (activeRole || user.role || "").toLowerCase()
            const data = user.roleData || {}

            const asPairs = (pairs: Array<[string, string]>) => (
              <div className={cn("grid grid-cols-1 md:grid-cols-2 mt-4", SPACING.grid.formFields)}>
                {pairs.map(([label, value]) => (
                  <div key={label} className={cn(PADDING.card, BACKGROUNDS.muted.light, BORDER_RADIUS.default, BORDERS.default)}>
                    <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-2")}>{label}</p>
                    <p className={cn(TYPOGRAPHY.body.default, "leading-relaxed break-words")}>{value ?? 'Not specified'}</p>
                  </div>
                ))}
              </div>
            )

            if (roleName === 'teacher') {
              return (
                <div className={cn(PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
                  <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Teacher Details</p>
                  {asPairs([
                    ['Courses Taught', data.courses || data.coursesTaught],
                    ['Subjects', data.subjects],
                    ['Experience (years)', data.experience],
                  ])}
                </div>
              )
            }

            if (roleName === 'student') {
              return (
                <div className={cn(PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
                  <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Student Details</p>
                  {asPairs([
                    ['Courses Enrolled', data.enrolled_courses || data.coursesEnrolled],
                    ['Grade / Year', data.grade || data.year],
                    ['Interests', data.interests],
                  ])}
                </div>
              )
            }

            if (roleName === 'organization_admin') {
              return (
                <div className={cn(PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
                  <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Organization Admin Details</p>
                  {asPairs([
                    ['Organization', data.org_name],
                    ['Departments', data.departments],
                  ])}
                </div>
              )
            }

            if (roleName === 'super_admin') {
              return (
                <div className={cn(PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
                  <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Super Admin Details</p>
                  {asPairs([
                    ['Scope', 'Global'],
                  ])}
                </div>
              )
            }

            return null
          })()}

          {/* Role switching inside Profile - preserve existing style but move control here */}
          {roles && roles.length > 0 && (
            <div className={cn(PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
              <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Switch Role</p>
              <RoleSwitcher
                roles={roles}
                activeRole={activeRole || user.role}
                onRoleSwitch={onSwitchRole}
              />
            </div>
          )}

          {user.roleData && Object.keys(user.roleData).length > 0 && (
            <div className={cn(PADDING.container.medium, BACKGROUNDS.muted.subtle, BORDER_RADIUS.default)}>
              <p className={cn(TYPOGRAPHY.heading.card, "text-muted-foreground mb-4")}>Role Details</p>
              <div className="space-y-2">
                {Object.entries(user.roleData).map(([key, value]) => (
                  <div key={key} className={cn("flex justify-between items-center gap-4 bg-muted/50", PADDING.card, BORDER_RADIUS.default)}>
                    <span className={cn(TYPOGRAPHY.label.default, "text-muted-foreground capitalize flex-shrink-0")}>
                      {key.replace(/([A-Z])/g, ' $1').trim()}:
                    </span>
                    <span className={cn(TYPOGRAPHY.label.default, "font-semibold text-foreground text-right break-words")}>{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )

  return (
    <div className={cn("fixed inset-0 z-50 bg-background/90 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in", className)}>
      <GlassCard className="w-full max-w-6xl max-h-[95vh] overflow-hidden flex flex-col shadow-2xl animate-scale-in">
        <div className={cn("flex items-center justify-between border-b border-border/50", PADDING.modalHeader, BACKGROUNDS.card.subtle)}>
          <div>
            <h2 className={cn(TYPOGRAPHY.heading.page, "text-foreground")}>
              Profile Management
            </h2>
            <p className={cn(TYPOGRAPHY.body.muted, "mt-1")}>Manage your personal information and role settings</p>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="hover:bg-muted/50 transition-colors"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className={cn("flex-1 overflow-y-auto", PADDING.modalContent)}>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className={cn("grid w-full grid-cols-2 mb-6 bg-muted/30 p-1", BORDER_RADIUS.default)}>
              <TabsTrigger 
                value="basic-info" 
                className={cn("data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-colors", BORDER_RADIUS.default)}
              >
                Basic Info
              </TabsTrigger>
              <TabsTrigger 
                value="role-management"
                className={cn("data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-colors", BORDER_RADIUS.default)}
              >
                Role Management
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="basic-info" className="animate-fade-in">
              {renderBasicInfo()}
            </TabsContent>
            
            <TabsContent value="role-management" className="animate-fade-in">
              {renderRoleManagement()}
            </TabsContent>
          </Tabs>
        </div>
      </GlassCard>
    </div>
  )
}
