import { ms3Client, MS_ENDPOINTS } from './api'
import type { User } from '../types'

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    sub?: string
    username: string
    email: string
    role: string
    full_name: string
    is_active: boolean
  }
}

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    const res = await ms3Client.post<LoginResponse>('/auth/login', { username, password })
    this.storeSession(res.data)
    return res.data
  },

  async mockLogin(username: string, role: string): Promise<LoginResponse> {
    const res = await ms3Client.post<LoginResponse>('/auth/mock-login', { username, role })
    this.storeSession(res.data)
    return res.data
  },

  getOidcAuthorizeUrl(redirectUri: string = window.location.origin + '/callback'): string {
    return `${MS_ENDPOINTS.MS3_AUTH}/auth/authorize?client_id=dspace-cris-client&response_type=code&scope=openid%20profile%20email&redirect_uri=${encodeURIComponent(redirectUri)}`
  },

  async handleOidcCallback(code: string, redirectUri: string = window.location.origin + '/callback'): Promise<LoginResponse> {
    const res = await ms3Client.get<LoginResponse>(`/auth/callback?code=${code}&redirect_uri=${encodeURIComponent(redirectUri)}`)
    this.storeSession(res.data)
    return res.data
  },

  async getCurrentUser(): Promise<User | null> {
    try {
      const res = await ms3Client.get<{ user: any }>('/auth/me')
      return {
        id: String(res.data.user.id),
        sub: res.data.user.sub,
        username: res.data.user.username,
        email: res.data.user.email,
        role: res.data.user.role,
        fullName: res.data.user.full_name || res.data.user.username,
        isActive: res.data.user.is_active,
      }
    } catch {
      return null
    }
  },

  async listUsers(): Promise<User[]> {
    try {
      const res = await ms3Client.get<any[]>('/auth/users')
      return res.data.map((u) => ({
        id: String(u.id),
        sub: u.sub,
        username: u.username,
        email: u.email,
        role: u.role,
        fullName: u.full_name || u.username,
        isActive: u.is_active,
        createdAt: u.created_at,
      }))
    } catch {
      return []
    }
  },

  async createUser(data: { username: string; email: string; password?: string; role: string; full_name?: string }): Promise<User> {
    const res = await ms3Client.post<any>('/auth/users', data)
    return {
      id: String(res.data.id),
      sub: res.data.sub,
      username: res.data.username,
      email: res.data.email,
      role: res.data.role,
      fullName: res.data.full_name || res.data.username,
      isActive: res.data.is_active,
    }
  },

  storeSession(data: LoginResponse) {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('auth_user', JSON.stringify({
      id: String(data.user.id),
      sub: data.user.sub,
      username: data.user.username,
      email: data.user.email,
      role: data.user.role,
      fullName: data.user.full_name || data.user.username,
      isActive: data.user.is_active,
    }))
  },

  getStoredUser(): User | null {
    const stored = localStorage.getItem('auth_user')
    if (stored) {
      try {
        return JSON.parse(stored)
      } catch {
        return null
      }
    }
    return null
  },

  logout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('auth_user')
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('auth_user')
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }
}

