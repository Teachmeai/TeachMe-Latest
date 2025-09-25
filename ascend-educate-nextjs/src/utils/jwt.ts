/**
 * Utility functions for JWT token handling
 */

interface JWTPayload {
  sub?: string
  id?: string
  user_id?: string
  exp?: number
  iat?: number
  [key: string]: any
}

/**
 * Decode JWT token without verification (client-side only)
 * Note: This is for extracting user info from a token we already trust
 * The actual verification should be done on the server side
 */
export function decodeJWT(token: string): JWTPayload | null {
  try {
    if (!token) return null
    
    // Split the token into parts
    const parts = token.split('.')
    if (parts.length !== 3) {
      console.error('Invalid JWT format')
      return null
    }
    
    // Decode the payload (second part)
    const payload = parts[1]
    const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'))
    
    return JSON.parse(decoded) as JWTPayload
  } catch (error) {
    console.error('Error decoding JWT:', error)
    return null
  }
}

/**
 * Extract user ID from JWT token
 * Tries common claim names in order: 'sub', 'id', 'user_id'
 */
export function getUserIdFromToken(token: string): string | null {
  const payload = decodeJWT(token)
  if (!payload) return null
  
  return payload.sub || payload.id || payload.user_id || null
}

/**
 * Check if JWT token is expired
 */
export function isTokenExpired(token: string): boolean {
  const payload = decodeJWT(token)
  if (!payload || !payload.exp) return false
  
  const currentTime = Math.floor(Date.now() / 1000)
  return payload.exp < currentTime
}
