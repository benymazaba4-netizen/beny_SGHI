<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <IgFeed v-if="activeTab === 'overview'">
      <StatGrid>
        <StatCard label="Recettes jour" :value="formatFCFA(kpis.recettes_jour)" :image="STAT_IMAGES.factures" />
        <StatCard label="Recettes mois" :value="formatFCFA(kpis.recettes_mois)" :image="STAT_IMAGES.journal" />
        <StatCard label="Écritures journal" :value="journal.length" :image="STAT_IMAGES.factures" />
        <StatCard label="Admissions jour" :value="kpis.patients_admis_jour" :image="STAT_IMAGES.admissions" />
      </StatGrid>
    </IgFeed>

    <IgFeed v-if="activeTab === 'journal'" title="Journal comptable" subtitle="Écritures immuables">
      <DataTable :columns="journalCols" :rows="journal" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'factures'" title="Factures" subtitle="Recherche par patient">
      <div class="flex flex-col sm:flex-row gap-3 mb-4">
        <FormField label="Patient" v-model="patientIdSearch" type="select" :options="patientOptions" class="flex-1" />
        <button type="button" @click="searchFactures" class="ig-btn ig-btn-primary px-6 self-end">Rechercher</button>
      </div>
      <DataTable title="Factures patient" :columns="factureCols" :rows="factures" :loading="loadingFactures">
        <template #cell-montant_patient="{ value }">{{ formatFCFA(value) }}</template>
        <template #cell-montant_restant="{ value }">{{ formatFCFA(value) }}</template>
        <template #cell-actions="{ row }">
          <div class="flex flex-wrap gap-2">
            <button v-if="row.statut === 'BROUILLON'" type="button" @click="doTiersPayant(row.id)" class="ig-link">Tiers-payant</button>
            <button v-if="row.statut === 'BROUILLON'" type="button" @click="doEmettre(row.id)" class="ig-link ig-link-success">Émettre</button>
            <button v-if="row.pdf_disponible" type="button" @click="doPdf(row.id)" class="ig-link">PDF</button>
          </div>
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'facturation'" title="Facturation" subtitle="Génération et paiements">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FormCard title="Générer une facture automatique" :image="STAT_IMAGES.factures">
          <AlertBanner :message="msg" :type="msgType" />
          <form @submit.prevent="genererFacture" class="ig-stack">
            <FormField label="Patient *" v-model="formFacture.patient_id" type="select" :options="patientOptions" required />
            <FormField label="Admission *" v-model="formFacture.admission_id" type="select" :options="admissionOptionsForFacture" required />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">
              {{ submitting ? 'Calcul...' : 'Générer facture' }}
            </button>
          </form>
          <div v-if="lastFacture" class="mt-4 p-4 bg-slate-50 rounded-xl text-sm border border-slate-100">
            <p class="font-medium">Facture {{ lastFacture.numero_facture }} créée</p>
            <p>Sous-total : {{ formatFCFA(lastFacture.sous_total) }}</p>
            <p>Part patient : {{ formatFCFA(lastFacture.montant_patient) }}</p>
            <div class="flex gap-2 mt-2">
              <button type="button" @click="doTiersPayant(lastFacture.id)" class="ig-btn ig-btn-secondary text-xs px-3 py-1.5">Tiers-payant</button>
              <button type="button" @click="doEmettre(lastFacture.id)" class="ig-btn ig-btn-primary text-xs px-3 py-1.5">Émettre + PDF</button>
            </div>
          </div>
        </FormCard>

        <FormCard title="Enregistrer un paiement" :image="STAT_IMAGES.journal">
          <form @submit.prevent="submitPaiement" class="ig-stack">
            <FormField label="Patient" v-model="paiementPatientId" type="select" :options="patientOptions" />
            <FormField label="Facture *" v-model="formPaiement.facture_id" type="select" :options="facturePayOptions" required />
            <FormField label="Montant (FCFA) *" v-model="formPaiement.montant" type="number" required />
            <FormField label="Mode" v-model="formPaiement.mode_paiement" type="select" :options="modeOptions" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Enregistrer paiement</button>
          </form>
        </FormCard>

        <FormCard title="Plan d'échéances" :image="STAT_IMAGES.factures">
          <AlertBanner :message="msgEcheancier" :type="msgType" />
          <form @submit.prevent="submitEcheancier" class="ig-stack">
            <FormField label="Facture *" v-model="echeancierFactureId" type="select" :options="facturePayOptions" required />
            <FormField label="Date échéance 1 *" v-model="ech1.date" type="date" required />
            <FormField label="Montant 1 (FCFA) *" v-model="ech1.montant" type="number" required />
            <FormField label="Date échéance 2" v-model="ech2.date" type="date" />
            <FormField label="Montant 2 (FCFA)" v-model="ech2.montant" type="number" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-secondary w-full py-2.5">Créer échéancier</button>
          </form>
        </FormCard>
      </div>
    </IgFeed>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import IgFeed from '../../components/layout/IgFeed.vue'
import StatGrid from '../../components/ui/StatGrid.vue'
import StatCard from '../../components/ui/StatCard.vue'
import DataTable from '../../components/ui/DataTable.vue'
import FormCard from '../../components/ui/FormCard.vue'
import FormField from '../../components/ui/FormField.vue'
import AlertBanner from '../../components/ui/AlertBanner.vue'
import { useLookups } from '../../composables/useLookups'
import { dashboardApi, billingApi, downloadBlob, getApiError } from '../../api/modules'
import { formatFCFA } from '../../config/roles'
import { STAT_IMAGES } from '../../config/branding'

const { patientOptions, admissions, loadBasics, admissionsForPatient } = useLookups()

const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble' },
  { id: 'facturation', label: 'Facturation' },
  { id: 'factures', label: 'Factures' },
  { id: 'journal', label: 'Journal' },
]

const kpis = ref({ recettes_jour: 0, recettes_mois: 0, patients_admis_jour: 0 })
const journal = ref([])
const factures = ref([])
const facturesPaiement = ref([])
const lastFacture = ref(null)
const loading = ref(false)
const loadingFactures = ref(false)
const submitting = ref(false)
const patientIdSearch = ref('')
const paiementPatientId = ref('')
const msg = ref('')
const msgType = ref('success')

const formFacture = ref({ patient_id: '', admission_id: '' })
const formPaiement = ref({ facture_id: '', montant: '', mode_paiement: 'ESPECES' })
const echeancierFactureId = ref('')
const msgEcheancier = ref('')
const ech1 = ref({ date: '', montant: '' })
const ech2 = ref({ date: '', montant: '' })
const modeOptions = [
  { value: 'ESPECES', label: 'Espèces' },
  { value: 'CARTE', label: 'Carte bancaire' },
  { value: 'MTN', label: 'MTN Mobile Money' },
  { value: 'AIRTEL', label: 'Airtel Money' },
  { value: 'VIRAMENT', label: 'Virement' },
]

const admissionOptionsForFacture = computed(() => {
  if (!formFacture.value.patient_id) return []
  return admissionsForPatient(formFacture.value.patient_id)
})

const facturePayOptions = computed(() =>
  facturesPaiement.value
    .filter(f => f.montant_restant > 0)
    .map(f => ({ value: f.id, label: `${f.numero_facture} — reste ${formatFCFA(f.montant_restant)}` })),
)

const journalCols = [
  { key: 'timestamp', label: 'Date' },
  { key: 'facture', label: 'Facture' },
  { key: 'type_operation', label: 'Opération' },
  { key: 'montant', label: 'Montant' },
]
const factureCols = [
  { key: 'numero_facture', label: 'N°' },
  { key: 'statut', label: 'Statut' },
  { key: 'montant_patient', label: 'Patient' },
  { key: 'montant_restant', label: 'Reste' },
  { key: 'actions', label: 'Actions' },
]

watch(() => formFacture.value.patient_id, () => { formFacture.value.admission_id = '' })

watch(paiementPatientId, async (pid) => {
  formPaiement.value.facture_id = ''
  facturesPaiement.value = []
  if (!pid) return
  facturesPaiement.value = (await billingApi.getFacturesPatient(pid)).data
})

onMounted(async () => {
  await loadBasics()
  try { kpis.value = (await dashboardApi.getKpis()).data } catch (e) { console.error(e) }
})

watch(activeTab, async (tab) => {
  if (tab === 'journal' && !journal.value.length) {
    loading.value = true
    try {
      const { data } = await billingApi.getJournal()
      journal.value = data.map(j => ({ ...j, timestamp: j.timestamp?.slice(0, 16), montant: formatFCFA(j.montant) }))
    } finally { loading.value = false }
  }
})

const searchFactures = async () => {
  if (!patientIdSearch.value) return
  loadingFactures.value = true
  try {
    factures.value = (await billingApi.getFacturesPatient(patientIdSearch.value)).data
  } catch { factures.value = [] }
  finally { loadingFactures.value = false }
}

const genererFacture = async () => {
  submitting.value = true
  msg.value = ''
  try {
    const { data } = await billingApi.genererFactureAuto({
      patient_id: Number(formFacture.value.patient_id),
      admission_id: Number(formFacture.value.admission_id),
    })
    lastFacture.value = data.facture
    msgType.value = 'success'
    msg.value = data.message
  } catch (e) {
    msgType.value = 'error'
    msg.value = getApiError(e)
  } finally { submitting.value = false }
}

const doTiersPayant = async (id) => {
  try {
    const { data } = await billingApi.appliquerTiersPayant(id)
    msgType.value = 'success'
    msg.value = data.message
    if (lastFacture.value?.id === id) lastFacture.value = data.facture
  } catch (e) { msg.value = getApiError(e); msgType.value = 'error' }
}

const doEmettre = async (id) => {
  try {
    const { data } = await billingApi.emettreFacture(id)
    msgType.value = 'success'
    msg.value = data.message
    if (lastFacture.value?.id === id) lastFacture.value = data.facture
  } catch (e) { msg.value = getApiError(e); msgType.value = 'error' }
}

const doPdf = async (id) => {
  try {
    const res = await billingApi.downloadFacturePdf(id)
    await downloadBlob(res, `facture_${id}.pdf`)
  } catch { msg.value = 'PDF non disponible'; msgType.value = 'error' }
}

const submitPaiement = async () => {
  submitting.value = true
  try {
    const { data } = await billingApi.createPaiement({
      facture_id: Number(formPaiement.value.facture_id),
      montant: Number(formPaiement.value.montant),
      mode_paiement: formPaiement.value.mode_paiement,
    })
    msgType.value = 'success'
    msg.value = data.message
    if (paiementPatientId.value) {
      facturesPaiement.value = (await billingApi.getFacturesPatient(paiementPatientId.value)).data
    }
  } catch (e) {
    msgType.value = 'error'
    msg.value = getApiError(e)
  } finally { submitting.value = false }
}

const submitEcheancier = async () => {
  if (!echeancierFactureId.value) return
  submitting.value = true
  msgEcheancier.value = ''
  try {
    const echeances = [{ date_echeance: ech1.value.date, montant: Number(ech1.value.montant) }]
    if (ech2.value.date && ech2.value.montant) {
      echeances.push({ date_echeance: ech2.value.date, montant: Number(ech2.value.montant) })
    }
    const { data } = await billingApi.createEcheancier(Number(echeancierFactureId.value), { echeances })
    msgType.value = 'success'
    msgEcheancier.value = data.message
  } catch (e) {
    msgType.value = 'error'
    msgEcheancier.value = getApiError(e)
  } finally { submitting.value = false }
}
</script>
