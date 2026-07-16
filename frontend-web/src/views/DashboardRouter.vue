<template>
  <router-view />
</template>

<script setup>
import { onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

function redirectIfNeeded() {
  if (route.path === '/dashboard' || route.path === '/dashboard/') {
    const path = authStore.dashboardPath()
    if (path && path !== '/login') {
      router.replace(path)
    }
  }
}

onMounted(redirectIfNeeded)
watch(() => route.path, redirectIfNeeded)
</script>
