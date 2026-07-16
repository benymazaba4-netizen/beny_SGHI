import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { getRolePath } from '../config/roles'

const LoginView = () => import('../views/auth/Login.vue')
const RegisterView = () => import('../views/auth/Register.vue')
const PatientPortal = () => import('../views/PatientPortal.vue')
const DashboardRouter = () => import('../views/DashboardRouter.vue')
const MedecinDashboard = () => import('../views/medecin/Dashboard.vue')
const AdminDashboard = () => import('../views/admin/Dashboard.vue')
const InfirmierDashboard = () => import('../views/infirmier/Dashboard.vue')
const BiologisteDashboard = () => import('../views/biologiste/Dashboard.vue')
const PharmacienDashboard = () => import('../views/pharmacien/Dashboard.vue')
const ComptableDashboard = () => import('../views/comptable/Dashboard.vue')
const SecretaireDashboard = () => import('../views/secretaire/Dashboard.vue')

const dashboardChildren = [
  { path: 'patient', redirect: { path: '/', query: {} } },
  { path: 'medecin', name: 'MedecinDashboard', component: MedecinDashboard, meta: { role: 'MEDECIN' } },
  { path: 'admin', name: 'AdminDashboard', component: AdminDashboard, meta: { role: 'ADMIN' } },
  { path: 'infirmier', name: 'InfirmierDashboard', component: InfirmierDashboard, meta: { role: 'INFIRMIER' } },
  { path: 'biologiste', name: 'BiologisteDashboard', component: BiologisteDashboard, meta: { role: 'BIOLOGISTE' } },
  { path: 'pharmacien', name: 'PharmacienDashboard', component: PharmacienDashboard, meta: { role: 'PHARMACIEN' } },
  { path: 'comptable', name: 'ComptableDashboard', component: ComptableDashboard, meta: { role: 'COMPTABLE' } },
  { path: 'secretaire', name: 'SecretaireDashboard', component: SecretaireDashboard, meta: { role: 'SECRETAIRE' } },
]

const routes = [
  {
    path: '/',
    name: 'PatientPortal',
    component: PatientPortal,
    meta: { requiresAuth: false },
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
    meta: { requiresAuth: false },
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardRouter,
    meta: { requiresAuth: true },
    children: dashboardChildren,
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function resolvePostLoginRedirect(authStore, to) {
  const redirect = to.query.redirect
  if (redirect && typeof redirect === 'string' && redirect.startsWith('/')) {
    const tab = to.query.tab
    if (tab && redirect === '/') {
      return { path: '/', query: { tab } }
    }
    return redirect
  }
  if (authStore.isPatient) {
    const tab = to.query.tab
    return tab ? { path: '/', query: { tab } } : '/'
  }
  return authStore.dashboardPath()
}

router.beforeEach((to) => {
  const authStore = useAuthStore()
  const requiresAuth = to.meta.requiresAuth !== false

  if (requiresAuth && !authStore.isAuthenticated) {
    return {
      path: '/login',
      query: { redirect: to.fullPath },
    }
  }

  if ((to.path === '/login' || to.path === '/register') && authStore.isAuthenticated) {
    return resolvePostLoginRedirect(authStore, to)
  }

  const requiredRole = to.meta.role
  if (requiredRole && authStore.role) {
    const userRole = authStore.role
    if (userRole !== requiredRole && userRole !== 'ADMIN') {
      return getRolePath(userRole)
    }
  }

  return true
})

export default router
