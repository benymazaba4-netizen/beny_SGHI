<template>
  <div class="min-h-screen bg-slate-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-5xl mx-auto">
      <div class="rounded-3xl bg-white shadow-xl p-8 sm:p-10">
        <div class="text-center mb-10">
          <h1 class="text-4xl font-bold text-slate-900">Bienvenue sur SGHI</h1>
          <p class="mt-4 text-lg text-slate-600">
            Découvrez le fonctionnement du portail patient et connectez-vous pour réaliser vos opérations.
          </p>
        </div>

        <div class="grid gap-6 lg:grid-cols-3">
          <div class="rounded-3xl border border-slate-200 p-6 bg-slate-50">
            <div class="text-4xl">👤</div>
            <h2 class="mt-4 text-xl font-semibold text-slate-900">Mon dossier patient</h2>
            <p class="mt-3 text-slate-600 text-sm">
              Consultez vos informations personnelles, votre dossier médical et votre historique.
            </p>
            <div class="mt-6">
              <button
                @click="goTo('patients')"
                class="inline-flex items-center justify-center rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
              >
                Voir comment ça marche
              </button>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 p-6 bg-slate-50">
            <div class="text-4xl">🧾</div>
            <h2 class="mt-4 text-xl font-semibold text-slate-900">Mes factures</h2>
            <p class="mt-3 text-slate-600 text-sm">
              Suivez vos factures et paiements, et accédez à vos documents depuis votre espace sécurisé.
            </p>
            <div class="mt-6">
              <button
                @click="goTo('factures')"
                class="inline-flex items-center justify-center rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
              >
                Voir comment ça marche
              </button>
            </div>
          </div>

          <div class="rounded-3xl border border-slate-200 p-6 bg-slate-50">
            <div class="text-4xl">💊</div>
            <h2 class="mt-4 text-xl font-semibold text-slate-900">Pharmacie</h2>
            <p class="mt-3 text-slate-600 text-sm">
              Explorez la gestion des stocks et la disponibilité des médicaments pour votre traitement.
            </p>
            <div class="mt-6">
              <button
                @click="goTo('medicaments')"
                class="inline-flex items-center justify-center rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition"
              >
                Voir comment ça marche
              </button>
            </div>
          </div>
        </div>

        <div class="mt-10 rounded-3xl border border-slate-200 bg-slate-100 p-8">
          <div class="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <h3 class="text-2xl font-semibold text-slate-900">Point d’accès principal</h3>
              <p class="mt-2 text-slate-600 text-sm">
                Ce menu est le point d’entrée de l’application. Vous pouvez voir le fonctionnement librement, mais les opérations sont accessibles après connexion.
              </p>
            </div>
            <div class="flex flex-col gap-3 sm:flex-row">
              <button
                @click="goToLogin"
                class="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-900 hover:bg-slate-50 transition"
              >
                Se connecter
              </button>
              <button
                @click="goToRegister"
                class="inline-flex items-center justify-center rounded-full bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 transition"
              >
                S'inscrire (patient)
              </button>
            </div>
          </div>
        </div>

        <div class="mt-10 grid gap-6 lg:grid-cols-2">
          <div class="rounded-3xl border border-slate-200 p-6 bg-white">
            <h3 class="text-lg font-semibold text-slate-900">Navigation</h3>
            <ul class="mt-4 space-y-3 text-slate-600 text-sm">
              <li>📌 Mon dossier patient</li>
              <li>📌 Mes consultations</li>
              <li>📌 Mes examens de laboratoire</li>
              <li>📌 Mes factures et paiements</li>
            </ul>
          </div>

          <div class="rounded-3xl border border-slate-200 p-6 bg-white">
            <h3 class="text-lg font-semibold text-slate-900">Accès rapide</h3>
            <p class="mt-4 text-slate-600 text-sm">
              Pour réaliser des actions, connectez-vous : après authentification, vous aurez accès aux mêmes fonctionnalités que tous les utilisateurs autorisés.
            </p>
            <div class="mt-6 grid gap-3 sm:grid-cols-2">
              <button @click="goTo('dashboard')" class="rounded-full bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition">Dashboard</button>
              <button @click="goTo('patients')" class="rounded-full bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition">Patients</button>
              <button @click="goTo('admissions')" class="rounded-full bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition">Admissions</button>
              <button @click="goTo('factures')" class="rounded-full bg-slate-900 px-4 py-3 text-sm font-semibold text-white hover:bg-slate-800 transition">Factures</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = useRouter()
const { isLoggedIn } = useAuth()

const goTo = (routeName) => {
  if (isLoggedIn.value) {
    router.push({ name: routeName })
  } else {
    router.push('/login')
  }
}

const goToLogin = () => router.push('/login')
const goToRegister = () => router.push('/register')
</script>
