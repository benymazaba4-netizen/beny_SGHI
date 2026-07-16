<template>
  <div class="app-card overflow-hidden">
    <div class="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
      <h3 v-if="title" class="font-semibold text-slate-800 text-sm">{{ title }}</h3>
      <input
        v-if="searchable && rows.length"
        v-model="searchQuery"
        type="search"
        placeholder="Rechercher..."
        class="app-input max-w-xs text-sm py-2"
        @input="currentPage = 1"
      />
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-slate-100">
            <th v-for="col in columns" :key="col.key" class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">
              {{ col.label }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td :colspan="columns.length" class="px-0 py-0">
              <SkeletonTable :rows="pageSize" :columns="columns.length" />
            </td>
          </tr>
          <tr v-else-if="!displayRows.length">
            <td :colspan="columns.length">
              <EmptyState
                :title="emptyText"
                :description="searchQuery ? 'Essayez un autre terme de recherche.' : undefined"
                :image="searchQuery ? '/illustrations/empty-search.svg' : '/illustrations/empty-data.svg'"
              />
            </td>
          </tr>
          <tr
            v-for="(row, i) in displayRows"
            :key="row.id ?? i"
            class="border-b border-slate-50 hover:bg-slate-50/80 transition-colors duration-150"
          >
            <td v-for="col in columns" :key="col.key" class="px-4 py-3.5 text-slate-700">
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                {{ row[col.key] ?? '—' }}
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-if="paginated && filteredRows.length > pageSize" class="px-5 py-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
      <span>{{ filteredRows.length }} résultat(s)</span>
      <div class="flex items-center gap-2">
        <button type="button" class="ig-btn px-3 py-1.5 text-xs border border-slate-200 bg-white" :disabled="currentPage <= 1" @click="currentPage--">Préc.</button>
        <span>{{ currentPage }} / {{ totalPages }}</span>
        <button type="button" class="ig-btn px-3 py-1.5 text-xs border border-slate-200 bg-white" :disabled="currentPage >= totalPages" @click="currentPage++">Suiv.</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import EmptyState from './EmptyState.vue'
import SkeletonTable from './SkeletonTable.vue'

const props = defineProps({
  title: String,
  columns: Array,
  rows: { type: Array, default: () => [] },
  loading: Boolean,
  emptyText: { type: String, default: 'Aucune donnée' },
  searchable: { type: Boolean, default: true },
  paginated: { type: Boolean, default: true },
  pageSize: { type: Number, default: 10 },
})

const searchQuery = ref('')
const currentPage = ref(1)

watch(() => props.rows, () => { currentPage.value = 1 })

const filteredRows = computed(() => {
  if (!searchQuery.value.trim()) return props.rows
  const q = searchQuery.value.toLowerCase()
  return props.rows.filter((row) =>
    Object.values(row).some((v) => String(v ?? '').toLowerCase().includes(q)),
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredRows.value.length / props.pageSize)))

const displayRows = computed(() => {
  if (!props.paginated) return filteredRows.value
  const start = (currentPage.value - 1) * props.pageSize
  return filteredRows.value.slice(start, start + props.pageSize)
})
</script>
