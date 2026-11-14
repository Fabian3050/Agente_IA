<template>
  <div class="h-full overflow-y-auto space-y-6">
    <SectionHeader
      title="Gestión de Usuarios y Control de Permisos"
      description="Panel administrativo para crear nuevos usuarios, asignar o modificar roles y revocar privilegios de acceso al sistema."
    />

    <!-- Stats bar -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card
        v-for="(s, idx) in stats"
        :key="idx"
        customClass="p-4 flex items-center justify-between border border-gray-100 bg-white"
      >
        <div>
          <p class="text-[11px] text-[#6b7a90] mb-1 font-medium">{{ s.label }}</p>
          <p class="text-2xl font-bold" :style="{ color: s.color }">{{ s.value }}</p>
        </div>
        <div class="w-11 h-11 rounded-xl flex items-center justify-center bg-gray-50 text-gray-600">
          <component :is="s.icon" :size="20" :style="{ color: s.color }" />
        </div>
      </Card>
    </div>

    <!-- Main Table Card -->
    <Card>
      <!-- Toolbar -->
      <div class="flex flex-wrap items-center justify-between gap-3 p-4 border-b border-gray-50 bg-slate-50/40">
        <div class="flex items-center gap-3 flex-1 min-w-[280px]">
          <div class="relative flex-1 max-w-xs">
            <Search :size="14" class="absolute left-3 top-1/2 -translate-y-1/2 text-[#6b7a90]" />
            <input
              type="text"
              placeholder="Buscar por nombre, correo o ID..."
              v-model="search"
              class="w-full pl-9 pr-3 py-2 text-xs border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
            />
          </div>
          <div class="flex gap-1">
            <button
              v-for="f in ['Todos', 'Activo', 'Revocado']"
              :key="f"
              @click="statusFilter = f"
              class="px-3 py-1.5 text-xs rounded-lg font-medium transition-all cursor-pointer"
              :style="{
                background: statusFilter === f ? '#00aea7' : '#f0f4f8',
                color: statusFilter === f ? '#fff' : '#6b7a90',
              }"
            >
              {{ f }}
            </button>
          </div>
        </div>

        <button
          @click="isCreateModalOpen = true"
          class="flex items-center gap-1.5 px-4 py-2 text-xs font-medium text-white bg-[#00aea7] hover:bg-[#009b95] rounded-xl shadow-sm transition-all cursor-pointer"
        >
          <UserPlus :size="15" />
          <span>Crear Usuario y Asignar Permiso</span>
        </button>
      </div>

      <!-- Table -->
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b border-gray-100 bg-slate-50/80">
              <th
                v-for="h in ['Usuario / Correo', 'Rol & Departamento', 'Permisos Asignados', 'Estado', 'Última Actividad', 'Acciones']"
                :key="h"
                class="text-left px-4 py-3.5 text-[11px] font-semibold text-[#6b7a90] uppercase tracking-wide"
              >
                {{ h }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="u in filteredUsers"
              :key="u.id"
              :class="['border-b border-gray-50 transition-colors', u.status === 'Revocado' ? 'bg-red-50/20' : 'hover:bg-gray-50/50']"
            >
              <td class="px-4 py-3.5">
                <div class="flex items-center gap-3">
                  <div
                    :class="[
                      'w-9 h-9 rounded-full flex items-center justify-center font-bold text-xs',
                      u.status === 'Revocado' ? 'bg-red-100 text-red-700' : 'bg-[#00aea7]/10 text-[#00aea7]'
                    ]"
                  >
                    {{ getInitials(u.name) }}
                  </div>
                  <div>
                    <p class="text-xs font-bold text-[#1a2332]">{{ u.name }}</p>
                    <p class="text-[11px] text-[#6b7a90]">{{ u.email }}</p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-3.5">
                <p class="text-xs font-medium text-[#1a2332]">{{ u.role }}</p>
                <p class="text-[11px] text-[#6b7a90]">{{ u.department }}</p>
              </td>
              <td class="px-4 py-3.5 max-w-xs">
                <div class="flex flex-wrap gap-1">
                  <span
                    v-for="(p, i) in u.permissions.slice(0, 2)"
                    :key="i"
                    class="text-[10px] font-medium px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md border border-slate-200/60"
                  >
                    {{ p }}
                  </span>
                  <span
                    v-if="u.permissions.length > 2"
                    class="text-[10px] font-semibold px-1.5 py-0.5 bg-teal-50 text-teal-700 rounded-md border border-teal-200"
                  >
                    +{{ u.permissions.length - 2 }} más
                  </span>
                </div>
              </td>
              <td class="px-4 py-3.5">
                <span
                  :class="[
                    'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
                    u.status === 'Activo' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-red-50 text-red-700 border border-red-200'
                  ]"
                >
                  <span :class="['w-1.5 h-1.5 rounded-full', u.status === 'Activo' ? 'bg-emerald-500' : 'bg-red-500']" />
                  {{ u.status }}
                </span>
              </td>
              <td class="px-4 py-3.5 text-xs text-[#6b7a90]">{{ u.lastActive }}</td>
              <td class="px-4 py-3.5">
                <div class="flex items-center gap-2">
                  <button
                    @click="editingUser = { ...u }"
                    class="flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-slate-700 bg-white border border-gray-200 rounded-lg hover:bg-slate-50 cursor-pointer"
                  >
                    <Key :size="13" class="text-[#00aea7]" />
                    <span>Modificar</span>
                  </button>
                  <button
                    @click="toggleRevoke(u.id)"
                    :class="[
                      'flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-lg border transition-colors cursor-pointer',
                      u.status === 'Activo' ? 'text-red-600 border-red-200 bg-red-50/40 hover:bg-red-50' : 'text-emerald-700 border-emerald-200 bg-emerald-50/40 hover:bg-emerald-50'
                    ]"
                  >
                    <component :is="u.status === 'Activo' ? UserX : UserCheck" :size="13" />
                    <span>{{ u.status === 'Activo' ? 'Revocar' : 'Reactivar' }}</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </Card>

    <!-- Modal Crear Usuario -->
    <div
      v-if="isCreateModalOpen"
      class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    >
      <div class="bg-white rounded-2xl shadow-2xl max-w-lg w-full border border-gray-100 overflow-hidden flex flex-col">
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-slate-50/50">
          <div class="flex items-center gap-2.5">
            <div class="w-9 h-9 rounded-xl bg-[#00aea7]/10 text-[#00aea7] flex items-center justify-center font-bold">
              <UserPlus :size="18" />
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-800">Crear Usuario y Permisos</h3>
              <p class="text-[11px] text-slate-500">Asigne un nuevo rol institucional al sistema</p>
            </div>
          </div>
          <button @click="isCreateModalOpen = false" class="p-1.5 text-slate-400 hover:text-slate-600">
            <X :size="18" />
          </button>
        </div>

        <form @submit.prevent="handleCreateUser" class="p-6 space-y-4 max-h-[75vh] overflow-y-auto">
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-semibold text-slate-700 block mb-1">Nombre Completo</label>
              <input
                type="text"
                required
                placeholder="Ej: Carlos Fuentes"
                v-model="newUserName"
                class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
              />
            </div>
            <div>
              <label class="text-xs font-semibold text-slate-700 block mb-1">Correo Institucional</label>
              <input
                type="email"
                required
                placeholder="carlos.fuentes@usach.cl"
                v-model="newUserEmail"
                class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#00aea7]/20 focus:border-[#00aea7]"
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="text-xs font-semibold text-slate-700 block mb-1">Rol Asignado</label>
              <select
                v-model="newUserRole"
                class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg bg-white"
              >
                <option value="Administrador">Administrador</option>
                <option value="Curador">Curador</option>
                <option value="Auditor">Auditor</option>
              </select>
            </div>
            <div>
              <label class="text-xs font-semibold text-slate-700 block mb-1">Departamento</label>
              <input
                type="text"
                v-model="newUserDept"
                class="w-full px-3 py-2 text-xs border border-gray-200 rounded-lg"
              />
            </div>
          </div>

          <div class="pt-4 border-t border-gray-100 flex items-center justify-end gap-2">
            <button
              type="button"
              @click="isCreateModalOpen = false"
              class="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              Cancelar
            </button>
            <button
              type="submit"
              class="px-4 py-2 text-xs font-semibold text-white bg-[#00aea7] hover:bg-[#009b95] rounded-lg shadow-sm"
            >
              Guardar Usuario
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search, UserPlus, Users, UserCheck, UserX, Key, X } from 'lucide-vue-next'
import Card from '../components/common/Card.vue'
import SectionHeader from '../components/common/SectionHeader.vue'

interface UserItem {
  id: string
  name: string
  email: string
  role: string
  status: 'Activo' | 'Revocado'
  permissions: string[]
  department: string
  lastActive: string
}

const users = ref<UserItem[]>([
  {
    id: 'USR-001',
    name: 'Fabián Escobedo',
    email: 'admin.vriic@usach.cl',
    role: 'Administrador del Sistema',
    status: 'Activo',
    permissions: ['Gestión total del sistema', 'Crear/Revocar usuarios', 'Aprobación de metadatos', 'Configuración LLM'],
    department: 'VRIIC Central',
    lastActive: 'En línea ahora'
  },
  {
    id: 'USR-002',
    name: 'María González',
    email: 'maria.gonzalez@usach.cl',
    role: 'Curador Principal',
    status: 'Activo',
    permissions: ['Aprobación de metadatos', 'Sugerencias agente de IA', 'Ver monitoreo y alertas'],
    department: 'Facultad de Ciencia',
    lastActive: 'Hace 12 min'
  },
  {
    id: 'USR-003',
    name: 'Roberto Muñoz',
    email: 'roberto.munoz@usach.cl',
    role: 'Auditor de Calidad',
    status: 'Activo',
    permissions: ['Ver auditoría', 'Exportar reportes de calidad', 'Ver monitoreo y alertas'],
    department: 'Facultad de Química y Biología',
    lastActive: 'Ayer a las 18:20'
  },
  {
    id: 'USR-004',
    name: 'Patricia Soto',
    email: 'patricia.soto@usach.cl',
    role: 'Curador de Contenidos',
    status: 'Revocado',
    permissions: ['Ver monitoreo y alertas'],
    department: 'Facultad de Humanidades',
    lastActive: 'Hace 5 días (Sesión revocada)'
  }
])

const search = ref('')
const statusFilter = ref('Todos')
const isCreateModalOpen = ref(false)
const editingUser = ref<UserItem | null>(null)

const newUserName = ref('')
const newUserEmail = ref('')
const newUserRole = ref('Curador')
const newUserDept = ref('Facultad de Ingeniería')

const stats = computed(() => [
  { label: 'Total usuarios del sistema', value: users.value.length, color: '#1565C0', icon: Users },
  { label: 'Permisos activos', value: users.value.filter(u => u.status === 'Activo').length, color: '#00aea7', icon: UserCheck },
  { label: 'Accesos revocados', value: users.value.filter(u => u.status === 'Revocado').length, color: '#d32f2f', icon: UserX },
])

const filteredUsers = computed(() => {
  return users.value.filter(u => {
    const s = search.value.toLowerCase()
    const matchSearch = u.name.toLowerCase().includes(s) || u.email.toLowerCase().includes(s) || u.id.toLowerCase().includes(s)
    const matchStatus = statusFilter.value === 'Todos' || u.status === statusFilter.value
    return matchSearch && matchStatus
  })
})

const getInitials = (name: string) => {
  return name.split(' ').map(n => n[0]).slice(0, 2).join('').toUpperCase()
}

const toggleRevoke = (id: string) => {
  const target = users.value.find(u => u.id === id)
  if (target) {
    target.status = target.status === 'Activo' ? 'Revocado' : 'Activo'
    target.lastActive = target.status === 'Activo' ? 'Reactivado hoy' : 'Acceso revocado por admin'
  }
}

const handleCreateUser = () => {
  if (!newUserName.value || !newUserEmail.value) return
  users.value.unshift({
    id: `USR-00${users.value.length + 1}`,
    name: newUserName.value,
    email: newUserEmail.value,
    role: newUserRole.value,
    status: 'Activo',
    permissions: ['Aprobación de metadatos', 'Ver monitoreo y alertas'],
    department: newUserDept.value,
    lastActive: 'Registrado recién'
  })
  isCreateModalOpen.value = false
  newUserName.value = ''
  newUserEmail.value = ''
  alert('Usuario registrado exitosamente en el catálogo RBAC.')
}
</script>

