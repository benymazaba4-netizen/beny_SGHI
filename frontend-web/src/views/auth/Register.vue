<template>
  <AuthShell
    hero-title="Créez votre espace patient"
    hero-subtitle="Accédez à vos consultations, résultats labo et rendez-vous en toute sécurité."
    :hero-image="IMAGES.patientCare"
    :features="patientFeatures"
  >
    <div class="text-center mb-6">
      <router-link to="/" class="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-teal-600 mb-4 transition-colors">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Retour au portail patient
      </router-link>
      <img src="/illustrations/icon-heart.svg" alt="" class="w-10 h-10 mx-auto mb-3" />
      <h2 class="text-2xl font-bold text-slate-900">Inscription patient</h2>
      <p class="text-slate-500 text-sm mt-1">Rejoignez le portail SGHI</p>
    </div>

    <form @submit.prevent="handleRegister" class="ig-stack max-h-[60vh] overflow-y-auto pr-1 ig-scrollbar-hide">
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Prénom *</label>
          <input v-model="form.first_name" required class="app-input" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Nom *</label>
          <input v-model="form.last_name" required class="app-input" />
        </div>
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Nom d'utilisateur *</label>
        <input v-model="form.username" required class="app-input" />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Email *</label>
        <input v-model="form.email" type="email" required class="app-input" placeholder="votre@email.com" />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Téléphone *</label>
        <input v-model="form.telephone" required class="app-input" />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Date de naissance *</label>
        <input v-model="form.date_naissance" type="date" required class="app-input" />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Adresse *</label>
        <textarea v-model="form.adresse" required rows="2" class="app-input" />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Mot de passe * (8+ caractères)</label>
        <input v-model="form.password" type="password" required minlength="8" class="app-input" />
      </div>
      <label class="flex items-start gap-3 text-sm text-slate-600 p-3 rounded-xl bg-teal-50/80 border border-teal-100">
        <input v-model="form.consentement_donnees" type="checkbox" required class="mt-1" />
        <span>J'accepte le traitement sécurisé de mes données médicales conformément à la politique SGHI.</span>
      </label>
      <button type="submit" :disabled="loading" class="ig-btn ig-btn-primary w-full py-3">
        {{ loading ? 'Inscription...' : 'Créer mon compte' }}
      </button>
    </form>

    <div v-if="error" class="mt-4 p-3 rounded-xl bg-red-50 text-red-700 text-sm text-center">{{ error }}</div>

    <p class="mt-6 text-center text-sm text-slate-600">
      Déjà inscrit ?
      <router-link :to="{ path: '/login', query: $route.query }" class="font-semibold text-teal-600 hover:text-teal-700">Se connecter</router-link>
    </p>
  </AuthShell>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authApi } from '../../api/modules'
import AuthShell from '../../components/layout/AuthShell.vue'
import { IMAGES } from '../../config/branding'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const error = ref('')
const form = ref({
  username: '', password: '', first_name: '', last_name: '',
  email: '', telephone: '', adresse: '', date_naissance: '',
  consentement_donnees: true,
})

const patientFeatures = [
  { icon: '/illustrations/icon-heart.svg', title: 'Dossier médical', desc: 'Consultations, labo et ordonnances' },
  { icon: '/illustrations/icon-chart.svg', title: 'Rendez-vous en ligne', desc: 'Planification et rappels automatiques' },
  { icon: '/illustrations/icon-shield.svg', title: 'Confidentialité', desc: 'Accès strictement personnel' },
]

const handleRegister = async () => {
  loading.value = true
  error.value = ''
  try {
    await authApi.register(form.value)
    router.push({ path: '/login', query: route.query })
  } catch (e) {
    error.value = e.response?.data?.error || 'Erreur inscription'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:deep(.auth-card) {
  --theme-from: #0d9488;
  --theme-to: #14b8a6;
  --theme-accent: #0d9488;
  --theme-glow: rgba(13, 148, 136, 0.25);
}
</style>
