<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <IgFeed v-if="activeTab === 'overview'">
      <StatGrid>
        <StatCard label="Consultations" :value="consultations.length" :image="STAT_IMAGES.consultations" />
        <StatCard label="Examens" :value="examens.length" :image="STAT_IMAGES.examens" />
        <StatCard label="Factures" :value="factures.length" :image="STAT_IMAGES.factures" />
        <StatCard label="Prescriptions" :value="prescriptions.length" :image="STAT_IMAGES.prescriptions" />
      </StatGrid>
    </IgFeed>

    <IgFeed v-if="activeTab === 'dossier'" title="Mon dossier médical" subtitle="Historique des consultations">
      <DataTable :columns="consultCols" :rows="consultations" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'labo'" title="Résultats laboratoire" subtitle="Examens et téléchargements PDF">
      <DataTable :columns="laboCols" :rows="examens" :loading="loading">
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
    </IgFeed>

    <IgFeed v-if="activeTab === 'ordonnances'" title="Ordonnances" subtitle="Prescriptions en cours">
      <DataTable :columns="prescCols" :rows="prescriptions" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'factures'" title="Mes factures" subtitle="Paiements et soldes">
      <DataTable :columns="factureCols" :rows="factures" :loading="loading">
        <template #cell-montant_patient="{ value }">{{ formatFCFA(value) }}</template>
        <template #cell-montant_restant="{ value }">{{ formatFCFA(value) }}</template>
        <template #cell-actions="{ row }">
          <button v-if="row.pdf_disponible" type="button" class="ig-link" @click="downloadFacture(row.id)">
            PDF
          </button>
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'rdv'" title="Mes rendez-vous" subtitle="Prise de rendez-vous et annulation">
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
    </IgFeed>

    <IgFeed v-if="activeTab === 'messages'" title="Messages" subtitle="Conversation avec votre médecin">
      <FormCard title="Messagerie sécurisée" :image="STAT_IMAGES.consultations" class="mb-6">
        <div v-if="conversations.length" class="space-y-4">
          <div v-for="msg in messages" :key="msg.id" class="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <strong class="text-teal-800">{{ msg.expediteur }}</strong>
            <p class="text-sm text-slate-600 mt-1">{{ msg.contenu }}</p>
          </div>
          <div class="flex gap-2">
            <input v-model="newMessage" class="flex-1 border border-slate-200 rounded-xl px-3 py-2.5 focus:ring-2 focus:ring-teal-500/30" placeholder="Votre message..." />
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
    </IgFeed>

    <IgFeed v-if="activeTab === 'notifications'" title="Notifications" subtitle="Rappels et alertes">
      <DataTable :columns="notifCols" :rows="notifications" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'soins'" title="Plan de soins" subtitle="Suivi infirmier">
      <DataTable :columns="soinsCols" :rows="plansSoins" :loading="loading" />
    </IgFeed>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import IgFeed from '../../components/layout/IgFeed.vue'
import StatGrid from '../../components/ui/StatGrid.vue'
import StatCard from '../../components/ui/StatCard.vue'
import DataTable from '../../components/ui/DataTable.vue'
import FormCard from '../../components/ui/FormCard.vue'
import FormField from '../../components/ui/FormField.vue'
import AlertBanner from '../../components/ui/AlertBanner.vue'
import EmptyState from '../../components/ui/EmptyState.vue'
import { useAuthStore } from '../../stores/auth'
import { clinicalApi, laboratoryApi, prescriptionsApi, billingApi, appointmentsApi, messagingApi, notificationsApi, authApi, hospitalApi, downloadBlob, getApiError } from '../../api/modules'
import { formatFCFA } from '../../config/roles'
import { STAT_IMAGES } from '../../config/branding'

const authStore = useAuthStore()
const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble' },
  { id: 'dossier', label: 'Dossier' },
  { id: 'labo', label: 'Laboratoire' },
  { id: 'ordonnances', label: 'Ordonnances' },
  { id: 'factures', label: 'Factures' },
  { id: 'soins', label: 'Soins' },
  { id: 'rdv', label: 'RDV' },
  { id: 'messages', label: 'Messages' },
  { id: 'notifications', label: 'Alertes' },
]

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

const medecinOptions = computed(() => medecins.value.map(m => ({
  value: m.id,
  label: m.first_name ? `Dr ${m.first_name} ${m.last_name}` : m.username,
})))
const serviceOptions = computed(() => services.value.map(s => ({
  value: s.id,
  label: `${s.code} — ${s.nom}`,
})))
const loading = ref(false)

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

async function loadData() {
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
  try {
    const res = await laboratoryApi.downloadResultatPdf(resultatId)
    await downloadBlob(res, `resultat-${resultatId}.pdf`)
  } catch (e) {
    console.error(getApiError(e))
  }
}

async function downloadFacture(id) {
  try {
    const res = await billingApi.downloadFacturePdf(id)
    await downloadBlob(res, `facture-${id}.pdf`)
  } catch (e) {
    console.error(getApiError(e))
  }
}

async function annulerRdv(id) {
  try {
    await appointmentsApi.annulerRdv(id)
    await loadData()
  } catch (e) {
    console.error(getApiError(e))
  }
}

async function prendreRdv() {
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

onMounted(loadData)
</script>
