<template>
  <div class="h-full overflow-y-auto">
    <SectionHeader
      title="Auditoría y Trazabilidad"
      description="Listado de registros del catálogo científico y su historial completo de eventos de enriquecimiento y curaduría."
    />

    <!-- Stats -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">Registros Auditados</span>
          <div class="w-8 h-8 rounded-lg bg-teal-50 text-[#00aea7] flex items-center justify-center">
            <ClipboardList :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-[#1a2332]">
          {{ auditRecords.length }} <span class="text-xs font-normal text-[#6b7a90]">registros</span>
        </p>
        <p class="text-[10px] text-[#00aea7] font-medium mt-0.5">Trazabilidad en log (INSERT-only)</p>
      </Card>

      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">Eventos Registrados</span>
          <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Activity :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-[#1a2332]">20 <span class="text-xs font-normal text-[#6b7a90]">eventos</span></p>
        <p class="text-[10px] text-blue-600 font-medium mt-0.5">Promedio 4 eventos por registro</p>
      </Card>

      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">Fuentes Consultadas</span>
          <div class="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
            <Database :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-[#1a2332]">4 <span class="text-xs font-normal text-[#6b7a90]">fuentes</span></p>
        <p class="text-[10px] text-purple-600 font-medium mt-0.5">Scopus, WoS, Crossref, OpenAlex</p>
      </Card>

      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">Integridad de metadatos</span>
          <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <ShieldCheck :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-emerald-700">100%</p>
        <p class="text-[10px] text-emerald-600 font-medium mt-0.5">Sin alertas de inconsistencia</p>
      </Card>
    </div>

    <!-- Table Card -->
    <Card>
      <div class="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="relative flex-1 max-w-xs">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
          <input
            type="text"
            placeholder="Buscar por ID, nombre o metadato..."
            v-model="searchTerm"
            class="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
          />
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-50 bg-slate-50/50">
              <th
                v-for="h in ['ID del registro', 'Nombre del registro asociado', 'Metadatos recuperados', 'Última actualización', 'Acciones']"
                :key="h"
                class="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide whitespace-nowrap"
              >
                {{ h }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in filtered"
              :key="row.id"
              class="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
            >
              <td class="px-4 py-3.5 whitespace-nowrap">
                <span class="text-xs font-mono font-bold text-[#1565C0] bg-blue-50/80 border border-blue-100 px-2.5 py-1 rounded-md">
                  #{{ row.id }}
                </span>
              </td>
              <td class="px-4 py-3.5 max-w-[280px]">
                <p class="text-xs font-semibold text-[#1a2332] truncate" :title="row.nombre">{{ row.nombre }}</p>
              </td>
              <td class="px-4 py-3.5">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="meta in row.metadatoRecuperado.split(', ')"
                    :key="meta"
                    class="text-[11px] font-medium px-2 py-0.5 bg-teal-50 text-[#00aea7] rounded border border-teal-100 whitespace-nowrap"
                  >
                    {{ meta }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <span class="text-xs text-slate-500 font-mono">{{ row.fecha }}</span>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <button
                  @click="selectedAudit = row"
                  class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-[#00aea7] hover:opacity-90 transition-all rounded-lg shadow-sm cursor-pointer"
                >
                  <ClipboardList :size="13" />
                  <span>Ver auditoría</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Modal Trazabilidad y Auditoría -->
    <div
      v-if="selectedAudit"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
              <ClipboardList :size="18" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-800">Trazabilidad y Auditoría — Registro #{{ selectedAudit.id }}</h3>
              <p class="text-[11px] text-slate-500">Historial completo e inmutable de eventos de enriquecimiento</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="exportAuditLog(selectedAudit)"
              class="flex items-center gap-1.5 px-3 py-1 text-xs font-medium text-slate-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <Download :size="13" /> Exportar log
            </button>
            <button @click="selectedAudit = null" class="p-1 rounded-lg text-slate-400 hover:text-slate-600">
              <X :size="18" />
            </button>
          </div>
        </div>

        <div class="p-6 overflow-y-auto space-y-5 flex-1">
          <div class="bg-slate-50 p-4 rounded-xl border border-gray-100 space-y-2">
            <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Nombre del Registro Asociado</span>
            <p class="text-xs font-bold text-slate-800 mt-0.5">{{ selectedAudit.nombre }}</p>
          </div>

          <!-- Timeline of events -->
          <div class="space-y-4">
            <div
              v-for="(ev, idx) in selectedAudit.eventos"
              :key="idx"
              class="flex gap-3 text-xs"
            >
              <div class="flex flex-col items-center">
                <div
                  class="w-3 h-3 rounded-full mt-1 border-2 border-white shadow-sm flex-shrink-0"
                  :style="{ backgroundColor: ev.color }"
                />
                <div v-if="idx < selectedAudit.eventos.length - 1" class="w-0.5 flex-1 bg-gray-200 my-1" />
              </div>
              <div class="flex-1 pb-4">
                <div class="flex items-center gap-2 flex-wrap">
                  <span class="font-bold text-gray-800">{{ ev.event }}</span>
                  <span class="text-[10px] text-gray-400 font-mono">{{ ev.time }}</span>
                  <span class="text-[10px] px-2 py-0.5 rounded bg-gray-100 text-gray-600 font-medium">{{ ev.role }}: {{ ev.user }}</span>
                  <span class="text-[10px] text-teal-600 bg-teal-50 px-1.5 py-0.5 rounded font-mono">{{ ev.source }}</span>
                </div>
                <p class="text-xs text-gray-600 mt-1 leading-relaxed">{{ ev.result }}</p>
              </div>
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 bg-slate-50 flex justify-end">
          <button
            @click="selectedAudit = null"
            class="px-4 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-white border border-gray-200 hover:bg-gray-50 cursor-pointer"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ClipboardList, Activity, Database, ShieldCheck, Search, Download, X } from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import SectionHeader from '../components/common/SectionHeader.vue'

const searchTerm = ref('')
const selectedAudit = ref<any | null>(null)

const auditRecords = [
  {
    id: '13458',
    nombre: 'Machine Learning for Biodiversity in Andean Ecosystems',
    metadatoRecuperado: 'Abstract, Áreas ODS, Palabras clave',
    fecha: '28 jun 2024 · 09:17',
    eventos: [
      { time: '09:14:02', event: 'Detección de registro', user: 'Sistema CRIS', role: 'Sistema', source: 'DSpace local', result: 'ID Registro #13458 identificado sin Abstract, Áreas ODS ni Palabras clave.', color: '#6b7a90' },
      { time: '09:14:18', event: 'Recuperación de Abstract', user: 'Agente IA', role: 'Motor IA', source: 'OpenAlex API', result: 'Abstract científico recuperado e indexado desde OpenAlex (confianza 96%).', color: '#00aea7' },
      { time: '09:14:50', event: 'Extracción de Palabras clave', user: 'Agente IA', role: 'Motor IA', source: 'Extracción PDF', result: '6 palabras clave normalizadas extraídas mediante análisis OCR en texto completo.', color: '#1565C0' },
      { time: '09:15:30', event: 'Clasificación en Áreas ODS', user: 'Agente IA', role: 'Motor IA', source: 'Inferencia local', result: 'ODS 15 (Vida de ecosistemas terrestres) asignado algorítmicamente.', color: '#7B1FA2' },
      { time: '09:16:15', event: 'Validación humana de metadatos', user: 'Carlos Fuentes', role: 'Curador', source: 'Módulo de Validación', result: 'Abstract, Áreas ODS y Palabras clave validados técnicamente por el curador responsable.', color: '#00aea7' },
      { time: '09:16:48', event: 'Aprobación humana de metadatos', user: 'María González', role: 'Administrador', source: 'Módulo de Aprobación', result: 'Metadatos aprobados en curaduría definitiva para su publicación formal en el repositorio.', color: '#F57C00' },
      { time: '09:17:03', event: 'Sincronización de catálogo', user: 'Agente IA', role: 'Motor IA', source: 'Base de datos', result: 'Metadatos incorporados exitosamente en el registro #13458 de la base de datos local.', color: '#2E7D32' },
    ]
  },
  {
    id: '18954',
    nombre: 'Open Science Infrastructure and Policy Frameworks in Chile',
    metadatoRecuperado: 'Derechos de acceso, Palabras clave',
    fecha: '28 jun 2024 · 10:45',
    eventos: [
      { time: '10:40:12', event: 'Detección de registro', user: 'Sistema CRIS', role: 'Sistema', source: 'DSpace local', result: 'Registro #18954 identificado con licencia de acceso y palabras clave faltantes.', color: '#6b7a90' },
      { time: '10:41:05', event: 'Recuperación de Derechos de acceso', user: 'Agente IA', role: 'Motor IA', source: 'Crossref API', result: 'Licencia de acceso abierto Creative Commons CC BY 4.0 detectada y vinculada.', color: '#00aea7' },
      { time: '10:42:18', event: 'Extracción de Palabras clave', user: 'Agente IA', role: 'Motor IA', source: 'Extracción PDF', result: '5 palabras clave extraídas desde el pie de página y encabezado del documento PDF.', color: '#1565C0' },
      { time: '10:44:20', event: 'Aprobación humana de metadatos', user: 'Roberto Muñoz', role: 'Administrador', source: 'Módulo de Aprobación', result: 'Aprobación curatorial final emitida para difusión pública del registro.', color: '#F57C00' },
    ]
  },
  {
    id: '22103',
    nombre: 'Genomic Sequencing Methods for Marine Microorganisms',
    metadatoRecuperado: 'Área OCDE, Abstract',
    fecha: '27 jun 2024 · 16:20',
    eventos: [
      { time: '16:15:00', event: 'Detección de registro', user: 'Sistema CRIS', role: 'Sistema', source: 'DSpace local', result: 'Registro #22103 detectado sin clasificación de Área OCDE ni resumen científico.', color: '#6b7a90' },
      { time: '16:16:30', event: 'Recuperación de Área OCDE', user: 'Agente IA', role: 'Motor IA', source: 'WoS API', result: 'Clasificación 1.06 (Biología y Ciencias Biológicas) identificada en Web of Science.', color: '#00aea7' },
      { time: '16:19:15', event: 'Aprobación humana de metadatos', user: 'Patricia Soto', role: 'Administrador', source: 'Módulo de Aprobación', result: 'Metadatos autorizados por el curador responsable para indexación oficial.', color: '#F57C00' },
    ]
  }
]

const filtered = computed(() => {
  return auditRecords.filter(r =>
    r.id.includes(searchTerm.value) ||
    r.nombre.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    r.metadatoRecuperado.toLowerCase().includes(searchTerm.value.toLowerCase())
  )
})

const exportAuditLog = (item: any) => {
  alert(`Exportando reporte de auditoría completo para el registro #${item.id}...`)
}
</script>

