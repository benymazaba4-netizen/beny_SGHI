<template>
  <div class="p-4 bg-white rounded-xl border border-gray-200">
    <h3 class="font-semibold text-gray-800 mb-3">{{ title }}</h3>
    <svg :viewBox="`0 0 ${width} ${height}`" class="w-full h-32">
      <polyline
        :points="points"
        fill="none"
        stroke="#1E3A5F"
        stroke-width="2"
      />
      <circle
        v-for="(p, i) in coords"
        :key="i"
        :cx="p.x"
        :cy="p.y"
        r="3"
        fill="#2563eb"
      />
    </svg>
    <div class="flex justify-between text-xs text-gray-500 mt-2">
      <span v-for="(l, i) in labels.slice(0, 6)" :key="i">{{ l }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: { type: String, default: 'Tendance' },
  values: { type: Array, default: () => [] },
  labels: { type: Array, default: () => [] },
})

const width = 300
const height = 100
const padding = 10

const coords = computed(() => {
  const vals = props.values.filter(v => v != null && !Number.isNaN(Number(v)))
  if (vals.length < 2) return []
  const min = Math.min(...vals)
  const max = Math.max(...vals) || 1
  const range = max - min || 1
  return vals.map((v, i) => ({
    x: padding + (i / (vals.length - 1)) * (width - padding * 2),
    y: height - padding - ((Number(v) - min) / range) * (height - padding * 2),
  }))
})

const points = computed(() => coords.value.map(p => `${p.x},${p.y}`).join(' '))
</script>
