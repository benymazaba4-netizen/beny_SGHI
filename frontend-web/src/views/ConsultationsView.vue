<template>
  <div>
    <h2 class="text-xl font-bold mb-6">Consultations</h2>

    <div class="bg-white rounded-lg shadow">
      <div class="p-6 border-b border-gray-200 flex justify-between items-center">
        <h3 class="font-bold">Historique des Consultations</h3>
        <button class="px-4 py-2 bg-blue-600 text-white rounded text-sm">+ Nouvelle</button>
      </div>

      <table class="w-full">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Médecin</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Motif</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Diagnostic</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="c in consultations" :key="c.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm">{{ c.patient_nom }}</td>
            <td class="px-6 py-4 text-sm">{{ c.medecin__username }}</td>
            <td class="px-6 py-4 text-sm">{{ c.motif }}</td>
            <td class="px-6 py-4 text-sm">{{ formatDate(c.date_consultation) }}</td>
            <td class="px-6 py-4 text-sm">{{ c.diagnostic || '-' }}</td>
          </tr>
        </tbody>
      </table>

      <div v-if="!consultations.length" class="p-6 text-center text-gray-500">
        Aucune consultation
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const consultations = ref([])

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
}

onMounted(async () => {
  // Charger les consultations
  console.log('Loading consultations...')
})
</script>
