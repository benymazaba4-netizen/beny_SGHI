import apiClient from './client'

/** Déplie les réponses paginées `{ items, pagination }` ou renvoie un tableau brut. */
export function unwrapList(data) {
  if (Array.isArray(data)) return data
  return data?.items ?? []
}

/** GET liste avec pagination standard (page 1, 100 éléments par défaut). */
async function listGet(url, params = {}) {
  const res = await apiClient.get(url, { params: { page: 1, page_size: 100, ...params } })
  return { ...res, data: unwrapList(res.data), pagination: res.data?.pagination }
}

export const dashboardApi = {
  getKpis: () => apiClient.get('/dashboard/kpis'),
}

export const adminApi = {
  getStats: () => apiClient.get('/admin/stats'),
}

export const authApi = {
  getUsers: () => listGet('/auth/users'),
  updateUser: (id, data) => apiClient.patch(`/auth/users/${id}`, data),
  getMedecins: () => listGet('/auth/medecins'),
  getJournalConnexions: (params) => listGet('/auth/journal-connexions', params),
  register: (data) => apiClient.post('/auth/register', data),
}

export const hospitalApi = {
  getBatiments: () => listGet('/hospital/batiments'),
  getServices: () => listGet('/hospital/services'),
  getChambres: () => listGet('/hospital/chambres'),
  getLits: () => listGet('/hospital/lits'),
  getLitsLibres: (serviceId) => listGet('/hospital/lits/libres', serviceId ? { service_id: serviceId } : {}),
  createBatiment: (data) => apiClient.post('/hospital/batiments', data),
  createService: (data) => apiClient.post('/hospital/services', data),
  createChambre: (data) => apiClient.post('/hospital/chambres', data),
  createLit: (data) => apiClient.post('/hospital/lits', data),
}

export const clinicalApi = {
  getPatients: () => listGet('/clinical/patients'),
  getPatient: (id) => apiClient.get(`/clinical/patients/${id}`),
  generatePatientQrAccess: (id) => apiClient.post(`/clinical/patients/${id}/qr-access`),
  verifyPatientQrAccess: (token) => apiClient.post('/clinical/patients/qr-access/verify', { token }),
  updatePatient: (id, data) => apiClient.put(`/clinical/patients/${id}`, data),
  getAdmissionsActives: () => listGet('/clinical/admissions/actives'),
  getAdmission: (id) => apiClient.get(`/clinical/admissions/${id}`),
  getAdmissionsPatient: (id) => listGet(`/clinical/admissions/patient/${id}`),
  getConsultationsPatient: (id) => listGet(`/clinical/consultations/patient/${id}`),
  createPatient: (data) => apiClient.post('/clinical/patients', data),
  createAdmission: (data) => apiClient.post('/clinical/admissions', data),
  createConsultation: (data) => apiClient.post('/clinical/consultations', data),
  createConstante: (data) => apiClient.post('/clinical/constantes', data),
  sortieAdmission: (id, data) => apiClient.post(`/clinical/admissions/${id}/sortie`, data),
  transfertAdmission: (id, data) => apiClient.post(`/clinical/admissions/${id}/transfert`, data),
  getConstantesPatient: (id) => listGet(`/clinical/constantes/patient/${id}`),
  getPlansSoins: (id) => listGet(`/clinical/plans-soins/patient/${id}`),
  createPlanSoin: (data) => apiClient.post('/clinical/plans-soins', data),
}

export const laboratoryApi = {
  getExamensTypes: () => listGet('/laboratory/examens-types'),
  getDemande: (id) => apiClient.get(`/laboratory/demandes/${id}`),
  getDemandesEnCours: () => listGet('/laboratory/demandes/en-cours'),
  getAttenteValidation: () => listGet('/laboratory/demandes/attente-validation'),
  getDemandesPatient: (id) => listGet(`/laboratory/demandes/patient/${id}`),
  createExamenType: (data) => apiClient.post('/laboratory/examens-types', data),
  createDemande: (data) => apiClient.post('/laboratory/demandes', data),
  createPrelevement: (data) => apiClient.post('/laboratory/prelevements', data),
  affecterDemande: (id, data) => apiClient.post(`/laboratory/demandes/${id}/affecter`, data),
  createResultat: (data) => apiClient.post('/laboratory/resultats', data),
  getResultat: (id) => apiClient.get(`/laboratory/resultats/${id}`),
  updateResultat: (id, data) => apiClient.put(`/laboratory/resultats/${id}`, data),
  validerResultat: (id) => apiClient.post(`/laboratory/resultats/${id}/valider`),
  downloadResultatPdf: (id) => apiClient.get(`/laboratory/resultats/${id}/pdf`, { responseType: 'blob' }),
}

export const prescriptionsApi = {
  getMedicaments: () => listGet('/prescriptions/medicaments'),
  getPrescription: (id) => apiClient.get(`/prescriptions/prescriptions/${id}`),
  getPrescriptionsPatient: (id) => listGet(`/prescriptions/prescriptions/patient/${id}`),
  getAlertesDoses: () => listGet('/prescriptions/prescriptions/alertes-doses'),
  createMedicament: (data) => apiClient.post('/prescriptions/medicaments', data),
  createPrescription: (data) => apiClient.post('/prescriptions/prescriptions', data),
  addLignePrescription: (data) => apiClient.post('/prescriptions/prescriptions/lignes', data),
  validerPrescription: (id) => apiClient.post(`/prescriptions/prescriptions/${id}/valider`),
  annulerPrescription: (id) => apiClient.post(`/prescriptions/prescriptions/${id}/annuler`),
  createAdministration: (data) => apiClient.post('/prescriptions/administrations', data),
  signalerDoseOmise: (ligneId, data) => apiClient.post(`/prescriptions/prescriptions/lignes/${ligneId}/dose-omise`, data),
}

export const pharmacyApi = {
  getStocks: () => listGet('/pharmacy/stocks'),
  getAlertes: () => listGet('/pharmacy/alertes'),
  createLot: (data) => apiClient.post('/pharmacy/lots', data),
  createMouvement: (data) => apiClient.post('/pharmacy/mouvements', data),
}

export const billingApi = {
  getAssurances: () => listGet('/billing/assurances'),
  getFacturesPatient: (id) => listGet(`/billing/factures/patient/${id}`),
  getFacture: (id) => apiClient.get(`/billing/factures/${id}`),
  getJournal: () => listGet('/billing/journal'),
  genererFactureAuto: (data) => apiClient.post('/billing/factures/generer-automatique', data),
  createFacture: (data) => apiClient.post('/billing/factures', data),
  createFactureLigne: (data) => apiClient.post('/billing/factures/lignes', data),
  appliquerTiersPayant: (id) => apiClient.post(`/billing/factures/${id}/tiers-payant`),
  emettreFacture: (id) => apiClient.post(`/billing/factures/${id}/emettre`),
  createPaiement: (data) => apiClient.post('/billing/paiements', data),
  createPaiementMobileMoney: (data) => apiClient.post('/billing/paiements/mobile-money', data),
  getEcheancier: (factureId) => listGet(`/billing/factures/${factureId}/echeancier`),
  createEcheancier: (factureId, data) => apiClient.post(`/billing/factures/${factureId}/echeancier`, data),
  createAssurance: (data) => apiClient.post('/billing/assurances', data),
  createPriseEnCharge: (data) => apiClient.post('/billing/prises-en-charge', data),
  downloadFacturePdf: (id) => apiClient.get(`/billing/factures/${id}/pdf`, { responseType: 'blob' }),
}

export const rhApi = {
  getPersonnel: () => listGet('/rh/personnel'),
  getPlanningGardes: () => listGet('/rh/planning-gardes'),
  createPlanningGarde: (data) => apiClient.post('/rh/planning-gardes', data),
  getPresences: () => listGet('/rh/presences'),
  getConges: () => listGet('/rh/conges'),
  getFichesPaie: () => listGet('/rh/fiches-paie'),
  createPresence: (data) => apiClient.post('/rh/presences', data),
  createConge: (data) => apiClient.post('/rh/conges', data),
  validerConge: (id, data) => apiClient.post(`/rh/conges/${id}/valider`, data),
  createFichePaie: (data) => apiClient.post('/rh/fiches-paie', data),
}

export const appointmentsApi = {
  getCreneaux: (params) => apiClient.get('/appointments/disponibilites/creneaux', { params }),
  createDisponibilite: (data) => apiClient.post('/appointments/disponibilites', data),
  createRendezVous: (data) => apiClient.post('/appointments/rendez-vous', data),
  getRdvPatient: (id) => listGet(`/appointments/rendez-vous/patient/${id}`),
  getRdvMedecin: (id) => listGet(`/appointments/rendez-vous/medecin/${id}`),
  annulerRdv: (id) => apiClient.post(`/appointments/rendez-vous/${id}/annuler`),
}

export const secretariatApi = {
  getInvoices: (params) => listGet('/secretariat/invoices', params),
  createInvoice: (data) => apiClient.post('/secretariat/invoices', data),
  payInvoice: (id, data) => apiClient.post(`/secretariat/invoices/${id}/pay`, data),
}

export const messagingApi = {
  getConversations: () => listGet('/messaging/conversations'),
  createConversation: (data) => apiClient.post('/messaging/conversations', data),
  getMessages: (id, sinceId) => listGet(`/messaging/conversations/${id}/messages`, sinceId ? { since_id: sinceId } : {}),
  sendMessage: (id, data) => apiClient.post(`/messaging/conversations/${id}/messages`, data),
}

export const notificationsApi = {
  getNotifications: (nonLues) => listGet('/notifications/notifications', nonLues ? { non_lues: true } : {}),
  marquerLue: (id) => apiClient.post(`/notifications/notifications/${id}/lue`),
  registerDevice: (data) => apiClient.post('/notifications/devices', data),
}

export const referentialsApi = {
  searchCim10: (q) => listGet('/referentials/cim10', { q, page_size: 20 }),
  getCim10: (code) => apiClient.get(`/referentials/cim10/${code}`),
}

export const governanceApi = {
  getAccesDossiers: (params) => listGet('/governance/acces-dossiers', params),
  getArchives: () => listGet('/governance/archives'),
  archiverPatient: (id) => apiClient.post(`/governance/patients/${id}/archiver`),
  createAnonymisation: (data) => apiClient.post('/governance/anonymisation', data),
  getAnonymisations: () => listGet('/governance/anonymisation'),
}

export const mfaApi = {
  getStatus: () => apiClient.get('/mfa/status'),
  setup: () => apiClient.post('/mfa/setup'),
  verify: (totp_token) => apiClient.post('/mfa/verify', { totp_token }),
  disable: (password) => apiClient.post('/mfa/disable', null, { params: { password } }),
}

export const auditApi = {
  getLogs: (params) => listGet('/audit/logs', params),
  getLog: (id) => apiClient.get(`/audit/logs/${id}`),
}

export async function downloadBlob(response, filename) {
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(url)
}

export function getApiError(error) {
  return error.response?.data?.error || error.message || 'Erreur inconnue'
}
