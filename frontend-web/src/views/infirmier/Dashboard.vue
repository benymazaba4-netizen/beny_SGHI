<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <IgFeed v-if="activeTab === 'overview'">
      <StatGrid>
        <StatCard label="Admissions actives" :value="admissions.length" :image="STAT_IMAGES.admissions" />
        <StatCard label="Alertes doses" :value="alertes.length" :image="STAT_IMAGES.alertes" />
        <StatCard label="Lignes à administrer" :value="ligneOptions.length" :image="STAT_IMAGES.nursing" />
      </StatGrid>
    </IgFeed>

    <IgFeed v-if="activeTab === 'admissions'" title="Hospitalisations" subtitle="Patients hospitalisés">
      <DataTable :columns="admissionCols" :rows="admissions" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'alertes'" title="Alertes doses" subtitle="Doses omises et retards">
      <DataTable :columns="alerteCols" :rows="alertes" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'constantes'" title="Constantes vitales" subtitle="Tendances par patient">
      <FormField label="Patient hospitalisé" v-model="chartPatientId" type="select" :options="patientFromAdmissions" />
      <div v-if="chartPatientId" class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <VitalsChart title="Fréquence cardiaque" :values="fcValues" :labels="chartLabels" />
        <VitalsChart title="Température (°C)" :values="tempValues" :labels="chartLabels" />
        <VitalsChart title="Saturation O2 (%)" :values="satValues" :labels="chartLabels" />
      </div>
    </IgFeed>

    <IgFeed v-if="activeTab === 'actions'" title="Soins" subtitle="Constantes, administrations et prélèvements">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FormCard title="Constantes vitales" :image="STAT_IMAGES.nursing">
          <AlertBanner :message="msgConst" :type="msgType" />
          <form @submit.prevent="submitConstantes" class="ig-stack">
            <FormField label="Admission *" v-model="formConst.admission_id" type="select" :options="admissionOptions" required />
            <FormField label="Tension artérielle" v-model="formConst.tension_arterielle" placeholder="120/80" />
            <FormField label="Fréquence cardiaque" v-model="formConst.frequence_cardiaque" type="number" />
            <FormField label="Température (°C)" v-model="formConst.temperature" type="number" step="0.1" />
            <FormField label="Saturation O2 (%)" v-model="formConst.saturation_o2" type="number" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Enregistrer</button>
          </form>
        </FormCard>

        <FormCard title="Administration médicament" :image="STAT_IMAGES.prescriptions">
          <AlertBanner :message="msgAdmin" :type="msgType" />
          <form @submit.prevent="submitAdmin" class="ig-stack">
            <FormField label="Patient *" v-model="adminPatientId" type="select" :options="patientFromAdmissions" required />
            <FormField label="Ligne prescription *" v-model="formAdmin.ligne_prescription_id" type="select" :options="ligneOptions" required />
            <FormField label="Quantité administrée *" v-model="formAdmin.quantite_administree" type="number" required />
            <FormField label="Commentaire" v-model="formAdmin.commentaire" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Enregistrer administration</button>
          </form>
          <form @submit.prevent="submitDoseOmise" class="ig-stack mt-4">
            <FormField label="Ligne prescription *" v-model="formDoseOmise.ligne_id" type="select" :options="ligneOptions" required />
            <FormField label="Commentaire" v-model="formDoseOmise.commentaire" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-danger w-full py-2.5">Signaler dose omise</button>
          </form>
        </FormCard>

        <FormCard title="Prélèvement labo" :image="STAT_IMAGES.examens">
          <AlertBanner :message="msgPrelev" :type="msgType" />
          <form @submit.prevent="submitPrelevement" class="ig-stack">
            <FormField label="Demande examen *" v-model="formPrelev.demande_id" type="select" :options="demandeOptions" required />
            <FormField label="Type" v-model="formPrelev.type_prelevement" type="select" :options="typePrelevOptions" />
            <FormField label="Type de tube" v-model="formPrelev.tube_type" />
            <FormField label="Conditions" v-model="formPrelev.conditions" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Enregistrer prélèvement</button>
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
import VitalsChart from '../../components/ui/VitalsChart.vue'
import { useLookups } from '../../composables/useLookups'
import { clinicalApi, laboratoryApi, prescriptionsApi, getApiError } from '../../api/modules'
import { STAT_IMAGES } from '../../config/branding'

const { admissionOptions, loadBasics, admissions } = useLookups()

const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble' },
  { id: 'actions', label: 'Soins' },
  { id: 'constantes', label: 'Constantes' },
  { id: 'admissions', label: 'Hospitalisations' },
  { id: 'alertes', label: 'Alertes doses' },
]

const alertes = ref([])
const demandesLabo = ref([])
const lignesPrescription = ref([])
const loading = ref(false)
const submitting = ref(false)
const msgConst = ref(''); const msgAdmin = ref(''); const msgPrelev = ref('')
const msgType = ref('success')
const adminPatientId = ref('')
const chartPatientId = ref('')
const constantesHistory = ref([])

const chartLabels = computed(() =>
  constantesHistory.value.map(c => (c.date_saisie || '').slice(0, 10)).reverse(),
)
const fcValues = computed(() => constantesHistory.value.map(c => c.frequence_cardiaque).reverse())
const tempValues = computed(() => constantesHistory.value.map(c => c.temperature).reverse())
const satValues = computed(() => constantesHistory.value.map(c => c.saturation_o2).reverse())

watch(chartPatientId, async (pid) => {
  constantesHistory.value = []
  if (!pid) return
  const { data } = await clinicalApi.getConstantesPatient(pid)
  constantesHistory.value = data
})

const formConst = ref({ patient_id: '', admission_id: '', tension_arterielle: '', frequence_cardiaque: '', temperature: '', saturation_o2: '' })
const formAdmin = ref({ ligne_prescription_id: '', quantite_administree: 1, commentaire: '' })
const formDoseOmise = ref({ ligne_id: '', commentaire: '' })
const formPrelev = ref({ demande_id: '', type_prelevement: 'SANG', tube_type: '', conditions: '' })

const typePrelevOptions = [
  { value: 'SANG', label: 'Sang' }, { value: 'URINE', label: 'Urines' },
  { value: 'SELLES', label: 'Selles' }, { value: 'ECOUVILLON', label: 'Ecouvillon' },
]

const patientFromAdmissions = computed(() => {
  const seen = new Set()
  return admissions.value
    .filter(a => {
      if (seen.has(a.patient_id)) return false
      seen.add(a.patient_id)
      return true
    })
    .map(a => ({ value: a.patient_id, label: a.patient_nom }))
})

const ligneOptions = computed(() =>
  lignesPrescription.value.map(l => ({
    value: l.id,
    label: `${l.medicament_nom} — reste ${l.quantite_restante} dose(s)`,
  })),
)

const demandeOptions = computed(() =>
  demandesLabo.value
    .filter(d => ['PRESCRIT', 'EN_COURS', 'PRELEVE'].includes(d.statut))
    .map(d => ({ value: d.id, label: `#${d.id} — ${d.patient_nom || d.patient_prenom} · ${d.examen_type_nom || d.examen_nom}` })),
)

const admissionCols = [{ key: 'patient_nom', label: 'Patient' }, { key: 'service_nom', label: 'Service' }, { key: 'lit_numero', label: 'Lit' }, { key: 'id', label: 'Admission' }]
const alerteCols = [{ key: 'type', label: 'Type' }, { key: 'patient', label: 'Patient' }, { key: 'medicament', label: 'Médicament' }, { key: 'message', label: 'Message' }]

watch(() => formConst.value.admission_id, (id) => {
  const adm = admissions.value.find(a => String(a.id) === String(id))
  if (adm) formConst.value.patient_id = adm.patient_id
})

watch(adminPatientId, async (pid) => {
  formAdmin.value.ligne_prescription_id = ''
  formDoseOmise.value.ligne_id = ''
  lignesPrescription.value = []
  if (!pid) return
  const { data } = await prescriptionsApi.getPrescriptionsPatient(pid)
  const lignes = []
  for (const p of data.filter(x => x.est_verrouillee)) {
    for (const l of p.lignes || []) {
      if (l.quantite_restante > 0) lignes.push(l)
    }
  }
  lignesPrescription.value = lignes
})

const load = async () => {
  loading.value = true
  try {
    await loadBasics()
    const [a, al, dl] = await Promise.all([
      clinicalApi.getAdmissionsActives(),
      prescriptionsApi.getAlertesDoses(),
      laboratoryApi.getDemandesEnCours(),
    ])
    admissions.value = a.data
    alertes.value = al.data
    demandesLabo.value = dl.data.map(d => ({ ...d, patient_nom: `${d.patient_nom} ${d.patient_prenom}` }))
  } finally { loading.value = false }
}

const submitConstantes = async () => {
  submitting.value = true
  try {
    await clinicalApi.createConstante({
      patient_id: Number(formConst.value.patient_id),
      admission_id: Number(formConst.value.admission_id),
      tension_arterielle: formConst.value.tension_arterielle,
      frequence_cardiaque: formConst.value.frequence_cardiaque ? Number(formConst.value.frequence_cardiaque) : null,
      temperature: formConst.value.temperature ? Number(formConst.value.temperature) : null,
      saturation_o2: formConst.value.saturation_o2 ? Number(formConst.value.saturation_o2) : null,
    })
    msgType.value = 'success'; msgConst.value = 'Constantes enregistrées'
  } catch (e) { msgType.value = 'error'; msgConst.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitAdmin = async () => {
  submitting.value = true
  try {
    await prescriptionsApi.createAdministration({
      ligne_prescription_id: Number(formAdmin.value.ligne_prescription_id),
      quantite_administree: Number(formAdmin.value.quantite_administree),
      commentaire: formAdmin.value.commentaire,
    })
    msgType.value = 'success'; msgAdmin.value = 'Administration enregistrée'
    if (adminPatientId.value) {
      const { data } = await prescriptionsApi.getPrescriptionsPatient(adminPatientId.value)
      const lignes = []
      for (const p of data.filter(x => x.est_verrouillee)) {
        for (const l of p.lignes || []) {
          if (l.quantite_restante > 0) lignes.push(l)
        }
      }
      lignesPrescription.value = lignes
    }
  } catch (e) { msgType.value = 'error'; msgAdmin.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitDoseOmise = async () => {
  submitting.value = true
  try {
    await prescriptionsApi.signalerDoseOmise(Number(formDoseOmise.value.ligne_id), { commentaire: formDoseOmise.value.commentaire })
    msgType.value = 'success'; msgAdmin.value = 'Dose omise signalée'
    await load()
  } catch (e) { msgType.value = 'error'; msgAdmin.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitPrelevement = async () => {
  submitting.value = true
  try {
    await laboratoryApi.createPrelevement({
      demande_id: Number(formPrelev.value.demande_id),
      type_prelevement: formPrelev.value.type_prelevement,
      tube_type: formPrelev.value.tube_type,
      conditions: formPrelev.value.conditions,
    })
    msgType.value = 'success'; msgPrelev.value = 'Prélèvement enregistré'
    await load()
  } catch (e) { msgType.value = 'error'; msgPrelev.value = getApiError(e) }
  finally { submitting.value = false }
}

onMounted(load)
</script>
