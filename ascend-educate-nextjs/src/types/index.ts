// Shared types for the entire application
export interface UserProfile {
  id?: string
  name: string
  email: string
  role: string
  avatar?: string
  institute?: string
  phoneNumber?: string
  socialMedia?: {
    linkedin?: string
    twitter?: string
    github?: string
    website?: string
  }
  roleData?: Record<string, string>
  isProfileComplete?: boolean
  profileCompletionPercentage?: number
  createdAt?: string
  updatedAt?: string
}

export interface Role {
  id: string
  title: string
  description: string
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>> // Lucide icon component
  color: string
  fields: RoleField[]
}

export interface RoleField {
  name: string
  label: string
  type: 'text' | 'textarea' | 'select' | 'email' | 'tel' | 'url'
  required: boolean
  options?: string[]
  placeholder?: string
}

export interface FormData {
  name: string
  email: string
  phoneNumber: string
  address: string
  city: string
  state: string
  country: string
  postalCode: string
  bio: string
  profilePicture: string
  linkedin: string
  twitter: string
  github: string
  website: string
}

export interface ValidationErrors {
  [key: string]: string
}

export interface ProfileManagementProps {
  user: UserProfile
  onProfileUpdate: (profile: UserProfile) => void
  onClose: () => void
  className?: string
}

// API Response Types (for future backend integration)
export interface ApiResponse<T> {
  data: T
  message: string
  success: boolean
}

export interface ApiError {
  message: string
  code: string
  details?: Record<string, unknown>
}

// Form validation types
export interface ValidationRule {
  required?: boolean
  minLength?: number
  maxLength?: number
  pattern?: RegExp
  custom?: (value: string) => string | null
}

// Assistant & Chat Types
export interface Assistant {
  id: string
  name: string
  description?: string
  model: string
  instructions?: string
  tools?: string[]
  metadata?: Record<string, any>
}

export interface ChatThread {
  id: string
  assistant_id: string
  created_at?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: number
}