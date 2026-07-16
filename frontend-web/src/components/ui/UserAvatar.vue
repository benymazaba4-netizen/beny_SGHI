<template>
  <div
    class="inline-flex items-center justify-center rounded-full font-semibold text-white shadow-sm ring-2 ring-white/80 shrink-0"
    :class="sizeClass"
    :style="{ background: gradient }"
    :title="name"
  >
    <img
      v-if="photoUrl"
      :src="photoUrl"
      :alt="name"
      class="w-full h-full rounded-full object-cover"
    />
    <span v-else>{{ initials }}</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: 'Utilisateur' },
  photoUrl: { type: String, default: '' },
  size: { type: String, default: 'md' },
})

const sizeClass = computed(() => ({
  sm: 'w-8 h-8 text-xs',
  md: 'w-10 h-10 text-sm',
  lg: 'w-14 h-14 text-base',
  xl: 'w-20 h-20 text-xl',
}[props.size] || 'w-10 h-10 text-sm'))

const initials = computed(() => {
  const parts = (props.name || '?').trim().split(/\s+/).filter(Boolean)
  if (!parts.length) return '?'
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
})

const gradient = computed(() => {
  const name = props.name || 'user'
  let hash = 0
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash)
  }
  const hue1 = Math.abs(hash % 360)
  const hue2 = (hue1 + 40) % 360
  return `linear-gradient(135deg, hsl(${hue1}, 65%, 45%) 0%, hsl(${hue2}, 70%, 38%) 100%)`
})
</script>
