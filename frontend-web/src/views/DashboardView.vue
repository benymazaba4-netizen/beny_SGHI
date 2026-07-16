<template>
  <div class="space-y-6">
    <!-- KPIs -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-600 text-sm">Patients Actifs</p>
        <p class="text-3xl font-bold text-blue-600">{{ kpis.patients_actifs }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-600 text-sm">Admissions En Cours</p>
        <p class="text-3xl font-bold text-green-600">{{ kpis.admissions_actives }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-600 text-sm">Examens en Attente</p>
        <p class="text-3xl font-bold text-orange-600">{{ kpis.demandes_examens_en_attente }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-gray-600 text-sm">Factures Impayées</p>
        <p class="text-3xl font-bold text-red-600">{{ kpis.factures_impayees }}</p>
      </div>
    </div>

    <!-- Taux d'occupation -->
    <div class="bg-white rounded-lg shadow p-6">
      <h3 class="text-lg font-bold mb-4">État du Système</h3>
      <div class="space-y-4">
        <div>
          <p class="text-sm font-medium text-gray-700">CPU</p>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-blue-600 h-2 rounded-full" :style="{ width: `${health.cpu_percent}%` }"></div>
          </div>
          <p class="text-xs text-gray-500 mt-1">{{ health.cpu_percent }}%</p>
        </div>
        <div>
          <p class="text-sm font-medium text-gray-700">Mémoire</p>
          <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-green-600 h-2 rounded-full" :style="{ width: `${health.memory_percent}%` }"></div>
          </div>
          <p class="text-xs text-gray-500 mt-1">{{ health.memory_percent }}%</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const kpis = ref({
  patients_actifs: 0,
  admissions_actives: 0,
  demandes_examens_en_attente: 0,
  factures_impayees: 0,
})

const health = ref({
  cpu_percent: 0,
  memory_percent: 0,
  disk_percent: 0,
})

onMounted(async () => {
  try {
    const kpiResponse = await apiClient.get('/kpi')
    kpis.value = kpiResponse.data

    const healthResponse = await apiClient.get('/sante')
    health.value = healthResponse.data
  } catch (err) {
    console.error('Error loading dashboard:', err)
  }
})
</script>
