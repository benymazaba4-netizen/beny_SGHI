<template>
  <div class="app-card stat-card-hover p-5 relative overflow-hidden group">
    <div
      class="absolute top-0 left-0 w-full h-1 opacity-80"
      :style="{ background: `linear-gradient(90deg, var(--theme-from, #6366f1), var(--theme-to, #818cf8))` }"
    />
    <div class="flex items-start justify-between gap-3">
      <div class="min-w-0 flex-1">
        <p class="text-xs font-semibold text-slate-500 uppercase tracking-wide">{{ label }}</p>
        <p class="text-2xl font-bold mt-2 text-slate-900" :class="valueClass">{{ value }}</p>
        <p v-if="subtitle" class="text-xs text-slate-400 mt-1">{{ subtitle }}</p>
      </div>
      <div
        v-if="icon || image"
        class="shrink-0 w-12 h-12 rounded-2xl flex items-center justify-center overflow-hidden transition-transform group-hover:scale-110"
        :style="{ background: `linear-gradient(135deg, var(--theme-light, #eef2ff), var(--theme-glow, rgba(99,102,241,0.15)))` }"
      >
        <img v-if="image" :src="image" :alt="label" class="w-full h-full object-cover" />
        <img v-else-if="icon" :src="icon" :alt="label" class="w-6 h-6" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: String,
  value: [String, Number],
  subtitle: String,
  valueClass: { type: String, default: '' },
  icon: String,
  image: String,
})
</script>
