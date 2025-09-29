"use client"

import * as React from "react"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { ROLES, getRoleById } from "@/config/roles"
import { ValidationErrors } from "@/types"
import { cn } from "@/lib/utils"
import { backend } from "@/lib/backend"
import { useToast } from "@/hooks/use-toast"

interface RoleManagementFormProps {
  selectedRole: string
  roleData: Record<string, string>
  errors: ValidationErrors
  onRoleFieldChange: (field: string, value: string) => void
  className?: string
  hasGlobalRole?: boolean
  userRoles?: Array<{ scope: 'global' | 'org'; role: string; org_id?: string; org_name?: string }>
  onRoleAssigned?: () => void
}

export function RoleManagementForm({
  selectedRole,
  roleData,
  errors,
  onRoleFieldChange,
  className,
  hasGlobalRole = true,
  userRoles = [],
  onRoleAssigned
}: RoleManagementFormProps) {
  const currentRole = getRoleById(selectedRole)
  const [isAssigningRole, setIsAssigningRole] = React.useState(false)
  const { toast } = useToast()

  const handleAssignGlobalRole = async (role: 'student' | 'teacher') => {
    setIsAssigningRole(true)
    try {
      const response = await backend.assignGlobalRole(role)
      if (response.ok) {
        toast({
          title: "Role Assigned",
          description: response.data?.message || `Successfully assigned ${role} role`,
        })
        onRoleAssigned?.()
      } else {
        toast({
          title: "Error",
          description: response.error || "Failed to assign role",
          variant: "destructive"
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to assign role. Please try again.",
        variant: "destructive"
      })
    } finally {
      setIsAssigningRole(false)
    }
  }

  // Check which global roles the user currently has
  const currentGlobalRoles = userRoles.filter(role => role.scope === 'global').map(role => role.role)
  const hasStudentRole = currentGlobalRoles.includes('student')
  const hasTeacherRole = currentGlobalRoles.includes('teacher')
  
  // Show assignment options if user doesn't have a particular global role
  const showStudentOption = !hasStudentRole
  const showTeacherOption = !hasTeacherRole
  const showGlobalRoleSection = showStudentOption || showTeacherOption

  return (
    <div className={cn("space-y-6", className)}>
      {/* Global Role Assignment Section */}
      {showGlobalRoleSection && (
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">Global Role Options</h4>
          <p className="text-sm text-blue-700 mb-4">
            {!hasGlobalRole 
              ? "You don't have a global role yet. Choose to become a global student or teacher to access platform features."
              : "You can add additional global roles to expand your platform access."
            }
          </p>
          <div className="flex gap-2">
            {showStudentOption && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleAssignGlobalRole('student')}
                disabled={isAssigningRole}
                className="border-blue-300 text-blue-700 hover:bg-blue-100"
              >
                {hasGlobalRole ? 'Add Student Role' : 'Become Student'}
              </Button>
            )}
            {showTeacherOption && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleAssignGlobalRole('teacher')}
                disabled={isAssigningRole}
                className="border-blue-300 text-blue-700 hover:bg-blue-100"
              >
                {hasGlobalRole ? 'Add Teacher Role' : 'Become Teacher'}
              </Button>
            )}
          </div>
        </div>
      )}

      {/* Role Description */}
      {currentRole && (
        <div className="p-4 bg-muted/50 rounded-lg">
          <h4 className="font-medium text-sm mb-2">{currentRole.title}</h4>
          <p className="text-sm text-muted-foreground">{currentRole.description}</p>
        </div>
      )}

      {/* Role-specific Fields */}
      {currentRole && (
        <div className="space-y-4">
          <h4 className="text-sm font-medium">Role-specific Information</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {currentRole.fields.map((field) => (
              <div key={field.name} className="space-y-2">
                <Label htmlFor={field.name}>
                  {field.label} {field.required && '*'}
                </Label>
                
                {field.type === 'textarea' ? (
                  <Textarea
                    id={field.name}
                    value={roleData[field.name] || ''}
                    onChange={(e) => onRoleFieldChange(field.name, e.target.value)}
                    className={cn(errors[field.name] && "border-destructive")}
                    placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}`}
                    rows={3}
                  />
                ) : field.type === 'select' ? (
                  <Select
                    value={roleData[field.name] || ''}
                    onValueChange={(value) => onRoleFieldChange(field.name, value)}
                  >
                    <SelectTrigger className={cn(errors[field.name] && "border-destructive")}>
                      <SelectValue placeholder={field.placeholder || `Select ${field.label.toLowerCase()}`} />
                    </SelectTrigger>
                    <SelectContent>
                      {field.options?.map((option) => (
                        <SelectItem key={option} value={option}>
                          {option}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    id={field.name}
                    type={field.type}
                    value={roleData[field.name] || ''}
                    onChange={(e) => onRoleFieldChange(field.name, e.target.value)}
                    className={cn(errors[field.name] && "border-destructive")}
                    placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}`}
                  />
                )}
                
                {errors[field.name] && (
                  <p className="text-sm text-destructive">{errors[field.name]}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
