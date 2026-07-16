<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-600 to-blue-900 flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
      <div class="text-center mb-6">
        <h1 class="text-3xl font-bold text-gray-900">SGHI</h1>
        <p class="text-gray-600 text-sm mt-1">Système de Gestion Hospitalière</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-6">
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">
            Identifiant
          </label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Entrez votre identifiant"
            class="mt-1 w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            :disabled="loading"
            required
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">
            Mot de passe
          </label>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Entrez votre mot de passe"
            class="mt-1 w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            :disabled="loading"
            required
          />
        </div>

        <div v-if="error" class="p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg text-sm">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-blue-600 text-white font-medium py-2 rounded-lg hover:bg-blue-700 transition disabled:opacity-50"
        >
          {{ loading ? 'Connexion en cours...' : 'Se connecter' }}
        </button>
      </form>

      <div class="mt-6 text-center">
        <button
          @click="goToRegister"
          class="text-sm text-blue-700 underline hover:text-blue-900"
        >
          S'inscrire en tant que patient
        </button>
      </div>

      <div class="mt-6 bg-gray-50 p-4 rounded-lg border border-gray-200 text-sm text-gray-700">
        <p class="font-semibold text-gray-900 mb-2">Identifiants de test</p>
        <ul class="space-y-1 text-left">
          <li><strong>Admin :</strong> admin / Demo2026!</li>
          <li><strong>Médecin :</strong> medecin / Demo2026!</li>
          <li><strong>Infirmier :</strong> infirmier / Demo2026!</li>
          <li><strong>Patient :</strong> patient / Demo2026!</li>
        </ul>
        <p class="mt-3 text-xs text-gray-500">Le bouton d'inscription est valable uniquement pour les patients.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { login, loading, error } = useAuth()

const username = ref('')
const password = ref('')

const handleLogin = async () => {
  const result = await login(username.value, password.value)
  if (result.success) {
    router.push('/app/dashboard')
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>
