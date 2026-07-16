<template>
  <section class="visitor-showcase space-y-10">
    <!-- Hero premium avec collage d'images -->
    <div class="visitor-hero relative overflow-hidden rounded-3xl shadow-2xl shadow-teal-900/25">
      <img :src="IMAGES.patientCare" alt="" class="absolute inset-0 w-full h-full object-cover scale-105" />
      <div class="absolute inset-0 bg-gradient-to-r from-slate-950/96 via-slate-950/75 to-slate-900/40" />
      <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_70%_30%,rgba(20,184,166,0.28),transparent_55%)]" />
      <div class="absolute top-0 right-0 w-96 h-96 bg-teal-400/15 rounded-full blur-3xl animate-pulse-slow" />

      <div class="relative z-10 px-6 py-10 lg:px-12 lg:py-16 grid grid-cols-1 lg:grid-cols-2 gap-10 items-center">
        <div>
          <p class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-teal-200 text-xs font-semibold uppercase tracking-widest mb-5">
            <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            {{ BRAND.institution }}
          </p>
          <h2 class="text-3xl lg:text-5xl font-extrabold text-white leading-[1.1] tracking-tight">
            Votre santé,<br />
            <span class="text-transparent bg-clip-text bg-gradient-to-r from-teal-300 via-cyan-200 to-white">à portée de main</span>
          </h2>
          <p class="text-white/80 text-base lg:text-lg mt-5 leading-relaxed max-w-lg">
            {{ BRAND.tagline }} — RDV, laboratoire, ordonnances et paiements sécurisés sur une plateforme unique.
          </p>
          <div class="mt-8 flex flex-wrap gap-3">
            <router-link to="/login" class="visitor-btn-primary">
              Se connecter
              <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
            </router-link>
            <router-link to="/register" class="visitor-btn-ghost">Créer mon compte gratuit</router-link>
          </div>
          <div class="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div v-for="stat in trustStats" :key="stat.label" class="visitor-stat-card">
              <p class="text-xl lg:text-2xl font-extrabold text-white">{{ stat.value }}</p>
              <p class="text-white/55 text-[11px] mt-0.5 font-medium">{{ stat.label }}</p>
            </div>
          </div>
        </div>

        <!-- Collage visuel desktop -->
        <div class="hidden lg:block relative h-[420px]">
          <div class="visitor-photo-float visitor-photo-main">
            <img :src="IMAGES.medicalTeam" alt="Équipe médicale" class="w-full h-full object-cover" />
            <span class="visitor-photo-label">Équipe soignante</span>
          </div>
          <div class="visitor-photo-float visitor-photo-sub-a">
            <img :src="IMAGES.laboratory" alt="Laboratoire" class="w-full h-full object-cover" />
          </div>
          <div class="visitor-photo-float visitor-photo-sub-b">
            <img :src="IMAGES.reception" alt="Accueil" class="w-full h-full object-cover" />
          </div>
          <div class="visitor-photo-float visitor-photo-sub-c">
            <img :src="IMAGES.nursing" alt="Soins" class="w-full h-full object-cover" />
          </div>
        </div>
      </div>
    </div>

    <!-- Galerie bento -->
    <div>
      <div class="mb-5">
        <p class="text-teal-600 text-xs font-bold uppercase tracking-widest mb-1">Notre établissement</p>
        <h3 class="text-2xl font-extrabold text-slate-900 tracking-tight">L'excellence du CHU en images</h3>
      </div>
      <div class="visitor-bento">
        <div class="visitor-bento-item visitor-bento-large group">
          <img :src="IMAGES.hospitalWide" alt="CHU" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
          <div class="visitor-bento-overlay" />
          <p class="visitor-bento-caption">Infrastructure moderne</p>
        </div>
        <div class="visitor-bento-item group">
          <img :src="IMAGES.medicalTeam" alt="Médecins" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
          <div class="visitor-bento-overlay" />
          <p class="visitor-bento-caption">Médecins spécialistes</p>
        </div>
        <div class="visitor-bento-item group">
          <img :src="IMAGES.laboratory" alt="Labo" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
          <div class="visitor-bento-overlay" />
          <p class="visitor-bento-caption">Laboratoire certifié</p>
        </div>
        <div class="visitor-bento-item group">
          <img :src="IMAGES.pharmacy" alt="Pharmacie" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
          <div class="visitor-bento-overlay" />
          <p class="visitor-bento-caption">Pharmacie hospitalière</p>
        </div>
        <div class="visitor-bento-item visitor-bento-wide group">
          <img :src="IMAGES.patientCare" alt="Soins patients" class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105" />
          <div class="visitor-bento-overlay" />
          <p class="visitor-bento-caption">Parcours patient digitalisé</p>
        </div>
      </div>
    </div>

    <!-- Services avec photos -->
    <div>
      <div class="mb-5">
        <p class="text-teal-600 text-xs font-bold uppercase tracking-widest mb-1">Services digitaux</p>
        <h3 class="text-2xl font-extrabold text-slate-900 tracking-tight">Tout votre parcours de soins</h3>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="(feat, i) in services"
          :key="feat.title"
          class="visitor-service-card group cursor-pointer"
          :style="{ animationDelay: `${i * 0.06}s` }"
          role="button"
          tabindex="0"
          @click="$emit('open-service', feat.id)"
          @keydown.enter="$emit('open-service', feat.id)"
        >
          <div class="relative h-44 overflow-hidden">
            <img :src="feat.image" :alt="feat.title" class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-900/30 to-transparent" />
            <div class="absolute top-4 left-4 w-11 h-11 rounded-xl bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center">
              <img :src="feat.icon" alt="" class="w-5 h-5 brightness-0 invert" />
            </div>
            <h4 class="absolute bottom-4 left-4 right-4 text-white font-bold text-lg">{{ feat.title }}</h4>
          </div>
          <div class="p-4 bg-white">
            <p class="text-sm text-slate-500 leading-relaxed">{{ feat.desc }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Étapes illustrées -->
    <div class="visitor-steps rounded-3xl overflow-hidden border border-slate-200/80 bg-white shadow-lg">
      <div class="grid grid-cols-1 lg:grid-cols-2">
        <div class="relative min-h-[240px] lg:min-h-full">
          <img :src="IMAGES.reception" alt="Accueil CHU" class="absolute inset-0 w-full h-full object-cover" />
          <div class="absolute inset-0 bg-gradient-to-r from-slate-950/80 to-slate-900/20" />
          <div class="relative z-10 p-8 lg:p-10 flex flex-col justify-end h-full min-h-[240px]">
            <p class="text-teal-300 text-xs font-bold uppercase tracking-widest mb-2">Simple & rapide</p>
            <h3 class="text-2xl font-extrabold text-white">Comment ça marche ?</h3>
          </div>
        </div>
        <div class="p-6 lg:p-8 space-y-5">
          <div v-for="(step, i) in steps" :key="step.title" class="flex gap-4 items-start group">
            <div class="relative shrink-0 w-16 h-16 rounded-2xl overflow-hidden ring-2 ring-teal-100 shadow-md">
              <img :src="step.image" :alt="step.title" class="w-full h-full object-cover transition-transform group-hover:scale-110" />
              <span class="absolute inset-0 flex items-center justify-center bg-teal-600/80 text-white font-extrabold text-sm">{{ i + 1 }}</span>
            </div>
            <div class="pt-1">
              <h4 class="font-bold text-slate-900">{{ step.title }}</h4>
              <p class="text-sm text-slate-500 mt-1 leading-relaxed">{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bandeau confiance avec image -->
    <div class="visitor-trust-banner relative overflow-hidden rounded-3xl">
      <img :src="IMAGES.nursing" alt="" class="absolute inset-0 w-full h-full object-cover" />
      <div class="absolute inset-0 bg-gradient-to-r from-slate-950/92 to-teal-900/80" />
      <div class="relative z-10 flex flex-wrap items-center justify-center gap-x-8 gap-y-4 py-8 px-6 text-white/95 text-sm font-medium">
        <span v-for="badge in badges" :key="badge" class="flex items-center gap-2">
          <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" class="text-teal-300 shrink-0">
            <path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
          </svg>
          {{ badge }}
        </span>
      </div>
    </div>
  </section>
</template>

<script setup>
import { BRAND, IMAGES } from '../../config/branding'

defineEmits(['open-service'])

const trustStats = [
  { value: '24/7', label: 'Accès sécurisé' },
  { value: '100%', label: 'Chiffré' },
  { value: 'PDF', label: 'Résultats' },
  { value: 'MTN', label: 'Paiement' },
]

const services = [
  { id: 'rdv', image: IMAGES.patientCare, icon: '/illustrations/icon-chart.svg', title: 'Rendez-vous', desc: 'Planifiez avec le spécialiste de votre choix en quelques clics.' },
  { id: 'labo', image: IMAGES.laboratory, icon: '/illustrations/icon-shield.svg', title: 'Laboratoire', desc: 'Résultats PDF disponibles dès validation par le biologiste.' },
  { id: 'dossier', image: IMAGES.medicalTeam, icon: '/illustrations/icon-heart.svg', title: 'Dossier médical', desc: 'Historique, diagnostics CIM-10 et plans de soins centralisés.' },
  { id: 'ordonnances', image: IMAGES.pharmacy, icon: '/illustrations/icon-heart.svg', title: 'Ordonnances', desc: 'Suivi des prescriptions actives et rappels de prise.' },
  { id: 'factures', image: IMAGES.finance, icon: '/illustrations/icon-chart.svg', title: 'Facturation', desc: 'Mobile Money, carte ou espèces — suivi transparent.' },
  { id: 'messages', image: IMAGES.reception, icon: '/illustrations/icon-shield.svg', title: 'Messagerie', desc: 'Échangez en toute sécurité avec votre équipe soignante.' },
]

const steps = [
  { image: IMAGES.reception, title: 'Créez votre compte', desc: 'Inscription gratuite en 2 minutes — code OTP par e-mail.' },
  { image: IMAGES.patientCare, title: 'Explorez vos services', desc: 'RDV, labo, messagerie et facturation au même endroit.' },
  { image: IMAGES.nursing, title: 'Suivez votre santé', desc: 'Notifications, rappels médicaments et observance.' },
]

const badges = ['JWT + MFA', 'Chiffrement AES-256', 'Conformité RGPD', 'Audit immuable']
</script>

<style scoped>
.visitor-hero { min-height: 320px; }

.visitor-btn-primary {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 28px; border-radius: 14px;
  background: linear-gradient(135deg, #14b8a6, #06b6d4);
  color: white; font-weight: 700; font-size: 0.95rem;
  box-shadow: 0 8px 28px rgba(20, 184, 166, 0.5);
  transition: transform 0.2s, box-shadow 0.2s;
}
.visitor-btn-primary:hover { transform: translateY(-2px); box-shadow: 0 14px 36px rgba(20, 184, 166, 0.55); }
.visitor-btn-ghost {
  display: inline-flex; align-items: center;
  padding: 14px 24px; border-radius: 14px;
  background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.28);
  color: white; font-weight: 600; font-size: 0.95rem;
  backdrop-filter: blur(10px);
  transition: background 0.2s;
}
.visitor-btn-ghost:hover { background: rgba(255,255,255,0.22); }

.visitor-stat-card {
  padding: 12px 14px; border-radius: 14px;
  background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12);
  backdrop-filter: blur(12px);
}

/* Collage hero */
.visitor-photo-float {
  position: absolute; overflow: hidden; border-radius: 20px;
  border: 3px solid rgba(255,255,255,0.2);
  box-shadow: 0 20px 50px rgba(0,0,0,0.35);
}
.visitor-photo-main { top: 0; right: 0; width: 72%; height: 68%; }
.visitor-photo-sub-a { bottom: 8%; left: 0; width: 38%; height: 38%; }
.visitor-photo-sub-b { bottom: 0; right: 8%; width: 32%; height: 32%; }
.visitor-photo-sub-c { top: 12%; left: 4%; width: 28%; height: 28%; }
.visitor-photo-label {
  position: absolute; bottom: 12px; left: 12px;
  padding: 6px 12px; border-radius: 10px;
  background: rgba(15,23,42,0.75); backdrop-filter: blur(8px);
  color: white; font-size: 11px; font-weight: 700;
}

/* Bento gallery */
.visitor-bento {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(2, 180px);
  gap: 12px;
}
.visitor-bento-large { grid-column: span 2; grid-row: span 2; }
.visitor-bento-wide { grid-column: span 2; }
.visitor-bento-item { position: relative; border-radius: 20px; overflow: hidden; }
.visitor-bento-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(15,23,42,0.75) 0%, transparent 60%);
}
.visitor-bento-caption {
  position: absolute; bottom: 14px; left: 16px; right: 16px;
  color: white; font-weight: 700; font-size: 14px;
}

@media (max-width: 768px) {
  .visitor-bento {
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto;
  }
  .visitor-bento-large { grid-column: span 2; grid-row: span 1; height: 220px; }
  .visitor-bento-item:not(.visitor-bento-large):not(.visitor-bento-wide) { height: 140px; }
  .visitor-bento-wide { grid-column: span 2; height: 160px; }
}

.visitor-service-card {
  border-radius: 22px; overflow: hidden;
  border: 1px solid rgba(226,232,240,0.9);
  box-shadow: 0 8px 30px rgba(15,23,42,0.06);
  transition: transform 0.35s, box-shadow 0.35s;
  animation: rise-in 0.6s cubic-bezier(0.22,1,0.36,1) both;
}
.visitor-service-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 24px 50px rgba(13,148,136,0.15);
}

.visitor-trust-banner { min-height: 100px; }

@keyframes rise-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-slow {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50% { opacity: 0.9; transform: scale(1.06); }
}
.animate-pulse-slow { animation: pulse-slow 5s ease-in-out infinite; }
</style>
