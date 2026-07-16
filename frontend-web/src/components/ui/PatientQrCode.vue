<template>
  <article class="rounded-3xl border border-teal-100 bg-gradient-to-br from-white to-teal-50 p-5 shadow-sm">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-xs uppercase tracking-[0.22em] text-teal-700 font-black">Accès temporaire</p>
        <h3 class="mt-1 text-lg font-black text-slate-900">QR dossier patient sécurisé</h3>
        <p class="mt-1 text-sm text-slate-600">
          Token signé et chiffré, valable {{ expiresInMinutes }} minute(s).
        </p>
      </div>
      <span class="rounded-full bg-teal-100 px-3 py-1 text-xs font-bold text-teal-800">Confidentiel</span>
    </div>

    <div v-if="qrCodeBase64" class="mt-5 grid grid-cols-1 md:grid-cols-[180px_1fr] gap-4 items-center">
      <img
        :src="`data:image/png;base64,${qrCodeBase64}`"
        alt="QR code d'accès temporaire au dossier patient"
        class="w-44 h-44 rounded-2xl border border-white bg-white p-3 shadow mx-auto"
      />
      <div class="space-y-3">
        <p class="text-sm text-slate-700">Présentez ce QR code au médecin ou à la tablette autorisée pour ouvrir le dossier complet pendant une fenêtre courte.</p>
        <div class="rounded-2xl bg-white/80 border border-teal-100 p-3">
          <p class="text-xs text-slate-500">Expire le</p>
          <p class="font-bold text-slate-900">{{ formattedExpiry }}</p>
        </div>
      </div>
    </div>

    <button
      type="button"
      class="ig-btn ig-btn-primary mt-5 w-full py-2.5"
      :disabled="loading"
      @click="$emit('generate')"
    >
      {{ loading ? 'Génération...' : qrCodeBase64 ? 'Régénérer un QR sécurisé' : 'Générer le QR sécurisé' }}
    </button>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  qrCodeBase64: { type: String, default: '' },
  expiresAt: { type: String, default: '' },
  expiresInSeconds: { type: Number, default: 300 },
  loading: { type: Boolean, default: false },
})

defineEmits(['generate'])

const expiresInMinutes = computed(() => Math.max(1, Math.round(props.expiresInSeconds / 60)))
const formattedExpiry = computed(() => {
  if (!props.expiresAt) return 'Non généré'
  return new Date(props.expiresAt).toLocaleString('fr-FR')
})
</script>
