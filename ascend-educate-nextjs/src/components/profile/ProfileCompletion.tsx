"use client"

import * as React from "react"
import { Progress } from "../../app/components/ui/progress"
import { Badge } from "../../app/components/ui/badge"
import { CheckCircle, AlertCircle } from "lucide-react"
import { UserProfile } from "../../types"
import { calculateProfileCompletion } from "../../utils/validation"
import { cn } from "../../app/lib/utils"

interface ProfileCompletionProps {
  profile: UserProfile
  className?: string
}

export function ProfileCompletion({ profile, className }: ProfileCompletionProps) {
  const { isComplete, percentage } = calculateProfileCompletion(profile)

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Profile Completion</h3>
        <Badge variant={isComplete ? "default" : "secondary"}>
          {percentage}% Complete
        </Badge>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span>Progress</span>
          <span>{percentage}%</span>
        </div>
        <Progress value={percentage} className="h-2" />
      </div>

      <div className="flex items-center gap-2 text-sm">
        {isComplete ? (
          <>
            <CheckCircle className="h-4 w-4 text-green-500" />
            <span className="text-green-600">Profile is complete!</span>
          </>
        ) : (
          <>
            <AlertCircle className="h-4 w-4 text-amber-500" />
            <span className="text-amber-600">
              Complete your profile to unlock all features
            </span>
          </>
        )}
      </div>
    </div>
  )
}
