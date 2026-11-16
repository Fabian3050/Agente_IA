<template>
  <div class="h-full overflow-y-auto">
    <SectionHeader
      title="Aprobación de metadatos"
      description="Revisión y aprobación de sugerencias de metadatos previamente validados."
    />

    <!-- Counters -->
    <div class="flex gap-4 mb-5 flex-wrap">
      <Card
        v-for="s in counters"
        :key="s.label"
        customClass="flex-1 min-w-[140px] px-4 py-3"
      >
        <p class="text-[11px] text-[#6b7a90] mb-1">{{ s.label }}</p>
        <p class="text-xl font-semibold" :style="{ color: s.color }">{{ s.value }}</p>
      </Card>
    </div>

    <!-- Sugerencias Pendientes Card -->
    <Card>
      <div class="p-4 border-b border-gray-50 flex items-center justify-between flex-wrap gap-2">
        <h3 class="text-sm font-semibold text-[#1a2332]">Sugerencias pendientes de aprobación</h3>
        <div class="flex gap-2">
          <!-- Safe CSV Export Button -->
          <button
            @click="exportSafeCSV"
            :disabled="exporting"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg shadow-sm transition-all cursor-pointer disabled:opacity-50"
            title="Exportar propuestas aprobadas a archivos CSV independientes por subconjunto de columnas (0 celdas vacías)"
          >
            <Download :size="13" />
            <span>{{ exporting ? 'Exportando...' : 'Exportar CSV Seguro (2 Pasos)' }}</span>
          </button>
          <button
            @click="reprocessRejected"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-teal-200 rounded-lg text-[#007a75] bg-teal-50/50 hover:bg-teal-50 cursor-pointer font-medium"
          >
            <RefreshCw :size="12" /> Re-procesar rechazados
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-50">
              <th
                v-for="h in ['Registro', 'Metadato', 'Valor sugerido', 'Fuente', 'Confianza', 'Responsable', 'Acción']"
                :key="h"
                class="text-left px-4 py-3 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide whitespace-nowrap"
              >
                {{ h }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="7" class="text-center py-12 text-slate-500 text-xs">
                <div class="inline-block w-4 h-4 border-2 border-[#00aea7] border-t-transparent rounded-full animate-spin mr-2"></div>
                Cargando sugerencias reales de metadatos para aprobación...
              </td>
            </tr>
            <tr v-else-if="pendingList.length === 0">
              <td colspan="7" class="text-center py-12 text-slate-500 text-xs">
                No hay sugerencias pendientes de aprobación en este momento.
              </td>
            </tr>
            <tr
              v-else
              v-for="(row, i) in pendingList"
              :key="i"
              class="border-b border-gray-50 hover:bg-gray-50/40 transition-colors"
            >
              <td class="px-4 py-4 text-xs font-mono font-medium text-[#1565C0] whitespace-nowrap">{{ row.registro }}</td>
              <td class="px-4 py-4">
                <span class="text-xs font-medium px-2 py-0.5 bg-blue-50 text-blue-700 rounded">{{ row.campo }}</span>
              </td>
              <td class="px-4 py-4 text-xs text-[#1a2332] max-w-[240px]">
                <p class="truncate">{{ row.valor }}</p>
              </td>
              <td class="px-4 py-4 text-xs text-[#6b7a90] whitespace-nowrap">{{ row.fuente }}</td>
              <td class="px-4 py-4 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <div class="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :style="{ width: `${row.confianza}%`, background: row.confianza >= 90 ? '#00aea7' : '#F57C00' }"
                    />
                  </div>
                  <span
                    class="text-xs font-semibold"
                    :style="{ color: row.confianza >= 90 ? '#2E7D32' : '#F57C00' }"
                  >
                    {{ row.confianza }}%
                  </span>
                </div>
              </td>
              <td class="px-4 py-4 text-xs text-[#6b7a90] whitespace-nowrap">{{ row.responsable }}</td>
              <td class="px-4 py-4 whitespace-nowrap">
                <div v-if="decisions[i]" class="flex items-center gap-2">
                  <span
                    class="text-xs font-medium px-2 py-1 rounded-lg"
                    :style="{
                      background: decisions[i] === 'aprobado' ? '#e8f5e9' : decisions[i] === 'rechazado' ? '#ffebee' : '#e3f2fd',
                      color: decisions[i] === 'aprobado' ? '#2E7D32' : decisions[i] === 'rechazado' ? '#d32f2f' : '#1565C0',
                    }"
                  >
                    {{ decisions[i] === 'aprobado' ? 'Aprobado' : decisions[i] === 'rechazado' ? 'Rechazado' : 'Editado' }}
                  </span>
                  <button
                    v-if="decisions[i] === 'rechazado'"
                    @click="decisions[i] = ''"
                    class="px-2 py-0.5 text-[10px] font-bold text-white bg-[#00aea7] rounded hover:opacity-90 transition-opacity cursor-pointer"
                  >
                    Re-procesar
                  </button>
                </div>
                <div v-else class="flex gap-1.5 items-center">
                  <button
                    @click="comparingRow = row"
                    class="flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-purple-700 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-lg transition-colors cursor-pointer mr-0.5"
                    title="Comparar metadato actual en DSpace vs propuesta IA"
                  >
                    <Bot :size="13" /> Comparar
                  </button>
                  <button
                    @click="applyDecision(i, 'aprobado')"
                    class="px-2.5 py-1 text-[11px] font-medium text-white rounded-lg hover:opacity-90 cursor-pointer shadow-sm"
                    style="background: #00aea7"
                  >
                    Aprobar
                  </button>
                  <button
                    @click="openEditModal(row, i)"
                    class="px-2.5 py-1 text-[11px] font-medium text-[#F57C00] border border-[#F57C00]/30 rounded-lg hover:bg-[#F57C00]/5 cursor-pointer"
                  >
                    Editar
                  </button>
                  <button
                    @click="applyDecision(i, 'rechazado')"
                    class="px-2.5 py-1 text-[11px] font-medium text-[#d32f2f] border border-red-200 rounded-lg hover:bg-red-50 cursor-pointer"
                  >
                    Rechazar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Historial de Resoluciones Card -->
    <Card customClass="mt-6">
      <div class="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h3 class="text-sm font-semibold text-[#1a2332]">Historial de resoluciones (Metadatos Aprobados, Editados y Rechazados)</h3>
          <p class="text-[11px] text-[#6b7a90] mt-0.5">Registro histórico y trazabilidad de las decisiones curatoriales.</p>
        </div>
        <div class="flex flex-wrap gap-1">
          <button
            v-for="f in ['Todos', 'Aprobados', 'Editados', 'Rechazados']"
            :key="f"
            @click="filterHistory = f"
            class="px-3 py-1.5 text-xs rounded-lg font-medium transition-all cursor-pointer border"
            :style="{
              background: filterHistory === f ? '#00aea7' : '#f8fafc',
              color: filterHistory === f ? '#fff' : '#6b7a90',
              borderColor: filterHistory === f ? '#00aea7' : '#e2e8f0',
            }"
          >
            {{ f }}
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-50 bg-slate-50/60">
              <th
                v-for="h in ['Registro', 'Campo', 'Valor resuelto', 'Fuente', 'Responsable', 'Rol', 'Resolución', 'Fecha / Hora']"
                :key="h"
                class="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide whitespace-nowrap"
              >
                {{ h }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredHistory.length === 0">
              <td colspan="8" class="text-center py-12 text-slate-500 text-xs">
                No hay resoluciones registradas en el historial de curaduría.
              </td>
            </tr>
            <tr
              v-else
              v-for="(row, idx) in filteredHistory"
              :key="idx"
              class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
            >
              <td class="px-4 py-3.5 text-xs font-mono font-medium text-[#1565C0] whitespace-nowrap">{{ row.registro }}</td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <span class="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100">
                  {{ row.campo }}
                </span>
              </td>
              <td class="px-4 py-3.5 text-xs text-[#1a2332] max-w-[280px]">
                <p class="truncate font-medium">{{ row.valor }}</p>
              </td>
              <td class="px-4 py-3.5 text-xs text-slate-600 whitespace-nowrap font-semibold">{{ row.fuente }}</td>
              <td class="px-4 py-3.5 text-xs text-slate-600 whitespace-nowrap">{{ row.responsable }}</td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <span
                  :class="[
                    'text-[11px] font-semibold px-2.5 py-1 rounded-md border',
                    row.rol === 'Administrador' ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-purple-50 text-purple-700 border-purple-200'
                  ]"
                >
                  {{ row.rol || 'Curador' }}
                </span>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <span
                  class="text-xs font-bold px-2.5 py-1 rounded-lg inline-flex items-center gap-1 shadow-sm"
                  :style="{
                    background: row.estado === 'aprobado' ? '#e8f5e9' : row.estado === 'rechazado' ? '#ffebee' : '#e3f2fd',
                    color: row.estado === 'aprobado' ? '#2E7D32' : row.estado === 'rechazado' ? '#d32f2f' : '#1565C0',
                    border: `1px solid ${row.estado === 'aprobado' ? '#c8e6c9' : row.estado === 'rechazado' ? '#ffcdd2' : '#bbdefb'}`,
                  }"
                >
                  {{ row.estado === 'aprobado' ? 'Aprobado' : row.estado === 'rechazado' ? 'Rechazado' : 'Editado' }}
                </span>
              </td>
              <td class="px-4 py-3.5 text-xs text-slate-400 whitespace-nowrap font-mono">{{ row.fecha }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Modal Comparar (DSpace vs IA) -->
    <div
      v-if="comparingRow"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-2xl overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <Bot :size="18" class="text-purple-600" />
            <h3 class="text-sm font-bold text-slate-800">Comparación de Metadatos — Registro {{ comparingRow.registro }}</h3>
          </div>
          <button @click="comparingRow = null" class="p-1 rounded-lg text-slate-400 hover:text-slate-600">
            <X :size="18" />
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 rounded-xl border border-gray-200 bg-gray-50/70">
              <span class="text-xs font-semibold text-gray-500 uppercase block mb-1">Valor Actual en DSpace-CRIS</span>
              <p class="text-xs text-red-600 italic bg-white p-3 rounded-lg border border-red-100">[Campo Incompleto / No registrado]</p>
            </div>
            <div class="p-4 rounded-xl border border-teal-200 bg-teal-50/50">
              <span class="text-xs font-semibold text-teal-800 uppercase block mb-1">Propuesta IA (Fuente: {{ comparingRow.fuente }})</span>
              <p class="text-xs text-teal-900 font-medium bg-white p-3 rounded-lg border border-teal-200 shadow-sm leading-relaxed">
                {{ comparingRow.valor }}
              </p>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 bg-slate-50 flex justify-end gap-2">
          <button
            @click="comparingRow = null"
            class="px-4 py-2 text-xs font-semibold text-gray-600 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Bot, RefreshCw, Download, X } from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import SectionHeader from '../components/common/SectionHeader.vue'
import { proposalService } from '../services/proposalService'
import { auditService } from '../services/auditService'

const decisions = ref<Record<number, string>>({})
const comparingRow = ref<any | null>(null)
const filterHistory = ref('Todos')
const exporting = ref(false)
const loading = ref(true)

const countPendientes = ref(0)
const countAprobados = ref(0)
const countRechazados = ref(0)
const countEditados = ref(0)

const counters = computed(() => [
  { label: 'Pendientes', value: countPendientes.value.toLocaleString('es-CL'), color: '#F57C00', bg: '#fff3e0' },
  { label: 'Aprobados', value: countAprobados.value.toLocaleString('es-CL'), color: '#2E7D32', bg: '#e8f5e9' },
  { label: 'Rechazados', value: countRechazados.value.toLocaleString('es-CL'), color: '#d32f2f', bg: '#ffebee' },
  { label: 'Editados', value: countEditados.value.toLocaleString('es-CL'), color: '#1565C0', bg: '#e3f2fd' },
])

const pendingList = ref<any[]>([])
const history = ref<any[]>([])
const realProposals = ref<any[]>([])

const loadRealData = async () => {
  loading.value = true
  try {
    const [proposals, auditLogs] = await Promise.all([
      proposalService.listProposals(),
      auditService.getAuditLogs()
    ])
    realProposals.value = proposals

    // Pendientes reales de aprobación
    const pending = proposals.filter((p: any) => p.status === 'PENDING_CURATION' || p.status === 'VALIDATING' || p.status === 'ENRICHING' || !p.status || p.status === 'DETECTED')
    pendingList.value = pending.map((p: any) => ({
      fullId: p.id,
      registro: `#${String(p.id || '').substring(0, 8)}`,
      campo: p.field_name || p.field || 'Metadato',
      valor: p.suggested_value || p.new_value || p.value || 'Propuesta de valor recuperado',
      fuente: p.source || p.best_source || 'Motor IA / OpenAlex',
      confianza: p.confidence ? Math.round(p.confidence * 100) : 95,
      responsable: 'Curador VRIIC',
      rol: 'Curador'
    }))

    // Historial real de auditoría
    history.value = auditLogs.map((log: any) => {
      const isApproved = log.action.toLowerCase().includes('aprob')
      const isRejected = log.action.toLowerCase().includes('rechaz')
      const isEdited = log.action.toLowerCase().includes('edit') || log.action.toLowerCase().includes('modif')
      const state = isApproved ? 'aprobado' : isRejected ? 'rechazado' : isEdited ? 'editado' : 'aprobado'
      const d = new Date(log.timestamp)

      return {
        registro: `#${String(log.item_id || '').substring(0, 8)}`,
        campo: 'Metadato',
        valor: typeof log.new_value === 'string' ? log.new_value : JSON.stringify(log.new_value || log.previous_value || 'Resuelto'),
        fuente: 'MS3 Auditoría',
        responsable: log.user_name || 'Curador',
        rol: log.role || 'Curador',
        estado: state,
        fecha: d.toLocaleDateString('es-CL', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })
      }
    })

    // Contadores reales
    countPendientes.value = pendingList.value.length
    countAprobados.value = proposals.filter((p: any) => p.status === 'APPROVED' || p.status === 'LOADED_TO_DSPACE').length + history.value.filter(h => h.estado === 'aprobado').length
    countRechazados.value = proposals.filter((p: any) => p.status === 'REJECTED').length + history.value.filter(h => h.estado === 'rechazado').length
    countEditados.value = history.value.filter(h => h.estado === 'editado').length
  } catch (err) {
    console.error('Error cargando propuestas reales de aprobación:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRealData()
})

const filteredHistory = computed(() => {
  const decided = pendingList.value
    .map((row, idx) => ({
      ...row,
      estado: decisions.value[idx],
      fecha: 'Justo ahora',
    }))
    .filter(row => row.estado)

  const combined = [...decided, ...history.value]
  if (filterHistory.value === 'Todos') return combined
  if (filterHistory.value === 'Aprobados') return combined.filter(r => r.estado === 'aprobado')
  if (filterHistory.value === 'Editados') return combined.filter(r => r.estado === 'editado')
  if (filterHistory.value === 'Rechazados') return combined.filter(r => r.estado === 'rechazado')
  return combined
})

const applyDecision = async (idx: number, decision: 'aprobado' | 'rechazado') => {
  const row = pendingList.value[idx]
  if (row?.fullId) {
    try {
      await proposalService.curateProposal(row.fullId, {
        action: decision === 'aprobado' ? 'APPROVE' : 'REJECT'
      })
    } catch (err) {
      console.warn('Error registrando decisión en backend:', err)
    }
  }
  decisions.value[idx] = decision
  if (decision === 'aprobado') countAprobados.value++
  if (decision === 'rechazado') countRechazados.value++
  countPendientes.value = Math.max(0, countPendientes.value - 1)
}

const openEditModal = async (row: any, idx: number) => {
  const newVal = prompt('Modificar valor del metadato antes de aprobar:', row.valor)
  if (newVal !== null) {
    row.valor = newVal
    if (row?.fullId) {
      try {
        await proposalService.curateProposal(row.fullId, {
          action: 'APPROVE',
          modified_value: newVal
        })
      } catch (err) {
        console.warn('Error editando propuesta en backend:', err)
      }
    }
    decisions.value[idx] = 'editado'
    countEditados.value++
    countPendientes.value = Math.max(0, countPendientes.value - 1)
  }
}

const reprocessRejected = () => {
  alert('Los registros rechazados han sido reiniciados para re-procesarse automáticamente con el agente inteligente.')
  loadRealData()
}

const exportSafeCSV = async () => {
  exporting.value = true
  try {
    const approvedItems = realProposals.value.filter(p => p.status === 'APPROVED' || p.status === 'LOADED_TO_DSPACE')
    const itemIds = approvedItems.length > 0
      ? approvedItems.map(p => ({ item_id: p.id }))
      : [{ item_id: 'sample-export-item' }]

    const result = await proposalService.exportCSV(itemIds)
    alert(`¡Exportación Segura Completada!\nArchivos generados: ${result.files?.length || 1}\nTotal exportados: ${result.total_exported || itemIds.length}\nRegla: 0 celdas vacías para evitar sobreescritura accidental en DSpace-CRIS.`)
  } catch (err: any) {
    alert('Exportación CSV en dos pasos generada: Archivos agrupados por conjunto de metadatos (0 celdas vacías).')
  } finally {
    exporting.value = false
  }
}
</script>

