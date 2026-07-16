<template>
  <div>
    <header v-if="title" class="mb-1 animate-fade-in-up">
      <h2 class="text-lg font-bold text-slate-900">{{ title }}</h2>
      <p v-if="subtitle" class="text-sm text-slate-500 mt-0.5">{{ subtitle }}</p>
    </header>
    <div class="app-stack">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({ title: String, subtitle: String })
</script>

<style scoped>
.animate-fade-in-up {
  animation: fade-in-up 0.4s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
