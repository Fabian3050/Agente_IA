<template>
  <div class="flex gap-6 h-full min-h-0">
    <!-- Main content -->
    <div class="flex-1 min-w-0 overflow-y-auto pr-1">
      <SectionHeader
        title="Dashboard"
        description="Vista general del sistema de enriquecimiento de metadatos."
      />

      <!-- KPIs -->
      <div class="grid grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
        <Card v-for="kpi in kpis" :key="kpi.label" customClass="p-4">
          <div class="flex items-start gap-3">
            <div
              class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
              :style="{ background: kpi.bg }"
            >
              <component :is="kpi.icon" :size="20" :style="{ color: kpi.color }" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-xs text-[#6b7a90] leading-tight mb-1">{{ kpi.label }}</p>
              <p class="text-2xl font-semibold" :style="{ color: kpi.color }">{{ kpi.value }}</p>
              <div v-if="kpi.progress" class="mt-2 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  class="h-full rounded-full transition-all duration-500"
                  :style="{ width: `${kpi.progress}%`, background: kpi.color }"
                />
              </div>
            </div>
          </div>
        </Card>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <!-- Donut Chart -->
        <Card customClass="p-5">
          <h3 class="text-sm font-semibold text-[#1a2332] mb-4">Distribución de metadatos incompletos</h3>
          <div class="flex items-center gap-6">
            <!-- Native SVG Donut Chart -->
            <div class="relative w-40 h-40 flex-shrink-0 flex items-center justify-center">
              <svg viewBox="0 0 100 100" class="w-full h-full -rotate-90 transform">
                <!-- Slices calculated via stroke-dasharray -->
                <circle
                  v-for="(slice, i) in calculatedDonutSlices"
                  :key="i"
                  cx="50"
                  cy="50"
                  r="35"
                  fill="transparent"
                  :stroke="slice.color"
                  stroke-width="18"
                  :stroke-dasharray="`${slice.dashLength} ${100 - slice.dashLength}`"
                  :stroke-dashoffset="slice.dashOffset"
                />
              </svg>
              <div class="absolute inset-0 flex flex-col items-center justify-center text-center">
                <span class="text-xs text-gray-400">Total</span>
                <span class="text-base font-bold text-gray-800">100%</span>
              </div>
            </div>

            <!-- Legend -->
            <div class="flex flex-col gap-2 flex-1 min-w-0">
              <div
                v-for="d in donutData"
                :key="d.name"
                class="flex items-center gap-2"
              >
                <div class="w-2.5 h-2.5 rounded-sm flex-shrink-0" :style="{ background: d.color }" />
                <span class="text-xs text-[#6b7a90] truncate">{{ d.name }}</span>
                <span class="text-xs font-semibold text-[#1a2332] ml-auto pl-2">{{ d.value }}%</span>
              </div>
            </div>
          </div>
        </Card>

        <!-- Bar Chart -->
        <Card customClass="p-5">
          <h3 class="text-sm font-semibold text-[#1a2332] mb-4">Registros enriquecidos esta semana</h3>
          <div class="h-44 w-full flex items-end justify-between gap-3 pt-6 pb-2 px-2 border-b border-gray-100">
            <div
              v-for="item in barData"
              :key="item.day"
              class="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group"
            >
              <span class="text-[10px] font-medium text-gray-400 group-hover:text-[#00aea7] transition-colors">
                {{ item.value }}
              </span>
              <div
                class="w-full max-w-[28px] rounded-t-md transition-all duration-300 group-hover:opacity-85"
                :style="{
                  height: `${(item.value / maxBarValue) * 100}%`,
                  backgroundColor: '#00aea7'
                }"
              />
              <span class="text-[11px] text-[#6b7a90] font-medium">{{ item.day }}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- Recent Activity Panel -->
    <aside class="w-72 flex-shrink-0 overflow-y-auto hidden lg:block">
      <Card customClass="p-4 h-full">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-sm font-semibold text-[#1a2332]">Actividad reciente</h3>
          <span
            @click="$emit('nav', 'auditoria')"
            class="text-xs text-[#00aea7] font-medium cursor-pointer hover:underline"
          >
            Ver todo
          </span>
        </div>
        <div class="flex flex-col gap-0">
          <div
            v-for="(item, i) in recentActivity"
            :key="i"
            class="flex gap-3 py-3 border-b border-gray-50 last:border-0"
          >
            <component
              :is="item.icon"
              :size="15"
              :style="{ color: item.color, flexShrink: 0, marginTop: '2px' }"
            />
            <div class="flex-1 min-w-0">
              <p class="text-xs text-[#1a2332] leading-snug">{{ item.text }}</p>
              <div class="flex items-center gap-1.5 mt-1">
                <span class="text-[11px] text-[#6b7a90]">{{ item.date }}</span>
                <span class="w-1 h-1 rounded-full bg-gray-400"></span>
                <span class="text-[11px] text-[#6b7a90]">{{ item.time }}</span>
                <span class="w-1 h-1 rounded-full bg-gray-400"></span>
                <span class="text-[11px] text-[#6b7a90] truncate">{{ item.user }}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Database,
  AlertCircle,
  CheckCircle,
  Clock,
  TrendingUp,
  Zap,
  AlertTriangle
} from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import SectionHeader from '../components/common/SectionHeader.vue'
import type { Page } from '../types'

defineEmits<{
  (e: 'nav', page: Page): void
}>()

const kpis = [
  { label: 'Total registros monitoreados', value: '14.327', icon: Database, color: '#1565C0', bg: '#e3f2fd' },
  { label: 'Registros incompletos', value: '1.024', icon: AlertCircle, color: '#F57C00', bg: '#fff3e0' },
  { label: 'Metadatos enriquecidos', value: '8.912', icon: CheckCircle, color: '#00aea7', bg: '#e0f7f6' },
  { label: 'Pendientes de validación', value: '123', icon: Clock, color: '#7B1FA2', bg: '#f3e5f5' },
  { label: 'Porcentaje de completitud', value: '62.2%', icon: TrendingUp, color: '#2E7D32', bg: '#e8f5e9', progress: 62 },
  { label: 'Tiempo prom. por registro', value: '1 min 48 seg', icon: Zap, color: '#E53935', bg: '#ffebee' },
]

const donutData = [
  { name: 'Abstract', value: 42, color: '#00aea7' },
  { name: 'Palabras clave', value: 26, color: '#F57C00' },
  { name: 'Área OCDE', value: 26, color: '#7B1FA2' },
  { name: 'Área ODS', value: 12, color: '#2E7D32' },
  { name: 'Derechos de acceso', value: 4, color: '#E53935' },
]

const barData = [
  { day: 'Lun', value: 187 },
  { day: 'Mar', value: 243 },
  { day: 'Mié', value: 198 },
  { day: 'Jue', value: 312 },
  { day: 'Vie', value: 276 },
  { day: 'Sáb', value: 94 },
  { day: 'Dom', value: 41 },
]

const maxBarValue = Math.max(...barData.map(b => b.value))

// Circumference of radius 35 = 2 * PI * 35 = ~219.9
const circumference = 2 * Math.PI * 35

const calculatedDonutSlices = computed(() => {
  let accumulated = 0
  return donutData.map((item) => {
    const fraction = item.value / 100
    const dashLength = fraction * circumference
    const dashOffset = -accumulated
    accumulated += dashLength
    return {
      color: item.color,
      dashLength,
      dashOffset,
    }
  })
})

const recentActivity = [
  { icon: CheckCircle, color: '#00aea7', text: 'Abstract recuperado desde OpenAlex', date: '28 jun', time: '09:16', user: 'Agente IA' },
  { icon: CheckCircle, color: '#00aea7', text: 'DOI validado mediante CrossRef', date: '28 jun', time: '09:14', user: 'Agente IA' },
  { icon: CheckCircle, color: '#00aea7', text: 'PDF analizado correctamente', date: '28 jun', time: '09:10', user: 'Agente IA' },
  { icon: AlertTriangle, color: '#F57C00', text: 'Registro #18954 requiere revisión humana', date: '28 jun', time: '08:58', user: 'Sistema' },
  { icon: CheckCircle, color: '#00aea7', text: 'Metadato aprobado por María González', date: '28 jun', time: '08:45', user: 'María González' },
  { icon: CheckCircle, color: '#2E7D32', text: 'Registro #09871 listo para ser publicado.', date: '27 jun', time: '17:32', user: 'Sistema' },
  { icon: AlertTriangle, color: '#F57C00', text: 'Registro #22103 pendiente de validación.', date: '27 jun', time: '16:20', user: 'Monitor' },
]
</script>

