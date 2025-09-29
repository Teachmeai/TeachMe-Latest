import { useState, useCallback, useEffect, useRef } from 'react'
import { FormData, ValidationErrors, UserProfile } from '../types'
import { calculateProfileCompletion, validateBasicFields, validateRoleFields } from '../utils/validation'
import { backend } from '../lib/backend'
import { useToast } from './use-toast'

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
  const [isSaving, setIsSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
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
  const { toast } = useToast()
  const hasLoadedProfile = useRef(false)

  // Update selectedRole when activeRole changes from session
  useEffect(() => {
    if (activeRole && activeRole !== selectedRole) {
      setSelectedRole(activeRole)
    }
  }, [activeRole, selectedRole])

  // Prefill form from backend profile when available (only once)
  useEffect(() => {
    if (!initialProfile || hasLoadedProfile.current) return
    
    hasLoadedProfile.current = true
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
    setSaveSuccess(false)
  }, [])

  const handleCancel = useCallback(() => {
    setIsEditing(false)
    setIsSaving(false)
    setSaveSuccess(false)
    
    // Reset to the current profile data (what was loaded from backend)
    if (initialProfile) {
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
    }
    
    setSelectedRole(activeRole || initialUser.role)
    setRoleData(initialUser.roleData || {})
    setBasicErrors({})
    setRoleErrors({})
  }, [activeRole, initialUser.role, initialUser.roleData, initialProfile])

  const handleSaveBasic = useCallback(async () => {
    const validationErrors = validateBasicFields(formData)
    setBasicErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return false

    setIsSaving(true)
    setSaveSuccess(false)

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
        setIsSaving(false)
        toast({
          title: "Error",
          description: "Failed to save profile changes. Please try again.",
          variant: "destructive"
        })
        return false
      }
      onProfileUpdate(updatedProfile)
      setIsSaving(false)
      setSaveSuccess(true)
      toast({
        title: "Success",
        description: "Profile changes saved successfully!",
      })
      
      // Auto-hide success message after 3 seconds
      setTimeout(() => {
        setSaveSuccess(false)
      }, 3000)
      
      return true
    } catch {
      setIsSaving(false)
      toast({
        title: "Error",
        description: "Failed to save profile changes. Please try again.",
        variant: "destructive"
      })
      return false
    }
  }, [formData, selectedRole, roleData, initialUser, onProfileUpdate, toast])

  const handleSaveRole = useCallback(async () => {
    const validationErrors = validateRoleFields(selectedRole, roleData)
    setRoleErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return false
    
    setIsSaving(true)
    setSaveSuccess(false)
    
    try {
      // For now, role data is local only; persist when backend is ready
      setIsSaving(false)
      setSaveSuccess(true)
      toast({
        title: "Success",
        description: "Role changes saved successfully!",
      })
      
      // Auto-hide success message after 3 seconds
      setTimeout(() => {
        setSaveSuccess(false)
      }, 3000)
      
      return true
    } catch {
      setIsSaving(false)
      toast({
        title: "Error",
        description: "Failed to save role changes. Please try again.",
        variant: "destructive"
      })
      return false
    }
  }, [selectedRole, roleData, toast])

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
    isSaving,
    saveSuccess,
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
