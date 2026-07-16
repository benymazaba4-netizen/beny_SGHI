<template>
  <section class="space-y-6">
    <div class="relative overflow-hidden rounded-3xl bg-slate-950 text-white shadow-2xl">
      <div class="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(20,184,166,0.35),_transparent_35%),radial-gradient(circle_at_bottom_left,_rgba(59,130,246,0.25),_transparent_30%)]" />
      <div class="relative p-6 md:p-8">
        <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <p class="text-xs uppercase tracking-[0.3em] text-teal-200 font-bold">SGHL Command Center</p>
            <h2 class="mt-2 text-3xl md:text-4xl font-black">Pilotage global hospitalier</h2>
            <p class="mt-2 text-slate-300 max-w-2xl">
              Supervision temps réel des lits, recettes, admissions et flux LIS avec cache backend sécurisé.
            </p>
          </div>
          <span class="inline-flex items-center rounded-full border border-white/15 bg-white/10 px-4 py-2 text-xs font-semibold text-teal-100">
            Cache {{ stats.cache?.hit ? 'servi' : 'rafraîchi' }} · TTL {{ stats.cache?.ttl_seconds || 0 }}s
          </span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <article v-for="card in cards" :key="card.label" class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm text-slate-500">{{ card.label }}</p>
            <p class="mt-2 text-3xl font-black text-slate-900">{{ card.value }}</p>
          </div>
          <div :class="card.iconClass" class="w-12 h-12 rounded-2xl flex items-center justify-center">
            <svg v-if="card.icon === 'bed'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M3 7v10m0-4h18m0 4V9a2 2 0 00-2-2h-5v6M7 7h4v6H3V9a2 2 0 012-2h2z" />
            </svg>
            <svg v-else-if="card.icon === 'money'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 6v12m-4-9.5C8 6.57 9.79 5 12 5s4 1.57 4 3.5S14.21 12 12 12s-4 1.57-4 3.5S9.79 19 12 19s4-1.57 4-3.5M4 12h16" />
            </svg>
            <svg v-else-if="card.icon === 'lab'" class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M10 2v6l-5 9a3 3 0 002.6 4.5h8.8A3 3 0 0019 17l-5-9V2M8 14h8" />
            </svg>
            <svg v-else class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.8" d="M12 6v12m6-6H6m13 8H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v12a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
        <div class="mt-4 h-2 rounded-full bg-slate-100 overflow-hidden">
          <div class="h-full rounded-full transition-all duration-700" :class="card.barClass" :style="{ width: `${card.progress}%` }" />
        </div>
        <p class="mt-2 text-xs font-medium" :class="card.textClass">{{ card.caption }}</p>
      </article>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <article class="xl:col-span-2 rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <div class="flex items-center justify-between">
          <div>
            <h3 class="font-bold text-slate-900">Tendances 7 jours</h3>
            <p class="text-sm text-slate-500">Structures prêtes pour graphiques linéaires</p>
          </div>
        </div>
        <div class="mt-5 grid grid-cols-7 gap-2">
          <div v-for="point in trendPoints" :key="point.label" class="min-h-40 rounded-2xl bg-slate-50 p-2 flex flex-col justify-end gap-1">
            <div class="rounded bg-teal-400" :style="{ height: `${point.recettesHeight}px` }" title="Recettes" />
            <div class="rounded bg-blue-400" :style="{ height: `${point.admissionsHeight}px` }" title="Admissions" />
            <div class="rounded bg-violet-400" :style="{ height: `${point.examensHeight}px` }" title="Examens" />
            <p class="pt-2 text-[10px] text-center text-slate-500">{{ point.label.slice(5) }}</p>
          </div>
        </div>
      </article>
      <article class="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
        <h3 class="font-bold text-slate-900">Flux LIS</h3>
        <p class="text-sm text-slate-500">Attente vs publication</p>
        <div class="mt-5 space-y-3">
          <div v-for="item in lisBreakdown" :key="item.label">
            <div class="flex items-center justify-between text-sm">
              <span class="font-medium text-slate-700">{{ item.label }}</span>
              <span class="font-bold text-slate-900">{{ item.value }}</span>
            </div>
            <div class="mt-1 h-2 rounded-full bg-slate-100 overflow-hidden">
              <div class="h-full rounded-full bg-gradient-to-r from-violet-500 to-fuchsia-500" :style="{ width: `${item.percent}%` }" />
            </div>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: { type: Object, required: true },
})

function formatFCFA(value) {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'XAF', maximumFractionDigits: 0 }).format(value || 0)
}

const cards = computed(() => [
  {
    label: 'Occupation des lits',
    value: `${props.stats.occupation?.taux || 0}%`,
    caption: `${props.stats.occupation?.lits_occupes || 0}/${props.stats.occupation?.total_lits || 0} lits occupés`,
    progress: Math.min(100, props.stats.occupation?.taux || 0),
    icon: 'bed',
    iconClass: 'bg-teal-50 text-teal-700',
    barClass: 'bg-teal-500',
    textClass: 'text-teal-700',
  },
  {
    label: 'Recettes validées',
    value: formatFCFA(props.stats.finances?.recettes_globales),
    caption: `${props.stats.finances?.factures_validees || 0} facture(s) validée(s)`,
    progress: Math.min(100, (props.stats.finances?.factures_validees || 0) * 10),
    icon: 'money',
    iconClass: 'bg-emerald-50 text-emerald-700',
    barClass: 'bg-emerald-500',
    textClass: 'text-emerald-700',
  },
  {
    label: 'Examens LIS',
    value: `${props.stats.laboratoire?.attente || 0}/${props.stats.laboratoire?.publies || 0}`,
    caption: 'En attente vs publiés',
    progress: Math.min(100, ((props.stats.laboratoire?.publies || 0) / Math.max(1, (props.stats.laboratoire?.attente || 0) + (props.stats.laboratoire?.publies || 0))) * 100),
    icon: 'lab',
    iconClass: 'bg-violet-50 text-violet-700',
    barClass: 'bg-violet-500',
    textClass: 'text-violet-700',
  },
  {
    label: 'Admissions actives',
    value: props.stats.admissions?.actives || 0,
    caption: 'Patients actuellement hospitalisés',
    progress: Math.min(100, (props.stats.admissions?.actives || 0) * 8),
    icon: 'admission',
    iconClass: 'bg-blue-50 text-blue-700',
    barClass: 'bg-blue-500',
    textClass: 'text-blue-700',
  },
])

const trendPoints = computed(() => {
  const trends = props.stats.trends || {}
  const labels = trends.labels || []
  const max = Math.max(1, ...(trends.recettes || []), ...(trends.admissions || []), ...(trends.examens || []))
  return labels.map((label, index) => ({
    label,
    recettesHeight: Math.max(6, ((trends.recettes?.[index] || 0) / max) * 96),
    admissionsHeight: Math.max(6, ((trends.admissions?.[index] || 0) / max) * 96),
    examensHeight: Math.max(6, ((trends.examens?.[index] || 0) / max) * 96),
  }))
})

const lisBreakdown = computed(() => {
  const byStatus = props.stats.laboratoire?.par_statut || {}
  const total = Math.max(1, Object.values(byStatus).reduce((sum, value) => sum + Number(value || 0), 0))
  return Object.entries(byStatus).map(([label, value]) => ({
    label,
    value,
    percent: Math.round((Number(value || 0) / total) * 100),
  }))
})
</script>
