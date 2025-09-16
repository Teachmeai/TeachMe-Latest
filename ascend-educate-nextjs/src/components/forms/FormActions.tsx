"use client"

import * as React from "react"
import { Save, X } from "lucide-react"
import { Button } from "../../app/components/ui/button"
import { ValidationErrors } from "../../types"
import { cn } from "../../app/lib/utils"

interface FormActionsProps {
  isEditing: boolean
  errors: ValidationErrors
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
  className?: string
}

export function FormActions({
  isEditing,
  errors,
  onEdit,
  onCancel,
  onSave,
  className
}: FormActionsProps) {
  const hasErrors = Object.keys(errors).length > 0

  if (!isEditing) {
    return (
      <div className={cn("flex justify-end", className)}>
        <Button variant="outline" size="sm" onClick={onEdit}>
          Edit Profile
        </Button>
      </div>
    )
  }

  return (
    <div className={cn("space-y-4", className)}>
      {/* Error Display */}
      {hasErrors && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
          <h4 className="text-sm font-medium text-destructive mb-2">
            Please fix the following errors:
          </h4>
          <ul className="text-sm text-destructive space-y-1">
            {Object.entries(errors).map(([field, error]) => (
              <li key={field}>
                • <strong>{field}:</strong> {error}
              </li>
            ))}
          </ul>
          <p className="text-xs text-muted-foreground mt-2">
            Fill in all required fields marked with * to save your changes.
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-end gap-2">
        <Button variant="outline" onClick={onCancel}>
          <X className="h-4 w-4 mr-2" />
          Cancel
        </Button>
        <Button 
          onClick={onSave}
          className={cn(
            "bg-primary hover:bg-primary/90",
            hasErrors && "opacity-75 cursor-not-allowed"
          )}
        >
          <Save className="h-4 w-4 mr-2" />
          Save Changes
        </Button>
      </div>
    </div>
  )
}
