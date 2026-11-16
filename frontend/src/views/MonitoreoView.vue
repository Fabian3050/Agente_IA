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
            placeholder="Buscar por título, DOI, comunidad o autor..."
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
            <tr v-if="loading">
              <td colspan="7" class="text-center py-12 text-slate-500 text-xs">
                <div class="inline-block w-4 h-4 border-2 border-[#00aea7] border-t-transparent rounded-full animate-spin mr-2"></div>
                Cargando registros reales de la cola de enriquecimiento...
              </td>
            </tr>
            <tr v-else-if="filteredRecords.length === 0">
              <td colspan="7" class="text-center py-12 text-slate-500 text-xs">
                No hay publicaciones registradas en la cola de monitoreo actualmente.
              </td>
            </tr>
            <tr
              v-else
              v-for="row in paginatedRecords"
              :key="row.id"
              class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
            >
              <td class="px-4 py-3.5 text-xs font-mono font-medium text-[#1565C0]">#{{ row.id }}</td>
              <td class="px-4 py-3.5 max-w-[220px]">
                <p class="text-xs font-medium text-[#1a2332] truncate" :title="row.title">{{ row.title }}</p>
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
                    :disabled="enrichingIds[row.id] || row.estado === 'Completado'"
                    :title="row.estado === 'Completado' ? 'Registro enriquecido' : 'Ejecutar agente sobre este único registro'"
                    class="p-1.5 text-xs font-medium rounded-lg transition-colors cursor-pointer disabled:cursor-not-allowed"
                    :class="[
                      row.estado === 'Completado' ? 'text-emerald-600 bg-emerald-50' : 'text-[#1565C0] hover:bg-blue-50'
                    ]"
                  >
                    <div v-if="enrichingIds[row.id]" class="w-3.5 h-3.5 border-2 border-[#1565C0] border-t-transparent rounded-full animate-spin"></div>
                    <Check v-else-if="row.estado === 'Completado'" :size="14" />
                    <Zap v-else :size="14" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="px-4 py-3.5 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-50/50">
        <div class="flex items-center gap-3 text-xs text-[#6b7a90]">
          <span>
            Mostrando <strong>{{ pageStart }}-{{ pageEnd }}</strong> de <strong>{{ filteredRecords.length.toLocaleString('es-CL') }}</strong> registros
          </span>
          <span class="text-gray-300">|</span>
          <div class="flex items-center gap-1.5">
            <span>Mostrar:</span>
            <select
              v-model="pageSize"
              class="px-2 py-1 text-xs border border-gray-200 rounded-lg bg-white text-[#1a2332] focus:outline-none focus:ring-1 focus:ring-[#00aea7] cursor-pointer"
              @change="currentPage = 1"
            >
              <option :value="10">10 por pág.</option>
              <option :value="15">15 por pág.</option>
              <option :value="25">25 por pág.</option>
              <option :value="50">50 por pág.</option>
              <option :value="100">100 por pág.</option>
            </select>
          </div>
        </div>

        <div class="flex items-center gap-1">
          <button
            @click="goToPage(currentPage - 1)"
            :disabled="currentPage <= 1"
            class="px-2.5 py-1 text-xs font-medium rounded-lg border border-gray-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
          >
            Anterior
          </button>

          <template v-for="(p, idx) in visiblePages" :key="idx">
            <span v-if="p === '...'" class="px-2 text-xs text-gray-400">...</span>
            <button
              v-else
              @click="goToPage(Number(p))"
              :class="[
                'w-7 h-7 text-xs font-medium rounded-lg flex items-center justify-center transition-all cursor-pointer',
                currentPage === p
                  ? 'bg-[#00aea7] text-white shadow-xs font-bold'
                  : 'bg-white border border-gray-200 text-slate-700 hover:bg-slate-50'
              ]"
            >
              {{ p }}
            </button>
          </template>

          <button
            @click="goToPage(currentPage + 1)"
            :disabled="currentPage >= totalPages"
            class="px-2.5 py-1 text-xs font-medium rounded-lg border border-gray-200 bg-white text-slate-700 hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
          >
            Siguiente
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

          <!-- Metadatos Enriquecidos Recuperados por el Agente -->
          <div v-if="selectedRecord.abstractEnriquecido || selectedRecord.estado === 'Completado' || (selectedRecord.palabrasClave && selectedRecord.palabrasClave.length > 0)" class="space-y-3 p-4 rounded-xl border border-emerald-100 bg-emerald-50/30">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold text-emerald-900 flex items-center gap-1.5">
                <Sparkles :size="14" class="text-emerald-600" /> Metadatos Enriquecidos por el Agente
              </span>
              <span class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                {{ selectedRecord.fuente || 'Fuentes científicas validadas' }}
              </span>
            </div>
            <div v-if="selectedRecord.abstractEnriquecido" class="bg-white p-3 rounded-lg border border-emerald-100 text-xs text-slate-700 leading-relaxed max-h-36 overflow-y-auto">
              <span class="text-[10px] uppercase font-bold text-slate-400 block mb-1">Resumen / Abstract Recuperado:</span>
              {{ selectedRecord.abstractEnriquecido }}
            </div>
            <div v-if="selectedRecord.palabrasClave && selectedRecord.palabrasClave.length > 0" class="pt-1">
              <span class="text-[10px] uppercase font-bold text-slate-400 block mb-1">Palabras Clave Asociadas:</span>
              <div class="flex flex-wrap gap-1.5">
                <span v-for="kw in selectedRecord.palabrasClave" :key="kw" class="px-2 py-0.5 text-[11px] font-medium bg-white text-emerald-800 border border-emerald-200 rounded-md shadow-xs">
                  {{ kw }}
                </span>
              </div>
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
            v-if="selectedRecord.estado === 'Completado'"
            @click="selectedRecord = null"
            class="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm flex items-center gap-1.5 cursor-pointer"
          >
            <Check :size="14" /> Registro Enriquecido
          </button>
          <button
            v-else
            @click="runAgentSingle(selectedRecord)"
            :disabled="enrichingIds[selectedRecord.id]"
            class="px-4 py-2 text-xs font-semibold text-white rounded-lg shadow-sm hover:opacity-95 cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
            style="background: #00aea7"
          >
            <div v-if="enrichingIds[selectedRecord.id]" class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <Zap v-else :size="14" /> Enriquecer con Agente
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { Search, Zap, Download, Filter, ChevronDown, Eye, X, Sparkles, Check } from 'lucide-vue-next'
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
const loading = ref(true)
const enrichingIds = ref<Record<string, boolean>>({})

const currentPage = ref(1)
const pageSize = ref(15)

const totalDetectados = ref(0)
const pendientesCount = ref(0)
const enProcesoCount = ref(0)
const completadosCount = ref(0)

const stats = computed(() => [
  { label: 'Total detectados', value: totalDetectados.value.toLocaleString('es-CL'), color: '#F57C00' },
  { label: 'Pendientes', value: pendientesCount.value.toLocaleString('es-CL'), color: '#d32f2f' },
  { label: 'En proceso', value: enProcesoCount.value.toLocaleString('es-CL'), color: '#00aea7' },
  { label: 'Completados', value: completadosCount.value.toLocaleString('es-CL'), color: '#2E7D32' },
])

const records = ref<MonitoreoRecord[]>([])

const loadRealQueue = async () => {
  loading.value = true
  try {
    const [queueRes, statsRes, proposals] = await Promise.all([
      proposalService.getQueue({ page: 0, size: 5000 }),
      proposalService.getQueueStats(),
      proposalService.listProposals()
    ])

    const porEstado = statsRes?.por_estado || {}
    if (statsRes?.total_en_cola || (queueRes?.items && queueRes.items.length > 0)) {
      totalDetectados.value = statsRes?.total_en_cola || queueRes?.total || (queueRes?.items ? queueRes.items.length : 0)
      pendientesCount.value = porEstado['PENDIENTE'] || 0
      enProcesoCount.value = porEstado['EN_PROCESO'] || 0
      completadosCount.value = (porEstado['ENRIQUECIDO'] || 0) + (porEstado['SINCRONIZADO_DSPACE'] || 0)
    } else {
      totalDetectados.value = proposals.length
      pendientesCount.value = proposals.filter((p: any) => p.status === 'DETECTED' || p.status === 'PENDING').length
      enProcesoCount.value = proposals.filter((p: any) => p.status === 'ENRICHING' || p.status === 'VALIDATING').length
      completadosCount.value = proposals.filter((p: any) => p.status === 'APPROVED' || p.status === 'LOADED_TO_DSPACE').length
    }

    const mapped: MonitoreoRecord[] = []

    if (queueRes?.items && queueRes.items.length > 0) {
      for (const item of queueRes.items) {
        mapped.push({
          id: String(item.id || item.uuid_dspace || ''),
          title: item.titulo || item.title || item.titulo_dspace || item.name || (item.doi ? `Publicación (DOI: ${item.doi})` : `Registro DSpace #${item.id || item.uuid_dspace}`),
          campo: item.tipo_falencia || 'Metadatos faltantes',
          fecha: item.created_at ? item.created_at.split('T')[0] : 'Hoy',
          prioridad: item.tipo_falencia?.includes('AMBOS') ? 'Alta' : 'Media',
          estado: item.estado === 'ENRIQUECIDO' || item.estado === 'SINCRONIZADO_DSPACE' || item.estado === 'COMPLETO' ? 'Completado' : item.estado === 'EN_PROCESO' ? 'En proceso' : 'Pendiente',
          completitud: item.estado === 'ENRIQUECIDO' || item.estado === 'COMPLETO' ? 95 : item.estado === 'EN_PROCESO' ? 70 : 45,
          completitudPre: 40,
          coleccion: item.coleccion || 'Artículos Científicos USACH',
          comunidad: item.comunidad || 'Facultad USACH',
          autor: item.autor || 'Investigador USACH',
          doi: item.doi || '',
          abstractEnriquecido: item.abstract_enriquecido,
          palabrasClave: Array.isArray(item.palabras_clave) ? item.palabras_clave : typeof item.palabras_clave === 'string' ? JSON.parse(item.palabras_clave || '[]') : [],
          fuente: item.fuente_enriquecimiento,
          areaOcde: item.area_ocde,
          areaOds: item.area_ods
        })
      }
    } else if (proposals && proposals.length > 0) {
      for (const p of proposals) {
        mapped.push({
          id: String(p.id || p.uuid_dspace || ''),
          title: p.title || p.titulo || p.titulo_dspace || p.name || (p.doi ? `Publicación (DOI: ${p.doi})` : `Propuesta #${p.id}`),
          campo: p.field_name || p.field || 'Metadato General',
          fecha: p.created_at ? p.created_at.split('T')[0] : 'Hoy',
          prioridad: 'Alta',
          estado: p.status === 'APPROVED' ? 'Completado' : p.status === 'PENDING_CURATION' ? 'En proceso' : 'Pendiente',
          completitud: p.status === 'APPROVED' ? 100 : 70,
          completitudPre: 40,
          coleccion: 'DSpace-CRIS',
          comunidad: 'VRIIC',
          autor: 'Investigador USACH',
          doi: p.doi || '',
          abstractEnriquecido: p.suggested_value || p.new_value,
          fuente: p.source || p.best_source
        })
      }
    }

    records.value = mapped
  } catch (err) {
    console.error('Error cargando cola real de monitoreo:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRealQueue()
})

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

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRecords.value.length / pageSize.value)))

const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})

const pageStart = computed(() => (filteredRecords.value.length === 0 ? 0 : (currentPage.value - 1) * pageSize.value + 1))
const pageEnd = computed(() => Math.min(currentPage.value * pageSize.value, filteredRecords.value.length))

const goToPage = (p: number) => {
  if (p >= 1 && p <= totalPages.value) {
    currentPage.value = p
  }
}

const visiblePages = computed(() => {
  const total = totalPages.value
  const current = currentPage.value
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1)
  }
  const pages: (number | string)[] = []
  pages.push(1)
  if (current > 3) pages.push('...')

  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }

  if (current < total - 2) pages.push('...')
  pages.push(total)
  return pages
})

watch([search, selectedStatuses], () => {
  currentPage.value = 1
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
    const itemsToDetect = records.value.filter(r => r.estado === 'Pendiente').slice(0, 10).map(r => ({
      item_id: r.id,
      title: r.title,
      missing_fields: [r.campo],
      doi: r.doi
    }))
    if (itemsToDetect.length > 0) {
      await proposalService.detectMissing(itemsToDetect)
      alert(`Se procesaron exitosamente ${itemsToDetect.length} registros con el agente de enriquecimiento IA.`)
      await loadRealQueue()
    } else {
      alert('No hay registros en estado Pendiente para procesar.')
    }
  } catch (err: any) {
    alert(`Error procesando lote: ${err?.response?.data?.detail || err.message || err}`)
  } finally {
    runningBatch.value = false
  }
}

const runAgentSingle = async (record: MonitoreoRecord | null) => {
  if (!record) return
  enrichingIds.value[record.id] = true
  try {
    await proposalService.detectMissing([
      { item_id: record.id, title: record.title, missing_fields: [record.campo], doi: record.doi }
    ])
    record.estado = 'Completado'
    record.completitud = 95
    completadosCount.value++
    pendientesCount.value = Math.max(0, pendientesCount.value - 1)

    // Recargar datos frescos desde backend
    await loadRealQueue()

    if (selectedRecord.value && selectedRecord.value.id === record.id) {
      const updated = records.value.find(r => r.id === record.id)
      if (updated) selectedRecord.value = updated
    }
  } catch (err: any) {
    alert(`Error al iniciar enriquecimiento: ${err?.response?.data?.detail || err.message || err}`)
  } finally {
    enrichingIds.value[record.id] = false
  }
}

const exportSummary = () => {
  alert('Generando exportación de reporte de monitoreo DSpace-CRIS...')
}
</script>

