<template>
  <div class="h-full overflow-y-auto">
    <SectionHeader
      title="Análisis Documental PDF"
      description="Listado de registros científicos procesados y enriquecidos mediante herramientas de extracción directa de PDF con OCR e IA."
    />

    <!-- Stats Cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">Archivos Procesados</span>
          <div class="w-8 h-8 rounded-lg bg-teal-50 text-[#00aea7] flex items-center justify-center">
            <FileText :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-[#1a2332]">5 <span class="text-xs font-normal text-[#6b7a90]">documentos</span></p>
        <p class="text-[10px] text-[#00aea7] font-medium mt-0.5">OCR UTF-8 normalizado</p>
      </Card>

      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">Confianza Promedio</span>
          <div class="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-[#1a2332]">93.4%</p>
        <p class="text-[10px] text-emerald-600 font-medium mt-0.5">Alta precisión en extracción</p>
      </Card>

      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">DOIs Identificados</span>
          <div class="w-8 h-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
            <Globe :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-[#1a2332]">100%</p>
        <p class="text-[10px] text-blue-600 font-medium mt-0.5">Enlaces resueltos exitosamente</p>
      </Card>

      <Card customClass="p-4">
        <div class="flex items-center justify-between mb-2">
          <span class="text-[11px] font-semibold text-[#6b7a90] uppercase">Extracciones Aprobadas</span>
          <div class="w-8 h-8 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
            <Zap :size="16" />
          </div>
        </div>
        <p class="text-xl font-bold text-purple-700">
          {{ Object.keys(approvedIds).length }} <span class="text-xs font-normal text-[#6b7a90]">de 3</span>
        </p>
        <p class="text-[10px] text-purple-600 font-medium mt-0.5">Listos para aprobación</p>
      </Card>
    </div>

    <!-- Table Card -->
    <Card>
      <div class="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="relative flex-1 max-w-xs">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
          <input
            type="text"
            placeholder="Buscar por ID, título o archivo..."
            v-model="searchTerm"
            class="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
          />
        </div>
        <div class="flex items-center gap-2">
          <button
            @click="validateAll"
            class="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-[#00aea7] rounded-lg shadow-sm hover:opacity-95 transition-all cursor-pointer"
          >
            <CheckCircle :size="13" />
            <span>Validar todas las extracciones</span>
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-50 bg-slate-50/50">
              <th
                v-for="h in ['ID & Título', 'Metadato procesado', 'Documento', 'DOI', 'Confianza IA', 'Acciones']"
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
              <td class="px-4 py-3.5 max-w-[220px]">
                <span class="text-xs font-mono font-bold text-[#1565C0]">#{{ row.id }}</span>
                <p class="text-xs font-medium text-[#1a2332] truncate mt-0.5" :title="row.title">{{ row.title }}</p>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <span class="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100">
                  {{ row.campo }}
                </span>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <button
                  @click="openPdfPreview(row)"
                  class="flex items-center gap-1.5 px-2.5 py-1 bg-teal-50/60 hover:bg-teal-50 border border-teal-200/80 rounded-lg text-xs font-medium text-slate-700 transition-colors cursor-pointer"
                  title="Haz clic para abrir el documento PDF original"
                >
                  <FileText :size="14" class="text-[#00aea7] shrink-0" />
                  <span class="underline decoration-teal-300 font-mono text-[11px]">{{ row.documento }}</span>
                  <span class="text-[10px] text-slate-400">({{ row.pags }})</span>
                </button>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <a
                  :href="`https://doi.org/${row.doi}`"
                  target="_blank"
                  rel="noreferrer"
                  class="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 hover:underline font-mono"
                  title="Resolver DOI en CrossRef/org"
                >
                  <Globe :size="13" class="shrink-0 text-blue-500" />
                  <span>{{ row.doi }}</span>
                </a>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <div class="w-14 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :style="{ width: `${row.confianza}%`, background: row.confianza >= 90 ? '#00aea7' : '#F57C00' }"
                    />
                  </div>
                  <span
                    class="text-xs font-bold"
                    :style="{ color: row.confianza >= 90 ? '#2E7D32' : '#F57C00' }"
                  >
                    {{ row.confianza }}%
                  </span>
                </div>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="flex items-center gap-1.5">
                  <button
                    @click="toggleValidate(row.id)"
                    :class="[
                      'flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold rounded-lg transition-all cursor-pointer shadow-sm',
                      approvedIds[row.id]
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : 'text-emerald-700 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100'
                    ]"
                  >
                    <CheckCircle :size="13" :class="approvedIds[row.id] ? 'text-emerald-700' : ''" />
                    <span>{{ approvedIds[row.id] ? 'Validado' : 'Validar extracción' }}</span>
                  </button>
                  <button
                    @click="selectedItem = row"
                    class="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-[#00aea7] bg-[#00aea7]/10 border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/20 transition-all cursor-pointer shadow-sm"
                  >
                    <Eye :size="13" />
                    <span>Ver metadato</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Modal Visualizar Metadato Extraído -->
    <div
      v-if="selectedItem"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
              <FileText :size="18" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-800">Metadato Extraído desde PDF</h3>
              <p class="text-[11px] text-slate-500">Registro #{{ selectedItem.id }} — Documento: {{ selectedItem.documento }}</p>
            </div>
          </div>
          <button
            @click="selectedItem = null"
            class="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            <X :size="18" />
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div class="grid grid-cols-2 gap-3 bg-slate-50 p-3.5 rounded-xl border border-gray-100">
            <div>
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Campo Procesado</span>
              <span class="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded border border-blue-100 inline-block mt-1">
                {{ selectedItem.campo }}
              </span>
            </div>
            <div>
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Confianza OCR/IA</span>
              <span class="text-xs font-bold text-emerald-700 mt-1 inline-block">{{ selectedItem.confianza }}%</span>
            </div>
            <div class="col-span-2 pt-2 border-t border-gray-200/60">
              <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">Identificador Digital (DOI)</span>
              <span class="text-xs font-mono text-slate-700 font-medium block mt-0.5">{{ selectedItem.doi }}</span>
            </div>
          </div>

          <div>
            <span class="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
              Valor Extraído del Documento original
            </span>
            <div class="bg-emerald-50/60 border border-emerald-200/80 rounded-xl p-4 text-xs text-slate-800 font-medium leading-relaxed">
              {{ selectedItem.metadatoExtraido }}
            </div>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 bg-slate-50/60 flex items-center justify-end gap-2">
          <button
            v-if="!approvedIds[selectedItem.id]"
            @click="approvedIds[selectedItem.id] = true; selectedItem = null"
            class="px-4 py-1.5 rounded-lg text-xs font-semibold text-white bg-[#00aea7] hover:opacity-90 transition-opacity cursor-pointer shadow-sm flex items-center gap-1.5"
          >
            <CheckCircle :size="14" /> Validar extracción ahora
          </button>
          <button
            @click="selectedItem = null"
            class="px-4 py-1.5 rounded-lg text-xs font-semibold text-slate-600 bg-white border border-gray-200 hover:bg-gray-50 transition-colors cursor-pointer"
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
import { FileText, CheckCircle, Globe, Zap, Search, Eye, X } from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import SectionHeader from '../components/common/SectionHeader.vue'

const searchTerm = ref('')
const selectedItem = ref<any | null>(null)
const approvedIds = ref<Record<string, boolean>>({})

const pdfRecords = [
  {
    id: '13458',
    title: 'Machine Learning for Biodiversity in Andean Ecosystems',
    campo: 'Áreas ODS',
    documento: 'paper_2024_biodiversity.pdf',
    doi: '10.1016/j.envsoft.2024.105892',
    confianza: 96,
    metadatoExtraido: "ODS 15: Vida de ecosistemas terrestres. Extracción verificada de la sección 'Impact and Sustainability' (Página 11).",
    pags: '12 págs',
    tamaño: '2.4 MB'
  },
  {
    id: '18954',
    title: 'Open Science Infrastructure and Policy Frameworks in Chile',
    campo: 'Derechos de acceso',
    documento: 'open_science_chile_report.pdf',
    doi: '10.1038/s41586-024-07123-x',
    confianza: 88,
    metadatoExtraido: 'Acceso Abierto — Creative Commons Atribución 4.0 Internacional (CC BY 4.0). Declarado explícitamente en pie de página (Página 2).',
    pags: '24 págs',
    tamaño: '4.1 MB'
  },
  {
    id: '22103',
    title: 'Genomic Sequencing Methods for Marine Microorganisms',
    campo: 'Área OCDE',
    documento: 'marine_genomics_study.pdf',
    doi: '10.1016/j.genomics.2024.110234',
    confianza: 94,
    metadatoExtraido: '106 Biología y Ciencias Biológicas (1.06). Clasificado algorítmicamente mediante análisis semántico del texto completo.',
    pags: '18 págs',
    tamaño: '3.7 MB'
  }
]

const filtered = computed(() => {
  return pdfRecords.filter(r =>
    r.title.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    r.id.includes(searchTerm.value) ||
    r.documento.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    r.campo.toLowerCase().includes(searchTerm.value.toLowerCase())
  )
})

const toggleValidate = (id: string) => {
  approvedIds.value[id] = !approvedIds.value[id]
}

const validateAll = () => {
  pdfRecords.forEach(r => { approvedIds.value[r.id] = true })
  alert('¡Todas las extracciones PDF han sido marcadas como validadas!')
}

const openPdfPreview = (row: any) => {
  alert(`Cargando vista previa del documento original: ${row.documento} (${row.pags})`)
}
</script>

