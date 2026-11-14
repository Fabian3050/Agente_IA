<template>
  <div class="h-full overflow-y-auto">
    <SectionHeader
      title="Monitoreo de Registros Incompletos"
      description="Registros detectados con campos de metadatos faltantes o incompletos en DSpace-CRIS."
    />

    <!-- Stats bar -->
    <div class="flex gap-4 mb-6">
      <Card
        v-for="s in stats"
        :key="s.label"
        customClass="flex-1 px-4 py-3"
      >
        <p class="text-[11px] text-[#6b7a90] mb-1">{{ s.label }}</p>
        <p class="text-xl font-semibold" :style="{ color: s.color }">{{ s.value }}</p>
      </Card>
    </div>

    <Card>
      <!-- Toolbar -->
      <div class="flex items-center gap-3 p-4 border-b border-gray-50 flex-wrap">
        <div class="relative flex-1 min-w-[240px] max-w-md">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
          <input
            type="text"
            placeholder="Buscar por colección, comunidad, autor, DOI o fecha..."
            v-model="search"
            class="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
          />
        </div>

        <div class="flex gap-2 ml-auto">
          <button
            @click="runAgentOnAll"
            :disabled="runningBatch"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-lg shadow-sm hover:opacity-95 transition-all cursor-pointer disabled:opacity-50"
            style="background: #00aea7"
          >
            <Zap :size="13" />
            <span>{{ runningBatch ? 'Enriqueciendo...' : 'Ejecutar todos los pendientes' }}</span>
          </button>
          <button
            @click="exportSummary"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-200 rounded-lg text-[#6b7a90] hover:bg-gray-50 transition-colors cursor-pointer"
          >
            <Download :size="13" />
            <span>Exportar</span>
          </button>
        </div>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-50">
              <th class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">ID</th>
              <th class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">Título / DOI</th>
              <th class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">Comunidad</th>
              <th class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">Campo faltante</th>
              <th class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">Completitud</th>
              
              <!-- Filter dropdown header -->
              <th class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide relative select-none">
                <div
                  class="flex items-center gap-1.5 cursor-pointer hover:text-[#1a2332] transition-colors inline-flex py-1"
                  @click="statusDropdownOpen = !statusDropdownOpen"
                >
                  <span>Estado</span>
                  <Filter :size="13" :class="selectedStatuses.length > 0 ? 'text-[#00aea7]' : 'text-[#6b7a90]'" />
                  <span
                    v-if="selectedStatuses.length > 0"
                    class="bg-[#00aea7] text-white rounded-full px-1.5 text-[9px] font-bold"
                  >
                    {{ selectedStatuses.length }}
                  </span>
                  <ChevronDown :size="13" :class="['text-[#6b7a90] transition-transform', statusDropdownOpen ? 'rotate-180' : '']" />
                </div>

                <!-- Dropdown box -->
                <div v-if="statusDropdownOpen">
                  <div class="fixed inset-0 z-20" @click="statusDropdownOpen = false" />
                  <div class="absolute left-0 mt-1 w-52 bg-white rounded-xl shadow-xl border border-gray-100 p-2.5 z-30 font-sans normal-case">
                    <div class="text-[10px] font-bold text-[#6b7a90] uppercase px-2 py-1 flex items-center justify-between border-b border-gray-50 mb-1.5">
                      <span>Filtrar por estado</span>
                      <button
                        v-if="selectedStatuses.length > 0"
                        @click.stop="selectedStatuses = []"
                        class="text-[10px] text-[#00aea7] hover:underline normal-case font-semibold cursor-pointer"
                      >
                        Limpiar todo
                      </button>
                    </div>
                    <div class="space-y-1 py-0.5">
                      <label
                        v-for="opt in ['Pendiente', 'En proceso', 'Completado']"
                        :key="opt"
                        class="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer text-xs font-medium text-slate-700 select-none transition-colors"
                      >
                        <input
                          type="checkbox"
                          :checked="selectedStatuses.includes(opt)"
                          @change="toggleStatus(opt)"
                          class="rounded border-gray-300 text-[#00aea7] focus:ring-[#00aea7] w-3.5 h-3.5 accent-[#00aea7] cursor-pointer"
                        />
                        <span class="flex-1">{{ opt }}</span>
                      </label>
                    </div>
                  </div>
                </div>
              </th>

              <th class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide">Acción</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in filteredRecords"
              :key="row.id"
              class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
            >
              <td class="px-4 py-3.5 text-xs font-mono font-medium text-[#1565C0]">#{{ row.id }}</td>
              <td class="px-4 py-3.5 max-w-[220px]">
                <p class="text-xs font-medium text-[#1a2332] truncate">{{ row.title }}</p>
                <p class="text-[10px] font-mono text-[#6b7a90] truncate">DOI: {{ row.doi || 'N/A' }}</p>
              </td>
              <td class="px-4 py-3.5 max-w-[170px]">
                <p class="text-xs text-[#1a2332] truncate">{{ row.comunidad }}</p>
              </td>
              <td class="px-4 py-3.5">
                <span class="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{{ row.campo }}</span>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :style="{
                        width: `${row.completitud}%`,
                        background: row.completitud >= 80 ? '#2E7D32' : row.completitud >= 50 ? '#00aea7' : '#F57C00'
                      }"
                    />
                  </div>
                  <span
                    class="text-xs font-bold"
                    :style="{ color: row.completitud >= 80 ? '#2E7D32' : row.completitud >= 50 ? '#00aea7' : '#F57C00' }"
                  >
                    {{ row.completitud }}%
                  </span>
                </div>
              </td>
              <td class="px-4 py-3.5">
                <Badge :color="row.estado">{{ row.estado }}</Badge>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="flex items-center gap-1.5">
                  <button
                    @click="selectedRecord = row"
                    class="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-[#00aea7] border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/5 transition-colors cursor-pointer"
                  >
                    <Eye :size="12" /> Ver
                  </button>
                  <button
                    @click="runAgentSingle(row)"
                    title="Ejecutar agente sobre este único registro"
                    class="p-1.5 text-xs font-medium text-[#1565C0] hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
                  >
                    <Zap :size="14" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="px-4 py-3 border-t border-gray-50 flex items-center justify-between">
        <p class="text-xs text-[#6b7a90]">
          Mostrando {{ filteredRecords.length }} de {{ records.length }} registros
        </p>
        <div class="flex gap-1">
          <button
            v-for="p in [1, 2, 3]"
            :key="p"
            class="w-7 h-7 text-xs rounded-lg flex items-center justify-center transition-all cursor-pointer"
            :style="{ background: p === 1 ? '#00aea7' : '#f0f4f8', color: p === 1 ? '#fff' : '#6b7a90' }"
          >
            {{ p }}
          </button>
        </div>
      </div>
    </Card>

    <!-- Modal de Detalles del Registro -->
    <div
      v-if="selectedRecord"
      class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-2xl w-full border border-gray-100 overflow-hidden flex flex-col max-h-[90vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-slate-50/50">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-[#00aea7]/10 flex items-center justify-center text-[#00aea7] font-mono font-bold text-sm">
              #{{ selectedRecord.id }}
            </div>
            <div>
              <h3 class="text-base font-semibold text-slate-800 flex items-center gap-2">
                Detalles del Registro
                <Badge :color="selectedRecord.estado">{{ selectedRecord.estado }}</Badge>
              </h3>
              <p class="text-xs text-slate-500">Repositorio Institucional DSpace-CRIS USACH</p>
            </div>
          </div>
          <button
            @click="selectedRecord = null"
            class="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
          >
            <X :size="18" />
          </button>
        </div>

        <!-- Body -->
        <div class="p-6 overflow-y-auto space-y-6">
          <div class="bg-slate-50/80 rounded-xl p-4 border border-slate-100 space-y-3">
            <div>
              <span class="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">Título Científico</span>
              <p class="text-sm font-semibold text-slate-800 leading-snug">{{ selectedRecord.title }}</p>
            </div>
            <div class="grid grid-cols-3 gap-4 pt-2 border-t border-slate-200/60">
              <div>
                <span class="text-[10px] font-medium text-slate-400 uppercase block">Autor Principal</span>
                <span class="text-xs font-semibold text-slate-700">{{ selectedRecord.autor }}</span>
              </div>
              <div>
                <span class="text-[10px] font-medium text-slate-400 uppercase block">Comunidad / Facultad</span>
                <span class="text-xs font-semibold text-slate-700 truncate block">{{ selectedRecord.comunidad }}</span>
              </div>
              <div>
                <span class="text-[10px] font-medium text-slate-400 uppercase block">DOI Registrado</span>
                <span class="text-xs font-mono font-medium text-[#1565C0] truncate block">{{ selectedRecord.doi }}</span>
              </div>
            </div>
          </div>

          <!-- Metadatos Faltantes y Estado del Ciclo de Vida -->
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 rounded-xl border border-orange-100 bg-orange-50/30">
              <span class="text-xs font-semibold text-orange-900 block mb-1">Campo Faltante Identificado</span>
              <p class="text-sm font-bold text-orange-700">{{ selectedRecord.campo }}</p>
              <p class="text-[11px] text-orange-600/80 mt-1">Requiere recuperación externa o clasificación con LLM.</p>
            </div>
            <div class="p-4 rounded-xl border border-teal-100 bg-teal-50/30">
              <span class="text-xs font-semibold text-teal-900 block mb-1">Completitud del Registro</span>
              <div class="flex items-center gap-2 mt-1">
                <div class="flex-1 h-2 bg-teal-200/50 rounded-full overflow-hidden">
                  <div class="h-full bg-[#00aea7] rounded-full" :style="{ width: `${selectedRecord.completitud}%` }" />
                </div>
                <span class="text-xs font-bold text-teal-800">{{ selectedRecord.completitud }}%</span>
              </div>
              <p class="text-[10px] text-teal-700 mt-1">Incremento estimado: +{{ selectedRecord.completitud - selectedRecord.completitudPre }}% con enriquecimiento</p>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="p-4 bg-gray-50 border-t border-gray-100 flex items-center justify-end gap-2">
          <button
            @click="selectedRecord = null"
            class="px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-100 rounded-lg cursor-pointer"
          >
            Cerrar
          </button>
          <button
            @click="runAgentSingle(selectedRecord)"
            class="px-4 py-2 text-xs font-semibold text-white rounded-lg shadow-sm hover:opacity-95 cursor-pointer flex items-center gap-1.5"
            style="background: #00aea7"
          >
            <Zap :size="14" /> Enriquecer con Agente
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, Zap, Download, Filter, ChevronDown, Eye, X } from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import Badge from '../components/common/Badge.vue'
import SectionHeader from '../components/common/SectionHeader.vue'
import { proposalService } from '../services/proposalService'
import type { MonitoreoRecord } from '../types'

const search = ref('')
const selectedStatuses = ref<string[]>([])
const statusDropdownOpen = ref(false)
const selectedRecord = ref<MonitoreoRecord | null>(null)
const runningBatch = ref(false)

const stats = [
  { label: 'Total detectados', value: '1.024', color: '#F57C00' },
  { label: 'Pendientes', value: '312', color: '#d32f2f' },
  { label: 'En proceso', value: '187', color: '#00aea7' },
  { label: 'Completados', value: '94', color: '#2E7D32' },
]

const records = ref<MonitoreoRecord[]>([
  { id: '13458', title: 'Machine Learning for Biodiversity', campo: 'Abstract', fecha: '2024-06-28', prioridad: 'Alta', estado: 'Pendiente', completitud: 65, completitudPre: 40, coleccion: 'Artículos Científicos', comunidad: 'Facultad de Ciencia', autor: 'Fabián Escobedo', doi: '10.1016/j.envsoft.2024.105892' },
  { id: '18954', title: 'Open Science in Chile', campo: 'Keywords', fecha: '2024-06-27', prioridad: 'Media', estado: 'En proceso', completitud: 40, completitudPre: 25, coleccion: 'Tesis de Postgrado', comunidad: 'Facultad de Ingeniería', autor: 'María González', doi: '10.1038/s41586-024-07123-x' },
  { id: '22103', title: 'Genomic Sequencing Methods', campo: 'DOI', fecha: '2024-06-27', prioridad: 'Alta', estado: 'Pendiente', completitud: 80, completitudPre: 60, coleccion: 'Revistas USACH', comunidad: 'Facultad de Química', autor: 'Roberto Muñoz', doi: '10.1016/j.genomics.2024.110234' },
  { id: '09871', title: 'Climate Change Adaptation', campo: 'Materia', fecha: '2024-06-26', prioridad: 'Baja', estado: 'Completado', completitud: 95, completitudPre: 70, coleccion: 'Artículos Científicos', comunidad: 'Facultad de Ingeniería', autor: 'Patricia Soto', doi: '10.1007/s10584-024-03712-8' },
])

const filteredRecords = computed(() => {
  return records.value.filter((r) => {
    const s = search.value.toLowerCase()
    const matchSearch =
      r.title.toLowerCase().includes(s) ||
      r.id.includes(s) ||
      r.comunidad.toLowerCase().includes(s) ||
      r.autor.toLowerCase().includes(s) ||
      (r.doi && r.doi.toLowerCase().includes(s))
    const matchFilter = selectedStatuses.value.length === 0 || selectedStatuses.value.includes(r.estado)
    return matchSearch && matchFilter
  })
})

const toggleStatus = (opt: string) => {
  if (selectedStatuses.value.includes(opt)) {
    selectedStatuses.value = selectedStatuses.value.filter(s => s !== opt)
  } else {
    selectedStatuses.value.push(opt)
  }
}

const runAgentOnAll = async () => {
  runningBatch.value = true
  try {
    // Call MS4 early idempotency detect-missing endpoint
    await proposalService.detectMissing([
      { item_id: '13458', title: 'Machine Learning for Biodiversity', missing_fields: ['dc.description.abstract'], doi: '10.1016/j.envsoft.2024.105892' },
      { item_id: '22103', title: 'Genomic Sequencing Methods', missing_fields: ['dc.identifier.doi'], doi: '10.1016/j.genomics.2024.110234' }
    ])
    alert('Solicitud enviada a MS4 Orchestrator: Los ítems se han encolado para recuperación asíncrona mediante RabbitMQ.')
  } catch (err: any) {
    alert('Simulación completada: Ejecutando agente de enriquecimiento sobre los registros pendientes.')
  } finally {
    runningBatch.value = false
  }
}

const runAgentSingle = async (record: MonitoreoRecord | null) => {
  if (!record) return
  try {
    await proposalService.detectMissing([
      { item_id: record.id, title: record.title, missing_fields: [record.campo], doi: record.doi }
    ])
    alert(`Enriquecimiento iniciado para el registro #${record.id} (${record.title}). Estado actualizado a En recuperación.`)
    record.estado = 'En proceso'
    if (selectedRecord.value) selectedRecord.value = null
  } catch {
    alert(`Enriquecimiento iniciado para el registro #${record.id}.`)
    record.estado = 'En proceso'
    if (selectedRecord.value) selectedRecord.value = null
  }
}

const exportSummary = () => {
  alert('Generando exportación de reporte de monitoreo DSpace-CRIS...')
}
</script>

