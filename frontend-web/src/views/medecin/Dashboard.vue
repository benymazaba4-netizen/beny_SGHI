<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <IgFeed v-if="activeTab === 'overview'">
      <StatGrid>
        <StatCard label="Patients" :value="patients.length" :image="STAT_IMAGES.patients" />
        <StatCard label="Admissions actives" :value="admissions.length" :image="STAT_IMAGES.admissions" />
        <StatCard label="Alertes doses" :value="alertesDoses.length" :image="STAT_IMAGES.alertes" />
        <StatCard label="Examens en cours" :value="demandesLabo.length" :image="STAT_IMAGES.examens" />
      </StatGrid>
    </IgFeed>

    <IgFeed v-if="activeTab === 'patients'" title="Patients" subtitle="Registre des dossiers">
      <div class="grid grid-cols-1 xl:grid-cols-[1fr_420px] gap-6">
        <DataTable :columns="patientCols" :rows="patients" :loading="loading">
          <template #cell-avatar="{ row }">
            <UserAvatar :name="`${row.nom} ${row.prenom}`" size="sm" />
          </template>
          <template #cell-actions="{ row }">
            <button type="button" class="ig-link" @click="selectQrPatient(row)">QR sécurisé</button>
          </template>
        </DataTable>
        <PatientQrCode
          :qr-code-base64="patientQr.qr_code_base64"
          :expires-at="patientQr.expires_at"
          :expires-in-seconds="patientQr.expires_in_seconds || 300"
          :loading="qrLoading"
          @generate="generateQr"
        />
      </div>
    </IgFeed>

    <IgFeed v-if="activeTab === 'admissions'" title="Hospitalisations" subtitle="Admissions en cours">
      <DataTable :columns="admissionCols" :rows="admissions" :loading="loading">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="`${row.patient_nom || ''} ${row.patient_prenom || ''}`.trim()" size="sm" />
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'labo'" title="Laboratoire" subtitle="Demandes d'examens">
      <DataTable :columns="laboCols" :rows="demandesLabo" :loading="loading">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="row.patient_nom || 'Patient'" size="sm" />
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'actions'" title="Actions médicales" subtitle="Consultations, prescriptions et mouvements">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FormCard title="Consultation" :image="STAT_IMAGES.consultations">
          <AlertBanner :message="msgConsult" :type="msgType" />
          <form @submit.prevent="submitConsultation" class="ig-stack">
            <FormField label="Patient *" v-model="formConsult.patient_id" type="select" :options="patientOptions" required />
            <FormField label="Service *" v-model="formConsult.service_id" type="select" :options="serviceOptions" required />
            <FormField label="Admission (si hospitalisé)" v-model="formConsult.admission_id" type="select" :options="admissionOptionsForConsult" />
            <FormField label="Motif *" v-model="formConsult.motif" type="textarea" required />
            <FormField label="Diagnostic" v-model="formConsult.diagnostic" type="textarea" />
            <FormField label="Code CIM-10" v-model="formConsult.diagnostic_cim10" placeholder="Rechercher un code..." />
            <div v-if="cim10Results.length" class="max-h-32 overflow-y-auto border border-slate-200 rounded-xl">
              <button
                v-for="c in cim10Results"
                :key="c.code"
                type="button"
                class="block w-full text-left px-3 py-2 text-xs hover:bg-indigo-50 border-b border-slate-100 last:border-0"
                @click="selectCim10(c)"
              >
                <strong>{{ c.code }}</strong> — {{ c.libelle }}
              </button>
            </div>
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Enregistrer consultation</button>
          </form>
          <div v-if="lastConsultationId" class="mt-4 pt-4 border-t border-slate-100">
            <p class="text-sm font-medium text-slate-700 mb-2">Archiver un document (PDF / imagerie)</p>
            <AlertBanner :message="msgDoc" :type="msgType" />
            <input type="file" accept=".pdf,image/*" class="text-sm w-full" @change="uploadDocConsultation" />
          </div>
        </FormCard>

        <FormCard title="Prescription" :image="STAT_IMAGES.prescriptions">
          <AlertBanner :message="msgPresc" :type="msgType" />
          <form @submit.prevent="submitPrescription" class="ig-stack">
            <FormField label="Patient *" v-model="formPresc.patient_id" type="select" :options="patientOptions" required />
            <FormField label="Consultation *" v-model="formPresc.consultation_id" type="select" :options="consultationOptions" required />
            <FormField label="Date début *" v-model="formPresc.date_debut" type="date" required />
            <FormField label="Instructions" v-model="formPresc.instructions" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Créer prescription</button>
          </form>
          <hr class="my-4 border-slate-100" />
          <form @submit.prevent="submitLigne" class="ig-stack">
            <FormField label="Prescription *" v-model="formLigne.prescription_id" type="select" :options="prescriptionOptions" required />
            <FormField label="Médicament *" v-model="formLigne.medicament_id" type="select" :options="medicamentOptions" required />
            <FormField label="Quantité *" v-model="formLigne.quantite_prescitee" type="number" required />
            <FormField label="Fréquence *" v-model="formLigne.frequence" placeholder="ex: 3x par jour" required />
            <FormField label="Durée (jours) *" v-model="formLigne.duree_jours" type="number" required />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-secondary w-full py-2.5">Ajouter ligne</button>
          </form>
          <form @submit.prevent="validerPresc" class="ig-stack mt-4">
            <FormField label="Prescription à valider *" v-model="prescIdValider" type="select" :options="prescriptionBrouillonOptions" required />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Valider & verrouiller</button>
          </form>
        </FormCard>

        <FormCard title="Demande d'examen labo" :image="STAT_IMAGES.examens">
          <AlertBanner :message="msgLabo" :type="msgType" />
          <form @submit.prevent="submitDemandeLabo" class="ig-stack">
            <FormField label="Patient *" v-model="formLabo.patient_id" type="select" :options="patientOptions" required />
            <FormField label="Consultation *" v-model="formLabo.consultation_id" type="select" :options="consultationOptionsLabo" required />
            <FormField label="Type d'examen *" v-model="formLabo.examen_type_id" type="select" :options="examenOptions" required />
            <FormField label="Urgent" v-model="formLabo.urgence" type="select" :options="[{value:'false',label:'Non'},{value:'true',label:'Oui'}]" />
            <FormField label="Notes" v-model="formLabo.notes_prescripteur" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Prescrire examen</button>
          </form>
        </FormCard>

        <FormCard title="Plan de soins" :image="STAT_IMAGES.nursing">
          <AlertBanner :message="msgPlan" :type="msgType" />
          <form @submit.prevent="submitPlanSoin" class="ig-stack">
            <FormField label="Patient *" v-model="formPlan.patient_id" type="select" :options="patientOptions" required />
            <FormField label="Admission *" v-model="formPlan.admission_id" type="select" :options="admissionOptionsPlan" required />
            <FormField label="Prescription liée" v-model="formPlan.prescription_id" type="select" :options="prescriptionOptionsPlan" />
            <FormField label="Titre *" v-model="formPlan.titre" required />
            <FormField label="Description *" v-model="formPlan.description" type="textarea" required />
            <FormField label="Fréquence" v-model="formPlan.frequence" placeholder="ex: 2x/jour" />
            <FormField label="Date début *" v-model="formPlan.date_debut" type="date" required />
            <FormField label="Date fin" v-model="formPlan.date_fin" type="date" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Créer plan de soins</button>
          </form>
        </FormCard>

        <FormCard title="Sortie / Transfert" :image="STAT_IMAGES.admissions">
          <AlertBanner :message="msgSortie" :type="msgType" />
          <form @submit.prevent="submitSortie" class="ig-stack">
            <FormField label="Admission *" v-model="formSortie.admission_id" type="select" :options="admissionOptions" required />
            <FormField label="Notes" v-model="formSortie.notes" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-danger w-full py-2.5">Enregistrer sortie</button>
          </form>
          <form @submit.prevent="submitTransfert" class="ig-stack mt-4">
            <FormField label="Admission *" v-model="formTransfert.admission_id" type="select" :options="admissionOptions" required />
            <FormField label="Nouveau service *" v-model="formTransfert.nouveau_service_id" type="select" :options="serviceOptions" required />
            <FormField label="Nouveau lit *" v-model="formTransfert.nouveau_lit_id" type="select" :options="litTransfertOptions" required />
            <FormField label="Motif" v-model="formTransfert.motif" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-secondary w-full py-2.5">Transférer patient</button>
          </form>
        </FormCard>
      </div>
    </IgFeed>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import AppLayout from '../../components/layout/AppLayout.vue'
import IgFeed from '../../components/layout/IgFeed.vue'
import StatGrid from '../../components/ui/StatGrid.vue'
import StatCard from '../../components/ui/StatCard.vue'
import DataTable from '../../components/ui/DataTable.vue'
import FormCard from '../../components/ui/FormCard.vue'
import FormField from '../../components/ui/FormField.vue'
import AlertBanner from '../../components/ui/AlertBanner.vue'
import UserAvatar from '../../components/ui/UserAvatar.vue'
import PatientQrCode from '../../components/ui/PatientQrCode.vue'
import { useLookups } from '../../composables/useLookups'
import { clinicalApi, hospitalApi, laboratoryApi, prescriptionsApi, referentialsApi, getApiError } from '../../api/modules'
import apiClient from '../../api/client'
import { STAT_IMAGES } from '../../config/branding'

const authStore = useAuthStore()
const { patientOptions, admissionOptions, serviceOptions, admissions, loadBasics, admissionsForPatient } = useLookups()

const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble' },
  { id: 'actions', label: 'Actions médicales' },
  { id: 'patients', label: 'Patients' },
  { id: 'admissions', label: 'Hospitalisations' },
  { id: 'labo', label: 'Laboratoire' },
]

const patients = ref([])
const demandesLabo = ref([])
const alertesDoses = ref([])
const medicaments = ref([])
const examensTypes = ref([])
const consultations = ref([])
const prescriptions = ref([])
const litsTransfert = ref([])
const loading = ref(false)
const submitting = ref(false)
const msgConsult = ref(''); const msgPresc = ref(''); const msgLabo = ref(''); const msgSortie = ref(''); const msgPlan = ref(''); const msgDoc = ref('')
const msgType = ref('success')
const prescIdValider = ref('')
const lastConsultationId = ref(null)
const cim10Results = ref([])
const selectedQrPatient = ref(null)
const patientQr = ref({})
const qrLoading = ref(false)
let cim10Timer = null

const formConsult = ref({ patient_id: '', service_id: '', admission_id: '', motif: '', diagnostic: '', diagnostic_cim10: '' })
const formPlan = ref({
  patient_id: '', admission_id: '', prescription_id: '', titre: '', description: '',
  frequence: '', date_debut: new Date().toISOString().slice(0, 10), date_fin: '',
})
const formPresc = ref({ patient_id: '', consultation_id: '', date_debut: new Date().toISOString().slice(0, 10), instructions: '' })
const formLigne = ref({ prescription_id: '', medicament_id: '', quantite_prescitee: 1, frequence: '2x par jour', duree_jours: 7 })
const formLabo = ref({ patient_id: '', consultation_id: '', examen_type_id: '', urgence: 'false', notes_prescripteur: '' })
const formSortie = ref({ admission_id: '', version: 0, notes: '' })
const formTransfert = ref({ admission_id: '', nouveau_service_id: '', nouveau_lit_id: '', version: 0, motif: '' })

const medicamentOptions = computed(() => medicaments.value.map(m => ({ value: m.id, label: `${m.nom} (${m.dosage})` })))
const examenOptions = computed(() => examensTypes.value.map(e => ({ value: e.id, label: `${e.code} — ${e.nom}` })))
const litTransfertOptions = computed(() => litsTransfert.value.map(l => ({ value: l.id, label: `Lit ${l.numero}` })))

const admissionOptionsForConsult = computed(() => {
  if (!formConsult.value.patient_id) return [{ value: '', label: '— Aucune —' }]
  return [{ value: '', label: '— Aucune —' }, ...admissionsForPatient(formConsult.value.patient_id)]
})

const consultationOptions = computed(() =>
  consultations.value.map(c => ({ value: c.id, label: `#${c.id} — ${c.motif?.slice(0, 40) || 'Consultation'} (${c.date_consultation?.slice(0, 10)})` })),
)
const consultationOptionsLabo = computed(() => consultationOptions.value)

const prescriptionOptions = computed(() =>
  prescriptions.value.map(p => ({ value: p.id, label: `#${p.id} — ${p.statut} (${p.nb_lignes} ligne(s))` })),
)
const prescriptionBrouillonOptions = computed(() =>
  prescriptions.value.filter(p => !p.est_verrouillee).map(p => ({ value: p.id, label: `#${p.id} — brouillon` })),
)
const admissionOptionsPlan = computed(() => {
  if (!formPlan.value.patient_id) return []
  return admissionsForPatient(formPlan.value.patient_id)
})
const prescriptionOptionsPlan = computed(() => [
  { value: '', label: '— Aucune —' },
  ...prescriptions.value.map(p => ({ value: p.id, label: `#${p.id} — ${p.statut}` })),
])

const patientCols = [
  { key: 'avatar', label: '' },
  { key: 'numero_dossier', label: 'Dossier' },
  { key: 'nom', label: 'Nom' },
  { key: 'prenom', label: 'Prénom' },
  { key: 'telephone', label: 'Tél.' },
  { key: 'actions', label: 'Accès' },
]
const admissionCols = [
  { key: 'avatar', label: '' },
  { key: 'patient_nom', label: 'Patient' },
  { key: 'service_nom', label: 'Service' },
  { key: 'lit_numero', label: 'Lit' },
  { key: 'id', label: 'ID' },
]
const laboCols = [
  { key: 'avatar', label: '' },
  { key: 'patient_nom', label: 'Patient' },
  { key: 'examen_type_nom', label: 'Examen' },
  { key: 'statut', label: 'Statut' },
]

const loadConsultations = async (patientId) => {
  if (!patientId) { consultations.value = []; return }
  consultations.value = (await clinicalApi.getConsultationsPatient(patientId)).data
}

const loadPrescriptions = async (patientId) => {
  if (!patientId) { prescriptions.value = []; return }
  prescriptions.value = (await prescriptionsApi.getPrescriptionsPatient(patientId)).data
}

function selectQrPatient(row) {
  selectedQrPatient.value = row
  patientQr.value = {}
}

async function generateQr() {
  if (!selectedQrPatient.value?.id) {
    msgType.value = 'error'
    msgConsult.value = 'Sélectionnez un patient avant de générer le QR sécurisé.'
    return
  }
  qrLoading.value = true
  try {
    const { data } = await clinicalApi.generatePatientQrAccess(selectedQrPatient.value.id)
    patientQr.value = data
  } catch (e) {
    msgType.value = 'error'
    msgConsult.value = getApiError(e)
  } finally {
    qrLoading.value = false
  }
}

const loadData = async () => {
  loading.value = true
  try {
    await loadBasics()
    const [p, l, d, m, e] = await Promise.allSettled([
      clinicalApi.getPatients(),
      laboratoryApi.getDemandesEnCours(),
      prescriptionsApi.getAlertesDoses(),
      prescriptionsApi.getMedicaments(),
      laboratoryApi.getExamensTypes(),
    ])
    if (p.status === 'fulfilled') patients.value = p.value.data
    if (l.status === 'fulfilled') demandesLabo.value = l.value.data.map(x => ({ ...x, patient_nom: `${x.patient_nom} ${x.patient_prenom}` }))
    if (d.status === 'fulfilled') alertesDoses.value = d.value.data
    if (m.status === 'fulfilled') medicaments.value = m.value.data
    if (e.status === 'fulfilled') examensTypes.value = e.value.data
  } finally { loading.value = false }
}

watch(() => formPresc.value.patient_id, async (pid) => {
  formPresc.value.consultation_id = ''
  await loadConsultations(pid)
  await loadPrescriptions(pid)
})
watch(() => formLabo.value.patient_id, async (pid) => {
  formLabo.value.consultation_id = ''
  await loadConsultations(pid)
})
watch(() => formTransfert.value.nouveau_service_id, async (sid) => {
  formTransfert.value.nouveau_lit_id = ''
  litsTransfert.value = sid ? (await hospitalApi.getLitsLibres(sid)).data : []
})
watch(() => formSortie.value.admission_id, (id) => {
  const adm = admissionOptions.value.find(a => String(a.value) === String(id))
  if (adm) formSortie.value.version = adm.version ?? 0
})
watch(() => formTransfert.value.admission_id, (id) => {
  const adm = admissionOptions.value.find(a => String(a.value) === String(id))
  if (adm) formTransfert.value.version = adm.version ?? 0
})

watch(() => formPlan.value.patient_id, async (pid) => {
  formPlan.value.admission_id = ''
  formPlan.value.prescription_id = ''
  if (pid) await loadPrescriptions(pid)
})

watch(() => formConsult.value.diagnostic_cim10, (q) => searchCim10(q))

function searchCim10(q) {
  clearTimeout(cim10Timer)
  if (!q || q.length < 2) { cim10Results.value = []; return }
  cim10Timer = setTimeout(async () => {
    try {
      cim10Results.value = (await referentialsApi.searchCim10(q)).data.slice(0, 8)
    } catch { cim10Results.value = [] }
  }, 300)
}

function selectCim10(c) {
  formConsult.value.diagnostic_cim10 = c.code
  if (!formConsult.value.diagnostic) formConsult.value.diagnostic = c.libelle
  cim10Results.value = []
}

const submitPlanSoin = async () => {
  submitting.value = true
  try {
    const payload = {
      patient_id: Number(formPlan.value.patient_id),
      admission_id: Number(formPlan.value.admission_id),
      medecin_prescripteur_id: authStore.user.id,
      titre: formPlan.value.titre,
      description: formPlan.value.description,
      frequence: formPlan.value.frequence,
      date_debut: formPlan.value.date_debut,
    }
    if (formPlan.value.prescription_id) payload.prescription_id = Number(formPlan.value.prescription_id)
    if (formPlan.value.date_fin) payload.date_fin = formPlan.value.date_fin
    const { data } = await clinicalApi.createPlanSoin(payload)
    msgType.value = 'success'
    msgPlan.value = data.message || 'Plan de soins créé'
  } catch (e) { msgType.value = 'error'; msgPlan.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitConsultation = async () => {
  submitting.value = true
  try {
    const payload = {
      patient_id: Number(formConsult.value.patient_id),
      medecin_id: authStore.user.id,
      service_id: Number(formConsult.value.service_id),
      motif: formConsult.value.motif,
      diagnostic: formConsult.value.diagnostic,
      diagnostic_cim10: formConsult.value.diagnostic_cim10,
    }
    if (formConsult.value.admission_id) payload.admission_id = Number(formConsult.value.admission_id)
    const { data } = await clinicalApi.createConsultation(payload)
    msgType.value = 'success'
    msgConsult.value = `Consultation #${data.id} créée`
    lastConsultationId.value = data.id
    await loadConsultations(formConsult.value.patient_id)
  } catch (e) { msgType.value = 'error'; msgConsult.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitPrescription = async () => {
  submitting.value = true
  try {
    const { data } = await prescriptionsApi.createPrescription({
      patient_id: Number(formPresc.value.patient_id),
      medecin_id: authStore.user.id,
      consultation_id: Number(formPresc.value.consultation_id),
      date_debut: formPresc.value.date_debut,
      instructions: formPresc.value.instructions,
    })
    msgType.value = 'success'
    msgPresc.value = `Prescription #${data.id} créée (brouillon)`
    formLigne.value.prescription_id = data.id
    prescIdValider.value = data.id
    await loadPrescriptions(formPresc.value.patient_id)
  } catch (e) { msgType.value = 'error'; msgPresc.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitLigne = async () => {
  submitting.value = true
  try {
    await prescriptionsApi.addLignePrescription({
      ...formLigne.value,
      prescription_id: Number(formLigne.value.prescription_id),
      medicament_id: Number(formLigne.value.medicament_id),
      quantite_prescitee: Number(formLigne.value.quantite_prescitee),
      duree_jours: Number(formLigne.value.duree_jours),
    })
    msgType.value = 'success'
    msgPresc.value = 'Ligne ajoutée'
    if (formPresc.value.patient_id) await loadPrescriptions(formPresc.value.patient_id)
  } catch (e) { msgType.value = 'error'; msgPresc.value = getApiError(e) }
  finally { submitting.value = false }
}

const validerPresc = async () => {
  if (!prescIdValider.value) return
  submitting.value = true
  try {
    const { data } = await prescriptionsApi.validerPrescription(Number(prescIdValider.value))
    msgType.value = 'success'
    msgPresc.value = data.message
    if (formPresc.value.patient_id) await loadPrescriptions(formPresc.value.patient_id)
  } catch (e) { msgType.value = 'error'; msgPresc.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitDemandeLabo = async () => {
  submitting.value = true
  try {
    const { data } = await laboratoryApi.createDemande({
      patient_id: Number(formLabo.value.patient_id),
      medecin_prescripteur_id: authStore.user.id,
      consultation_id: Number(formLabo.value.consultation_id),
      examen_type_id: Number(formLabo.value.examen_type_id),
      urgence: formLabo.value.urgence === 'true',
      notes_prescripteur: formLabo.value.notes_prescripteur,
    })
    msgType.value = 'success'
    msgLabo.value = `Demande #${data.id} créée`
    await loadData()
  } catch (e) { msgType.value = 'error'; msgLabo.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitSortie = async () => {
  submitting.value = true
  try {
    await clinicalApi.sortieAdmission(Number(formSortie.value.admission_id), {
      statut: 'SORTI', notes: formSortie.value.notes, version: Number(formSortie.value.version),
    })
    msgType.value = 'success'
    msgSortie.value = 'Sortie enregistrée — lit libéré'
    await loadData()
  } catch (e) { msgType.value = 'error'; msgSortie.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitTransfert = async () => {
  submitting.value = true
  try {
    await clinicalApi.transfertAdmission(Number(formTransfert.value.admission_id), {
      nouveau_service_id: Number(formTransfert.value.nouveau_service_id),
      nouveau_lit_id: Number(formTransfert.value.nouveau_lit_id),
      version: Number(formTransfert.value.version),
      motif: formTransfert.value.motif,
    })
    msgType.value = 'success'
    msgSortie.value = 'Transfert effectué'
    await loadData()
  } catch (e) { msgType.value = 'error'; msgSortie.value = getApiError(e) }
  finally { submitting.value = false }
}

const uploadDocConsultation = async (event) => {
  const file = event.target.files?.[0]
  if (!file || !lastConsultationId.value) return
  msgDoc.value = ''
  try {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('contenu_type', 'consultation')
    formData.append('contenu_id', String(lastConsultationId.value))
    const endpoint = file.type === 'application/pdf' ? '/files/upload/pdf' : '/files/upload/image'
    await apiClient.post(endpoint, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    msgType.value = 'success'
    msgDoc.value = `${file.name} archivé pour la consultation #${lastConsultationId.value}`
  } catch (e) {
    msgType.value = 'error'
    msgDoc.value = getApiError(e)
  }
}

onMounted(loadData)
</script>
