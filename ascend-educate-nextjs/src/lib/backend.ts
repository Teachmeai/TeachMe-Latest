import { supabase } from './supabase'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface BackendRole {
  scope: 'global' | 'org'
  role: string
  org_id?: string
  org_name?: string
}

export interface UserSession {
  user_id: string
  roles: BackendRole[]
  active_role: string
  device_id?: string
  exp?: number
}

export interface BackendResponse<T> {
  ok?: boolean
  error?: string
  data?: T
}

export interface BackendProfile {
  id: string
  email?: string
  full_name?: string
  phone?: string
  address?: string
  city?: string
  state?: string
  country?: string
  postal_code?: string
  date_of_birth?: string
  bio?: string
  avatar_url?: string
  website?: string
  linkedin_url?: string
  twitter_url?: string
  github_url?: string
  profile_completion_percentage?: number
  created_at?: string
  updated_at?: string
}

class BackendClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<BackendResponse<T>> {
    const token = (await supabase.auth.getSession()).data.session?.access_token
    console.log('Backend request:', endpoint, token ? 'JWT present' : 'No JWT')
    console.log('Request options:', options)
    
    const response = await fetch(`${BACKEND_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
      },
    })

    console.log('Backend response:', response.status, response.statusText)

    if (!response.ok) {
      const error = await response.text()
      console.error('Backend error:', error)
      return { ok: false, error }
    }

    const data = await response.json()
    return { ok: true, data }
  }

  async getMe(deviceId?: string): Promise<BackendResponse<UserSession>> {
    return this.request<UserSession>('/auth/me', {
      headers: deviceId ? { 'X-Device-Id': deviceId } : {},
    })
  }

  async switchRole(role: string, orgId?: string): Promise<BackendResponse<{ active_role: string; active_org_id?: string }>> {
    const params = new URLSearchParams({ role })
    if (orgId) params.append('org_id', orgId)
    
    return this.request(`/auth/switch-role?${params}`, {
      method: 'POST',
    })
  }

  async logout(deviceId?: string): Promise<BackendResponse<{ ok: boolean }>> {
    console.log('Backend logout called with deviceId:', deviceId)
    return this.request('/auth/logout', {
      method: 'POST',
      headers: deviceId ? { 'X-Device-Id': deviceId } : {},
    })
  }

  async forceLogout(userId: string, deviceId?: string): Promise<BackendResponse<{ ok: boolean }>> {
    console.log('Backend force logout called with userId:', userId, 'deviceId:', deviceId)
    return this.request(`/auth/logout/force?user_id=${userId}`, {
      method: 'POST',
      headers: deviceId ? { 'X-Device-Id': deviceId } : {},
    })
  }

  async getProfile(): Promise<BackendResponse<BackendProfile>> {
    return this.request<BackendProfile>('/profiles/me')
  }

  async updateProfile(payload: Partial<BackendProfile>): Promise<BackendResponse<BackendProfile>> {
    return this.request<BackendProfile>('/profiles/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    })
  }
}

export const backend = new BackendClient()
