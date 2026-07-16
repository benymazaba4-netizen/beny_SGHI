<template>
  <div class="animate-pulse space-y-3 py-2">
    <div v-for="n in rows" :key="n" class="flex gap-4 items-center px-4">
      <div v-for="col in columns" :key="col" class="h-4 bg-slate-200/80 rounded-lg flex-1" :style="{ maxWidth: colWidths[col % colWidths.length] }" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  rows: { type: Number, default: 5 },
  columns: { type: Number, default: 4 },
})

const colWidths = ['40%', '25%', '20%', '15%']
</script>
