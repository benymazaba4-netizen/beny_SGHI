<template>
  <div
    class="hero-banner relative overflow-hidden rounded-2xl shadow-lg mb-6 animate-fade-in"
    :class="{ 'hero-banner--large': large }"
  >
    <img
      :src="image"
      :alt="title"
      class="absolute inset-0 w-full h-full object-cover scale-105 transition-transform duration-[8s] hover:scale-110"
      loading="lazy"
    />
    <div class="absolute inset-0 bg-gradient-to-r from-slate-900/90 via-teal-950/70 to-slate-900/30" />
    <div class="absolute inset-0 bg-gradient-to-t from-slate-900/50 to-transparent" />
    <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_80%_20%,rgba(20,184,166,0.25),transparent_50%)]" />
    <div class="absolute top-0 right-0 w-40 h-40 bg-teal-400/10 rounded-full blur-3xl" />

    <div class="relative z-10 flex flex-col sm:flex-row sm:items-end justify-between gap-4 p-6 lg:p-8 min-h-[160px] lg:min-h-[200px]" :class="{ 'lg:min-h-[240px]': large }">
      <div>
        <p v-if="eyebrow" class="text-teal-200/90 text-xs font-semibold uppercase tracking-widest mb-2">{{ eyebrow }}</p>
        <h2 class="text-xl lg:text-2xl font-bold text-white tracking-tight" :class="{ 'lg:text-3xl': large }">{{ title }}</h2>
        <p v-if="subtitle" class="text-white/80 text-sm mt-2 max-w-xl leading-relaxed">{{ subtitle }}</p>
      </div>
      <div v-if="$slots.default" class="shrink-0">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  image: { type: String, required: true },
  title: { type: String, required: true },
  subtitle: String,
  eyebrow: { type: String, default: 'SGHI · CHU' },
  large: { type: Boolean, default: false },
})
</script>

<style scoped>
.animate-fade-in {
  animation: fade-in-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
.hero-banner--large {
  box-shadow: 0 20px 50px rgba(13, 148, 136, 0.2);
}
</style>
