import { useState, useCallback } from 'react'
import { FormData, ValidationErrors, UserProfile } from '../types'
import { validateProfile, calculateProfileCompletion } from '../utils/validation'

interface UseProfileFormProps {
  initialUser: UserProfile
  onProfileUpdate: (profile: UserProfile) => void
}

export const useProfileForm = ({ initialUser, onProfileUpdate }: UseProfileFormProps) => {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState<FormData>({
    name: initialUser.name,
    email: initialUser.email,
    institute: initialUser.institute || '',
    phoneNumber: initialUser.phoneNumber || '',
    profilePicture: initialUser.avatar || '',
    linkedin: initialUser.socialMedia?.linkedin || '',
    twitter: initialUser.socialMedia?.twitter || '',
    github: initialUser.socialMedia?.github || '',
    website: initialUser.socialMedia?.website || ''
  })
  const [selectedRole, setSelectedRole] = useState(initialUser.role)
  const [roleData, setRoleData] = useState<Record<string, string>>(initialUser.roleData || {})
  const [errors, setErrors] = useState<ValidationErrors>({})

  const handleEdit = useCallback(() => {
    setIsEditing(true)
    setErrors({})
  }, [])

  const handleCancel = useCallback(() => {
    setIsEditing(false)
    setFormData({
      name: initialUser.name,
      email: initialUser.email,
      institute: initialUser.institute || '',
      phoneNumber: initialUser.phoneNumber || '',
      profilePicture: initialUser.avatar || '',
      linkedin: initialUser.socialMedia?.linkedin || '',
      twitter: initialUser.socialMedia?.twitter || '',
      github: initialUser.socialMedia?.github || '',
      website: initialUser.socialMedia?.website || ''
    })
    setSelectedRole(initialUser.role)
    setRoleData(initialUser.roleData || {})
    setErrors({})
  }, [initialUser])

  const handleSave = useCallback(() => {
    const validationErrors = validateProfile(formData, selectedRole, roleData)
    setErrors(validationErrors)

    if (Object.keys(validationErrors).length > 0) {
      return false
    }

    const updatedProfile: UserProfile = {
      ...initialUser,
      name: formData.name,
      email: formData.email,
      role: selectedRole,
      avatar: formData.profilePicture || undefined,
      institute: formData.institute,
      phoneNumber: formData.phoneNumber,
      socialMedia: {
        linkedin: formData.linkedin || undefined,
        twitter: formData.twitter || undefined,
        github: formData.github || undefined,
        website: formData.website || undefined
      },
      roleData: roleData
    }

    // Calculate profile completion
    const { isComplete, percentage } = calculateProfileCompletion(updatedProfile)
    updatedProfile.isProfileComplete = isComplete
    updatedProfile.profileCompletionPercentage = percentage

    onProfileUpdate(updatedProfile)
    setIsEditing(false)
    return true
  }, [formData, selectedRole, roleData, initialUser, onProfileUpdate])

  const handleFieldChange = useCallback((field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }, [errors])

  const handleRoleFieldChange = useCallback((field: string, value: string) => {
    setRoleData(prev => ({ ...prev, [field]: value }))
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }, [errors])

  const handleRoleChange = useCallback((roleId: string) => {
    setSelectedRole(roleId)
    setRoleData({}) // Reset role data when role changes
    if (errors.role) {
      setErrors(prev => ({ ...prev, role: '' }))
    }
  }, [errors.role])

  return {
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
  }
}
