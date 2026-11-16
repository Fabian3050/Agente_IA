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
        <span v-if="notifications.length > 0" class="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#F57C00]" />
      </button>

      <!-- Notifications Dropdown -->
      <div
        v-if="showNotifications"
        class="absolute right-36 top-12 w-80 bg-white rounded-xl shadow-xl border border-gray-100 p-4 z-50"
      >
        <div class="flex items-center justify-between pb-2 mb-2 border-b border-gray-100">
          <span class="text-xs font-semibold text-[#1a2332]">Notificaciones del sistema</span>
          <span class="text-[10px] text-[#00aea7] font-medium cursor-pointer" @click="showNotifications = false">Cerrar</span>
        </div>
        <div v-if="notifications.length === 0" class="py-4 text-center text-xs text-gray-400">
          No hay notificaciones ni eventos pendientes.
        </div>
        <div v-else class="space-y-3">
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
          <p class="text-xs font-medium text-[#1a2332] leading-tight">{{ user?.fullName || user?.name || 'Usuario USACH' }}</p>
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
import { ref, computed, onMounted } from 'vue'
import { Bell, LogOut } from 'lucide-vue-next'
import { auditService } from '../../services/auditService'
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
  const name = props.user?.fullName || props.user?.name || 'US'
  const parts = name.trim().split(' ')
  if (parts.length >= 2) return `${parts[0][0]}${parts[1][0]}`.toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const notifications = ref<{ text: string; time: string; color: string }[]>([])

onMounted(async () => {
  try {
    const logs = await auditService.getAuditLogs()
    notifications.value = (logs || []).slice(0, 5).map(l => ({
      text: `${l.action}${l.item_id ? ` · Ítem ${l.item_id}` : ''}${l.user_name ? ` (${l.user_name})` : ''}`,
      time: l.timestamp ? new Date(l.timestamp).toLocaleTimeString('es-CL', { hour: '2-digit', minute: '2-digit' }) : 'Reciente',
      color: l.action.includes('REJECT') ? '#d32f2f' : l.action.includes('APPROV') ? '#00aea7' : '#1565C0'
    }))
  } catch {
    notifications.value = []
  }
})

const meta: Record<Page, { title: string; desc: string }> = {
  dashboard: { title: 'Dashboard', desc: 'Estadísticas generales del sistema de enriquecimiento de metadatos.' },
  monitoreo: { title: 'Monitoreo de Registros', desc: 'Supervisión de registros incompletos detectados en el repositorio DSpace-CRIS.' },
  recuperacion: { title: 'Reportes y Estadísticas de Recuperación', desc: 'Análisis integral del rendimiento del agente inteligente, consultas y conectividad con fuentes externas.' },
  validacion: { title: 'Validación Humana de Metadatos', desc: 'Revisión de los metadatos extraídos por el agente para asegurar su calidad y precisión.' },
  aprobacion: { title: 'Aprobación Humana de Metadatos', desc: 'Revisión final y decisión humana para autorizar metadatos validados previamente.' },
  auditoria: { title: 'Auditoría y Trazabilidad', desc: 'Línea temporal completa e inmutable del proceso de enriquecimiento por registro.' },
  reportes: { title: 'Reportes y Estadísticas de Recuperación', desc: 'Análisis integral del rendimiento del agente inteligente, consultas y conectividad con fuentes externas.' },
  usuarios: { title: 'Gestión de Usuarios', desc: 'Administración, asignación de roles RBAC y control de acceso OpenID Connect.' },
  configuracion: { title: 'Configuración', desc: 'Configuración de microservicios, endpoints de conexión y parámetros de IA.' },
  perfil: { title: 'Perfil de Usuario', desc: 'Información del usuario autenticado, credenciales y preferencias institucionales.' },
}
</script>

