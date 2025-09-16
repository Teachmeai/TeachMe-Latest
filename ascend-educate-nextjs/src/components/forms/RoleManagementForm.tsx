"use client"

import * as React from "react"
import { Input } from "../../app/components/ui/input"
import { Label } from "../../app/components/ui/label"
import { Textarea } from "../../app/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../app/components/ui/select"
import { ROLES, getRoleById } from "../../config/roles"
import { ValidationErrors } from "../../types"
import { cn } from "../../app/lib/utils"

interface RoleManagementFormProps {
  selectedRole: string
  roleData: Record<string, string>
  errors: ValidationErrors
  onRoleChange: (roleId: string) => void
  onRoleFieldChange: (field: string, value: string) => void
  className?: string
}

export function RoleManagementForm({
  selectedRole,
  roleData,
  errors,
  onRoleChange,
  onRoleFieldChange,
  className
}: RoleManagementFormProps) {
  const currentRole = getRoleById(selectedRole)

  return (
    <div className={cn("space-y-6", className)}>
      {/* Role Selection */}
      <div className="space-y-2">
        <Label htmlFor="role">Select Your Role *</Label>
        <Select value={selectedRole} onValueChange={onRoleChange}>
          <SelectTrigger className={cn(errors.role && "border-destructive")}>
            <SelectValue placeholder="Choose your role" />
          </SelectTrigger>
          <SelectContent>
            {ROLES.map((role) => (
              <SelectItem key={role.id} value={role.id}>
                <div className="flex items-center gap-2">
                  <role.icon className="h-4 w-4" />
                  {role.title}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {errors.role && (
          <p className="text-sm text-destructive">{errors.role}</p>
        )}
      </div>

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
