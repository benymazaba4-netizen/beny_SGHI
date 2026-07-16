<template>
  <article
    class="group relative overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5"
  >
    <div class="h-28 bg-gradient-to-br from-sky-50 via-white to-emerald-50 relative overflow-hidden">
      <img
        v-if="thumbnail"
        :src="thumbnail"
        :alt="title"
        class="absolute inset-0 w-full h-full object-cover opacity-90 group-hover:scale-105 transition-transform duration-500"
      />
      <div v-else class="absolute inset-0 flex items-center justify-center">
        <svg class="w-14 h-14 text-sky-200" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      <span
        class="absolute top-3 right-3 text-[10px] font-bold uppercase tracking-wide px-2.5 py-1 rounded-full shadow-sm"
        :class="badgeClass"
      >{{ statusLabel }}</span>
    </div>
    <div class="p-4">
      <div class="flex items-start gap-3">
        <UserAvatar :name="patientName" size="sm" />
        <div class="min-w-0 flex-1">
          <h4 class="font-semibold text-slate-800 truncate">{{ title }}</h4>
          <p class="text-xs text-slate-500 mt-0.5">{{ patientName }}</p>
          <p v-if="subtitle" class="text-xs text-slate-400 mt-1">{{ subtitle }}</p>
        </div>
      </div>
      <div v-if="$slots.actions" class="mt-4 flex flex-wrap gap-2">
        <slot name="actions" />
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import UserAvatar from './UserAvatar.vue'

const props = defineProps({
  title: { type: String, required: true },
  patientName: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  status: { type: String, default: 'PRESCRIT' },
  thumbnail: { type: String, default: '' },
})

const STATUS_MAP = {
  PRESCRIT: { label: 'En attente', cls: 'bg-amber-100 text-amber-800' },
  PRELEVE: { label: 'Prélevé', cls: 'bg-sky-100 text-sky-800' },
  EN_COURS: { label: 'En cours', cls: 'bg-indigo-100 text-indigo-800' },
  VALIDATION: { label: 'À valider', cls: 'bg-orange-100 text-orange-800' },
  VALIDE: { label: 'Validé', cls: 'bg-emerald-100 text-emerald-800' },
  REFUSE: { label: 'Refusé', cls: 'bg-red-100 text-red-800' },
  CRITIQUE: { label: 'Critique', cls: 'bg-red-600 text-white' },
}

const statusLabel = computed(() => STATUS_MAP[props.status]?.label || props.status)
const badgeClass = computed(() => STATUS_MAP[props.status]?.cls || 'bg-slate-100 text-slate-700')
</script>
