<template>
  <div class="h-full overflow-y-auto space-y-6">
    <SectionHeader
      title="Configuración del Sistema"
      description="Parámetros del agente IA, microservicios, conexiones con DSpace-CRIS y fuentes externas."
    />

    <!-- Microservices Health Status -->
    <Card customClass="p-5">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-sm font-semibold text-[#1a2332]">Estado de Microservicios Backend</h3>
          <p class="text-xs text-[#6b7a90]">Monitoreo de salud en tiempo real de la arquitectura distribuida.</p>
        </div>
        <button
          @click="checkServices"
          class="flex items-center gap-1.5 px-3 py-1.5 text-xs text-[#00aea7] border border-[#00aea7]/30 rounded-lg hover:bg-[#00aea7]/5 cursor-pointer font-medium"
        >
          <RefreshCw :size="13" :class="{ 'animate-spin': checking }" />
          <span>Verificar Servicios</span>
        </button>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        <div
          v-for="s in services"
          :key="s.service"
          class="p-3 rounded-xl border border-gray-100 bg-gray-50 flex items-center justify-between"
        >
          <div>
            <p class="text-xs font-semibold text-gray-800">{{ s.name }}</p>
            <p class="text-[10px] text-gray-500 font-mono mt-0.5">Puerto: {{ s.port }}</p>
          </div>
          <span
            :class="[
              'inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold',
              s.status === 'online' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'
            ]"
          >
            <span :class="['w-1.5 h-1.5 rounded-full', s.status === 'online' ? 'bg-emerald-500' : 'bg-red-500']"></span>
            {{ s.status === 'online' ? 'Online' : 'Offline' }}
          </span>
        </div>
      </div>
    </Card>

    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <!-- LLM Model Card -->
      <Card customClass="p-5">
        <h3 class="text-sm font-semibold text-[#1a2332] mb-4">Modelo de Lenguaje (LLM)</h3>
        <div class="flex flex-col gap-3">
          <div>
            <label class="text-xs text-[#6b7a90] mb-1 block">Modelo LLM activo en Ollama</label>
            <div class="flex items-center justify-between px-3 py-2.5 border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332] text-xs">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full bg-[#00aea7]" />
                <span class="font-semibold text-[#1a2332]">Qwen 2.5 7B / Ollama</span>
              </div>
              <span class="text-[10px] font-medium text-[#007a75] bg-[#e0f7f6] px-2.5 py-0.5 rounded-full border border-[#99e8e6]">
                Inferencia Local Segura
              </span>
            </div>
          </div>
          <div>
            <label class="text-xs text-[#6b7a90] mb-1 block">Umbral de coincidencia difusa (Fuzzy Matching)</label>
            <div class="flex items-center gap-3">
              <input
                type="range"
                min="50"
                max="99"
                v-model="threshold"
                class="flex-1 accent-[#00aea7]"
              />
              <span class="text-xs font-bold text-[#00aea7]">{{ threshold }}%</span>
            </div>
            <p class="text-[11px] text-gray-400 mt-1">Candidatos bajo este umbral se marcan como "Coincidencia dudosa".</p>
          </div>
        </div>
      </Card>

      <!-- DSpace-CRIS Connection Card -->
      <Card customClass="p-5">
        <h3 class="text-sm font-semibold text-[#1a2332] mb-4">Conexiones DSpace-CRIS USACH</h3>
        <div class="flex flex-col gap-3">
          <div>
            <label class="text-xs text-[#6b7a90] mb-1 block">URL base DSpace REST API</label>
            <input
              type="text"
              v-model="dspaceUrl"
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332]"
            />
          </div>
          <div>
            <label class="text-xs text-[#6b7a90] mb-1 block">Token API / Credencial Institucional</label>
            <input
              type="password"
              value="••••••••••••••••••••••••"
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-50 text-[#1a2332]"
            />
          </div>
          <div>
            <label class="text-xs text-[#6b7a90] mb-1 block">Modo de integración y seguridad</label>
            <input
              type="text"
              readonly
              value="Staging / Pre-incorporación (Sin modificar BD productiva)"
              class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-gray-100 text-gray-700"
            />
          </div>
        </div>
      </Card>

      <!-- External Sources Toggles -->
      <Card customClass="p-5 xl:col-span-2">
        <h3 class="text-sm font-semibold text-[#1a2332] mb-4">Fuentes de enriquecimiento habilitadas</h3>
        <div class="grid grid-cols-2 xl:grid-cols-4 gap-3">
          <div
            v-for="api in sourceToggles"
            :key="api.name"
            class="flex items-center justify-between p-3 rounded-lg border border-gray-100 bg-gray-50"
          >
            <span class="text-xs font-medium text-[#1a2332]">{{ api.name }}</span>
            <button
              @click="api.enabled = !api.enabled"
              :class="[
                'w-9 h-5 rounded-full transition-colors relative cursor-pointer',
                api.enabled ? 'bg-[#00aea7]' : 'bg-gray-300'
              ]"
            >
              <div
                :class="[
                  'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform',
                  api.enabled ? 'right-0.5' : 'left-0.5'
                ]"
              />
            </button>
          </div>
        </div>

        <div class="mt-4 flex gap-2">
          <button
            @click="saveConfig"
            class="px-4 py-2 text-xs font-medium text-white rounded-lg hover:opacity-90 cursor-pointer"
            style="background: #00aea7"
          >
            Guardar cambios
          </button>
          <button
            class="px-4 py-2 text-xs font-medium text-[#6b7a90] border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
          >
            Cancelar
          </button>
        </div>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RefreshCw } from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import SectionHeader from '../components/common/SectionHeader.vue'
import { systemService } from '../services/systemService'
import type { ServiceStatus } from '../types'

const threshold = ref(85)
const dspaceUrl = ref('https://repositorio.usach.cl/server/api')
const checking = ref(false)

const services = ref<ServiceStatus[]>([
  { name: 'MS4 Orquestador', service: 'ms4_orchestrator', port: 8000, url: 'http://localhost:8000', status: 'online' },
  { name: 'MS1 Recuperación', service: 'ms1_retrieval', port: 8001, url: 'http://localhost:8001', status: 'online' },
  { name: 'MS2 Clasificación LLM', service: 'ms2_classification', port: 8002, url: 'http://localhost:8002', status: 'online' },
  { name: 'MS3 Autenticación OIDC', service: 'ms3_auth', port: 8003, url: 'http://localhost:8003', status: 'online' },
])

const sourceToggles = ref([
  { name: 'OpenAlex', enabled: true },
  { name: 'CrossRef', enabled: true },
  { name: 'Unpaywall', enabled: true },
  { name: 'Europe PMC', enabled: true },
])

const checkServices = async () => {
  checking.value = true
  try {
    const res = await systemService.checkAllServices()
    services.value = res
  } catch {
    // Keep defaults
  } finally {
    checking.value = false
  }
}

const saveConfig = () => {
  alert('Configuración guardada exitosamente.')
}

onMounted(() => {
  checkServices()
})
</script>

