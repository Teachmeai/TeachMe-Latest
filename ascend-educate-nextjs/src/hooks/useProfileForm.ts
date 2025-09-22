import { useState, useCallback, useEffect } from 'react'
import { FormData, ValidationErrors, UserProfile } from '../types'
import { validateProfile, calculateProfileCompletion, validateBasicFields, validateRoleFields } from '../utils/validation'
import { backend } from '../lib/backend'

interface UseProfileFormProps {
  initialUser: UserProfile
  onProfileUpdate: (profile: UserProfile) => void
  activeRole?: string
  initialProfile?: {
    full_name?: string
    avatar_url?: string
    phone?: string
    address?: string
    city?: string
    state?: string
    country?: string
    postal_code?: string
    bio?: string
    website?: string
    linkedin_url?: string
    twitter_url?: string
    github_url?: string
  }
}

export const useProfileForm = ({ initialUser, onProfileUpdate, activeRole, initialProfile }: UseProfileFormProps) => {
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState<FormData>({
    name: initialUser.name,
    email: initialUser.email,
    phoneNumber: initialUser.phoneNumber || '',
    address: '',
    city: '',
    state: '',
    country: '',
    postalCode: '',
    bio: '',
    profilePicture: initialUser.avatar || '',
    linkedin: initialUser.socialMedia?.linkedin || '',
    twitter: initialUser.socialMedia?.twitter || '',
    github: initialUser.socialMedia?.github || '',
    website: initialUser.socialMedia?.website || ''
  })
  const [selectedRole, setSelectedRole] = useState(activeRole || initialUser.role)
  const [roleData, setRoleData] = useState<Record<string, string>>(initialUser.roleData || {})
  const [basicErrors, setBasicErrors] = useState<ValidationErrors>({})
  const [roleErrors, setRoleErrors] = useState<ValidationErrors>({})

  // Update selectedRole when activeRole changes from session
  useEffect(() => {
    if (activeRole && activeRole !== selectedRole) {
      setSelectedRole(activeRole)
    }
  }, [activeRole, selectedRole])

  // Prefill form from backend profile when available
  useEffect(() => {
    if (!initialProfile) return
    setFormData(prev => ({
      ...prev,
      name: initialProfile.full_name ?? prev.name,
      profilePicture: initialProfile.avatar_url ?? prev.profilePicture,
      phoneNumber: initialProfile.phone ?? prev.phoneNumber,
      address: initialProfile.address ?? prev.address,
      city: initialProfile.city ?? prev.city,
      state: initialProfile.state ?? prev.state,
      country: initialProfile.country ?? prev.country,
      postalCode: initialProfile.postal_code ?? prev.postalCode,
      bio: initialProfile.bio ?? prev.bio,
      website: initialProfile.website ?? prev.website,
      linkedin: initialProfile.linkedin_url ?? prev.linkedin,
      twitter: initialProfile.twitter_url ?? prev.twitter,
      github: initialProfile.github_url ?? prev.github,
    }))
  }, [initialProfile])

  const handleEdit = useCallback(() => {
    setIsEditing(true)
    setBasicErrors({})
    setRoleErrors({})
  }, [])

  const handleCancel = useCallback(() => {
    setIsEditing(false)
    setFormData({
      name: initialUser.name,
      email: initialUser.email,
      phoneNumber: initialUser.phoneNumber || '',
      address: '',
      city: '',
      state: '',
      country: '',
      postalCode: '',
      bio: '',
      profilePicture: initialUser.avatar || '',
      linkedin: initialUser.socialMedia?.linkedin || '',
      twitter: initialUser.socialMedia?.twitter || '',
      github: initialUser.socialMedia?.github || '',
      website: initialUser.socialMedia?.website || ''
    })
    setSelectedRole(activeRole || initialUser.role)
    setRoleData(initialUser.roleData || {})
    setBasicErrors({})
    setRoleErrors({})
  }, [initialUser, activeRole])

  const handleSaveBasic = useCallback(async () => {
    const validationErrors = validateBasicFields(formData)
    setBasicErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return false

    const updatedProfile: UserProfile = {
      ...initialUser,
      name: formData.name,
      email: formData.email,
      role: selectedRole,
      avatar: formData.profilePicture || undefined,
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

    // Persist to backend profiles API
    try {
      const payload = {
        full_name: updatedProfile.name,
        avatar_url: updatedProfile.avatar,
        phone: updatedProfile.phoneNumber,
        address: formData.address || undefined,
        city: formData.city || undefined,
        state: formData.state || undefined,
        country: formData.country || undefined,
        postal_code: formData.postalCode || undefined,
        bio: formData.bio || undefined,
        website: updatedProfile.socialMedia?.website,
        linkedin_url: updatedProfile.socialMedia?.linkedin,
        twitter_url: updatedProfile.socialMedia?.twitter,
        github_url: updatedProfile.socialMedia?.github,
      }
      const resp = await backend.updateProfile(payload)
      if (!resp.ok) {
        return false
      }
      onProfileUpdate(updatedProfile)
      setIsEditing(false)
      return true
    } catch (e) {
      return false
    }
  }, [formData, selectedRole, roleData, initialUser, onProfileUpdate])

  const handleSaveRole = useCallback(async () => {
    const validationErrors = validateRoleFields(selectedRole, roleData)
    setRoleErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return false
    // For now, role data is local only; persist when backend is ready
    setIsEditing(false)
    return true
  }, [selectedRole, roleData])

  const handleFieldChange = useCallback((field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
    if (basicErrors[field]) {
      setBasicErrors(prev => ({ ...prev, [field]: '' }))
    }
  }, [basicErrors])

  const handleRoleFieldChange = useCallback((field: string, value: string) => {
    setRoleData(prev => ({ ...prev, [field]: value }))
    if (roleErrors[field]) {
      setRoleErrors(prev => ({ ...prev, [field]: '' }))
    }
  }, [roleErrors])


  return {
    isEditing,
    formData,
    selectedRole,
    roleData,
    basicErrors,
    roleErrors,
    handleEdit,
    handleCancel,
    handleSave: handleSaveBasic,
    handleSaveBasic,
    handleSaveRole,
    handleFieldChange,
    handleRoleFieldChange
  }
}
