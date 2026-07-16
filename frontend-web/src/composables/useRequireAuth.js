import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getRolePath } from '../config/roles'

export function useRequireAuth() {
  const router = useRouter()
  const route = useRoute()
  const authStore = useAuthStore()

  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const isPatient = computed(() => authStore.isPatient)
  const isStaff = computed(() => authStore.isAuthenticated && !authStore.isPatient)

  function loginUrl(tab) {
    const query = { redirect: '/' }
    if (tab) query.tab = tab
    return { path: '/login', query }
  }

  function promptLogin(tab) {
    router.push(loginUrl(tab))
  }

  /** Action réservée aux patients connectés */
  function requirePatient(tab) {
    if (!authStore.isAuthenticated) {
      promptLogin(tab)
      return false
    }
    if (!authStore.isPatient) {
      router.push(getRolePath(authStore.role))
      return false
    }
    return true
  }

  /** Toute action nécessitant une connexion (staff → espace pro) */
  function requireAuth(tab) {
    if (!authStore.isAuthenticated) {
      promptLogin(tab)
      return false
    }
    return true
  }

  return {
    isAuthenticated,
    isPatient,
    isStaff,
    loginUrl,
    promptLogin,
    requirePatient,
    requireAuth,
  }
}
