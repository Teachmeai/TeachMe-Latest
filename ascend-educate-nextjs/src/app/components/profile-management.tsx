"use client"

import * as React from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { GlassCard } from "@/components/ui/glass-card"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
// lightweight props; avoid external type deps
import { useProfileForm } from "../../hooks/useProfileForm"
import { BasicInfoForm } from "../../components/forms/BasicInfoForm"
import { RoleManagementForm } from "../../components/forms/RoleManagementForm"
import { FormActions } from "../../components/forms/FormActions"
import { ProfileCompletion } from "../../components/profile/ProfileCompletion"
import { getRoleById } from "../../config/roles"
import { cn } from "@/lib/utils"
import { RoleSwitcher } from "../../components/role-switcher"

export function ProfileManagement({ 
  user, 
  onProfileUpdate, 
  onClose, 
  className,
  roles,
  activeRole,
  activeOrgId,
  onSwitchRole
}: {
  user: any
  onProfileUpdate?: (u: any) => void
  onClose?: () => void
  className?: string
  roles?: Array<{ scope: 'global' | 'org'; role: string; org_id?: string; org_name?: string }>
  activeRole?: string
  activeOrgId?: string
  onSwitchRole?: (role: string, orgId?: string) => Promise<boolean> | void
}) {
  const {
    isEditing,
    formData,
    selectedRole,
    roleData,
    errors,
    handleEdit,
    handleCancel,
    handleSave,
    handleFieldChange,
    handleRoleFieldChange,
    handleRoleChange
  } = useProfileForm({ initialUser: user, onProfileUpdate })

  const currentRole = getRoleById(selectedRole)

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map(n => n[0])
      .join("")
      .toUpperCase()
  }

  const renderBasicInfo = () => (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Basic Information
          {isEditing && (
            <span className="ml-2 text-sm text-primary font-normal">(Editing)</span>
          )}
        </h3>
        <FormActions
          isEditing={isEditing}
          errors={errors}
          onEdit={handleEdit}
          onCancel={handleCancel}
          onSave={handleSave}
        />
      </div>

      {isEditing ? (
        <BasicInfoForm
          formData={formData}
          errors={errors}
          onFieldChange={handleFieldChange}
          onImageChange={(imageUrl) => handleFieldChange('profilePicture', imageUrl)}
        />
      ) : (
        <div className="space-y-4">
          <div className="flex items-center space-x-4">
            <Avatar className="h-16 w-16">
              <AvatarImage src={user.avatar} alt={user.name} />
              <AvatarFallback className="bg-primary/10 text-primary text-lg">
                {getInitials(user.name)}
              </AvatarFallback>
            </Avatar>
            <div>
              <h4 className="text-lg font-semibold">{user.name}</h4>
              <p className="text-muted-foreground">{user.email}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Institute</p>
              <p className="text-sm">{user.institute || 'Not specified'}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Phone</p>
              <p className="text-sm">{user.phoneNumber || 'Not specified'}</p>
            </div>
          </div>

          {user.socialMedia && Object.values(user.socialMedia).some(value => value) && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Social Media</p>
              <div className="flex flex-wrap gap-2">
                {user.socialMedia.linkedin && (
                  <a href={user.socialMedia.linkedin} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                    LinkedIn
                  </a>
                )}
                {user.socialMedia.twitter && (
                  <a href={user.socialMedia.twitter} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                    Twitter
                  </a>
                )}
                {user.socialMedia.github && (
                  <a href={user.socialMedia.github} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
                    GitHub
                  </a>
                )}
                {user.socialMedia.website && (
                  <a href={user.socialMedia.website} target="_blank" rel="noopener noreferrer" className="text-sm text-blue-600 hover:underline">
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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">
          Role Management
          {isEditing && (
            <span className="ml-2 text-sm text-primary font-normal">(Editing)</span>
          )}
        </h3>
        <FormActions
          isEditing={isEditing}
          errors={errors}
          onEdit={handleEdit}
          onCancel={handleCancel}
          onSave={handleSave}
        />
      </div>

      {isEditing ? (
        <RoleManagementForm
          selectedRole={selectedRole}
          roleData={roleData}
          errors={errors}
          onRoleChange={handleRoleChange}
          onRoleFieldChange={handleRoleFieldChange}
        />
      ) : (
        <div className="space-y-4">
          <div>
            <p className="text-sm font-medium text-muted-foreground">Current Role</p>
            <div className="flex items-center gap-2 mt-1">
              {user.role && currentRole && (
                <>
                  <currentRole.icon className="h-4 w-4" />
                  <span className="text-sm font-medium">{currentRole.title}</span>
                </>
              )}
            </div>
            {currentRole && (
              <p className="text-sm text-muted-foreground mt-1">{currentRole.description}</p>
            )}
          </div>

          {/* Role-specific fields (display only) */}
          {(() => {
            const roleName = (activeRole || user.role || "").toLowerCase()
            const data = user.roleData || {}

            const asPairs = (pairs: Array<[string, any]>) => (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                {pairs.map(([label, value]) => (
                  <div key={label}>
                    <p className="text-sm font-medium text-muted-foreground">{label}</p>
                    <p className="text-sm">{value ?? 'Not specified'}</p>
                  </div>
                ))}
              </div>
            )

            if (roleName === 'teacher') {
              return (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">Teacher Details</p>
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
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">Student Details</p>
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
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">Organization Admin Details</p>
                  {asPairs([
                    ['Organization', data.org_name],
                    ['Departments', data.departments],
                  ])}
                </div>
              )
            }

            if (roleName === 'super_admin') {
              return (
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-1">Super Admin Details</p>
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
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Switch Role</p>
              <RoleSwitcher
                roles={roles}
                activeRole={activeRole || user.role}
                activeOrgId={activeOrgId}
                onRoleSwitch={onSwitchRole}
              />
            </div>
          )}

          {user.roleData && Object.keys(user.roleData).length > 0 && (
            <div>
              <p className="text-sm font-medium text-muted-foreground mb-2">Role Details</p>
              <div className="space-y-2">
                {Object.entries(user.roleData).map(([key, value]) => (
                  <div key={key} className="flex justify-between">
                    <span className="text-sm text-muted-foreground capitalize">
                      {key.replace(/([A-Z])/g, ' $1').trim()}:
                    </span>
                    <span className="text-sm">{value}</span>
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
    <div className={cn("fixed inset-0 z-50 bg-background/80 backdrop-blur-sm flex items-center justify-center p-4", className)}>
      <GlassCard className="w-full max-w-5xl max-h-[95vh] overflow-hidden flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold">Profile Management</h2>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 pb-8">
          {/* Profile Completion Progress */}
          <ProfileCompletion profile={user} className="mb-6" />

          <Tabs defaultValue="basic-info" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="basic-info">Basic Info</TabsTrigger>
              <TabsTrigger value="role-management">Role Management</TabsTrigger>
            </TabsList>
            
            <TabsContent value="basic-info" className="space-y-6">
              {renderBasicInfo()}
            </TabsContent>
            
            <TabsContent value="role-management" className="space-y-6">
              {renderRoleManagement()}
            </TabsContent>
          </Tabs>
        </div>
      </GlassCard>
    </div>
  )
}
