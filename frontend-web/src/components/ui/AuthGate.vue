<template>
  <div class="auth-gate relative">
    <div :class="locked ? 'auth-gate-blur select-none pointer-events-none' : ''">
      <slot />
    </div>

    <div
      v-if="locked"
      class="auth-gate-overlay absolute inset-0 flex items-center justify-center p-6 rounded-2xl"
    >
      <div class="auth-gate-card max-w-md w-full text-center p-8 rounded-3xl bg-white/95 backdrop-blur-xl shadow-2xl border border-teal-100/50 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-teal-50/80 via-white to-cyan-50/60 pointer-events-none" />
        <div class="absolute -top-12 -right-12 w-32 h-32 bg-teal-200/30 rounded-full blur-2xl" />

        <div class="relative">
          <div class="relative mx-auto w-24 h-24 mb-5">
            <img
              v-if="image"
              :src="image"
              :alt="title"
              class="w-full h-full object-cover rounded-2xl ring-4 ring-teal-100 shadow-lg"
            />
            <span
              class="absolute -bottom-2 -right-2 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-teal-500 to-cyan-600 text-white shadow-lg ring-4 ring-white"
            >
              <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
              </svg>
            </span>
          </div>
          <h3 class="text-xl font-extrabold text-slate-900 tracking-tight">{{ title }}</h3>
          <p class="text-sm text-slate-500 mt-2 leading-relaxed">{{ description }}</p>

          <ul class="mt-5 flex flex-wrap justify-center gap-2 text-xs text-teal-700 font-medium">
            <li v-for="tag in tags" :key="tag" class="px-2.5 py-1 rounded-full bg-teal-50 border border-teal-100">{{ tag }}</li>
          </ul>

          <div class="mt-7 flex flex-col sm:flex-row gap-3 justify-center">
            <button type="button" class="auth-gate-btn-primary" @click="$emit('login')">
              Se connecter
            </button>
            <button type="button" class="auth-gate-btn-secondary" @click="$emit('register')">
              Créer un compte patient
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  locked: { type: Boolean, default: true },
  title: { type: String, default: 'Connexion requise' },
  description: {
    type: String,
    default: 'Connectez-vous pour accéder à vos données personnelles et réaliser cette opération.',
  },
  image: String,
  tags: {
    type: Array,
    default: () => ['Sécurisé', 'Gratuit', '2 min'],
  },
})

defineEmits(['login', 'register'])
</script>

<style scoped>
.auth-gate-blur {
  filter: blur(4px);
  opacity: 0.5;
}
.auth-gate-overlay {
  background: linear-gradient(135deg, rgba(240, 253, 250, 0.8), rgba(255, 255, 255, 0.9));
}
.auth-gate-card {
  animation: gate-pop 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes gate-pop {
  from { opacity: 0; transform: scale(0.95) translateY(12px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
.auth-gate-btn-primary {
  padding: 12px 28px; border-radius: 14px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  color: white; font-weight: 700; font-size: 0.9rem;
  box-shadow: 0 6px 20px rgba(13, 148, 136, 0.35);
  transition: transform 0.2s;
}
.auth-gate-btn-primary:hover { transform: translateY(-2px); }
.auth-gate-btn-secondary {
  padding: 12px 24px; border-radius: 14px;
  background: white; border: 1px solid #e2e8f0;
  color: #0f172a; font-weight: 600; font-size: 0.9rem;
  transition: border-color 0.2s, background 0.2s;
}
.auth-gate-btn-secondary:hover { border-color: #99f6e4; background: #f0fdfa; }
</style>
