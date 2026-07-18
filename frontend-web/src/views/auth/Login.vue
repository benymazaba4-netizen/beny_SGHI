<template>
  <AuthShell
    hero-title="Connectez-vous pour continuer"
    hero-subtitle="Accédez à vos données et réalisez vos opérations sur le portail patient SGHI."
    :hero-image="IMAGES.loginHero"
  >
    <div class="text-center mb-8">
      <router-link to="/" class="inline-flex items-center gap-1 text-sm text-slate-500 hover:text-teal-600 mb-4 transition-colors">
        <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        Retour au portail patient
      </router-link>
      <h2 class="text-2xl font-bold text-slate-900">Connexion</h2>
      <p class="text-slate-500 text-sm mt-1">
        {{ loginHint }}
      </p>
    </div>

    <form v-if="!mfaStep && !otpStep" @submit.prevent="handleLogin" class="ig-stack">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Nom d'utilisateur</label>
        <input v-model="username" type="text" class="app-input" placeholder="ex. medecin" required />
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Mot de passe</label>
        <input v-model="password" type="password" class="app-input" placeholder="••••••••" required />
      </div>
      <button type="submit" :disabled="loading" class="ig-btn ig-btn-primary w-full py-3 mt-2">
        {{ loading ? 'Connexion...' : 'Se connecter' }}
      </button>
    </form>

    <form v-else-if="mfaStep" @submit.prevent="handleMfa" class="ig-stack">
      <div class="text-center mb-2">
        <img src="/illustrations/icon-shield.svg" alt="" class="w-12 h-12 mx-auto mb-3 opacity-80" />
        <p class="text-sm text-slate-600">
          Code MFA pour <strong class="text-slate-900">{{ username }}</strong>
        </p>
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Code authenticator (6 chiffres)</label>
        <input
          v-model="totpCode"
          type="text"
          maxlength="6"
          pattern="[0-9]{6}"
          class="app-input text-center text-2xl tracking-[0.4em] font-mono"
          required
          autofocus
        />
      </div>
      <button type="submit" :disabled="loading" class="ig-btn ig-btn-primary w-full py-3">
        {{ loading ? 'Vérification...' : 'Valider' }}
      </button>
      <button type="button" class="text-sm text-slate-500 hover:text-indigo-600 transition-colors" @click="mfaStep = false">
        ← Retour à la connexion
      </button>
    </form>

    <form v-else @submit.prevent="handleOtp" class="ig-stack">
      <div
        v-if="demoOtpCode"
        role="alert"
        class="p-4 rounded-xl border border-sky-200 bg-sky-50 text-sky-900 text-center"
      >
        <p class="text-xs font-bold uppercase tracking-wide">Mode démo</p>
        <p class="mt-1 text-sm">
          Votre code OTP est :
          <strong class="ml-1 font-mono text-xl tracking-[0.2em]">{{ demoOtpCode }}</strong>
        </p>
      </div>
      <div class="text-center mb-2">
        <img src="/illustrations/icon-shield.svg" alt="" class="w-12 h-12 mx-auto mb-3 opacity-80" />
        <p class="text-sm text-slate-600">
          Code de validation à 2 étapes envoyé à <strong class="text-slate-900">{{ otpEmailHint || 'votre e-mail' }}</strong>
        </p>
        <p class="text-xs text-slate-500 mt-2 leading-relaxed">
          Vérifiez votre boîte de réception (et le dossier Spam). Code de validation à 2 étapes — expire dans 10 minutes.
        </p>
        <p class="text-xs text-slate-500 mt-1">Compte : {{ username }}</p>
      </div>
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1.5">Code reçu par e-mail (6 chiffres)</label>
        <input
          v-model="otpCode"
          type="text"
          maxlength="6"
          pattern="[0-9]{6}"
          class="app-input text-center text-2xl tracking-[0.4em] font-mono"
          required
          autofocus
        />
      </div>
      <button type="submit" :disabled="loading" class="ig-btn ig-btn-primary w-full py-3">
        {{ loading ? 'Vérification...' : 'Valider le code' }}
      </button>
      <button
        type="button"
        class="text-sm text-teal-600 hover:text-teal-700 font-medium transition-colors disabled:opacity-50"
        :disabled="resendLoading || resendCooldown > 0"
        @click="handleResendOtp"
      >
        {{ resendCooldown > 0 ? `Renvoyer dans ${resendCooldown}s` : (resendLoading ? 'Envoi...' : 'Renvoyer le code') }}
      </button>
      <button type="button" class="text-sm text-slate-500 hover:text-indigo-600 transition-colors" @click="otpStep = false">
        ← Retour à la connexion
      </button>
    </form>

    <div v-if="error" class="mt-4 p-3 rounded-xl bg-red-50 border border-red-100 text-red-700 text-sm text-center">
      {{ error }}
    </div>

    <div class="mt-6 pt-6 border-t border-slate-100">
      <p class="text-center text-sm text-slate-600">
        Pas de compte patient ?
        <router-link :to="{ path: '/register', query: route.query }" class="font-semibold text-indigo-600 hover:text-indigo-700">S'inscrire</router-link>
      </p>
      <div class="mt-4 flex flex-wrap justify-center gap-2">
        <span v-for="role in demoRoles" :key="role" class="text-[10px] px-2 py-1 rounded-full bg-slate-100 text-slate-500">
          {{ role }}
        </span>
      </div>
      <p class="text-[10px] text-center text-slate-400 mt-2">Démo : mot de passe <code class="bg-slate-100 px-1 rounded">Demo2026!</code></p>
    </div>
  </AuthShell>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import AuthShell from '../../components/layout/AuthShell.vue'
import { IMAGES } from '../../config/branding'
import { getRolePath } from '../../config/roles'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const totpCode = ref('')
const otpCode = ref('')
const mfaStep = ref(false)
const otpStep = ref(false)
const otpEmailHint = ref('')
const demoOtpCode = ref(authStore.demoOtpCode || '')
const loading = ref(false)
const resendLoading = ref(false)
const resendCooldown = ref(0)
const error = ref('')
const demoRoles = ['admin', 'medecin', 'patient', 'infirmier', 'secretaire']
let resendTimer = null

onUnmounted(() => {
  if (resendTimer) clearInterval(resendTimer)
})

const loginHint = computed(() => {
  if (route.query.tab) {
    return `Connexion requise pour accéder à « ${route.query.tab} »`
  }
  return 'Identifiez-vous pour continuer — patients et personnels soignants'
})

function afterLogin() {
  const redirect = route.query.redirect
  const tab = route.query.tab
  if (redirect && typeof redirect === 'string' && redirect.startsWith('/')) {
    if (tab && redirect === '/') {
      router.push({ path: '/', query: { tab } })
    } else {
      router.push(redirect)
    }
    return
  }
  if (authStore.isPatient) {
    router.push(tab ? { path: '/', query: { tab } } : '/')
    return
  }
  router.push(getRolePath(authStore.role))
}

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  const result = await authStore.login(username.value, password.value)
  if (result.success && result.mfaRequired) {
    mfaStep.value = true
  } else if (result.success && result.otpRequired) {
    otpStep.value = true
    otpEmailHint.value = result.emailHint || ''
    demoOtpCode.value = result.demoOtpCode || ''
  } else if (result.success) {
    afterLogin()
  } else {
    error.value = result.error
  }
  loading.value = false
}

const handleOtp = async () => {
  loading.value = true
  error.value = ''
  const result = await authStore.loginOtp(otpCode.value, username.value)
  if (result.success) {
    afterLogin()
  } else {
    error.value = result.error
  }
  loading.value = false
}

const handleResendOtp = async () => {
  resendLoading.value = true
  error.value = ''
  const result = await authStore.resendOtp()
  if (result.success) {
    otpEmailHint.value = result.emailHint || otpEmailHint.value
    demoOtpCode.value = result.demoOtpCode || ''
    resendCooldown.value = 60
    resendTimer = setInterval(() => {
      resendCooldown.value -= 1
      if (resendCooldown.value <= 0 && resendTimer) {
        clearInterval(resendTimer)
        resendTimer = null
      }
    }, 1000)
  } else {
    error.value = result.error
  }
  resendLoading.value = false
}

const handleMfa = async () => {
  loading.value = true
  error.value = ''
  const result = await authStore.loginMfa(totpCode.value)
  if (result.success) {
    afterLogin()
  } else {
    error.value = result.error
  }
  loading.value = false
}
</script>

<style scoped>
:deep(.auth-card) {
  --theme-from: #4338ca;
  --theme-to: #6366f1;
  --theme-accent: #6366f1;
  --theme-glow: rgba(99, 102, 241, 0.25);
}
</style>
