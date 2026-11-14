<template>
  <div class="h-full overflow-y-auto">
    <SectionHeader
      title="Validación de metadatos"
      description="Asegure la calidad de los metadatos antes de su aprobación final."
    />

    <Card>
      <div class="p-4 border-b border-gray-50 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="relative flex-1 max-w-xs">
          <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
          <input
            type="text"
            placeholder="Buscar por ID, título o campo..."
            v-model="searchVal"
            class="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
          />
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <div class="flex gap-1">
            <button
              v-for="f in ['Todos', 'Apto p/ Aprobación', 'Anomalía Técnica']"
              :key="f"
              @click="filterStatus = f"
              class="px-3 py-1.5 text-xs rounded-lg font-medium transition-all cursor-pointer"
              :style="{
                background: filterStatus === f ? '#00aea7' : '#f0f4f8',
                color: filterStatus === f ? '#fff' : '#6b7a90',
              }"
            >
              {{ f }}
            </button>
          </div>
        </div>
      </div>

      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-50 bg-slate-50/50">
              <th
                v-for="h in ['ID & Título', 'Campo evaluado', 'Fuente', 'Confianza IA', 'Acciones']"
                :key="h"
                class="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide"
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
                <p class="text-xs font-medium text-[#1a2332] truncate mt-0.5">{{ row.title }}</p>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <span class="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100">
                  {{ row.campo }}
                </span>
              </td>
              <td class="px-4 py-3.5 text-xs">
                <div class="flex items-center gap-1.5 font-semibold text-slate-800">
                  <Cpu :size="14" class="text-[#00aea7] shrink-0" />
                  <span>{{ row.fuenteHerramienta }}</span>
                </div>
                <p class="text-[10px] font-mono text-slate-400 mt-0.5">{{ row.sintaxis }}</p>
              </td>
              <td class="px-4 py-3.5 whitespace-nowrap">
                <div class="flex items-center gap-2">
                  <div class="w-14 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full"
                      :style="{ width: `${row.confianza}%`, background: row.confianza >= 80 ? '#2E7D32' : '#F57C00' }"
                    />
                  </div>
                  <span
                    class="text-xs font-bold"
                    :style="{ color: row.confianza >= 80 ? '#2E7D32' : '#F57C00' }"
                  >
                    {{ row.confianza }}%
                  </span>
                </div>
              </td>
              <td class="px-4 py-3.5">
                <div class="flex items-center gap-1.5 whitespace-nowrap">
                  <button
                    @click="validateItem(row)"
                    class="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg hover:bg-emerald-100 transition-all cursor-pointer shadow-sm"
                    title="Validar el metadato recuperado"
                  >
                    <ShieldCheck :size="12" />
                    <span>Validar</span>
                  </button>
                  <button
                    @click="selectedVal = row"
                    class="flex items-center gap-1 px-2.5 py-1.5 text-xs font-semibold text-[#00aea7] bg-[#00aea7]/10 border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/20 transition-all cursor-pointer shadow-sm"
                    title="Ver el metadato recuperado"
                  >
                    <Eye :size="12" />
                    <span>Ver</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Modal de Metadato Recuperado -->
    <div
      v-if="selectedVal"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-xs p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl border border-gray-100 w-full max-w-lg overflow-hidden flex flex-col">
        <div class="px-6 py-4 border-b border-gray-100 bg-slate-50 flex items-center justify-between">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
              <Eye :size="18" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-800">Metadato Recuperado</h3>
              <p class="text-[11px] text-slate-500">Valor extraído y evaluado algorítmicamente</p>
            </div>
          </div>
          <button
            @click="selectedVal = null"
            class="p-1 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200/60 transition-colors cursor-pointer"
          >
            <X :size="18" />
          </button>
        </div>

        <div class="p-6 space-y-4">
          <div>
            <span class="text-[10px] font-bold uppercase tracking-wider text-[#00aea7] block mb-1">ID Registro #{{ selectedVal.id }}</span>
            <h4 class="text-base font-bold text-slate-800 leading-snug">{{ selectedVal.title }}</h4>
          </div>

          <div class="p-4 rounded-xl bg-slate-50 border border-slate-200/60 space-y-3">
            <div>
              <span class="text-[11px] font-semibold text-slate-500 uppercase block mb-1">Campo evaluado</span>
              <span class="text-xs font-semibold px-2.5 py-1 bg-blue-50 text-blue-700 rounded-md border border-blue-100 inline-block">
                {{ selectedVal.campo }}
              </span>
            </div>

            <div>
              <span class="text-[11px] font-semibold text-slate-500 uppercase block mb-1">Valor propuesto por IA (Metadato)</span>
              <div class="p-3 bg-white rounded-lg border border-slate-200 font-mono text-xs text-teal-900 font-medium break-words">
                {{ selectedVal.propuestaIA }}
              </div>
            </div>
          </div>

          <div class="p-3 rounded-xl border border-gray-100 bg-gray-50/50">
            <span class="text-[10px] text-slate-400 font-bold uppercase block mb-0.5">Sintaxis / Formato</span>
            <span class="font-mono text-slate-600 text-[11px] block">{{ selectedVal.sintaxis }}</span>
            <p class="text-[11px] text-slate-500 mt-2">{{ selectedVal.detalle }}</p>
          </div>
        </div>

        <div class="px-6 py-4 border-t border-gray-100 bg-slate-50 flex justify-end gap-2">
          <button
            @click="validateItem(selectedVal); selectedVal = null"
            class="px-4 py-2 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-sm transition-all cursor-pointer flex items-center gap-1.5"
          >
            <ShieldCheck :size="14" /> Validar metadato
          </button>
          <button
            @click="selectedVal = null"
            class="px-5 py-2 text-xs font-semibold text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm transition-all cursor-pointer"
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
import { Search, Cpu, ShieldCheck, Eye, X } from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import SectionHeader from '../components/common/SectionHeader.vue'

const searchVal = ref('')
const filterStatus = ref('Todos')
const selectedVal = ref<any | null>(null)

const validationRecords = ref([
  {
    id: '13458',
    title: 'Machine Learning for Biodiversity in Andean Ecosystems',
    campo: 'Áreas ODS',
    propuestaIA: 'ODS 15: Vida de ecosistemas terrestres',
    fuenteHerramienta: 'Scopus / OpenAlex',
    sintaxis: 'Clasificación oficial ODS (Válido)',
    confianza: 96,
    color: '#2E7D32',
    estado: 'Apto p/ Aprobación',
    detalle: 'La validación algorítmica verificó que la clasificación sugerida pertenece al vocabulario oficial de Objetivos de Desarrollo Sostenible (ODS 15).'
  },
  {
    id: '18954',
    title: 'Open Science Infrastructure and Policy Frameworks in Chile',
    campo: 'Derechos de acceso',
    propuestaIA: 'Acceso Abierto (Creative Commons CC BY 4.0)',
    fuenteHerramienta: 'Crossref / Unpaywall',
    sintaxis: 'Licencia CC BY 4.0 (Requiere URI)',
    confianza: 74,
    color: '#F57C00',
    estado: 'Anomalía Técnica',
    detalle: 'El motor detectó que el XML local de DSpace requiere el enlace URI completo (https://creativecommons.org/licenses/by/4.0/).'
  },
  {
    id: '22103',
    title: 'Genomic Sequencing Methods for Marine Microorganisms',
    campo: 'Área OCDE',
    propuestaIA: '106 Biología y Ciencias Biológicas (1.06)',
    fuenteHerramienta: 'WoS / Ollama LLM',
    sintaxis: 'Taxonomía OCDE 3 dígitos (Válido)',
    confianza: 94,
    color: '#2E7D32',
    estado: 'Apto p/ Aprobación',
    detalle: 'Clasificado dentro de la taxonomía oficial de Áreas Científico-Tecnológicas de la OCDE (Manual de Frascati).'
  },
  {
    id: '14729',
    title: 'Urban Mobility Patterns in Santiago Metropolitan Area',
    campo: 'Palabras clave',
    propuestaIA: 'movilidad urbana, transporte público, área metropolitana, planificación urbana',
    fuenteHerramienta: 'OpenAlex',
    sintaxis: 'Términos normalizados y separados por comas',
    confianza: 98,
    color: '#2E7D32',
    estado: 'Apto p/ Aprobación',
    detalle: 'Palabras clave contrastadas contra el Tesauro oficial de la UNESCO.'
  }
])

const filtered = computed(() => {
  return validationRecords.value.filter((r) => {
    const s = searchVal.value.toLowerCase()
    const matchSearch = r.title.toLowerCase().includes(s) || r.id.includes(s) || r.campo.toLowerCase().includes(s)
    const matchFilter = filterStatus.value === 'Todos' || r.estado === filterStatus.value
    return matchSearch && matchFilter
  })
})

const validateItem = (item: any) => {
  item.estado = 'Apto p/ Aprobación'
  alert(`¡Validación exitosa para el registro #${item.id}! El metadato ha pasado a estado "En revisión" para aprobación final.`)
}
</script>

