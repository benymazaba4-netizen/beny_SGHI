<template>
  <div>
    <h2 class="text-xl font-bold mb-6">Examens de Laboratoire</h2>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="p-6 border-b border-gray-200">
        <h3 class="font-bold mb-4">Demandes en Attente</h3>
        <div v-if="demandesEnAttente.length" class="space-y-3">
          <div v-for="d in demandesEnAttente" :key="d.id" class="p-3 bg-orange-50 border border-orange-200 rounded">
            <p class="font-medium">{{ d.patient_nom }} - {{ d.examen_type_nom }}</p>
            <p class="text-sm text-gray-600">Statut: {{ d.statut }}</p>
          </div>
        </div>
        <div v-else class="text-gray-500">Aucune demande en attente</div>
      </div>

      <div class="p-6">
        <h3 class="font-bold mb-4">Résultats Publiés</h3>
        <div v-if="resultatsPub.length" class="space-y-3">
          <div v-for="r in resultatsPub" :key="r.id" class="p-3 bg-green-50 border border-green-200 rounded">
            <p class="font-medium">{{ r.demande_patient }} - {{ r.examen_nom }}</p>
            <button class="text-sm text-blue-600 hover:underline mt-2">📄 Télécharger PDF</button>
          </div>
        </div>
        <div v-else class="text-gray-500">Aucun résultat publié</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const demandesEnAttente = ref([])
const resultatsPub = ref([])

onMounted(async () => {
  try {
    const enCoursResponse = await apiClient.get('/laboratory/demandes/en-cours')
    demandesEnAttente.value = enCoursResponse.data || []
  } catch (err) {
    console.error('Error loading exams:', err)
  }
})
</script>
