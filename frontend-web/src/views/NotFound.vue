<template>
  <div class="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
    <img :src="IMAGES.hospitalWide" alt="" class="absolute inset-0 w-full h-full object-cover" aria-hidden="true" />
    <div class="absolute inset-0 bg-slate-900/70 backdrop-blur-sm" />
    <div class="relative z-10 text-center max-w-md app-card p-8">
      <img src="/logo-sghi.svg" alt="SGHI" class="w-16 h-16 mx-auto mb-4 rounded-2xl shadow-md" />
      <p class="text-6xl font-bold text-indigo-200/30">404</p>
      <h1 class="text-2xl font-bold text-slate-900 mt-2">Page introuvable</h1>
      <p class="text-slate-500 mt-2 text-sm">Cette adresse n'existe pas ou vous n'y avez pas accès.</p>
      <router-link to="/dashboard" class="ig-btn ig-btn-primary inline-flex mt-8 px-6">
        Retour au tableau de bord
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { IMAGES } from '../config/branding'
</script>
