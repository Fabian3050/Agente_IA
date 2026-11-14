<template>
  <header class="h-16 bg-white border-b border-black/[0.06] flex items-center px-6 gap-4 flex-shrink-0">
    <div class="flex-1 min-w-0">
      <h1 class="text-base font-semibold text-[#1a2332] leading-tight">{{ meta[page]?.title }}</h1>
      <p class="text-xs text-[#6b7a90] truncate">{{ meta[page]?.desc }}</p>
    </div>

    <div class="flex items-center gap-3 relative">
      <!-- Notification Bell -->
      <button
        @click="showNotifications = !showNotifications"
        class="relative p-2 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
        title="Ver notificaciones y alertas del sistema"
      >
        <Bell :size="18" class="text-[#6b7a90]" />
        <span class="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#F57C00]" />
      </button>

      <!-- Notifications Dropdown -->
      <div
        v-if="showNotifications"
        class="absolute right-36 top-12 w-80 bg-white rounded-xl shadow-xl border border-gray-100 p-4 z-50"
      >
        <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-100">
          <span class="text-xs font-semibold text-[#1a2332]">Notificaciones recientes</span>
          <span class="text-[10px] text-[#00aea7] font-medium cursor-pointer" @click="showNotifications = false">Cerrar</span>
        </div>
        <div class="space-y-3">
          <div
            v-for="(n, idx) in notifications"
            :key="idx"
            class="flex items-start gap-2 text-xs"
          >
            <span
              class="w-2 h-2 rounded-full mt-1 flex-shrink-0"
              :style="{ backgroundColor: n.color }"
            />
            <div class="flex-1 min-w-0">
              <p class="text-[#1a2332] font-medium leading-snug">{{ n.text }}</p>
              <p class="text-[10px] text-[#6b7a90] mt-0.5">{{ n.time }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- User Profile / Pill -->
      <div
        @click="$emit('nav', 'perfil')"
        class="flex items-center gap-2.5 pl-3 border-l border-gray-200 cursor-pointer hover:opacity-85 transition-opacity"
      >
        <div class="w-8 h-8 rounded-full bg-[#00aea7]/15 flex items-center justify-center text-[#00aea7] font-semibold text-xs border border-[#00aea7]/30">
          {{ userInitials }}
        </div>
        <div class="hidden sm:block text-left">
          <p class="text-xs font-medium text-[#1a2332] leading-tight">{{ user?.fullName || 'Fabián Escobedo' }}</p>
          <div class="flex items-center gap-1">
            <span class="text-[10px] text-[#6b7a90]">{{ user?.role || 'Curador' }}</span>
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block"></span>
          </div>
        </div>
      </div>

      <!-- Logout button -->
      <button
        @click="$emit('logout')"
        title="Cerrar sesión"
        class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
      >
        <LogOut :size="18" />
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Bell, LogOut } from 'lucide-vue-next'
import type { Page, User } from '../../types'

const props = defineProps<{
  page: Page
  user: User | null
}>()

defineEmits<{
  (e: 'nav', page: Page): void
  (e: 'logout'): void
}>()

const showNotifications = ref(false)

const userInitials = computed(() => {
  const name = props.user?.fullName || 'FE'
  const parts = name.split(' ')
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const notifications = [
  { text: 'Registro #18954 requiere validación humana por coincidencia dudosa', time: 'Hace 5 min', color: '#F57C00' },
  { text: 'Proceso de extracción de PDF finalizado para 3 ítems', time: 'Hace 15 min', color: '#00aea7' },
  { text: 'Exportación CSV en dos pasos generada con éxito (0 celdas vacías)', time: 'Hace 30 min', color: '#2E7D32' },
]

const meta: Record<Page, { title: string; desc: string }> = {
  dashboard: { title: 'Dashboard', desc: 'Estadísticas generales del sistema de enriquecimiento de metadatos.' },
  monitoreo: { title: 'Monitoreo de Registros', desc: 'Supervisión de registros incompletos detectados en el repositorio DSpace-CRIS.' },
  recuperacion: { title: 'Reportes y Estadísticas de Recuperación', desc: 'Análisis integral del rendimiento del agente inteligente, consultas y conectividad con fuentes externas.' },
  analisis: { title: 'Análisis Documental PDF', desc: 'Extracción y análisis automatizado de metadatos desde documentos científicos.' },
  validacion: { title: 'Validación Humana de Metadatos', desc: 'Revisión de los metadatos extraídos por el agente para asegurar su calidad y precisión.' },
  aprobacion: { title: 'Aprobación Humana de Metadatos', desc: 'Revisión final y decisión humana para autorizar metadatos validados previamente.' },
  auditoria: { title: 'Auditoría y Trazabilidad', desc: 'Línea temporal completa e inmutable del proceso de enriquecimiento por registro.' },
  reportes: { title: 'Reportes y Estadísticas de Recuperación', desc: 'Análisis integral del rendimiento del agente inteligente, consultas y conectividad con fuentes externas.' },
  usuarios: { title: 'Gestión de Usuarios', desc: 'Administración, asignación de roles RBAC y control de acceso OpenID Connect.' },
  configuracion: { title: 'Configuración', desc: 'Configuración de microservicios, endpoints de conexión y parámetros de IA.' },
  perfil: { title: 'Perfil de Usuario', desc: 'Información del usuario autenticado, credenciales y preferencias institucionales.' },
}
</script>

