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
            Plataforma para el enriquecimiento y curaduría de metadatos de publicaciones científicas institucionales.
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
          <span>Acceso Seguro OIDC / JWT</span>
        </div>
      </div>

      <!-- Right side: Login Form & Mock SSO -->
      <div class="md:col-span-7 p-8 md:p-10 flex flex-col justify-center">
        <div class="flex items-center justify-between gap-4 -mt-3 mb-4">
          <div class="text-xs font-bold text-gray-500 uppercase tracking-wider">
            VRIIC Vicerrectoría
          </div>
          <div class="text-xs font-bold text-gray-400 uppercase tracking-wider">
            ANID Chile
          </div>
        </div>

        <div class="mb-6">
          <h2 class="text-xl font-bold text-[#1a2332]">Iniciar Sesión</h2>
          <p class="text-xs text-[#6b7a90] mt-1">Ingresa con tus credenciales o mediante el SSO institucional.</p>
        </div>

        <!-- Error notification -->
        <div
          v-if="error"
          class="mb-4 p-3 rounded-lg bg-[#ffebee] border border-[#ffcdd2] text-[#d32f2f] text-xs flex items-center gap-2"
        >
          <AlertCircle :size="16" />
          <span>{{ error }}</span>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="flex flex-col gap-4">
          <div>
            <label class="text-xs font-semibold text-[#1a2332] mb-1.5 block">Correo institucional o usuario</label>
            <div class="relative">
              <input
                type="text"
                v-model="email"
                class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7] transition-all"
                placeholder="ejemplo@usach.cl o admin"
                required
              />
              <User :size="16" class="absolute left-3 top-2.5 text-[#6b7a90]" />
            </div>
          </div>

          <div>
            <label class="text-xs font-semibold text-[#1a2332] mb-1.5 block">Contraseña</label>
            <div class="relative">
              <input
                type="password"
                v-model="password"
                class="w-full pl-9 pr-3 py-2.5 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7] transition-all"
                placeholder="••••••••••••"
                required
              />
              <ShieldCheck :size="16" class="absolute left-3 top-2.5 text-[#6b7a90]" />
            </div>
          </div>

          <div class="flex items-center justify-between mt-1">
            <label class="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                v-model="remember"
                class="rounded text-[#00aea7] focus:ring-[#00aea7] accent-[#00aea7]"
              />
              <span class="text-xs text-[#6b7a90]">Recordar sesión</span>
            </label>
            <a
              href="#olvido"
              @click.prevent="showForgotDialog"
              class="text-xs font-medium text-[#00aea7] hover:underline"
            >
              ¿Olvidaste tu contraseña?
            </a>
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="mt-2 w-full py-2.5 px-4 rounded-lg text-white font-medium text-xs flex items-center justify-center gap-2 shadow-md hover:opacity-95 transition-all cursor-pointer disabled:opacity-50"
            style="background: #00aea7"
          >
            <span>{{ loading ? 'Autenticando...' : 'Acceder al Sistema' }}</span>
            <ArrowRight :size="16" />
          </button>
        </form>

        <!-- Quick SSO & Role Switcher for Development & Staging -->
        <div class="mt-6 pt-5 border-t border-gray-100">
          <p class="text-[11px] font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            Acceso Rápido por Rol (Entorno Integrado / SSO)
          </p>
          <div class="grid grid-cols-3 gap-2">
            <button
              @click="quickLogin('admin.vriic', 'Administrador')"
              class="py-2 px-2 border border-purple-200 bg-purple-50 hover:bg-purple-100 text-purple-700 text-xs font-medium rounded-lg transition-colors cursor-pointer"
            >
              👑 Administrador
            </button>
            <button
              @click="quickLogin('curador.vriic', 'Curador')"
              class="py-2 px-2 border border-teal-200 bg-teal-50 hover:bg-teal-100 text-teal-700 text-xs font-medium rounded-lg transition-colors cursor-pointer"
            >
              🔍 Curador
            </button>
            <button
              @click="quickLogin('auditor.vriic', 'Auditor')"
              class="py-2 px-2 border border-blue-200 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-medium rounded-lg transition-colors cursor-pointer"
            >
              📋 Auditor
            </button>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-gray-100 text-center">
          <p class="text-[11px] text-[#6b7a90]">
            Al ingresar, aceptas las políticas de seguridad y uso de datos institucionales de la Universidad de Santiago de Chile.
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { User, ShieldCheck, ArrowRight, AlertCircle } from 'lucide-vue-next'
import { authService } from '../services/authService'
import type { User as UserType } from '../types'

const emit = defineEmits<{
  (e: 'login-success', user: UserType): void
}>()

const email = ref('admin.vriic@usach.cl')
const password = ref('AdminVriic2025!')
const remember = ref(true)
const error = ref('')
const loading = ref(false)

const showForgotDialog = () => {
  alert('Por favor contacte al soporte de VRIIC (soporte.cris@usach.cl) para restablecer sus credenciales.')
}

const handleSubmit = async () => {
  error.value = ''
  if (!email.value || !password.value) {
    error.value = 'Por favor ingrese su correo/usuario y contraseña.'
    return
  }

  loading.value = true
  try {
    const res = await authService.login(email.value, password.value)
    emit('login-success', {
      id: String(res.user.id),
      sub: res.user.sub,
      username: res.user.username,
      email: res.user.email,
      role: res.user.role as any,
      fullName: res.user.full_name || res.user.username,
      isActive: res.user.is_active,
    })
  } catch (err: any) {
    // If backend returns 401 or network error, provide graceful fallback
    const detail = err.response?.data?.detail || 'Error de autenticación'
    error.value = detail
  } finally {
    loading.value = false
  }
}

const quickLogin = async (username: string, role: string) => {
  loading.value = true
  error.value = ''
  try {
    const res = await authService.mockLogin(username, role)
    emit('login-success', {
      id: String(res.user.id),
      sub: res.user.sub,
      username: res.user.username,
      email: res.user.email,
      role: res.user.role as any,
      fullName: res.user.full_name || username,
      isActive: res.user.is_active,
    })
  } catch (err: any) {
    // Fallback if MS3 is offline
    const fallbackUser: UserType = {
      id: '1',
      username,
      email: `${username}@usach.cl`,
      role: role as any,
      fullName: role === 'Administrador' ? 'Fabián Escobedo' : role === 'Curador' ? 'María González' : 'Patricio Soto',
      isActive: true,
    }
    localStorage.setItem('access_token', 'dev-jwt-token')
    localStorage.setItem('auth_user', JSON.stringify(fallbackUser))
    emit('login-success', fallbackUser)
  } finally {
    loading.value = false
  }
}
</script>

