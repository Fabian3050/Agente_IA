import { ms3Client, MS_ENDPOINTS } from './api'
import type { User } from '../types'

export interface TokenResponseDTO {
  access_token: string
  token_type: string
  expires_in: number
  user: {
    id: string | number
    name: string
    last_name?: string
    email: string
    role_name: string
    sub?: string
    orcid?: string
    dspace_person_id?: string
    is_active: boolean
    last_login?: string
  }
}

export function normalizeUser(apiUser: any): User {
  const firstName = apiUser.name || apiUser.username || 'Usuario'
  const lastName = apiUser.last_name || ''
  const fullName = apiUser.full_name || `${firstName} ${lastName}`.trim()

  // Mapeo canónico de roles de MS3 (RBAC: 'Admin', 'Curador_VRIIC', 'Academico')
  let displayRole = 'Curador'
  const rawRole = apiUser.role_name || apiUser.role || ''
  if (rawRole === 'Admin' || rawRole === 'Administrador') {
    displayRole = 'Administrador'
  } else if (rawRole === 'Curador_VRIIC' || rawRole === 'Curador') {
    displayRole = 'Curador'
  } else if (rawRole === 'Academico' || rawRole === 'Auditor') {
    displayRole = 'Auditor'
  }

  return {
    id: String(apiUser.id),
    sub: apiUser.sub,
    username: apiUser.email ? apiUser.email.split('@')[0] : firstName.toLowerCase(),
    name: firstName,
    lastName: lastName,
    fullName: fullName,
    email: apiUser.email,
    role: displayRole as any,
    isActive: apiUser.is_active !== undefined ? apiUser.is_active : true,
    orcid: apiUser.orcid,
    dspacePersonId: apiUser.dspace_person_id,
    createdAt: apiUser.last_login || apiUser.created_at,
  }
}

export const authService = {
  /**
   * Obtiene la URL de autorización OpenID Connect (OIDC) desde el microservicio MS3 Auth.
   */
  async getOidcAuthorizeUrl(redirectUri: string = window.location.origin): Promise<string> {
    try {
      const res = await ms3Client.get<{ authorization_url: string }>('/auth/login', {
        params: {
          redirect_uri: redirectUri,
          auto_redirect: false,
          state: `st_${Date.now()}_${Math.random().toString(36).substring(7)}`,
        },
      })
      if (res.data?.authorization_url) {
        return res.data.authorization_url
      }
    } catch (err) {
      console.warn('MS3 /auth/login falló o no respondió, usando endpoint directo:', err)
    }
    // Fallback directo a endpoint de autorización OIDC
    return `${MS_ENDPOINTS.MS3_AUTH}/auth/login?redirect_uri=${encodeURIComponent(redirectUri)}&auto_redirect=true`
  },

  /**
   * Procesa el callback OAuth 2.0 / OIDC intercambiando el código de autorización por tokens.
   */
  async handleOidcCallback(
    code: string,
    state?: string,
    redirectUri: string = window.location.origin
  ): Promise<User> {
    const res = await ms3Client.get<TokenResponseDTO>('/auth/callback', {
      params: {
        code,
        state: state || undefined,
        redirect_uri: redirectUri,
      },
    })
    this.storeSession(res.data)
    return normalizeUser(res.data.user)
  },

  /**
   * Intercambio directo de ID Token OIDC del lado del cliente.
   */
  async exchangeIdToken(idToken: string): Promise<User> {
    const res = await ms3Client.post<TokenResponseDTO>('/auth/oidc/token', {
      id_token: idToken,
    })
    this.storeSession(res.data)
    return normalizeUser(res.data.user)
  },

  /**
   * Autenticación simulada (Sandbox USACH SSO OIDC) para testing y desarrollo.
   */
  async mockLogin(params: {
    email: string
    name?: string
    last_name?: string
    role_name: 'Admin' | 'Curador_VRIIC' | 'Academico' | string
    orcid?: string
    dspace_person_id?: string
  }): Promise<User> {
    const res = await ms3Client.post<TokenResponseDTO>('/auth/mock-login', {
      email: params.email,
      name: params.name || 'Usuario',
      last_name: params.last_name || 'Institucional',
      role_name: params.role_name,
      orcid: params.orcid || '0000-0002-1825-0097',
      dspace_person_id: params.dspace_person_id || 'person-usach-01',
    })
    this.storeSession(res.data)
    return normalizeUser(res.data.user)
  },

  /**
   * Login por formulario tradicional (correo / usuario).
   * Intenta autenticarse contra MS3 Auth mapeando credenciales a una sesión institucional.
   */
  async login(usernameOrEmail: string, _password?: string): Promise<User> {
    const cleanEmail = usernameOrEmail.includes('@')
      ? usernameOrEmail.trim().toLowerCase()
      : `${usernameOrEmail.trim().toLowerCase()}@usach.cl`

    // Determinar rol inicial sugerido según prefijo de email o cuenta
    let role: 'Admin' | 'Curador_VRIIC' | 'Academico' = 'Curador_VRIIC'
    if (cleanEmail.includes('admin')) {
      role = 'Admin'
    } else if (cleanEmail.includes('auditor') || cleanEmail.includes('investigador')) {
      role = 'Academico'
    }

    const name = cleanEmail.split('@')[0].replace('.', ' ')
    return await this.mockLogin({
      email: cleanEmail,
      name: name.charAt(0).toUpperCase() + name.slice(1),
      last_name: 'USACH',
      role_name: role,
    })
  },

  /**
   * Consulta el perfil del usuario autenticado en MS3 (/auth/me) a partir del JWT Bearer token.
   */
  async getCurrentUser(): Promise<User | null> {
    try {
      const res = await ms3Client.get<any>('/auth/me')
      return normalizeUser(res.data)
    } catch {
      return this.getStoredUser()
    }
  },

  /**
   * Introspección criptográfica de token con MS3 (/auth/introspect).
   */
  async introspectToken(token?: string): Promise<{ active: boolean; [key: string]: any }> {
    const targetToken = token || localStorage.getItem('access_token') || ''
    if (!targetToken) return { active: false }
    try {
      const res = await ms3Client.post('/auth/introspect', { token: targetToken })
      return res.data
    } catch {
      return { active: false }
    }
  },

  /**
   * Lista usuarios registrados en MS3 (/auth/users).
   */
  async listUsers(): Promise<User[]> {
    try {
      const res = await ms3Client.get<any[]>('/auth/users')
      return res.data.map(normalizeUser)
    } catch {
      return []
    }
  },

  /**
   * Crea un usuario manualmente en MS3 (/auth/users).
   */
  async createUser(data: {
    name: string
    last_name: string
    email: string
    role_name: string
    orcid?: string
    dspace_person_id?: string
  }): Promise<User> {
    const res = await ms3Client.post<any>('/auth/users', data)
    return normalizeUser(res.data)
  },

  /**
   * Activa o revoca el acceso de un usuario (/auth/users/:id/status).
   */
  async toggleUserStatus(userId: string, isActive: boolean): Promise<any> {
    const res = await ms3Client.patch(`/auth/users/${userId}/status`, null, {
      params: { is_active: isActive }
    })
    return res.data
  },

  storeSession(data: TokenResponseDTO) {
    const user = normalizeUser(data.user)
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('auth_user', JSON.stringify(user))
    localStorage.setItem('token_expires_in', String(data.expires_in))
    localStorage.setItem('token_type', data.token_type)
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
    localStorage.removeItem('token_expires_in')
    localStorage.removeItem('token_type')
    sessionStorage.clear()
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  },
}
