<template>
  <div class="rounded-2xl border border-slate-100 bg-white/80 p-3">
    <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-2">
      <div
        v-for="step in steps"
        :key="step.code"
        class="rounded-xl border px-3 py-2 text-xs"
        :class="stepClass(step.state)"
      >
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full" :class="dotClass(step.state)" />
          <span class="font-bold">{{ step.label }}</span>
        </div>
        <p class="mt-1 text-[11px] opacity-80">{{ step.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  steps: { type: Array, default: () => [] },
})

function stepClass(state) {
  if (state === 'done') return 'border-emerald-100 bg-emerald-50 text-emerald-800'
  if (state === 'current') return 'border-blue-200 bg-blue-50 text-blue-800 shadow-sm'
  return 'border-slate-100 bg-slate-50 text-slate-500'
}

function dotClass(state) {
  if (state === 'done') return 'bg-emerald-500'
  if (state === 'current') return 'bg-blue-500 animate-pulse'
  return 'bg-slate-300'
}
</script>
