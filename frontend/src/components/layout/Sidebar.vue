<template>
  <aside
    class="flex flex-col h-full transition-all duration-300"
    :style="{
      width: collapsed ? '64px' : '260px',
      background: '#00aea7',
      flexShrink: 0,
    }"
  >
    <!-- Logo -->
    <div
      :class="[
        'flex items-center gap-3 py-5 border-b border-white/[0.15]',
        collapsed ? 'justify-center px-2' : 'px-4'
      ]"
    >
      <button
        @click="$emit('toggle')"
        :title="collapsed ? 'Desplegar sidebar' : 'Cerrar sidebar'"
        class="flex-shrink-0 w-14 h-14 rounded-xl bg-[#00aea7] p-1 flex items-center justify-center cursor-pointer hover:opacity-95 shadow-sm transition-all overflow-hidden"
      >
        <div class="w-full h-full rounded-lg bg-white/20 flex items-center justify-center text-white font-bold text-xl tracking-tighter">
          U
        </div>
      </button>

      <div v-if="!collapsed" class="overflow-hidden">
        <p class="text-white text-xs font-semibold leading-tight">Agente Inteligente</p>
        <p class="text-[10px] leading-tight text-white/85">Enriquecimiento de Metadatos</p>
        <p class="text-[10px] leading-tight text-white/75">DSpace-CRIS | VRIIC</p>
      </div>

      <button
        v-if="!collapsed"
        @click="$emit('toggle')"
        title="Cerrar sidebar"
        class="ml-auto text-white/70 hover:text-white transition-colors cursor-pointer"
      >
        <Menu :size="16" />
      </button>
    </div>

    <!-- Navigation items -->
    <nav class="flex-1 py-3 overflow-y-auto">
      <button
        v-for="item in navItems"
        :key="item.key"
        @click="$emit('nav', item.key)"
        :title="collapsed ? item.label : undefined"
        :class="[
          'w-full flex items-center gap-3 py-2.5 text-left transition-all duration-150 group cursor-pointer',
          collapsed ? 'justify-center px-2' : 'px-4',
          current === item.key ? 'bg-[#00968f]' : 'hover:bg-[#00968f]'
        ]"
        :style="{
          borderLeft: current === item.key ? '3px solid #ffffff' : '3px solid transparent'
        }"
      >
        <component
          :is="item.icon"
          :size="18"
          :style="{
            color: current === item.key ? '#ffffff' : 'rgba(255, 255, 255, 0.85)',
            flexShrink: 0
          }"
        />
        <span
          v-if="!collapsed"
          class="text-sm font-medium truncate group-hover:text-white transition-colors"
          :style="{
            color: current === item.key ? '#ffffff' : 'rgba(255, 255, 255, 0.85)'
          }"
        >
          {{ item.label }}
        </span>
      </button>
    </nav>

    <!-- Footer -->
    <div v-if="!collapsed" class="px-4 py-4 border-t border-white/[0.15]">
      <p class="text-[10px] text-white/75">USACH · VRIIC</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import {
  LayoutDashboard,
  FileText,
  BookOpen,
  ShieldCheck,
  CheckSquare,
  ClipboardList,
  BarChart2,
  Users,
  Settings,
  User,
  Menu
} from 'lucide-vue-next'
import type { Page } from '../../types'

defineProps<{
  current: Page
  collapsed: boolean
}>()

defineEmits<{
  (e: 'nav', page: Page): void
  (e: 'toggle'): void
}>()

const navItems = [
  { key: 'dashboard' as Page, label: 'Dashboard', icon: LayoutDashboard },
  { key: 'monitoreo' as Page, label: 'Monitoreo de registros', icon: FileText },
  { key: 'analisis' as Page, label: 'Análisis documental PDF', icon: BookOpen },
  { key: 'validacion' as Page, label: 'Validación de metadatos', icon: ShieldCheck },
  { key: 'aprobacion' as Page, label: 'Aprobación de metadatos', icon: CheckSquare },
  { key: 'auditoria' as Page, label: 'Auditoría', icon: ClipboardList },
  { key: 'reportes' as Page, label: 'Reportes y Estadísticas', icon: BarChart2 },
  { key: 'usuarios' as Page, label: 'Gestión de usuarios', icon: Users },
  { key: 'configuracion' as Page, label: 'Configuración', icon: Settings },
  { key: 'perfil' as Page, label: 'Perfil', icon: User },
]
</script>

