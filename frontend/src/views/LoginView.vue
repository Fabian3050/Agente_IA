<template>
  <div class="min-h-screen w-full flex items-center justify-center bg-[#F7F9FB] p-4 font-sans">
    <div class="max-w-4xl w-full bg-white rounded-2xl shadow-xl overflow-hidden grid grid-cols-1 md:grid-cols-12 border border-gray-100">
      
      <!-- Left side: USACH Branding -->
      <div
        class="md:col-span-5 p-8 flex flex-col justify-between relative overflow-hidden text-white"
        style="background: linear-gradient(135deg, #00aea7 0%, #007a75 100%)"
      >
        <div class="absolute -right-10 -top-10 w-40 h-40 rounded-full bg-white/10 blur-xl pointer-events-none" />
        <div class="absolute -left-10 -bottom-10 w-40 h-40 rounded-full bg-black/10 blur-xl pointer-events-none" />

        <div class="relative z-10 flex items-center gap-3">
          <div class="w-full h-24 rounded-xl bg-[#00aea7] p-3 shadow-md flex items-center justify-center flex-shrink-0">
            <div class="text-white text-3xl font-black tracking-widest border-2 border-white/40 px-6 py-2 rounded-lg">
              USACH
            </div>
          </div>
        </div>

        <div class="translate-y-3 relative z-10">
          <span class="text-xs font-semibold tracking-wider uppercase block text-white/80">VRIIC · USACH</span>
          <span class="text-sm font-bold block leading-tight">DSpace-CRIS</span>
        </div>

        <div class="relative z-10 my-8">
          <h1 class="text-2xl font-bold leading-tight mb-3">Agente Inteligente para el Enriquecimiento de Metadatos</h1>
          <p class="text-xs text-white/85 leading-relaxed">
            Plataforma institucional para el enriquecimiento y curaduría de metadatos de publicaciones científicas.
          </p>
        </div>

        <div class="relative z-10 mt-8">
          <h2 class="text-xs font-bold leading-tight mb-1">Agradecimiento</h2>
          <p class="text-xs text-white/85 leading-relaxed">
            El presente trabajo fue desarrollado gracias al proyecto INCAR250006, financiado por ANID.
          </p>
        </div>

        <div class="relative z-10 pt-6 border-t border-white/20 flex items-center justify-between text-[11px] text-white/75">
          <span>Universidad de Santiago de Chile</span>
          <span class="flex items-center gap-1.5">
            <Lock :size="12" /> SSO / OpenID Connect
          </span>
        </div>
      </div>

      <!-- Right side: Login Form & OAuth 2.0 / OIDC Flow -->
      <div class="md:col-span-7 p-8 md:p-10 flex flex-col justify-center">
        <div class="flex items-center justify-between gap-4 -mt-3 mb-4">
          <div class="text-xs font-bold text-gray-500 uppercase tracking-wider">
            VRIIC Vicerrectoría
          </div>
          <div class="text-xs font-bold text-gray-400 uppercase tracking-wider">
            ANID Chile
          </div>
        </div>

        <div class="mb-5">
          <h2 class="text-xl font-bold text-[#1a2332]">Iniciar Sesión</h2>
          <p class="text-xs text-[#6b7a90] mt-1">Acceso seguro mediante el proveedor de identidad institucional (OIDC).</p>
        </div>

        <!-- Error notification -->
        <div
          v-if="error"
          class="mb-4 p-3 rounded-lg bg-[#ffebee] border border-[#ffcdd2] text-[#d32f2f] text-xs flex items-center gap-2"
        >
          <AlertCircle :size="16" class="flex-shrink-0" />
          <span>{{ error }}</span>
        </div>

        <!-- Loading OIDC callback notification -->
        <div
          v-if="loadingCallback"
          class="mb-4 p-3 rounded-lg bg-teal-50 border border-teal-200 text-teal-800 text-xs flex items-center gap-2 animate-pulse"
        >
          <div class="w-4 h-4 border-2 border-[#00aea7] border-t-transparent rounded-full animate-spin"></div>
          <span>Autenticación exitosa con Google. Obteniendo sesión institucional en MS3...</span>
        </div>

        <!-- 1. BOTÓN PRINCIPAL OAUTH 2.0 / OPENID CONNECT (GOOGLE WORKSPACE) -->
        <div class="mb-5">
          <button
            @click="handleOidcLogin"
            :disabled="loading || loadingCallback"
            type="button"
            class="w-full py-3 px-4 rounded-xl text-[#1a2332] font-semibold text-xs flex items-center justify-center gap-3 bg-white border border-gray-300 shadow-sm hover:bg-gray-50 hover:border-gray-400 hover:shadow transition-all cursor-pointer disabled:opacity-50"
          >
            <!-- Google "G" SVG Icon -->
            <svg class="w-4 h-4 flex-shrink-0" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>{{ loading || loadingCallback ? 'Conectando con Google...' : 'Acceder con Google Institucional (@usach.cl)' }}</span>
            <ExternalLink :size="14" class="text-gray-400 ml-auto" />
          </button>
          
        </div>

    

        <!-- Sandbox OIDC / Selector Rápido de Roles de MS3 Auth -->
        <div class="mt-5 pt-4 border-t border-gray-100">
          <p class="text-[11px] font-semibold text-gray-500 mb-2 uppercase tracking-wide flex items-center justify-between">
            <span>Roles Institucionales RBAC (MS3 Auth)</span>
            <span class="text-[10px] text-teal-600 font-mono">/auth/mock-login</span>
          </p>
          <div class="grid grid-cols-3 gap-2">
            <button
              @click="quickLogin('admin.vriic@usach.cl', 'Admin')"
              :disabled="loading || loadingCallback"
              class="py-2 px-2 border border-purple-200 bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-medium rounded-lg transition-colors cursor-pointer text-center"
            >
              👑 Administrador
            </button>
            <button
              @click="quickLogin('curador.vriic@usach.cl', 'Curador_VRIIC')"
              :disabled="loading || loadingCallback"
              class="py-2 px-2 border border-teal-200 bg-teal-50 hover:bg-teal-100 text-teal-700 text-xs font-medium rounded-lg transition-colors cursor-pointer text-center"
            >
              🔍 Curador VRIIC
            </button>
            <button
              @click="quickLogin('investigador@usach.cl', 'Academico')"
              :disabled="loading || loadingCallback"
              class="py-2 px-2 border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium rounded-lg transition-colors cursor-pointer text-center"
            >
              📋 Académico
            </button>
          </div>
        </div>

        <div class="mt-5 pt-3 border-t border-gray-100 text-center">
          <p class="text-[11px] text-[#6b7a90]">
            Universidad de Santiago de Chile · Vicerrectoría de Investigación, Innovación y Creación (VRIIC).
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { User, ShieldCheck, ArrowRight, AlertCircle, ExternalLink, Lock } from 'lucide-vue-next'
import { authService } from '../services/authService'
import type { User as UserType } from '../types'

const emit = defineEmits<{
  (e: 'login-success', user: UserType): void
}>()

const email = ref('curador.vriic@usach.cl')
const password = ref('CuradorVriic2025!')
const remember = ref(true)
const error = ref('')
const loading = ref(false)
const loadingCallback = ref(false)

const showForgotDialog = () => {
  alert('Para restablecer sus credenciales institucionales, contacte a soporte.cris@usach.cl o al portal de identidad USACH.')
}

/**
 * Inicia el flujo de autorización OAuth 2.0 / OpenID Connect hacia el SSO institucional USACH.
 * Redirige al navegador hacia el portal de login institucional (SSO).
 */
const handleOidcLogin = async () => {
  error.value = ''
  loading.value = true
  try {
    const redirectUri = window.location.origin + window.location.pathname
    const authUrl = await authService.getOidcAuthorizeUrl(redirectUri)

    // Redirigir el navegador hacia el portal SSO
    window.location.href = authUrl
  } catch (err: any) {
    console.error('Error en login OIDC:', err)
    error.value = err.response?.data?.detail || 'No se pudo iniciar el flujo OpenID Connect con el microservicio MS3 Auth.'
    loading.value = false
  }
}

/**
 * Login tradicional con correo/usuario.
 */
const handleDirectLogin = async () => {
  error.value = ''
  if (!email.value) {
    error.value = 'Por favor ingrese su correo o usuario institucional.'
    return
  }

  loading.value = true
  try {
    const user = await authService.login(email.value, password.value)
    emit('login-success', user)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error de autenticación con el servidor MS3.'
  } finally {
    loading.value = false
  }
}

/**
 * Autenticación simulada (Sandbox OIDC) que solicita un token JWT real a MS3 Auth (/auth/mock-login).
 */
const quickLogin = async (userEmail: string, roleName: 'Admin' | 'Curador_VRIIC' | 'Academico') => {
  loading.value = true
  error.value = ''
  try {
    const user = await authService.mockLogin({
      email: userEmail,
      name: userEmail.split('.')[0],
      last_name: 'USACH',
      role_name: roleName,
    })
    emit('login-success', user)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Error conectando con el servicio de autenticación MS3.'
  } finally {
    loading.value = false
  }
}

/**
 * Revisa si el navegador retornó desde el IdP con ?code= en la URL para procesar el callback OIDC.
 */
onMounted(async () => {
  const urlParams = new URLSearchParams(window.location.search)
  const code = urlParams.get('code')
  const state = urlParams.get('state')
  const oidcError = urlParams.get('error')

  if (oidcError) {
    error.value = `Error reportado por el proveedor de identidad: ${oidcError}`
    window.history.replaceState({}, document.title, window.location.pathname)
    return
  }

  if (code) {
    loadingCallback.value = true
    try {
      const redirectUri = window.location.origin + window.location.pathname
      const user = await authService.handleOidcCallback(code, state || undefined, redirectUri)
      // Limpiar el código de la URL para evitar re-ejecución accidental
      window.history.replaceState({}, document.title, window.location.pathname)
      emit('login-success', user)
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'No se pudo validar el código de autorización OIDC con MS3 Auth.'
      window.history.replaceState({}, document.title, window.location.pathname)
    } finally {
      loadingCallback.value = false
    }
  }
})
</script>
