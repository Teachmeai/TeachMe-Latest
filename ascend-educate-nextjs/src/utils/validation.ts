import { FormData, ValidationErrors, UserProfile } from "../types"
import { getRoleById } from "../config/roles"

export const validateEmail = (email: string): string | null => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!email.trim()) return "Email is required"
  if (!emailRegex.test(email)) return "Please enter a valid email address"
  return null
}

export const validatePhone = (phone: string): string | null => {
  // More flexible phone validation that accepts:
  // - International format: +92 321 1234567
  // - Pakistani format: 0321 1234567 or 03211234567
  // - US format: +1 234 567 8900
  // - General format: any 7-15 digits with optional + prefix
  
  if (!phone.trim()) return "Phone number is required"
  
  // Remove all spaces, dashes, and parentheses for validation
  const cleanPhone = phone.replace(/[\s\-\(\)]/g, '')
  
  // Check if it contains only digits and optional + at start
  if (!/^[\+]?[0-9]+$/.test(cleanPhone)) {
    return "Phone number can only contain digits and optional + prefix"
  }
  
  // Check if it has reasonable length (7-15 digits)
  if (cleanPhone.length < 7 || cleanPhone.length > 15) {
    return "Phone number must be between 7-15 digits"
  }
  
  // Additional check for Pakistani numbers starting with 0
  if (cleanPhone.startsWith('0') && cleanPhone.length >= 10) {
    return null // Valid Pakistani format
  }
  
  // Check for international format
  if (cleanPhone.startsWith('+') && cleanPhone.length >= 8) {
    return null // Valid international format
  }
  
  // Check for regular format (no + prefix)
  if (!cleanPhone.startsWith('+') && cleanPhone.length >= 7) {
    return null // Valid regular format
  }
  
  return "Please enter a valid phone number"
}

export const validateUrl = (url: string, fieldName: string): string | null => {
  if (!url.trim()) return null // Optional field
  try {
    new URL(url)
    return null
  } catch {
    return `Please enter a valid ${fieldName} URL`
  }
}

export const validateBasicFields = (formData: FormData): ValidationErrors => {
  const errors: ValidationErrors = {}

  if (!formData.name.trim()) {
    errors.name = 'Name is required'
  }

  const emailError = validateEmail(formData.email)
  if (emailError) {
    errors.email = emailError
  }

  if (!formData.institute.trim()) {
    errors.institute = 'Institute is required'
  }

  const phoneError = validatePhone(formData.phoneNumber)
  if (phoneError) {
    errors.phoneNumber = phoneError
  }

  // Validate social media URLs
  const linkedinError = validateUrl(formData.linkedin, 'LinkedIn')
  if (linkedinError) errors.linkedin = linkedinError

  const twitterError = validateUrl(formData.twitter, 'Twitter')
  if (twitterError) errors.twitter = twitterError

  const githubError = validateUrl(formData.github, 'GitHub')
  if (githubError) errors.github = githubError

  const websiteError = validateUrl(formData.website, 'Website')
  if (websiteError) errors.website = websiteError

  return errors
}

export const validateRoleFields = (roleId: string, roleData: Record<string, string>): ValidationErrors => {
  const errors: ValidationErrors = {}
  const role = getRoleById(roleId)

  if (!role) {
    errors.role = 'Invalid role selected'
    return errors
  }

  role.fields.forEach(field => {
    if (field.required && !roleData[field.name]?.trim()) {
      errors[field.name] = `${field.label} is required`
    }
  })

  return errors
}

export const validateProfile = (formData: FormData, roleId: string, roleData: Record<string, string>): ValidationErrors => {
  const basicErrors = validateBasicFields(formData)
  const roleErrors = validateRoleFields(roleId, roleData)

  return { ...basicErrors, ...roleErrors }
}

export const calculateProfileCompletion = (profile: UserProfile): { isComplete: boolean; percentage: number } => {
  let completedFields = 0
  let totalRequiredFields = 0

  // Basic required fields
  const basicFields = ['name', 'email', 'institute', 'phoneNumber', 'role']
  totalRequiredFields += basicFields.length
  
  if (profile.name?.trim()) completedFields++
  if (profile.email?.trim()) completedFields++
  if (profile.institute?.trim()) completedFields++
  if (profile.phoneNumber?.trim()) completedFields++
  if (profile.role?.trim()) completedFields++

  // Role-specific required fields
  if (profile.role) {
    const role = getRoleById(profile.role)
    if (role) {
      const requiredRoleFields = role.fields.filter(field => field.required)
      totalRequiredFields += requiredRoleFields.length
      
      requiredRoleFields.forEach(field => {
        if (profile.roleData?.[field.name]?.trim()) {
          completedFields++
        }
      })
    }
  }

  const percentage = totalRequiredFields > 0 ? Math.round((completedFields / totalRequiredFields) * 100) : 0
  const isComplete = percentage === 100

  return { isComplete, percentage }
}
