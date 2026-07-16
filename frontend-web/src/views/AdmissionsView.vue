<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold">Admissions Actives</h2>
      <button class="px-4 py-2 bg-blue-600 text-white rounded text-sm">+ Nouvelle Admission</button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div v-for="a in admissions" :key="a.id" class="bg-white rounded-lg shadow p-6">
        <h3 class="font-bold mb-2">{{ a.patient_nom }} {{ a.patient_prenom }}</h3>
        <div class="text-sm text-gray-600 space-y-1">
          <p>📂 Dossier: {{ a.numero_dossier }}</p>
          <p>🏥 Service: {{ a.service_nom }}</p>
          <p>🛏️ Lit: {{ a.lit_numero }}</p>
          <p>👨‍⚕️ Médecin: {{ a.medecin_referent }}</p>
          <p>📅 Entrée: {{ formatDate(a.date_entree) }}</p>
        </div>
        <button class="mt-4 px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700">
          Sortie
        </button>
      </div>
    </div>

    <div v-if="!admissions.length" class="bg-white rounded-lg shadow p-6 text-center text-gray-500">
      Aucune admission active
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const admissions = ref([])

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('fr-FR')
}

onMounted(async () => {
  try {
    const response = await apiClient.get('/clinical/admissions/actives')
    admissions.value = response.data || []
  } catch (err) {
    console.error('Error loading admissions:', err)
  }
})
</script>
