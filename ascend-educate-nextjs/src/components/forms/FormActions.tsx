"use client"

import * as React from "react"
import { Save, X, CheckCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ValidationErrors } from "@/types"
import { cn } from "@/lib/utils"

interface FormActionsProps {
  isEditing: boolean
  isSaving?: boolean
  saveSuccess?: boolean
  errors: ValidationErrors
  onEdit: () => void
  onCancel: () => void
  onSave: () => void
  className?: string
}

export function FormActions({
  isEditing,
  isSaving = false,
  saveSuccess = false,
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
      {/* Success Display */}
      {saveSuccess && !hasErrors && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
          <div className="flex items-center gap-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <h4 className="text-sm font-medium text-green-800">
              Changes saved successfully!
            </h4>
          </div>
          <p className="text-xs text-green-600 mt-1">
            Your profile has been updated.
          </p>
        </div>
      )}

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
        <Button variant="outline" onClick={onCancel} disabled={isSaving}>
          <X className="h-4 w-4 mr-2" />
          Cancel
        </Button>
        <Button 
          onClick={onSave}
          disabled={isSaving || hasErrors}
          className={cn(
            "bg-primary hover:bg-primary/90",
            (hasErrors || isSaving) && "opacity-75 cursor-not-allowed"
          )}
        >
          <Save className={cn("h-4 w-4 mr-2", isSaving && "animate-spin")} />
          {isSaving ? "Saving..." : "Save Changes"}
        </Button>
      </div>
    </div>
  )
}
