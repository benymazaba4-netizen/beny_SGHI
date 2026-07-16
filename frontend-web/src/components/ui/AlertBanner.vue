<template>
  <div
    v-if="message"
    class="px-4 py-3 rounded-xl text-sm font-medium transition-all duration-300 animate-fade-in"
    :class="type === 'success'
      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
      : 'bg-red-50 text-red-700 border border-red-200'"
  >
    {{ message }}
  </div>
</template>

<script setup>
defineProps({
  message: String,
  type: { type: String, default: 'success' },
})
</script>

<style scoped>
.animate-fade-in { animation: fade-in 0.3s ease; }
@keyframes fade-in { from { opacity: 0; transform: translateY(-4px); } to { opacity: 1; transform: translateY(0); } }
</style>
