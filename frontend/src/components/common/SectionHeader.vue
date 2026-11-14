<template>
  <div class="mb-6">
    <h1 class="text-xl font-semibold text-[#1a2332]">{{ title }}</h1>
    <p class="text-sm text-[#6b7a90] mt-1">{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description: string
}>()
</script>

