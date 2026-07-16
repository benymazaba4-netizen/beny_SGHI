<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar -->
    <div class="w-64 bg-gray-900 text-white p-6 overflow-y-auto">
      <div class="mb-8">
        <h2 class="text-2xl font-bold">SGHI</h2>
        <p class="text-gray-400 text-sm">ERP Médical</p>
      </div>

      <nav class="space-y-2">
        <router-link
          :to="{ name: 'dashboard' }"
          class="block px-4 py-2 rounded hover:bg-gray-800 transition"
          active-class="bg-blue-600"
        >
          📊 Dashboard
        </router-link>

        <div class="border-t border-gray-700 my-4"></div>

        <span class="text-xs text-gray-400 uppercase px-4 font-semibold">Clinique</span>
        <router-link
          :to="{ name: 'patients' }"
          class="block px-4 py-2 rounded hover:bg-gray-800 transition ml-2"
          active-class="bg-blue-600"
        >
          👥 Patients
        </router-link>
        <router-link
          :to="{ name: 'admissions' }"
          class="block px-4 py-2 rounded hover:bg-gray-800 transition ml-2"
          active-class="bg-blue-600"
        >
          🏥 Admissions
        </router-link>
        <router-link
          :to="{ name: 'consultations' }"
          class="block px-4 py-2 rounded hover:bg-gray-800 transition ml-2"
          active-class="bg-blue-600"
        >
          📋 Consultations
        </router-link>

        <div class="border-t border-gray-700 my-4"></div>

        <span class="text-xs text-gray-400 uppercase px-4 font-semibold">Laboratoire</span>
        <router-link
          :to="{ name: 'examens' }"
          class="block px-4 py-2 rounded hover:bg-gray-800 transition ml-2"
          active-class="bg-blue-600"
        >
          🔬 Examens
        </router-link>

        <div class="border-t border-gray-700 my-4"></div>

        <span class="text-xs text-gray-400 uppercase px-4 font-semibold">Pharmacie</span>
        <router-link
          :to="{ name: 'medicaments' }"
          class="block px-4 py-2 rounded hover:bg-gray-800 transition ml-2"
          active-class="bg-blue-600"
        >
          💊 Médicaments
        </router-link>

        <div class="border-t border-gray-700 my-4"></div>

        <span class="text-xs text-gray-400 uppercase px-4 font-semibold">Gestion</span>
        <router-link
          :to="{ name: 'factures' }"
          class="block px-4 py-2 rounded hover:bg-gray-800 transition ml-2"
          active-class="bg-blue-600"
        >
          💳 Factures
        </router-link>
      </nav>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Top Bar -->
      <div class="bg-white shadow-sm border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 class="text-2xl font-bold text-gray-900">{{ pageTitle }}</h1>
        <div class="flex items-center gap-4">
          <div class="text-right">
            <p class="text-sm font-medium text-gray-900">{{ user?.first_name || 'Utilisateur' }}</p>
            <p class="text-xs text-gray-500">{{ user?.role }}</p>
          </div>
          <button
            @click="handleLogout"
            class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition"
          >
            Déconnexion
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1 overflow-auto p-6">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const route = useRoute()
const { user, logout } = useAuth()

const handleLogout = async () => {
  await logout()
  router.push('/login')
}

const pageTitle = computed(() => {
  const titles = {
    'dashboard': 'Dashboard',
    'patients': 'Gestion des Patients',
    'admissions': 'Admissions',
    'consultations': 'Consultations',
    'examens': 'Examens de Laboratoire',
    'medicaments': 'Pharmacie',
    'factures': 'Facturation',
  }
  return titles[route.name] || 'SGHI'
})
</script>
