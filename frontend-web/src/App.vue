<template>
  <div id="app">
    <router-view />
  </div>
</template>

<script setup>
import { useAuthStore } from './stores/auth'

const authStore = useAuthStore()
// Vérifier l'état de l'authentification au chargement
</script>

<style>
@import './assets/main.css';
</style>