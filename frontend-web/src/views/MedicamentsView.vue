<template>
  <div>
    <h2 class="text-xl font-bold mb-6">Pharmacie - Stocks</h2>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="font-bold mb-4">Stocks Disponibles</h3>
        <div v-if="stocks.length" class="space-y-3">
          <div v-for="s in stocks" :key="s.id" class="p-3 border border-gray-200 rounded">
            <p class="font-medium">{{ s.medicament__nom }}</p>
            <p class="text-sm text-gray-600">Stock: {{ s.quantite_totale }} unités</p>
            <div v-if="s.quantite_totale <= s.seuil_alerte" class="mt-2 text-xs text-red-600 font-semibold">
              ⚠️ Seuil d'alerte atteint
            </div>
          </div>
        </div>
        <div v-else class="text-gray-500">Aucun stock</div>
      </div>

      <div class="bg-white rounded-lg shadow p-6">
        <h3 class="font-bold mb-4">Alertes</h3>
        <div v-if="alertes.length" class="space-y-3">
          <div v-for="a in alertes" :key="a.id" class="p-3 bg-red-50 border border-red-200 rounded">
            <p class="text-sm font-medium">{{ a.medicament__nom }}</p>
            <p class="text-xs text-gray-600">{{ a.message }}</p>
          </div>
        </div>
        <div v-else class="text-green-600 text-sm">✓ Aucune alerte</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '@/api/client'

const stocks = ref([])
const alertes = ref([])

onMounted(async () => {
  try {
    const stocksResponse = await apiClient.get('/pharmacy/stocks')
    stocks.value = stocksResponse.data || []

    const alertesResponse = await apiClient.get('/pharmacy/alertes')
    alertes.value = alertesResponse.data || []
  } catch (err) {
    console.error('Error loading pharmacy:', err)
  }
})
</script>
