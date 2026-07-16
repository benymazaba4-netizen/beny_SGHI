<template>
  <div class="empty-state flex flex-col items-center justify-center py-12 px-6 text-center">
    <img
      :src="image"
      :alt="title"
      class="w-40 h-32 object-contain mb-4 opacity-90"
      loading="lazy"
    />
    <h3 class="text-base font-semibold text-slate-700">{{ title }}</h3>
    <p v-if="description" class="text-sm text-slate-500 mt-1 max-w-sm">{{ description }}</p>
    <div v-if="$slots.action" class="mt-5">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'Aucune donnée' },
  description: String,
  image: { type: String, default: '/illustrations/empty-data.svg' },
})
</script>
