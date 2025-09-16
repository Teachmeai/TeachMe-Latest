import { User, Users, Building, Shield } from "lucide-react"
import { Role } from "../types"

export const ROLES: Role[] = [
  {
    id: 'student',
    title: 'Student',
    description: 'Personalized AI-powered learning experience',
    icon: User,
    color: 'from-blue-500 to-cyan-500',
    fields: [
      { 
        name: 'grade', 
        label: 'Grade Level', 
        type: 'select', 
        required: true, 
        options: ['Elementary', 'Middle School', 'High School', 'College', 'Graduate'],
        placeholder: 'Select your grade level'
      },
      { 
        name: 'subjects', 
        label: 'Interested Subjects', 
        type: 'textarea', 
        required: false,
        placeholder: 'List subjects you\'re interested in learning'
      },
      { 
        name: 'learningGoals', 
        label: 'Learning Goals', 
        type: 'textarea', 
        required: false,
        placeholder: 'Describe your learning objectives'
      }
    ]
  },
  {
    id: 'teacher',
    title: 'Teacher',
    description: 'Create content and manage your classes effectively',
    icon: Users,
    color: 'from-green-500 to-emerald-500',
    fields: [
      { 
        name: 'subject', 
        label: 'Subject Area', 
        type: 'text', 
        required: true,
        placeholder: 'e.g., Mathematics, Science, English'
      },
      { 
        name: 'experience', 
        label: 'Years of Experience', 
        type: 'select', 
        required: true, 
        options: ['0-2 years', '3-5 years', '6-10 years', '11-15 years', '16+ years'],
        placeholder: 'Select your experience level'
      },
      { 
        name: 'qualifications', 
        label: 'Educational Qualifications', 
        type: 'textarea', 
        required: false,
        placeholder: 'List your degrees, certifications, etc.'
      }
    ]
  },
  {
    id: 'organization_admin',
    title: 'Organization Admin',
    description: 'Manage multiple classrooms and institutional analytics',
    icon: Building,
    color: 'from-purple-500 to-violet-500',
    fields: [
      { 
        name: 'position', 
        label: 'Position/Title', 
        type: 'text', 
        required: true,
        placeholder: 'e.g., Principal, Director, Manager'
      },
      { 
        name: 'organizationSize', 
        label: 'Organization Size', 
        type: 'select', 
        required: true, 
        options: ['1-50 employees', '51-200 employees', '201-500 employees', '501-1000 employees', '1000+ employees'],
        placeholder: 'Select organization size'
      }
    ]
  },
  {
    id: 'super_admin',
    title: 'Super Admin',
    description: 'Platform-wide management and advanced analytics',
    icon: Shield,
    color: 'from-red-500 to-pink-500',
    fields: [
      { 
        name: 'department', 
        label: 'Department', 
        type: 'text', 
        required: true,
        placeholder: 'e.g., Engineering, Product, Operations'
      },
      { 
        name: 'accessLevel', 
        label: 'Access Level', 
        type: 'select', 
        required: true, 
        options: ['Level 1 - Basic', 'Level 2 - Standard', 'Level 3 - Advanced', 'Level 4 - Full Access'],
        placeholder: 'Select your access level'
      }
    ]
  }
]

export const getRoleById = (id: string): Role | undefined => {
  return ROLES.find(role => role.id === id)
}

export const getRoleFields = (roleId: string) => {
  const role = getRoleById(roleId)
  return role?.fields || []
}
