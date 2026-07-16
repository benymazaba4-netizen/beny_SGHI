<template>
  <div class="h-screen flex overflow-hidden portal-theme" :style="themeVars">
    <Transition name="overlay">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 lg:hidden"
        @click="sidebarOpen = false"
      />
    </Transition>

    <aside
      class="fixed lg:static inset-y-0 left-0 z-50 w-[280px] flex flex-col shrink-0 transition-transform duration-300 ease-out lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
      :style="{ background: sidebarGradient }"
    >
      <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-20 -right-20 w-56 h-56 rounded-full bg-white/10 blur-2xl" />
        <div class="absolute bottom-20 -left-10 w-40 h-40 rounded-full bg-white/5 blur-xl" />
      </div>

      <div class="relative p-6 border-b border-white/10">
        <router-link to="/" class="flex items-center gap-3 group" @click="sidebarOpen = false">
          <img src="/logo-sghi.svg" alt="SGHI" class="w-11 h-11 rounded-xl shadow-lg ring-2 ring-white/25" />
          <div>
            <h1 class="text-white font-bold text-xl tracking-tight">{{ BRAND.name }}</h1>
            <p class="text-white/70 text-xs mt-0.5">Portail patient</p>
          </div>
        </router-link>
      </div>

      <nav class="relative flex-1 p-3 space-y-1 overflow-y-auto ig-scrollbar-hide">
        <button
          v-for="(tab, i) in tabs"
          :key="tab.id"
          type="button"
          class="nav-tab w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 flex items-center gap-3"
          :class="activeTab === tab.id ? 'nav-tab-active' : 'nav-tab-idle'"
          :style="{ animationDelay: `${i * 0.04}s` }"
          @click="selectTab(tab.id)"
        >
          <img v-if="tab.icon" :src="tab.icon" :alt="tab.label" class="w-5 h-5 opacity-90 shrink-0" />
          <span
            v-else
            class="w-2 h-2 rounded-full shrink-0 transition-all duration-300"
            :class="activeTab === tab.id ? 'bg-white scale-125' : 'bg-white/40'"
          />
          {{ tab.label }}
        </button>
      </nav>

      <div class="relative p-4 border-t border-white/10 space-y-2">
        <div v-if="authStore.isAuthenticated" class="flex items-center gap-3 px-2 py-2">
          <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-white font-semibold text-sm ring-2 ring-white/30">
            {{ initials }}
          </div>
          <div class="min-w-0 flex-1">
            <p class="text-white text-sm font-medium truncate">{{ displayName }}</p>
            <p class="text-white/60 text-xs truncate">{{ roleLabel }}</p>
          </div>
        </div>

        <router-link
          v-if="isStaff"
          :to="staffDashboardPath"
          class="block w-full py-2.5 rounded-xl text-sm font-medium text-center text-white bg-white/20 hover:bg-white/30 border border-white/20 transition-all"
        >
          Espace professionnel →
        </router-link>

        <template v-if="!authStore.isAuthenticated">
          <router-link
            to="/login"
            class="block w-full py-2.5 rounded-xl text-sm font-semibold text-center text-sky-900 bg-white hover:bg-white/90 transition-all"
          >
            Se connecter
          </router-link>
          <router-link
            to="/register"
            class="block w-full py-2.5 rounded-xl text-sm font-medium text-center text-white/90 bg-white/10 hover:bg-white/20 border border-white/10 transition-all"
          >
            S'inscrire
          </router-link>
        </template>

        <button
          v-else
          type="button"
          class="w-full py-2.5 rounded-xl text-sm font-medium text-white/90 bg-white/10 hover:bg-white/20 border border-white/10 transition-all"
          @click="logout"
        >
          Déconnexion
        </button>
      </div>
    </aside>

    <main class="flex-1 flex flex-col min-w-0 bg-slate-50">
      <header class="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-slate-200/80 px-4 lg:px-8 py-4">
        <div class="flex items-center gap-4 max-w-6xl mx-auto">
          <button
            type="button"
            class="lg:hidden p-2 -ml-2 rounded-xl text-slate-600 hover:bg-slate-100"
            @click="sidebarOpen = true"
          >
            <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <div class="flex-1 min-w-0">
            <p class="text-[10px] font-semibold uppercase tracking-widest text-teal-600 mb-0.5">{{ BRAND.institution }}</p>
            <h2 class="text-lg lg:text-xl font-bold text-slate-900 truncate">{{ activeTabLabel }}</h2>
            <p class="text-sm text-slate-500 truncate hidden sm:block">
              {{ guestHint }}
            </p>
          </div>
          <div class="hidden sm:flex items-center gap-2">
            <span
              v-if="!authStore.isAuthenticated"
              class="visitor-badge px-3 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-teal-50 to-cyan-50 text-teal-700 border border-teal-200/80"
            >
              ✦ Mode visiteur
            </span>
            <span
              v-else
              class="px-3 py-1.5 rounded-full text-xs font-semibold text-white shadow-md"
              :style="{ background: `linear-gradient(135deg, ${palette.from}, ${palette.to})` }"
            >
              {{ roleLabel }}
            </span>
          </div>
        </div>
        <div
          class="h-1 rounded-full mt-3 max-w-6xl mx-auto opacity-80"
          :style="{ background: `linear-gradient(90deg, ${palette.from}, ${palette.to}, transparent)` }"
        />
      </header>

      <div v-if="isStaff" class="bg-amber-50 border-b border-amber-100 px-4 lg:px-8 py-3">
        <div class="max-w-6xl mx-auto flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-sm">
          <p class="text-amber-900">
            Connecté en tant que <strong>{{ roleLabel }}</strong> — le portail patient est en lecture seule.
          </p>
          <router-link :to="staffDashboardPath" class="font-semibold text-amber-800 hover:text-amber-950 underline-offset-2 hover:underline">
            Ouvrir mon tableau de bord →
          </router-link>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4 lg:p-8 portal-main-bg">
        <div class="max-w-6xl mx-auto">
          <Transition name="page" mode="out-in">
            <div :key="activeTab" class="app-page">
              <HeroBanner
                v-if="showHero"
                :image="heroImage"
                :title="heroTitle"
                :subtitle="heroSubtitle"
                :eyebrow="heroEyebrow"
                :large="!authStore.isAuthenticated"
              >
                <div v-if="!authStore.isAuthenticated" class="flex flex-wrap gap-2">
                  <router-link to="/login" class="hero-cta-primary">Connexion</router-link>
                  <router-link to="/register" class="hero-cta-secondary">S'inscrire</router-link>
                </div>
              </HeroBanner>
              <slot />
            </div>
          </Transition>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ROLES, getRolePath, getThemePalette } from '../../config/roles'
import { BRAND, getTabHeroImage, IMAGES } from '../../config/branding'
import HeroBanner from '../ui/HeroBanner.vue'

const props = defineProps({
  activeTab: { type: String, default: 'overview' },
  tabs: { type: Array, default: () => [] },
  hideHero: { type: Boolean, default: false },
})

const emit = defineEmits(['update:activeTab'])

const authStore = useAuthStore()
const router = useRouter()
const sidebarOpen = ref(false)

const palette = computed(() => getThemePalette('sky'))
const themeVars = computed(() => ({
  '--theme-from': palette.value.from,
  '--theme-via': palette.value.via,
  '--theme-to': palette.value.to,
  '--theme-light': palette.value.light,
  '--theme-accent': palette.value.accent,
  '--theme-glow': palette.value.glow,
}))

const sidebarGradient = computed(() =>
  `linear-gradient(180deg, ${palette.value.from} 0%, ${palette.value.via} 45%, ${palette.value.to} 100%)`,
)

const isStaff = computed(() => authStore.isAuthenticated && !authStore.isPatient)
const staffDashboardPath = computed(() => getRolePath(authStore.role))

const displayName = computed(() =>
  authStore.userName || authStore.user?.username || 'Visiteur',
)

const roleLabel = computed(() => {
  if (!authStore.isAuthenticated) return 'Visiteur'
  return ROLES[authStore.user?.role]?.label || 'Utilisateur'
})

const initials = computed(() => {
  const u = authStore.user
  if (!u) return '?'
  const a = (u.first_name?.[0] || u.username?.[0] || 'U').toUpperCase()
  const b = (u.last_name?.[0] || '').toUpperCase()
  return a + b
})

const activeTabLabel = computed(() =>
  props.tabs.find(t => t.id === props.activeTab)?.label || 'Portail patient',
)

const guestHint = computed(() => {
  if (!authStore.isAuthenticated) {
    return 'Parcourez librement — connectez-vous pour réaliser une opération.'
  }
  if (isStaff.value) {
    return 'Aperçu du parcours patient — utilisez votre espace professionnel pour agir.'
  }
  return 'Votre espace santé sécurisé.'
})

const heroImage = computed(() => getTabHeroImage('PATIENT', props.activeTab) || IMAGES.patientCare)

const heroTitle = computed(() => {
  if (authStore.isPatient && authStore.user?.first_name) {
    return `Bonjour, ${authStore.user.first_name}`
  }
  if (!authStore.isAuthenticated) {
    return 'Votre santé, à portée de main'
  }
  return activeTabLabel.value
})

const heroSubtitle = computed(() => {
  if (!authStore.isAuthenticated) {
    return 'Découvrez le portail SGHI. Toutes les opérations nécessitent une connexion sécurisée.'
  }
  return ROLES.PATIENT.description
})

const heroEyebrow = computed(() => {
  if (!authStore.isAuthenticated) return 'Bienvenue · Mode visiteur'
  return 'SGHI · CHU'
})

const showHero = computed(() => !props.hideHero)

const selectTab = (id) => {
  emit('update:activeTab', id)
  sidebarOpen.value = false
}

const logout = async () => {
  await authStore.logout()
  router.push('/')
}

const onResize = () => {
  if (window.innerWidth >= 1024) sidebarOpen.value = false
}

onMounted(() => window.addEventListener('resize', onResize))
onUnmounted(() => window.removeEventListener('resize', onResize))
</script>

<style scoped>
.nav-tab-idle {
  color: rgba(255, 255, 255, 0.75);
}
.nav-tab-idle:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
  transform: translateX(4px);
}
.nav-tab-active {
  color: #fff;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(8px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateX(4px);
}
.portal-main-bg {
  background-color: #f0f9ff;
  background-image:
    linear-gradient(rgba(240, 249, 255, 0.92), rgba(241, 245, 249, 0.96)),
    url('https://images.unsplash.com/photo-1631217868264-e5b36bb5938f?auto=format&fit=crop&w=1920&q=60');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
}
.visitor-badge {
  animation: badge-glow 3s ease-in-out infinite;
}
@keyframes badge-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(20, 184, 166, 0); }
  50% { box-shadow: 0 0 12px 2px rgba(20, 184, 166, 0.25); }
}
.hero-cta-primary {
  display: inline-flex; padding: 10px 20px; border-radius: 12px;
  background: linear-gradient(135deg, #14b8a6, #06b6d4);
  color: white; font-weight: 700; font-size: 0.875rem;
  box-shadow: 0 4px 16px rgba(20, 184, 166, 0.4);
  transition: transform 0.2s;
}
.hero-cta-primary:hover { transform: translateY(-2px); }
.hero-cta-secondary {
  display: inline-flex; padding: 10px 20px; border-radius: 12px;
  background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.35);
  color: white; font-weight: 600; font-size: 0.875rem;
  backdrop-filter: blur(8px);
}
.hero-cta-secondary:hover { background: rgba(255,255,255,0.25); }
</style>
