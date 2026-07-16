<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <AlertBanner v-if="loadError" :message="loadError" type="error" class="mb-2" />

    <IgFeed v-if="activeTab === 'overview'">
      <StatGrid>
        <StatCard label="Patients" :value="patients.length" :image="STAT_IMAGES.patients" />
        <StatCard label="Admissions" :value="admissions.length" :image="STAT_IMAGES.admissions" />
        <StatCard label="Lits occupés" :value="admissions.filter(a => a.lit_numero).length" :image="STAT_IMAGES.hospitalWide" />
        <StatCard label="Médecins" :value="medecins.length" :image="STAT_IMAGES.consultations" />
      </StatGrid>
    </IgFeed>

    <IgFeed v-if="activeTab === 'patients'" title="Patients" subtitle="Registre complet">
      <DataTable :columns="patientCols" :rows="patients" :loading="loading">
        <template #cell-actions="{ row }">
          <button type="button" class="ig-link" @click="startEditPatient(row)">Modifier</button>
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'admissions'" title="Admissions" subtitle="Hospitalisations en cours">
      <DataTable :columns="admissionCols" :rows="admissions" :loading="loading">
        <template #cell-actions="{ row }">
          <button type="button" class="ig-link ig-link-success" @click="startSortie(row)">Sortie</button>
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'new-patient'" title="Nouveau patient" subtitle="Enregistrement dossier">
      <FormCard title="Nouveau patient" :image="STAT_IMAGES.patients">
        <AlertBanner :message="msgPatient" :type="msgType" />
        <form @submit.prevent="submitPatient" class="ig-stack">
          <FormField label="Nom *" v-model="formPatient.nom" required />
          <FormField label="Prénom *" v-model="formPatient.prenom" required />
          <FormField label="Date de naissance *" v-model="formPatient.date_naissance" type="date" required />
          <FormField label="Téléphone *" v-model="formPatient.telephone" required />
          <FormField label="Adresse *" v-model="formPatient.adresse" type="textarea" required />
          <FormField label="Email" v-model="formPatient.email" type="email" />
          <FormField label="Mutuelle" v-model="formPatient.mutuelle" />
          <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">
            {{ submitting ? 'Enregistrement...' : 'Créer le patient' }}
          </button>
        </form>
      </FormCard>
    </IgFeed>

    <IgFeed v-if="activeTab === 'edit-patient'" title="Modifier patient" subtitle="Mise à jour du dossier">
      <FormCard title="Modifier patient" :image="STAT_IMAGES.patients">
        <AlertBanner :message="msgEdit" :type="msgTypeEdit" />
        <form @submit.prevent="submitEditPatient" class="ig-stack">
          <FormField label="Patient *" v-model="editPatientId" type="select" :options="patientOptions" required />
          <template v-if="editPatientId">
            <FormField label="Nom *" v-model="formEdit.nom" required />
            <FormField label="Prénom *" v-model="formEdit.prenom" required />
            <FormField label="Date de naissance *" v-model="formEdit.date_naissance" type="date" required />
            <FormField label="Téléphone *" v-model="formEdit.telephone" required />
            <FormField label="Adresse *" v-model="formEdit.adresse" type="textarea" required />
            <FormField label="Email" v-model="formEdit.email" type="email" />
            <FormField label="Mutuelle" v-model="formEdit.mutuelle" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">
              {{ submitting ? 'Mise à jour...' : 'Enregistrer les modifications' }}
            </button>
          </template>
        </form>
      </FormCard>
    </IgFeed>

    <IgFeed v-if="activeTab === 'new-admission'" title="Nouvelle admission" subtitle="Hospitalisation">
      <FormCard title="Nouvelle admission" :image="STAT_IMAGES.admissions">
        <AlertBanner :message="msgAdmission" :type="msgTypeAdmission" />
        <div v-if="!services.length" class="mb-3 p-3 rounded-lg bg-red-50 text-red-800 text-sm">
          Aucun service en base. Lancez : <code class="bg-red-100 px-1 rounded">python manage.py seed_demo_users</code>
          puis rafraîchissez (F5).
        </div>
        <div v-else class="mb-3 p-3 rounded-lg bg-slate-50 text-slate-600 text-sm">
          {{ services.length }} service(s) · {{ totalLitsLibres }} lit(s) libre(s) au total
          <span v-if="formAdmission.service_id && lits.length"> · {{ lits.length }} lit(s) dans ce service</span>
        </div>
        <div v-if="!medecins.length" class="mb-3 p-3 rounded-lg bg-amber-50 text-amber-900 text-sm">
          Aucun médecin — lancez <code class="bg-amber-100 px-1 rounded">python manage.py seed_demo_users</code>
        </div>
        <div v-if="!patientOptions.length" class="mb-3 p-3 rounded-lg bg-amber-50 text-amber-900 text-sm">
          Créez d'abord un patient via l'onglet « + Patient ».
        </div>
        <form @submit.prevent="submitAdmission" class="ig-stack">
          <FormField label="Patient *" v-model="formAdmission.patient_id" type="select" :options="patientOptions" required />
          <FormField label="Service *" v-model="formAdmission.service_id" type="select" :options="serviceOptions" required />
          <FormField label="Lit *" v-model="formAdmission.lit_id" type="select" :options="litOptions" required />
          <FormField label="Médecin référent *" v-model="formAdmission.medecin_referent_id" type="select" :options="medecinOptions" required />
          <FormField label="Sortie prévue *" v-model="formAdmission.date_previsionnelle_sortie" type="date" required />
          <FormField label="Motif *" v-model="formAdmission.motif_hospitalisation" type="textarea" required />
          <FormField label="Type" v-model="formAdmission.type_admission" type="select" :options="typeAdmissionOptions" />
          <button type="submit" :disabled="submitting || !services.length || !medecins.length || !patientOptions.length" class="ig-btn ig-btn-primary w-full py-2.5">
            {{ submitting ? 'Admission...' : 'Admettre' }}
          </button>
        </form>
      </FormCard>
    </IgFeed>

    <IgFeed v-if="activeTab === 'sortie'" title="Sortie patient" subtitle="Libération du lit">
      <FormCard title="Sortie patient" :image="STAT_IMAGES.hospitalWide">
        <AlertBanner :message="msgSortie" :type="msgTypeSortie" />
        <form @submit.prevent="submitSortie" class="ig-stack">
          <FormField label="Admission *" v-model="formSortie.admission_id" type="select" :options="admissionOptions" required />
          <FormField label="Notes" v-model="formSortie.notes" type="textarea" />
          <button type="submit" :disabled="submitting || !admissionOptions.length" class="ig-btn ig-btn-danger w-full py-2.5">
            {{ submitting ? 'Traitement...' : 'Enregistrer la sortie' }}
          </button>
        </form>
      </FormCard>
    </IgFeed>

    <IgFeed v-if="activeTab === 'caisse'" title="Caisse / Paiements" subtitle="Encaissement avant consultation">
      <div class="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6 mb-6">
        <FormCard title="Patient sans RDV" :image="STAT_IMAGES.patients">
          <form @submit.prevent="submitWalkInInvoice" class="ig-stack">
            <FormField label="Patient *" v-model="walkInPatientId" type="select" :options="patientOptions" required />
            <button type="submit" :disabled="submitting || !walkInPatientId" class="ig-btn ig-btn-secondary w-full py-2">
              {{ submitting ? 'Création...' : 'Créer facture consultation' }}
            </button>
          </form>
        </FormCard>
        <div class="flex flex-wrap items-center gap-3 self-end">
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-red-100 text-red-800">
            {{ pendingInvoices.length }} en attente
          </span>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
            {{ paidInvoices.length }} payé(s)
          </span>
          <button type="button" class="ig-btn ig-btn-secondary text-sm" @click="loadInvoices">
            {{ loadingInvoices ? 'Actualisation...' : 'Actualiser' }}
          </button>
        </div>
      </div>
      <AlertBanner :message="msgCaisse" :type="msgTypeCaisse" />
      <DataTable :columns="invoiceCols" :rows="invoices" :loading="loadingInvoices">
        <template #cell-status="{ row }">
          <span
            class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold"
            :class="row.status === 'PAID' ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'"
          >
            {{ row.status === 'PAID' ? 'Payé' : 'En attente de règlement' }}
          </span>
        </template>
        <template #cell-amount="{ row }">
          {{ formatAmount(row.amount) }}
        </template>
        <template #cell-actions="{ row }">
          <button
            v-if="row.status === 'PENDING'"
            type="button"
            class="ig-btn ig-btn-primary text-xs px-3 py-1.5"
            @click="openPayModal(row)"
          >
            Encaisser
          </button>
          <span v-else class="text-xs text-emerald-700 font-medium">Débloqué</span>
        </template>
      </DataTable>
    </IgFeed>

    <Teleport to="body">
      <div
        v-if="payModalOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
        @click.self="closePayModal"
      >
        <div class="w-full max-w-md rounded-2xl bg-white shadow-xl border border-slate-200 p-6">
          <h3 class="text-lg font-semibold text-slate-900 mb-1">Encaisser le patient</h3>
          <p class="text-sm text-slate-600 mb-4">
            {{ selectedInvoice?.patient_nom }} — {{ formatAmount(selectedInvoice?.amount) }}
          </p>
          <form @submit.prevent="submitPayment" class="ig-stack">
            <FormField
              label="Mode de paiement *"
              v-model="payForm.payment_method"
              type="select"
              :options="paymentMethodOptions"
              required
            />
            <FormField
              v-if="payForm.payment_method === 'MOBILE_MONEY'"
              label="Téléphone Mobile Money *"
              v-model="payForm.numero_telephone"
              placeholder="ex: 06 123 45 67"
              required
            />
            <div class="flex gap-3 pt-2">
              <button type="button" class="ig-btn ig-btn-secondary flex-1" @click="closePayModal">Annuler</button>
              <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary flex-1">
                {{ submitting ? 'Validation...' : 'Valider l\'encaissement' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Teleport>

    <IgFeed v-if="activeTab === 'rdv'" title="Rendez-vous" subtitle="Planification et suivi">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FormCard title="Nouveau rendez-vous" :image="STAT_IMAGES.rdv">
          <AlertBanner :message="msgRdv" :type="msgTypeRdv" />
          <form @submit.prevent="submitRdv" class="ig-stack">
            <FormField label="Patient *" v-model="formRdv.patient_id" type="select" :options="patientOptions" required />
            <FormField label="Médecin *" v-model="formRdv.medecin_id" type="select" :options="medecinOptions" required />
            <FormField label="Service *" v-model="formRdv.service_id" type="select" :options="serviceOptions" required />
            <FormField label="Date et heure *" v-model="formRdv.date_heure" type="datetime-local" required />
            <FormField label="Motif *" v-model="formRdv.motif" type="textarea" required />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">
              {{ submitting ? 'Planification...' : 'Confirmer le rendez-vous' }}
            </button>
          </form>
        </FormCard>
        <FormCard title="Disponibilité médecin" :image="STAT_IMAGES.consultations">
          <form @submit.prevent="submitDisponibilite" class="ig-stack">
            <FormField label="Médecin *" v-model="formDispo.medecin_id" type="select" :options="medecinOptions" required />
            <FormField label="Service *" v-model="formDispo.service_id" type="select" :options="serviceOptions" required />
            <FormField label="Début *" v-model="formDispo.date_debut" type="datetime-local" required />
            <FormField label="Fin *" v-model="formDispo.date_fin" type="datetime-local" required />
            <FormField label="Durée créneau (min)" v-model="formDispo.duree_creneau_minutes" type="number" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-secondary w-full py-2.5">Ajouter créneaux</button>
          </form>
        </FormCard>
      </div>
      <div class="mt-6">
        <h3 class="font-semibold mb-3">Rendez-vous à venir</h3>
        <DataTable :columns="rdvCols" :rows="rendezVous" :loading="loadingRdv" />
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
import { clinicalApi, hospitalApi, authApi, appointmentsApi, secretariatApi, getApiError } from '../../api/modules'
import { STAT_IMAGES } from '../../config/branding'

const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Accueil' },
  { id: 'patients', label: 'Patients' },
  { id: 'admissions', label: 'Admissions' },
  { id: 'caisse', label: 'Caisse / Paiements' },
  { id: 'rdv', label: 'RDV' },
  { id: 'new-patient', label: '+ Patient' },
  { id: 'edit-patient', label: 'Modifier' },
  { id: 'new-admission', label: '+ Admission' },
  { id: 'sortie', label: 'Sortie' },
]

const patients = ref([])
const admissions = ref([])
const services = ref([])
const lits = ref([])
const medecins = ref([])
const totalLitsLibres = ref(0)
const loading = ref(false)
const submitting = ref(false)
const loadError = ref('')
const msgPatient = ref('')
const msgAdmission = ref('')
const msgEdit = ref('')
const msgSortie = ref('')
const msgType = ref('success')
const msgTypeAdmission = ref('success')
const msgTypeEdit = ref('success')
const msgTypeSortie = ref('success')

const editPatientId = ref('')
const formPatient = ref({ nom: '', prenom: '', date_naissance: '', telephone: '', adresse: '', email: '', mutuelle: '' })
const formEdit = ref({ nom: '', prenom: '', date_naissance: '', telephone: '', adresse: '', email: '', mutuelle: '' })
const formAdmission = ref({
  patient_id: '', service_id: '', lit_id: '', medecin_referent_id: '',
  date_previsionnelle_sortie: '', motif_hospitalisation: '', type_admission: 'PROGRAMMEE',
})
const formSortie = ref({ admission_id: '', version: 0, notes: '' })
const formRdv = ref({ patient_id: '', medecin_id: '', service_id: '', date_heure: '', motif: '' })
const formDispo = ref({ medecin_id: '', service_id: '', date_debut: '', date_fin: '', duree_creneau_minutes: 30 })
const rendezVous = ref([])
const loadingRdv = ref(false)
const msgRdv = ref('')
const msgTypeRdv = ref('success')

const invoices = ref([])
const loadingInvoices = ref(false)
const msgCaisse = ref('')
const msgTypeCaisse = ref('success')
const payModalOpen = ref(false)
const selectedInvoice = ref(null)
const payForm = ref({ payment_method: 'CASH', numero_telephone: '' })
const walkInPatientId = ref('')

const paymentMethodOptions = [
  { value: 'CASH', label: 'Espèces' },
  { value: 'MOBILE_MONEY', label: 'Mobile Money' },
  { value: 'CARD', label: 'Carte bancaire' },
]

const pendingInvoices = computed(() => invoices.value.filter(i => i.status === 'PENDING'))
const paidInvoices = computed(() => invoices.value.filter(i => i.status === 'PAID'))

const formatAmount = (amount) => {
  const n = Number(amount || 0)
  return `${n.toLocaleString('fr-FR')} FCFA`
}

const invoiceCols = [
  { key: 'patient_nom', label: 'Patient' },
  { key: 'patient_dossier', label: 'N° Dossier' },
  { key: 'libelle', label: 'Motif' },
  { key: 'amount', label: 'Montant' },
  { key: 'status', label: 'Statut' },
  { key: 'created_at', label: 'Créé le' },
  { key: 'actions', label: 'Actions' },
]

const typeAdmissionOptions = [
  { value: 'PROGRAMMEE', label: 'Programmée' },
  { value: 'URGENCE', label: 'Urgence' },
  { value: 'TRANSFERT', label: 'Transfert' },
]

const patientOptions = computed(() => patients.value.map(p => ({ value: p.id, label: `${p.nom} ${p.prenom} (${p.numero_dossier})` })))
const serviceOptions = computed(() => services.value.map(s => ({ value: s.id, label: `${s.code} — ${s.nom}` })))
const litOptions = computed(() => lits.value.map(l => ({
  value: l.id,
  label: l.chambre_numero ? `Ch. ${l.chambre_numero} — Lit ${l.numero}` : `Lit ${l.numero}`,
})))
const medecinOptions = computed(() => medecins.value.map(m => ({
  value: m.id,
  label: m.first_name ? `Dr ${m.first_name} ${m.last_name}` : m.username,
})))
const admissionOptions = computed(() => admissions.value.map(a => ({
  value: a.id,
  label: `#${a.id} — ${a.patient_nom} · ${a.service_nom}`,
  version: a.version ?? 0,
})))

const patientCols = [
  { key: 'numero_dossier', label: 'N° Dossier' },
  { key: 'nom', label: 'Nom' },
  { key: 'prenom', label: 'Prénom' },
  { key: 'telephone', label: 'Téléphone' },
  { key: 'actions', label: 'Actions' },
]
const admissionCols = [
  { key: 'patient_nom', label: 'Patient' },
  { key: 'service_nom', label: 'Service' },
  { key: 'lit_numero', label: 'Lit' },
  { key: 'date_entree', label: 'Entrée' },
  { key: 'date_previsionnelle_sortie', label: 'Sortie prév.' },
  { key: 'actions', label: 'Actions' },
]
const rdvCols = [
  { key: 'date_heure', label: 'Date' },
  { key: 'patient', label: 'Patient' },
  { key: 'medecin', label: 'Médecin' },
  { key: 'motif', label: 'Motif' },
  { key: 'statut', label: 'Statut' },
]

const loadHospital = async () => {
  try {
    const [s, allLits] = await Promise.all([
      hospitalApi.getServices(),
      hospitalApi.getLitsLibres(),
    ])
    services.value = s.data
    totalLitsLibres.value = allLits.data.length
  } catch (e) {
    loadError.value = getApiError(e)
  }
}

const loadLitsForService = async (serviceId) => {
  formAdmission.value.lit_id = ''
  lits.value = []
  if (!serviceId) return
  try {
    lits.value = (await hospitalApi.getLitsLibres(Number(serviceId))).data
    if (!lits.value.length) {
      msgAdmission.value = 'Aucun lit libre dans ce service.'
      msgTypeAdmission.value = 'error'
    }
  } catch (e) {
    msgAdmission.value = getApiError(e)
    msgTypeAdmission.value = 'error'
  }
}

const load = async () => {
  loading.value = true
  loadError.value = ''
  const results = await Promise.allSettled([
    clinicalApi.getPatients(),
    clinicalApi.getAdmissionsActives(),
    hospitalApi.getServices(),
    authApi.getMedecins(),
    hospitalApi.getLitsLibres(),
  ])
  if (results[0].status === 'fulfilled') patients.value = results[0].value.data
  else loadError.value = getApiError(results[0].reason)

  if (results[1].status === 'fulfilled') {
    admissions.value = results[1].value.data.map(x => ({ ...x, date_entree: x.date_entree?.slice(0, 10) }))
  }

  if (results[2].status === 'fulfilled') services.value = results[2].value.data
  else if (!loadError.value) loadError.value = getApiError(results[2].reason)

  if (results[3].status === 'fulfilled') medecins.value = results[3].value.data

  if (results[4].status === 'fulfilled') totalLitsLibres.value = results[4].value.data.length

  loading.value = false

  if (formAdmission.value.service_id) {
    await loadLitsForService(formAdmission.value.service_id)
  }
}

watch(() => formAdmission.value.service_id, loadLitsForService)

watch(editPatientId, async (id) => {
  if (!id) return
  try {
    const { data } = await clinicalApi.getPatient(id)
    formEdit.value = {
      nom: data.nom,
      prenom: data.prenom,
      date_naissance: data.date_naissance,
      telephone: data.telephone,
      adresse: data.adresse,
      email: data.email || '',
      mutuelle: data.mutuelle || '',
    }
  } catch (e) {
    msgEdit.value = getApiError(e)
    msgTypeEdit.value = 'error'
  }
})

watch(() => formSortie.value.admission_id, (id) => {
  const adm = admissionOptions.value.find(a => String(a.value) === String(id))
  if (adm) formSortie.value.version = adm.version
})

watch(activeTab, async (tab) => {
  if (tab === 'new-admission') {
    await loadHospital()
    if (formAdmission.value.service_id) await loadLitsForService(formAdmission.value.service_id)
  } else if (['overview', 'patients', 'admissions', 'sortie', 'rdv', 'caisse'].includes(tab)) {
    load()
    if (tab === 'rdv') loadRdvList()
    if (tab === 'caisse') loadInvoices()
  }
})

const loadInvoices = async () => {
  loadingInvoices.value = true
  msgCaisse.value = ''
  try {
    const { data } = await secretariatApi.getInvoices({ page_size: 200 })
    invoices.value = data.map(inv => ({
      ...inv,
      created_at: inv.created_at?.slice(0, 16).replace('T', ' '),
    }))
  } catch (e) {
    msgTypeCaisse.value = 'error'
    msgCaisse.value = getApiError(e)
  } finally {
    loadingInvoices.value = false
  }
}

const openPayModal = (row) => {
  selectedInvoice.value = row
  payForm.value = { payment_method: 'CASH', numero_telephone: '' }
  payModalOpen.value = true
}

const closePayModal = () => {
  payModalOpen.value = false
  selectedInvoice.value = null
}

const submitWalkInInvoice = async () => {
  if (!walkInPatientId.value) return
  submitting.value = true
  msgCaisse.value = ''
  try {
    await secretariatApi.createInvoice({ patient_id: Number(walkInPatientId.value) })
    msgTypeCaisse.value = 'success'
    msgCaisse.value = 'Facture créée — en attente d\'encaissement'
    walkInPatientId.value = ''
    await loadInvoices()
  } catch (e) {
    msgTypeCaisse.value = 'error'
    msgCaisse.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

const submitPayment = async () => {
  if (!selectedInvoice.value) return
  submitting.value = true
  msgCaisse.value = ''
  try {
    await secretariatApi.payInvoice(selectedInvoice.value.id, {
      payment_method: payForm.value.payment_method,
      numero_telephone: payForm.value.numero_telephone,
    })
    msgTypeCaisse.value = 'success'
    msgCaisse.value = `Paiement validé — ${selectedInvoice.value.patient_nom} débloqué pour le médecin`
    closePayModal()
    await loadInvoices()
  } catch (e) {
    msgTypeCaisse.value = 'error'
    msgCaisse.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

const loadRdvList = async () => {
  loadingRdv.value = true
  rendezVous.value = []
  try {
    const all = []
    for (const p of patients.value.slice(0, 20)) {
      const { data } = await appointmentsApi.getRdvPatient(p.id)
      all.push(...data)
    }
    rendezVous.value = all.sort((a, b) => String(b.date_heure).localeCompare(String(a.date_heure)))
  } catch (e) {
    msgRdv.value = getApiError(e)
    msgTypeRdv.value = 'error'
  } finally {
    loadingRdv.value = false
  }
}

const submitRdv = async () => {
  submitting.value = true
  msgRdv.value = ''
  try {
    const dt = new Date(formRdv.value.date_heure)
    await appointmentsApi.createRendezVous({
      patient_id: Number(formRdv.value.patient_id),
      medecin_id: Number(formRdv.value.medecin_id),
      service_id: Number(formRdv.value.service_id),
      date_heure: dt.toISOString(),
      motif: formRdv.value.motif,
    })
    msgTypeRdv.value = 'success'
    msgRdv.value = 'Rendez-vous confirmé — email envoyé au patient'
    formRdv.value.motif = ''
    await loadRdvList()
  } catch (e) {
    msgTypeRdv.value = 'error'
    msgRdv.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

const submitDisponibilite = async () => {
  submitting.value = true
  try {
    await appointmentsApi.createDisponibilite({
      medecin_id: Number(formDispo.value.medecin_id),
      service_id: Number(formDispo.value.service_id),
      date_debut: new Date(formDispo.value.date_debut).toISOString(),
      date_fin: new Date(formDispo.value.date_fin).toISOString(),
      duree_creneau_minutes: Number(formDispo.value.duree_creneau_minutes) || 30,
    })
    msgTypeRdv.value = 'success'
    msgRdv.value = 'Disponibilités médecin enregistrées'
  } catch (e) {
    msgTypeRdv.value = 'error'
    msgRdv.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

const startEditPatient = (row) => {
  editPatientId.value = row.id
  activeTab.value = 'edit-patient'
}

const startSortie = (row) => {
  formSortie.value.admission_id = row.id
  formSortie.value.version = row.version ?? 0
  activeTab.value = 'sortie'
}

const submitPatient = async () => {
  submitting.value = true
  msgPatient.value = ''
  try {
    const { data } = await clinicalApi.createPatient({
      ...formPatient.value,
      consentement_donnees: true,
    })
    msgType.value = 'success'
    msgPatient.value = `Patient créé — Dossier ${data.numero_dossier}`
    formPatient.value = { nom: '', prenom: '', date_naissance: '', telephone: '', adresse: '', email: '', mutuelle: '' }
    await load()
  } catch (e) {
    msgType.value = 'error'
    msgPatient.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

const submitEditPatient = async () => {
  if (!editPatientId.value) return
  submitting.value = true
  msgEdit.value = ''
  try {
    const { data } = await clinicalApi.updatePatient(editPatientId.value, formEdit.value)
    msgTypeEdit.value = 'success'
    msgEdit.value = `Dossier ${data.numero_dossier} mis à jour`
    await load()
  } catch (e) {
    msgTypeEdit.value = 'error'
    msgEdit.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

const submitAdmission = async () => {
  submitting.value = true
  msgAdmission.value = ''
  try {
    await clinicalApi.createAdmission({
      patient_id: Number(formAdmission.value.patient_id),
      service_id: Number(formAdmission.value.service_id),
      lit_id: Number(formAdmission.value.lit_id),
      medecin_referent_id: Number(formAdmission.value.medecin_referent_id),
      date_previsionnelle_sortie: formAdmission.value.date_previsionnelle_sortie,
      motif_hospitalisation: formAdmission.value.motif_hospitalisation,
      type_admission: formAdmission.value.type_admission,
    })
    msgTypeAdmission.value = 'success'
    msgAdmission.value = 'Admission créée avec succès'
    formAdmission.value.lit_id = ''
    await load()
  } catch (e) {
    msgTypeAdmission.value = 'error'
    msgAdmission.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

const submitSortie = async () => {
  submitting.value = true
  msgSortie.value = ''
  try {
    await clinicalApi.sortieAdmission(Number(formSortie.value.admission_id), {
      statut: 'SORTI',
      notes: formSortie.value.notes,
      version: Number(formSortie.value.version),
    })
    msgTypeSortie.value = 'success'
    msgSortie.value = 'Sortie enregistrée — lit libéré'
    formSortie.value = { admission_id: '', version: 0, notes: '' }
    await load()
  } catch (e) {
    msgTypeSortie.value = 'error'
    msgSortie.value = getApiError(e)
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>
