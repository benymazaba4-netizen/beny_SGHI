<template>
  <div class="p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
    <div class="flex items-center justify-between mb-4">
      <button type="button" class="ig-btn ig-btn-secondary text-xs px-3 py-1" @click="prevMonth">←</button>
      <h3 class="text-sm font-bold text-slate-700 capitalize">{{ monthLabel }}</h3>
      <button type="button" class="ig-btn ig-btn-secondary text-xs px-3 py-1" @click="nextMonth">→</button>
    </div>
    <div class="grid grid-cols-7 gap-1 text-center text-[10px] font-semibold text-slate-400 mb-2">
      <span v-for="d in weekDays" :key="d">{{ d }}</span>
    </div>
    <div class="grid grid-cols-7 gap-1">
      <div
        v-for="(cell, idx) in cells"
        :key="idx"
        class="min-h-[36px] p-1 rounded-lg text-xs"
        :class="cell.inMonth ? 'bg-slate-50' : 'bg-transparent text-slate-300'"
      >
        <span class="font-medium">{{ cell.day || '' }}</span>
        <div v-if="cell.events.length" class="mt-0.5 space-y-0.5">
          <div
            v-for="ev in cell.events.slice(0, 2)"
            :key="ev.id"
            class="truncate text-[9px] px-1 py-0.5 rounded bg-teal-100 text-teal-800"
            :title="ev.label"
          >
            {{ ev.label }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  events: { type: Array, default: () => [] },
})

const cursor = ref(new Date())

const weekDays = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

const monthLabel = computed(() =>
  cursor.value.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' }),
)

function eventKey(rawDate) {
  if (!rawDate) return ''
  return String(rawDate).slice(0, 10)
}

const cells = computed(() => {
  const y = cursor.value.getFullYear()
  const m = cursor.value.getMonth()
  const first = new Date(y, m, 1)
  const startOffset = (first.getDay() + 6) % 7
  const daysInMonth = new Date(y, m + 1, 0).getDate()
  const result = []

  for (let i = 0; i < startOffset; i += 1) {
    result.push({ day: '', inMonth: false, events: [] })
  }
  for (let d = 1; d <= daysInMonth; d += 1) {
    const key = `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const dayEvents = props.events
      .filter(e => eventKey(e.date) === key)
      .map(e => ({ id: e.id, label: e.label || e.statut || 'RDV' }))
    result.push({ day: d, inMonth: true, events: dayEvents })
  }
  while (result.length % 7 !== 0) {
    result.push({ day: '', inMonth: false, events: [] })
  }
  return result
})

function prevMonth() {
  cursor.value = new Date(cursor.value.getFullYear(), cursor.value.getMonth() - 1, 1)
}

function nextMonth() {
  cursor.value = new Date(cursor.value.getFullYear(), cursor.value.getMonth() + 1, 1)
}
</script>
