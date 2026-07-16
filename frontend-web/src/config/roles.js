export const ROLES = {
  ADMIN: {
    label: 'Administrateur',
    path: '/dashboard/admin',
    theme: 'indigo',
    description: 'Pilotage global, structure, finances, RH, audit',
  },
  MEDECIN: {
    label: 'Médecin',
    path: '/dashboard/medecin',
    theme: 'blue',
    description: 'Patients, consultations, prescriptions',
  },
  INFIRMIER: {
    label: 'Infirmier(ère)',
    path: '/dashboard/infirmier',
    theme: 'teal',
    description: 'Soins, constantes, administrations',
  },
  BIOLOGISTE: {
    label: 'Biologiste',
    path: '/dashboard/biologiste',
    theme: 'purple',
    description: 'Laboratoire, résultats, validation',
  },
  PHARMACIEN: {
    label: 'Pharmacien',
    path: '/dashboard/pharmacien',
    theme: 'green',
    description: 'Stocks, lots, alertes pharmacie',
  },
  COMPTABLE: {
    label: 'Comptable',
    path: '/dashboard/comptable',
    theme: 'amber',
    description: 'Facturation, paiements, journal',
  },
  SECRETAIRE: {
    label: 'Secrétaire',
    path: '/dashboard/secretaire',
    theme: 'rose',
    description: 'Admissions, patients, accueil',
  },
  PATIENT: {
    label: 'Patient',
    path: '/',
    theme: 'sky',
    description: 'Factures, résultats, dossier',
  },
}

export const THEME_PALETTE = {
  indigo: { from: '#312e81', via: '#4338ca', to: '#6366f1', light: '#eef2ff', accent: '#4f46e5', glow: 'rgba(99,102,241,0.35)' },
  blue: { from: '#1e3a8a', via: '#2563eb', to: '#3b82f6', light: '#eff6ff', accent: '#2563eb', glow: 'rgba(59,130,246,0.35)' },
  teal: { from: '#115e59', via: '#0d9488', to: '#14b8a6', light: '#f0fdfa', accent: '#0d9488', glow: 'rgba(20,184,166,0.35)' },
  purple: { from: '#581c87', via: '#7c3aed', to: '#a855f7', light: '#faf5ff', accent: '#7c3aed', glow: 'rgba(168,85,247,0.35)' },
  green: { from: '#14532d', via: '#16a34a', to: '#22c55e', light: '#f0fdf4', accent: '#16a34a', glow: 'rgba(34,197,94,0.35)' },
  amber: { from: '#78350f', via: '#d97706', to: '#f59e0b', light: '#fffbeb', accent: '#d97706', glow: 'rgba(245,158,11,0.35)' },
  rose: { from: '#881337', via: '#e11d48', to: '#fb7185', light: '#fff1f2', accent: '#e11d48', glow: 'rgba(251,113,133,0.35)' },
  sky: { from: '#0c4a6e', via: '#0284c7', to: '#38bdf8', light: '#f0f9ff', accent: '#0284c7', glow: 'rgba(56,189,248,0.35)' },
}

export const THEME_CLASSES = {
  indigo: { bg: 'bg-indigo-600', hover: 'hover:bg-indigo-700', light: 'bg-indigo-50', text: 'text-indigo-600', ring: 'ring-indigo-500' },
  blue: { bg: 'bg-blue-600', hover: 'hover:bg-blue-700', light: 'bg-blue-50', text: 'text-blue-600', ring: 'ring-blue-500' },
  teal: { bg: 'bg-teal-600', hover: 'hover:bg-teal-700', light: 'bg-teal-50', text: 'text-teal-600', ring: 'ring-teal-500' },
  purple: { bg: 'bg-purple-600', hover: 'hover:bg-purple-700', light: 'bg-purple-50', text: 'text-purple-600', ring: 'ring-purple-500' },
  green: { bg: 'bg-green-600', hover: 'hover:bg-green-700', light: 'bg-green-50', text: 'text-green-600', ring: 'ring-green-500' },
  amber: { bg: 'bg-amber-600', hover: 'hover:bg-amber-700', light: 'bg-amber-50', text: 'text-amber-600', ring: 'ring-amber-500' },
  rose: { bg: 'bg-rose-600', hover: 'hover:bg-rose-700', light: 'bg-rose-50', text: 'text-rose-600', ring: 'ring-rose-500' },
  sky: { bg: 'bg-sky-600', hover: 'hover:bg-sky-700', light: 'bg-sky-50', text: 'text-sky-600', ring: 'ring-sky-500' },
}

export function getRolePath(role) {
  return ROLES[role]?.path || '/login'
}

export function getThemePalette(theme) {
  return THEME_PALETTE[theme] || THEME_PALETTE.indigo
}

export function formatFCFA(amount) {
  return new Intl.NumberFormat('fr-FR').format(amount || 0) + ' FCFA'
}

export function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })
}
