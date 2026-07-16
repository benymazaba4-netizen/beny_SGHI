<template>
  <PortalLayout v-model:activeTab="activeTab" :tabs="tabs" :hide-hero="!isPatient && activeTab === 'overview'">
    <!-- Vue d'ensemble -->
    <IgFeed v-if="activeTab === 'overview'">
      <VisitorShowcase v-if="!isPatient" class="mb-8" @open-service="openTab" />

      <StatGrid v-if="isPatient">
        <StatCard
          label="Consultations"
          :value="isPatient ? consultations.length : '—'"
          :image="STAT_IMAGES.consultations"
          :subtitle="guestSubtitle"
        />
        <StatCard
          label="Examens"
          :value="isPatient ? examens.length : '—'"
          :image="STAT_IMAGES.examens"
          :subtitle="guestSubtitle"
        />
        <StatCard
          label="Factures"
          :value="isPatient ? factures.length : '—'"
          :image="STAT_IMAGES.factures"
          :subtitle="guestSubtitle"
        />
        <StatCard
          label="Prescriptions"
          :value="isPatient ? prescriptions.length : '—'"
          :image="STAT_IMAGES.prescriptions"
          :subtitle="guestSubtitle"
        />
      </StatGrid>

      <div v-if="isPatient" class="mt-8 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        <button
          v-for="service in portalServices"
          :key="service.id"
          type="button"
          class="portal-service-card group text-left overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm hover:shadow-2xl hover:border-teal-300 hover:-translate-y-1 transition-all duration-300"
          @click="openTab(service.id)"
        >
          <div class="relative h-36 overflow-hidden">
            <img
              :src="service.image"
              :alt="service.title"
              class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            />
            <div class="absolute inset-0 bg-gradient-to-t from-slate-900/70 via-slate-900/20 to-transparent" />
            <span class="absolute bottom-3 left-4 text-white font-semibold text-sm">{{ service.title }}</span>
          </div>
          <div class="p-4">
            <p class="text-sm text-slate-600 leading-relaxed">{{ service.desc }}</p>
            <span class="inline-flex items-center gap-1 mt-3 text-sm font-semibold text-teal-600 group-hover:gap-2 transition-all">
              Explorer
              <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </span>
          </div>
        </button>
      </div>
    </IgFeed>

    <!-- Dossier -->
    <IgFeed v-if="activeTab === 'dossier'" title="Mon dossier médical" subtitle="Historique des consultations">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.consultations"
        title="Accédez à votre dossier"
        description="Connectez-vous avec votre compte patient pour consulter votre historique médical."
        @login="promptLogin('dossier')"
        @register="goRegister"
      >
        <DataTable :columns="consultCols" :rows="displayConsultations" :loading="loading" />
      </AuthGate>
    </IgFeed>

    <!-- Labo -->
    <IgFeed v-if="activeTab === 'labo'" title="Résultats laboratoire" subtitle="Examens et téléchargements PDF">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.examens"
        title="Résultats sécurisés"
        description="Vos résultats d'analyses sont disponibles après connexion."
        @login="promptLogin('labo')"
        @register="goRegister"
      >
        <DataTable :columns="laboCols" :rows="displayExamens" :loading="loading">
          <template #cell-actions="{ row }">
            <button
              v-if="row.resultat_publie && row.resultat_id"
              type="button"
              class="ig-link"
              @click="downloadPdf(row.resultat_id)"
            >
              Télécharger PDF
            </button>
          </template>
        </DataTable>
      </AuthGate>
    </IgFeed>

    <!-- Ordonnances -->
    <IgFeed v-if="activeTab === 'ordonnances'" title="Ordonnances" subtitle="Prescriptions en cours">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.prescriptions"
        @login="promptLogin('ordonnances')"
        @register="goRegister"
      >
        <DataTable :columns="prescCols" :rows="displayPrescriptions" :loading="loading" />
      </AuthGate>
    </IgFeed>

    <!-- Factures -->
    <IgFeed v-if="activeTab === 'factures'" title="Mes factures" subtitle="Paiements et soldes">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.factures"
        @login="promptLogin('factures')"
        @register="goRegister"
      >
        <DataTable :columns="factureCols" :rows="displayFactures" :loading="loading">
          <template #cell-montant_patient="{ value }">{{ formatFCFA(value) }}</template>
          <template #cell-montant_restant="{ value }">{{ formatFCFA(value) }}</template>
          <template #cell-actions="{ row }">
            <div class="flex flex-wrap gap-2">
              <button v-if="Number(row.montant_restant) > 0" type="button" class="ig-link ig-link-success" @click="openPaiement(row)">
                Payer
              </button>
              <button v-if="row.pdf_disponible" type="button" class="ig-link" @click="downloadFacture(row.id)">
                PDF
              </button>
            </div>
          </template>
        </DataTable>
        <FormCard v-if="paiementFacture" title="Paiement en ligne" class="mt-6 max-w-lg" :image="STAT_IMAGES.factures">
          <AlertBanner :message="msgPaiement" :type="msgTypePaiement" />
          <p class="text-sm mb-3">Facture <strong>{{ paiementFacture.numero_facture }}</strong> — reste {{ formatFCFA(paiementFacture.montant_restant) }}</p>
          <form @submit.prevent="submitPaiement" class="ig-stack">
            <FormField label="Montant (FCFA)" v-model="formPaiement.montant" type="number" required />
            <FormField label="Mode" v-model="formPaiement.mode_paiement" type="select" :options="modePaiementOptions" required />
            <FormField v-if="formPaiement.mode_paiement === 'MTN' || formPaiement.mode_paiement === 'AIRTEL'" label="Téléphone Mobile Money" v-model="formPaiement.numero_telephone" required />
            <button type="submit" :disabled="submittingPaiement" class="ig-btn ig-btn-primary py-2.5">Confirmer le paiement</button>
          </form>
        </FormCard>
      </AuthGate>
    </IgFeed>

    <!-- RDV -->
    <IgFeed v-if="activeTab === 'rdv'" title="Mes rendez-vous" subtitle="Prise de rendez-vous et annulation">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.rdv"
        title="Prendre un rendez-vous"
        description="Connectez-vous pour planifier ou annuler vos rendez-vous en ligne."
        @login="promptLogin('rdv')"
        @register="goRegister"
      >
        <RdvCalendar :events="rdvCalendarEvents" class="mb-6" />
        <FormCard title="Prendre un rendez-vous" class="mb-6" :image="STAT_IMAGES.rdv">
          <AlertBanner :message="msgRdv" :type="msgTypeRdv" />
          <form @submit.prevent="prendreRdv" class="ig-stack max-w-lg">
            <FormField label="Médecin" v-model="formRdv.medecin_id" type="select" :options="medecinOptions" required />
            <FormField label="Service" v-model="formRdv.service_id" type="select" :options="serviceOptions" required />
            <FormField label="Date et heure" v-model="formRdv.date_heure" type="datetime-local" required />
            <FormField label="Motif" v-model="formRdv.motif" type="textarea" required />
            <button type="submit" :disabled="submittingRdv" class="ig-btn ig-btn-primary py-2.5">Confirmer</button>
          </form>
        </FormCard>
        <DataTable :columns="rdvCols" :rows="rendezVous" :loading="loading">
          <template #cell-actions="{ row }">
            <button v-if="row.statut === 'CONFIRME'" type="button" class="ig-link text-red-600" @click="annulerRdv(row.id)">
              Annuler
            </button>
          </template>
        </DataTable>
      </AuthGate>
    </IgFeed>

    <!-- Messages -->
    <IgFeed v-if="activeTab === 'messages'" title="Messages" subtitle="Conversation avec votre médecin">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.consultations"
        title="Messagerie sécurisée"
        description="Échangez avec votre médecin après connexion."
        @login="promptLogin('messages')"
        @register="goRegister"
      >
        <FormCard title="Messagerie sécurisée" :image="STAT_IMAGES.consultations" class="mb-6">
          <div v-if="conversations.length" class="space-y-4">
            <div v-for="msg in messages" :key="msg.id" class="p-3 bg-slate-50 rounded-xl border border-slate-100">
              <strong class="text-teal-800">{{ msg.expediteur }}</strong>
              <p class="text-sm text-slate-600 mt-1">{{ msg.contenu }}</p>
            </div>
            <div class="flex gap-2">
              <input v-model="newMessage" class="flex-1 border border-slate-200 rounded-xl px-3 py-2.5" placeholder="Votre message..." />
              <button type="button" class="ig-btn ig-btn-primary" @click="envoyerMessage">Envoyer</button>
            </div>
          </div>
          <EmptyState
            v-else
            title="Aucune conversation"
            description="Votre médecin pourra vous contacter ici après une consultation."
            image="/illustrations/empty-search.svg"
          />
        </FormCard>
      </AuthGate>
    </IgFeed>

    <!-- Notifications -->
    <IgFeed v-if="activeTab === 'notifications'" title="Notifications" subtitle="Rappels et alertes">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.rdv"
        @login="promptLogin('notifications')"
        @register="goRegister"
      >
        <DataTable :columns="notifCols" :rows="displayNotifications" :loading="loading" />
      </AuthGate>
    </IgFeed>

    <!-- Soins -->
    <IgFeed v-if="activeTab === 'soins'" title="Plan de soins" subtitle="Suivi infirmier">
      <AuthGate
        :locked="!isPatient"
        :image="STAT_IMAGES.nursing"
        @login="promptLogin('soins')"
        @register="goRegister"
      >
        <DataTable :columns="soinsCols" :rows="displayPlansSoins" :loading="loading" />
      </AuthGate>
    </IgFeed>
  </PortalLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import PortalLayout from '../components/layout/PortalLayout.vue'
import IgFeed from '../components/layout/IgFeed.vue'
import StatGrid from '../components/ui/StatGrid.vue'
import StatCard from '../components/ui/StatCard.vue'
import DataTable from '../components/ui/DataTable.vue'
import FormCard from '../components/ui/FormCard.vue'
import FormField from '../components/ui/FormField.vue'
import AlertBanner from '../components/ui/AlertBanner.vue'
import EmptyState from '../components/ui/EmptyState.vue'
import AuthGate from '../components/ui/AuthGate.vue'
import RdvCalendar from '../components/ui/RdvCalendar.vue'
import VisitorShowcase from '../components/ui/VisitorShowcase.vue'
import { useAuthStore } from '../stores/auth'
import { useRequireAuth } from '../composables/useRequireAuth'
import { clinicalApi, laboratoryApi, prescriptionsApi, billingApi, appointmentsApi, messagingApi, notificationsApi, authApi, hospitalApi, downloadBlob, getApiError } from '../api/modules'
import { formatFCFA } from '../config/roles'
import { STAT_IMAGES, IMAGES } from '../config/branding'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { isPatient, promptLogin } = useRequireAuth()

const activeTab = ref(route.query.tab || 'overview')

const tabs = [
  { id: 'overview', label: 'Accueil', icon: '/illustrations/icon-chart.svg' },
  { id: 'dossier', label: 'Dossier', icon: '/illustrations/icon-heart.svg' },
  { id: 'labo', label: 'Laboratoire', icon: '/illustrations/icon-shield.svg' },
  { id: 'ordonnances', label: 'Ordonnances' },
  { id: 'factures', label: 'Factures' },
  { id: 'soins', label: 'Soins' },
  { id: 'rdv', label: 'RDV' },
  { id: 'messages', label: 'Messages' },
  { id: 'notifications', label: 'Alertes' },
]

const portalServices = [
  { id: 'rdv', title: 'Rendez-vous', desc: 'Planifiez une consultation avec un spécialiste.', image: IMAGES.patientCare },
  { id: 'dossier', title: 'Dossier médical', desc: 'Consultez votre historique et vos diagnostics.', image: IMAGES.medicalTeam },
  { id: 'labo', title: 'Laboratoire', desc: 'Accédez à vos résultats d\'analyses en PDF.', image: IMAGES.laboratory },
  { id: 'ordonnances', title: 'Ordonnances', desc: 'Suivez vos prescriptions et traitements.', image: IMAGES.pharmacy },
  { id: 'factures', title: 'Facturation', desc: 'Visualisez vos factures et paiements.', image: IMAGES.finance },
  { id: 'messages', title: 'Messagerie', desc: 'Contactez votre équipe soignante en toute sécurité.', image: IMAGES.reception },
]

const DEMO = {
  consultations: [
    { date_consultation: '12/03/2026', motif: 'Consultation générale', diagnostic: 'Exemple', diagnostic_cim10: 'Z00.0' },
    { date_consultation: '05/01/2026', motif: 'Suivi post-opératoire', diagnostic: 'Exemple', diagnostic_cim10: 'Z09' },
  ],
  examens: [
    { id: '—', examen_type_nom: 'NFS', statut: 'VALIDE', date_prescription: '10/03/2026', resultat_publie: false },
  ],
  prescriptions: [
    { id: '—', statut: 'ACTIVE', date_debut: '12/03/2026', date_fin: '12/04/2026' },
  ],
  factures: [
    { numero_facture: 'FAC-XXXX', statut: 'PAYEE', montant_patient: 45000, montant_restant: 0, pdf_disponible: false },
  ],
  notifications: [
    { titre: 'Rappel RDV', corps: 'Exemple de notification', date_creation: '—' },
  ],
  soins: [
    { titre: 'Surveillance post-op', frequence: '2×/jour', statut: 'ACTIF', date_debut: '12/03/2026' },
  ],
}

const guestSubtitle = computed(() =>
  isPatient.value ? undefined : 'Connectez-vous pour voir vos données',
)

const consultations = ref([])
const examens = ref([])
const prescriptions = ref([])
const factures = ref([])
const rendezVous = ref([])
const conversations = ref([])
const messages = ref([])
const notifications = ref([])
const plansSoins = ref([])
const newMessage = ref('')
const activeConvId = ref(null)
const medecins = ref([])
const services = ref([])
const formRdv = ref({ medecin_id: '', service_id: '', date_heure: '', motif: '' })
const msgRdv = ref('')
const msgTypeRdv = ref('success')
const submittingRdv = ref(false)
const loading = ref(false)
const paiementFacture = ref(null)
const formPaiement = ref({ montant: '', mode_paiement: 'MTN', numero_telephone: '' })
const msgPaiement = ref('')
const msgTypePaiement = ref('success')
const submittingPaiement = ref(false)
const modePaiementOptions = [
  { value: 'MTN', label: 'MTN Mobile Money' },
  { value: 'AIRTEL', label: 'Airtel Money' },
  { value: 'CARTE', label: 'Carte bancaire' },
  { value: 'ESPECES', label: 'Espèces (guichet)' },
]

const rdvCalendarEvents = computed(() =>
  rendezVous.value.map(r => ({
    id: r.id,
    date: r.date_heure,
    label: `${(r.date_heure || '').slice(11, 16)} Dr ${r.medecin || ''}`.trim(),
    statut: r.statut,
  })),
)

const displayConsultations = computed(() => (isPatient.value ? consultations.value : DEMO.consultations))
const displayExamens = computed(() => (isPatient.value ? examens.value : DEMO.examens))
const displayPrescriptions = computed(() => (isPatient.value ? prescriptions.value : DEMO.prescriptions))
const displayFactures = computed(() => (isPatient.value ? factures.value : DEMO.factures))
const displayNotifications = computed(() => (isPatient.value ? notifications.value : DEMO.notifications))
const displayPlansSoins = computed(() => (isPatient.value ? plansSoins.value : DEMO.soins))

const medecinOptions = computed(() => medecins.value.map(m => ({
  value: m.id,
  label: m.first_name ? `Dr ${m.first_name} ${m.last_name}` : m.username,
})))
const serviceOptions = computed(() => services.value.map(s => ({
  value: s.id,
  label: `${s.code} — ${s.nom}`,
})))

const consultCols = [
  { key: 'date_consultation', label: 'Date' },
  { key: 'motif', label: 'Motif' },
  { key: 'diagnostic', label: 'Diagnostic' },
  { key: 'diagnostic_cim10', label: 'CIM-10' },
]
const laboCols = [
  { key: 'id', label: 'N°' },
  { key: 'examen_type_nom', label: 'Examen' },
  { key: 'statut', label: 'Statut' },
  { key: 'date_prescription', label: 'Date' },
  { key: 'actions', label: 'Actions' },
]
const prescCols = [
  { key: 'id', label: 'N°' },
  { key: 'statut', label: 'Statut' },
  { key: 'date_debut', label: 'Début' },
  { key: 'date_fin', label: 'Fin' },
]
const factureCols = [
  { key: 'numero_facture', label: 'N°' },
  { key: 'statut', label: 'Statut' },
  { key: 'montant_patient', label: 'Montant' },
  { key: 'montant_restant', label: 'Reste' },
  { key: 'actions', label: 'Actions' },
]
const rdvCols = [
  { key: 'date_heure', label: 'Date' },
  { key: 'medecin', label: 'Médecin' },
  { key: 'motif', label: 'Motif' },
  { key: 'statut', label: 'Statut' },
  { key: 'actions', label: 'Actions' },
]
const notifCols = [
  { key: 'titre', label: 'Titre' },
  { key: 'corps', label: 'Message' },
  { key: 'date_creation', label: 'Date' },
]
const soinsCols = [
  { key: 'titre', label: 'Titre' },
  { key: 'frequence', label: 'Fréquence' },
  { key: 'statut', label: 'Statut' },
  { key: 'date_debut', label: 'Début' },
]

function openTab(id) {
  activeTab.value = id
}

function goRegister() {
  router.push({ path: '/register', query: { redirect: '/', tab: activeTab.value } })
}

async function loadData() {
  if (!isPatient.value) return
  const patientId = authStore.patientId
  if (!patientId) return
  loading.value = true
  try {
    const [consRes, labRes, prescRes, factRes, rdvRes, convRes, notifRes, soinsRes, medRes, srvRes] = await Promise.all([
      clinicalApi.getConsultationsPatient(patientId),
      laboratoryApi.getDemandesPatient(patientId),
      prescriptionsApi.getPrescriptionsPatient(patientId),
      billingApi.getFacturesPatient(patientId),
      appointmentsApi.getRdvPatient(patientId),
      messagingApi.getConversations(),
      notificationsApi.getNotifications(),
      clinicalApi.getPlansSoins(patientId),
      authApi.getMedecins(),
      hospitalApi.getServices(),
    ])
    consultations.value = consRes.data
    examens.value = labRes.data
    prescriptions.value = prescRes.data
    factures.value = factRes.data
    rendezVous.value = rdvRes.data
    conversations.value = convRes.data
    notifications.value = notifRes.data
    plansSoins.value = soinsRes.data
    medecins.value = medRes.data
    services.value = srvRes.data
    if (conversations.value.length) {
      activeConvId.value = conversations.value[0].id
      const msgRes = await messagingApi.getMessages(activeConvId.value)
      messages.value = msgRes.data
    }
  } catch (e) {
    console.error(getApiError(e))
  } finally {
    loading.value = false
  }
}

async function downloadPdf(resultatId) {
  if (!isPatient.value) return promptLogin('labo')
  try {
    const res = await laboratoryApi.downloadResultatPdf(resultatId)
    await downloadBlob(res, `resultat-${resultatId}.pdf`)
  } catch (e) {
    console.error(getApiError(e))
  }
}

async function downloadFacture(id) {
  if (!isPatient.value) return promptLogin('factures')
  try {
    const res = await billingApi.downloadFacturePdf(id)
    await downloadBlob(res, `facture-${id}.pdf`)
  } catch (e) {
    console.error(getApiError(e))
  }
}

function openPaiement(row) {
  if (!isPatient.value) return promptLogin('factures')
  paiementFacture.value = row
  formPaiement.value = {
    montant: String(row.montant_restant ?? ''),
    mode_paiement: 'MTN',
    numero_telephone: '',
  }
  msgPaiement.value = ''
}

async function submitPaiement() {
  if (!paiementFacture.value) return
  submittingPaiement.value = true
  msgPaiement.value = ''
  try {
    const payload = {
      facture_id: paiementFacture.value.id,
      montant: Number(formPaiement.value.montant),
      mode_paiement: formPaiement.value.mode_paiement,
      numero_telephone: formPaiement.value.numero_telephone,
      operateur: formPaiement.value.mode_paiement,
    }
    const apiCall = ['MTN', 'AIRTEL'].includes(formPaiement.value.mode_paiement)
      ? billingApi.createPaiementMobileMoney
      : billingApi.createPaiement
    const { data } = await apiCall(payload)
    msgTypePaiement.value = 'success'
    msgPaiement.value = data.message || 'Paiement enregistré'
    paiementFacture.value = null
    await loadData()
  } catch (e) {
    msgTypePaiement.value = 'error'
    msgPaiement.value = getApiError(e)
  } finally {
    submittingPaiement.value = false
  }
}

async function annulerRdv(id) {
  if (!isPatient.value) return promptLogin('rdv')
  try {
    await appointmentsApi.annulerRdv(id)
    await loadData()
  } catch (e) {
    console.error(getApiError(e))
  }
}

async function prendreRdv() {
  if (!isPatient.value) return promptLogin('rdv')
  const patientId = authStore.patientId
  if (!patientId) return
  submittingRdv.value = true
  msgRdv.value = ''
  try {
    await appointmentsApi.createRendezVous({
      patient_id: patientId,
      medecin_id: Number(formRdv.value.medecin_id),
      service_id: Number(formRdv.value.service_id),
      date_heure: new Date(formRdv.value.date_heure).toISOString(),
      motif: formRdv.value.motif,
    })
    msgTypeRdv.value = 'success'
    msgRdv.value = 'Rendez-vous confirmé'
    formRdv.value = { medecin_id: '', service_id: '', date_heure: '', motif: '' }
    await loadData()
  } catch (e) {
    msgTypeRdv.value = 'error'
    msgRdv.value = getApiError(e)
  } finally {
    submittingRdv.value = false
  }
}

async function envoyerMessage() {
  if (!isPatient.value) return promptLogin('messages')
  if (!activeConvId.value || !newMessage.value.trim()) return
  try {
    await messagingApi.sendMessage(activeConvId.value, { contenu: newMessage.value })
    newMessage.value = ''
    const msgRes = await messagingApi.getMessages(activeConvId.value)
    messages.value = msgRes.data
  } catch (e) {
    console.error(getApiError(e))
  }
}

watch(activeTab, (tab) => {
  router.replace({ query: { ...route.query, tab } })
})

watch(() => authStore.isAuthenticated, () => loadData())

watch(() => route.query.tab, (tab) => {
  if (tab && typeof tab === 'string') activeTab.value = tab
})

onMounted(loadData)
</script>

<style scoped>
:deep(.ig-btn-primary) {
  --theme-from: #0c4a6e;
  --theme-to: #0284c7;
}
</style>
