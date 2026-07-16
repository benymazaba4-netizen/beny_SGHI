<template>
  <div
    class="h-screen flex overflow-hidden"
    :style="themeVars"
  >
    <!-- Overlay mobile -->
    <Transition name="overlay">
      <div
        v-if="sidebarOpen"
        class="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 lg:hidden"
        @click="sidebarOpen = false"
      />
    </Transition>

    <!-- Sidebar colorée par rôle -->
    <aside
      class="fixed lg:static inset-y-0 left-0 z-50 w-[280px] flex flex-col shrink-0 transition-transform duration-300 ease-out lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'"
      :style="{ background: sidebarGradient }"
    >
      <!-- Décor -->
      <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-20 -right-20 w-56 h-56 rounded-full bg-white/10 blur-2xl" />
        <div class="absolute bottom-20 -left-10 w-40 h-40 rounded-full bg-white/5 blur-xl" />
      </div>

      <div class="relative p-6 border-b border-white/10">
        <div class="flex items-center gap-3">
          <img src="/logo-sghi.svg" alt="SGHI" class="w-11 h-11 rounded-xl shadow-lg ring-2 ring-white/25 animate-float" />
          <div>
            <h1 class="text-white font-bold text-xl tracking-tight">{{ BRAND.name }}</h1>
            <p class="text-white/70 text-xs mt-0.5">{{ roleConfig.label }}</p>
          </div>
        </div>
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
          <span
            class="w-2 h-2 rounded-full shrink-0 transition-all duration-300"
            :class="activeTab === tab.id ? 'bg-white scale-125' : 'bg-white/40'"
          />
          {{ tab.label }}
        </button>
      </nav>

      <div class="relative p-4 border-t border-white/10">
        <div class="flex items-center gap-3 px-2 py-2 mb-2">
          <UserAvatar
            :name="userName"
            :photo-url="authStore.user?.photo_url || ''"
            size="md"
          />
          <div class="min-w-0 flex-1">
            <p class="text-white text-sm font-medium truncate">{{ userName }}</p>
            <p class="text-white/60 text-xs truncate">{{ roleConfig.description }}</p>
          </div>
        </div>
        <router-link
          to="/"
          class="block w-full py-2.5 rounded-xl text-sm font-medium text-center text-white/90 bg-white/5 hover:bg-white/15 border border-white/10 transition-all mb-2"
        >
          ← Portail patient
        </router-link>
        <button
          type="button"
          class="w-full py-2.5 rounded-xl text-sm font-medium text-white/90 bg-white/10 hover:bg-white/20 border border-white/10 transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
          @click="logout"
        >
          Déconnexion
        </button>
      </div>
    </aside>

    <!-- Contenu principal -->
    <main class="flex-1 flex flex-col min-w-0 bg-slate-50">
      <!-- Header -->
      <header class="sticky top-0 z-30 bg-white/80 backdrop-blur-xl border-b border-slate-200/80 px-4 lg:px-8 py-4">
        <div class="flex items-center gap-4 max-w-6xl mx-auto">
          <button
            type="button"
            class="lg:hidden p-2 -ml-2 rounded-xl text-slate-600 hover:bg-slate-100 transition-colors"
            @click="sidebarOpen = true"
          >
            <svg width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path d="M4 6h16M4 12h16M4 18h16"/>
            </svg>
          </button>
          <div class="flex-1 min-w-0">
            <h2 class="text-lg lg:text-xl font-bold text-slate-900 truncate">{{ activeTabLabel }}</h2>
            <p class="text-sm text-slate-500 truncate hidden sm:block">{{ roleConfig.description }}</p>
          </div>
          <div
            class="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold text-white shadow-md"
            :style="{ background: `linear-gradient(135deg, ${palette.from}, ${palette.to})` }"
          >
            {{ roleConfig.label }}
          </div>
        </div>
        <div
          class="h-1 rounded-full mt-3 max-w-6xl mx-auto opacity-80"
          :style="{ background: `linear-gradient(90deg, ${palette.from}, ${palette.to}, transparent)` }"
        />
      </header>

      <!-- Zone contenu animée -->
      <div class="flex-1 overflow-y-auto p-4 lg:p-8 app-main-bg">
        <div class="max-w-6xl mx-auto">
          <Transition name="page" mode="out-in">
            <div :key="activeTab" class="app-page">
              <HeroBanner
                v-if="showHero"
                :image="heroImage"
                :title="heroTitle"
                :subtitle="roleConfig.description"
              />
              <slot />
            </div>
          </Transition>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, provide, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { ROLES, getThemePalette } from '../../config/roles'
import { BRAND, getRoleHeroImage, getTabHeroImage } from '../../config/branding'
import HeroBanner from '../ui/HeroBanner.vue'
import UserAvatar from '../ui/UserAvatar.vue'

const props = defineProps({
  activeTab: { type: String, default: '' },
  tabs: { type: Array, default: () => [] },
})

const emit = defineEmits(['update:activeTab'])

const authStore = useAuthStore()
const router = useRouter()
const sidebarOpen = ref(false)

const roleConfig = computed(() => ROLES[authStore.user?.role] || ROLES.ADMIN)
const palette = computed(() => getThemePalette(roleConfig.value.theme))

const themeVars = computed(() => ({
  '--theme-from': palette.value.from,
  '--theme-via': palette.value.via,
  '--theme-to': palette.value.to,
  '--theme-light': palette.value.light,
  '--theme-accent': palette.value.accent,
  '--theme-glow': palette.value.glow,
}))

provide('themePalette', palette)

const sidebarGradient = computed(() =>
  `linear-gradient(180deg, ${palette.value.from} 0%, ${palette.value.via} 45%, ${palette.value.to} 100%)`,
)

const userName = computed(() => authStore.userName || authStore.user?.username || 'Utilisateur')

const activeTabLabel = computed(() =>
  props.tabs.find(t => t.id === props.activeTab)?.label || roleConfig.value.label,
)

const showHero = computed(() => true)

const heroImage = computed(() => getTabHeroImage(authStore.user?.role, props.activeTab))

const heroTitle = computed(() => {
  const first = authStore.user?.first_name
  if (first) return `Bienvenue, ${first}`
  return activeTabLabel.value
})

const selectTab = (id) => {
  emit('update:activeTab', id)
  sidebarOpen.value = false
}

const logout = () => {
  authStore.logout()
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

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
.animate-float {
  animation: float 3s ease-in-out infinite;
}

.app-main-bg {
  background-color: #f1f5f9;
  background-image:
    linear-gradient(rgba(241, 245, 249, 0.94), rgba(241, 245, 249, 0.98)),
    url('https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1920&q=60');
  background-size: cover;
  background-position: center top;
  background-attachment: fixed;
}
</style>
