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
    <div className="space-y-8">
      <div className="flex items-center justify-between p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
        <div>
          <h3 className="text-xl font-bold text-foreground">
            Basic Information
            {isEditing && (
              <span className="ml-3 text-sm text-primary font-medium bg-primary/10 px-2 py-1 rounded-full">(Editing)</span>
            )}
          </h3>
          <p className="text-muted-foreground mt-1">Manage your personal details and contact information</p>
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
        <div className="space-y-6">
          <div className="flex items-center space-x-6 p-6 bg-gradient-to-r from-card/50 to-card/30 rounded-xl border border-border/50">
            <Avatar className="h-20 w-20 ring-4 ring-primary/20 shadow-lg">
              <AvatarImage src={profile?.avatar_url || user.avatar} alt={user.name} />
              <AvatarFallback className="bg-gradient-primary text-primary-foreground text-xl font-bold">
                {getInitials(user.name)}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1">
              <h4 className="text-2xl font-bold text-foreground">{profile?.full_name || user.name}</h4>
              <p className="text-muted-foreground text-lg">{user.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <div className="w-2 h-2 bg-primary rounded-full"></div>
                <span className="text-sm text-muted-foreground capitalize font-medium">{user.role}</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
              <p className="text-sm font-semibold text-muted-foreground mb-2">Address</p>
              <p className="text-base text-foreground">{profile ? [profile.address, profile.city, profile.state, profile.country].filter(Boolean).join(", ") : 'Not specified'}</p>
            </div>
            <div className="p-4 bg-muted/30 rounded-lg border border-border/50">
              <p className="text-sm font-semibold text-muted-foreground mb-2">Phone</p>
              <p className="text-base text-foreground">{profile?.phone || 'Not specified'}</p>
            </div>
          </div>

          {(profile?.linkedin_url || profile?.twitter_url || profile?.github_url || profile?.website) && (
            <div className="p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
              <p className="text-lg font-semibold text-muted-foreground mb-4">Social Media</p>
              <div className="flex flex-wrap gap-3">
                {profile?.linkedin_url && (
                  <a 
                    href={profile.linkedin_url} 
                    target="_blank" 
                    rel="noopener noreferrer" 
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-950/30 transition-all duration-200 hover:scale-105"
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
                    className="inline-flex items-center gap-2 px-4 py-2 bg-sky-50 dark:bg-sky-950/20 text-sky-700 dark:text-sky-300 rounded-lg hover:bg-sky-100 dark:hover:bg-sky-950/30 transition-all duration-200 hover:scale-105"
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
                    className="inline-flex items-center gap-2 px-4 py-2 bg-gray-50 dark:bg-gray-950/20 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-950/30 transition-all duration-200 hover:scale-105"
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
                    className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-all duration-200 hover:scale-105"
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
    <div className="space-y-8">
      <div className="flex items-center justify-between p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
        <div>
          <h3 className="text-xl font-bold text-foreground">
            Role Management
            {isEditing && (
              <span className="ml-3 text-sm text-primary font-medium bg-primary/10 px-2 py-1 rounded-full">(Editing)</span>
            )}
          </h3>
          <p className="text-muted-foreground mt-1">Configure your roles and permissions within the platform</p>
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
        <div className="space-y-6">
          <div className="p-6 bg-gradient-to-r from-card/50 to-card/30 rounded-xl border border-border/50">
            <p className="text-lg font-semibold text-muted-foreground mb-4">Current Role</p>
            <div className="flex items-center gap-4">
              {user.role && currentRole && (
                <>
                  <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
                    <currentRole.icon className="h-6 w-6 text-primary" />
                  </div>
                  <div>
                    <span className="text-xl font-bold text-foreground">{currentRole.title}</span>
                    {currentRole && (
                      <p className="text-muted-foreground mt-1">{currentRole.description}</p>
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                {pairs.map(([label, value]) => (
                  <div key={label} className="p-4 bg-muted/30 rounded-lg border border-border/50">
                    <p className="text-sm font-semibold text-muted-foreground mb-2">{label}</p>
                    <p className="text-base text-foreground">{value ?? 'Not specified'}</p>
                  </div>
                ))}
              </div>
            )

            if (roleName === 'teacher') {
              return (
                <div className="p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
                  <p className="text-lg font-semibold text-muted-foreground mb-4">Teacher Details</p>
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
                <div className="p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
                  <p className="text-lg font-semibold text-muted-foreground mb-4">Student Details</p>
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
                <div className="p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
                  <p className="text-lg font-semibold text-muted-foreground mb-4">Organization Admin Details</p>
                  {asPairs([
                    ['Organization', data.org_name],
                    ['Departments', data.departments],
                  ])}
                </div>
              )
            }

            if (roleName === 'super_admin') {
              return (
                <div className="p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
                  <p className="text-lg font-semibold text-muted-foreground mb-4">Super Admin Details</p>
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
            <div className="p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
              <p className="text-lg font-semibold text-muted-foreground mb-4">Switch Role</p>
              <RoleSwitcher
                roles={roles}
                activeRole={activeRole || user.role}
                onRoleSwitch={onSwitchRole}
              />
            </div>
          )}

          {user.roleData && Object.keys(user.roleData).length > 0 && (
            <div className="p-6 bg-gradient-to-r from-muted/30 to-muted/10 rounded-xl border border-border/50">
              <p className="text-lg font-semibold text-muted-foreground mb-4">Role Details</p>
              <div className="space-y-3">
                {Object.entries(user.roleData).map(([key, value]) => (
                  <div key={key} className="flex justify-between items-center p-3 bg-muted/50 rounded-lg">
                    <span className="text-sm font-medium text-muted-foreground capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}:
                    </span>
                    <span className="text-sm font-semibold text-foreground">{String(value)}</span>
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
        <div className="flex items-center justify-between p-8 border-b border-border/50 bg-gradient-to-r from-card/50 to-card/30">
          <div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text text-transparent">
              Profile Management
            </h2>
            <p className="text-muted-foreground mt-1">Manage your personal information and role settings</p>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={onClose}
            className="hover:bg-muted/50 transition-all duration-200 hover:scale-105"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-8 pb-10">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-8 bg-muted/30 p-1 rounded-xl">
              <TabsTrigger 
                value="basic-info" 
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all duration-200 rounded-lg"
              >
                Basic Info
              </TabsTrigger>
              <TabsTrigger 
                value="role-management"
                className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground transition-all duration-200 rounded-lg"
              >
                Role Management
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="basic-info" className="space-y-8 animate-fade-in">
              {renderBasicInfo()}
            </TabsContent>
            
            <TabsContent value="role-management" className="space-y-8 animate-fade-in">
              {renderRoleManagement()}
            </TabsContent>
          </Tabs>
        </div>
      </GlassCard>
    </div>
  )
}
