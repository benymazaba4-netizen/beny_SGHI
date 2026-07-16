<template>
  <div class="app-card overflow-hidden">
    <div v-if="image" class="relative h-24 overflow-hidden">
      <img :src="image" :alt="title" class="w-full h-full object-cover" />
      <div class="absolute inset-0 bg-gradient-to-t from-white via-white/40 to-transparent" />
    </div>
    <div class="p-6" :class="{ 'pt-5': !image }">
      <h3 v-if="title" class="text-base font-bold text-slate-900 mb-5 pb-4 border-b border-slate-100 flex items-center gap-2">
        <span
          class="w-1 h-5 rounded-full shrink-0"
          :style="{ background: `linear-gradient(180deg, var(--theme-from, #6366f1), var(--theme-to, #818cf8))` }"
        />
        {{ title }}
      </h3>
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: String,
  image: String,
})
</script>
