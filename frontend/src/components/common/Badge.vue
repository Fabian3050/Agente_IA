<template>
  <span
    :class="[
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      styleClasses
    ]"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  color?: string
}>()

const styles: Record<string, string> = {
  Alta: 'bg-red-50 text-red-700 border border-red-200',
  Media: 'bg-amber-50 text-amber-700 border border-amber-200',
  Baja: 'bg-blue-50 text-blue-600 border border-blue-200',
  Pendiente: 'bg-orange-50 text-orange-700 border border-orange-200',
  'En proceso': 'bg-teal-50 text-teal-700 border border-teal-200',
  'En recuperación': 'bg-blue-50 text-blue-700 border border-blue-200',
  'En clasificación': 'bg-purple-50 text-purple-700 border border-purple-200',
  'En revisión': 'bg-indigo-50 text-indigo-700 border border-indigo-200',
  Aprobada: 'bg-green-50 text-green-700 border border-green-200',
  Rechazada: 'bg-rose-50 text-rose-700 border border-rose-200',
  Invalidada: 'bg-zinc-100 text-zinc-700 border border-zinc-200',
  Exportada: 'bg-cyan-50 text-cyan-700 border border-cyan-200',
  Cargada: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  Cerrada: 'bg-gray-100 text-gray-700 border border-gray-200',
  Completado: 'bg-green-50 text-green-700 border border-green-200',
  Conectado: 'bg-green-50 text-green-700 border border-green-200',
  Administrador: 'bg-purple-50 text-purple-700 border border-purple-200',
  Curador: 'bg-teal-50 text-teal-700 border border-teal-200',
  Auditor: 'bg-blue-50 text-blue-700 border border-blue-200',
}

const styleClasses = computed(() => {
  return props.color && styles[props.color]
    ? styles[props.color]
    : 'bg-gray-50 text-gray-600 border border-gray-200'
})
</script>

