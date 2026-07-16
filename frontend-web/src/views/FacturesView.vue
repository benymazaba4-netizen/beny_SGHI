<template>
  <div>
    <h2 class="text-xl font-bold mb-6">Gestion des Factures</h2>

    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="p-6 border-b border-gray-200">
        <div class="flex justify-between items-center">
          <h3 class="font-bold">Factures</h3>
          <button class="px-4 py-2 bg-blue-600 text-white rounded text-sm">+ Nouvelle</button>
        </div>
      </div>

      <table class="w-full">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Numéro</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Patient</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Montant</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Statut</th>
            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="f in factures" :key="f.id" class="hover:bg-gray-50">
            <td class="px-6 py-4 text-sm font-mono">{{ f.numero_facture }}</td>
            <td class="px-6 py-4 text-sm">{{ f.patient_nom }}</td>
            <td class="px-6 py-4 text-sm">{{ f.montant_patient }} FCFA</td>
            <td class="px-6 py-4 text-sm">
              <span :class="['px-2 py-1 rounded text-xs font-semibold', getStatusClass(f.statut)]">
                {{ f.statut }}
              </span>
            </td>
            <td class="px-6 py-4 text-sm">
              <button class="text-blue-600 hover:text-blue-900 text-xs">📄 PDF</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!factures.length" class="p-6 text-center text-gray-500">
        Aucune facture
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const factures = ref([])

const getStatusClass = (status) => {
  const classes = {
    'PAYEE': 'bg-green-100 text-green-800',
    'PARTIELLE': 'bg-yellow-100 text-yellow-800',
    'IMPAYEE': 'bg-red-100 text-red-800',
    'EMISE': 'bg-blue-100 text-blue-800',
  }
  return classes[status] || 'bg-gray-100 text-gray-800'
}

onMounted(async () => {
  try {
    // Optionnel: charger les factures si endpoint disponible
    console.log('Loading factures...')
  } catch (err) {
    console.error('Error loading factures:', err)
  }
})
</script>
