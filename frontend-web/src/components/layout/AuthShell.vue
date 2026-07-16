<template>
  <div class="auth-shell min-h-screen flex">
    <!-- Panneau visuel -->
    <aside class="hidden lg:flex lg:w-[52%] xl:w-[55%] relative overflow-hidden">
      <img
        :src="heroImage"
        :alt="BRAND.fullName"
        class="absolute inset-0 w-full h-full object-cover scale-105"
      />
      <div class="absolute inset-0 bg-gradient-to-br from-indigo-950/92 via-teal-900/75 to-cyan-800/60" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(255,255,255,0.12),transparent_50%)]" />

      <div class="relative z-10 flex flex-col justify-between p-10 xl:p-14 w-full">
        <div class="flex items-center gap-4">
          <img src="/logo-sghi.svg" alt="SGHI" class="w-14 h-14 rounded-2xl shadow-2xl ring-2 ring-white/30" />
          <div>
            <p class="text-white font-bold text-2xl tracking-tight">{{ BRAND.name }}</p>
            <p class="text-white/70 text-sm">{{ BRAND.institution }}</p>
          </div>
        </div>

        <div class="max-w-lg">
          <p class="text-teal-200/90 text-sm font-semibold uppercase tracking-[0.2em] mb-3">{{ BRAND.tagline }}</p>
          <h1 class="text-3xl xl:text-4xl font-bold text-white leading-tight mb-4">
            {{ heroTitle }}
          </h1>
          <p class="text-white/75 text-base leading-relaxed mb-8">{{ heroSubtitle }}</p>

          <ul class="space-y-4">
            <li v-for="(feat, i) in features" :key="i" class="flex items-start gap-3 text-white/90">
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/15 backdrop-blur-sm">
                <img :src="feat.icon" :alt="feat.title" class="w-5 h-5" />
              </span>
              <div>
                <p class="font-semibold text-sm">{{ feat.title }}</p>
                <p class="text-white/60 text-xs mt-0.5">{{ feat.desc }}</p>
              </div>
            </li>
          </ul>
        </div>

        <p class="text-white/40 text-xs">© {{ year }} SGHI · Données de santé protégées</p>
      </div>
    </aside>

    <!-- Formulaire -->
    <main class="flex-1 flex items-center justify-center p-6 sm:p-10 bg-slate-50 relative overflow-hidden">
      <div class="absolute inset-0 lg:hidden">
        <img :src="mobileImage" alt="" class="w-full h-full object-cover opacity-20" />
        <div class="absolute inset-0 bg-gradient-to-b from-slate-50/95 to-slate-50" />
      </div>

      <div class="relative w-full max-w-md">
        <div class="lg:hidden flex items-center justify-center gap-3 mb-8">
          <img src="/logo-sghi.svg" alt="SGHI" class="w-12 h-12 rounded-xl shadow-lg" />
          <div>
            <p class="font-bold text-slate-900 text-lg">{{ BRAND.name }}</p>
            <p class="text-slate-500 text-xs">{{ BRAND.fullName }}</p>
          </div>
        </div>

        <div class="auth-card bg-white/90 backdrop-blur-xl rounded-3xl shadow-xl shadow-slate-200/60 border border-white p-8 sm:p-10">
          <slot />
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { BRAND, IMAGES } from '../../config/branding'

defineProps({
  heroImage: { type: String, default: IMAGES.loginHero },
  mobileImage: { type: String, default: IMAGES.loginMobile },
  heroTitle: { type: String, default: 'Votre parcours de soins, digitalisé de A à Z' },
  heroSubtitle: {
    type: String,
    default: 'Admissions, laboratoire, pharmacie et suivi patient — une plateforme sécurisée pour les équipes soignantes.',
  },
  features: {
    type: Array,
    default: () => [
      { icon: '/illustrations/icon-shield.svg', title: 'Sécurité bancaire', desc: 'JWT, MFA et chiffrement AES-256' },
      { icon: '/illustrations/icon-heart.svg', title: 'Parcours patient', desc: 'Consultations, labo et ordonnances unifiés' },
      { icon: '/illustrations/icon-chart.svg', title: 'Pilotage temps réel', desc: 'KPIs, lits et recettes en direct' },
    ],
  },
})

const year = new Date().getFullYear()
</script>

<style scoped>
.auth-card {
  animation: auth-rise 0.6s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes auth-rise {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
