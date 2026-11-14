<template>
  <div :class="['bg-white rounded-xl border border-black/[0.06] shadow-sm', customClass]">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  customClass?: string
}>()
</script>

