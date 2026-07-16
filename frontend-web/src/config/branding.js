/** Visuels institutionnels — photos Unsplash (usage démo / présentation) */

export const BRAND = {
  name: 'SGHI',
  fullName: 'Système de Gestion Hospitalière Intégré',
  institution: 'CHU — Centre Hospitalier Universitaire',
  tagline: 'Soins d\'excellence · Gestion intelligente',
}

export const IMAGES = {
  loginHero: 'https://images.unsplash.com/photo-1586773860418-d37222fbf3ad?auto=format&fit=crop&w=1600&q=80',
  loginMobile: 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=800&q=80',
  hospitalWide: 'https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1400&q=80',
  reception: 'https://images.unsplash.com/photo-1516549655169-df83a0774514?auto=format&fit=crop&w=1400&q=80',
  medicalTeam: 'https://images.unsplash.com/photo-1576091160399-112ba8d25d1f?auto=format&fit=crop&w=1400&q=80',
  laboratory: 'https://images.unsplash.com/photo-1579154204601-01588f351e67?auto=format&fit=crop&w=1400&q=80',
  pharmacy: 'https://images.unsplash.com/photo-1576602976842-054f3490a4a0?auto=format&fit=crop&w=1400&q=80',
  finance: 'https://images.unsplash.com/photo-1554224311-beee415c201f?auto=format&fit=crop&w=1400&q=80',
  patientCare: 'https://images.unsplash.com/photo-1631217868264-e5b36bb5938f?auto=format&fit=crop&w=1400&q=80',
  nursing: 'https://images.unsplash.com/photo-1579684385127-1ef15a5089a2?auto=format&fit=crop&w=1400&q=80',
  admin: 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=1400&q=80',
}

export const ROLE_HERO_IMAGES = {
  ADMIN: IMAGES.admin,
  MEDECIN: IMAGES.medicalTeam,
  INFIRMIER: IMAGES.nursing,
  BIOLOGISTE: IMAGES.laboratory,
  PHARMACIEN: IMAGES.pharmacy,
  COMPTABLE: IMAGES.finance,
  SECRETAIRE: IMAGES.reception,
  PATIENT: IMAGES.patientCare,
}

export function getRoleHeroImage(role) {
  return ROLE_HERO_IMAGES[role] || IMAGES.hospitalWide
}

export function getTabHeroImage(role, tabId) {
  const tabMap = {
    overview: ROLE_HERO_IMAGES[role] || IMAGES.hospitalWide,
    patients: IMAGES.reception,
    admissions: IMAGES.hospitalWide,
    actions: IMAGES.medicalTeam,
    labo: IMAGES.laboratory,
    validation: IMAGES.laboratory,
    encours: IMAGES.laboratory,
    stocks: IMAGES.pharmacy,
    alertes: IMAGES.nursing,
    factures: IMAGES.finance,
    journal: IMAGES.finance,
    rdv: IMAGES.patientCare,
    messages: IMAGES.patientCare,
    notifications: IMAGES.patientCare,
    soins: IMAGES.nursing,
    constantes: IMAGES.nursing,
    dossier: IMAGES.patientCare,
    ordonnances: IMAGES.pharmacy,
    users: IMAGES.admin,
    structure: IMAGES.hospitalWide,
    rh: IMAGES.admin,
    audit: IMAGES.admin,
    mfa: IMAGES.admin,
    'new-patient': IMAGES.reception,
    'new-admission': IMAGES.hospitalWide,
    sortie: IMAGES.hospitalWide,
    'edit-patient': IMAGES.reception,
  }
  return tabMap[tabId] || getRoleHeroImage(role)
}

/** Miniatures pour cartes statistiques (vue d'ensemble) */
export const STAT_IMAGES = {
  patients: IMAGES.reception,
  admissions: IMAGES.hospitalWide,
  hospitalWide: IMAGES.hospitalWide,
  consultations: IMAGES.medicalTeam,
  examens: IMAGES.laboratory,
  prescriptions: IMAGES.pharmacy,
  factures: IMAGES.finance,
  rdv: IMAGES.patientCare,
  alertes: IMAGES.nursing,
  nursing: IMAGES.nursing,
  stocks: IMAGES.pharmacy,
  validation: IMAGES.laboratory,
  journal: IMAGES.finance,
  admin: IMAGES.admin,
}
