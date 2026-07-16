<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <IgFeed v-if="activeTab === 'overview'">
      <StatGrid>
        <StatCard label="En cours" :value="enCours.length" :image="STAT_IMAGES.examens" />
        <StatCard label="À valider" :value="attenteValidation.length" :image="STAT_IMAGES.validation" />
        <StatCard label="Total file" :value="enCours.length + attenteValidation.length" :image="STAT_IMAGES.examens" />
      </StatGrid>
    </IgFeed>

    <IgFeed v-if="activeTab === 'encours'" title="File d'attente" subtitle="Demandes en cours de traitement">
      <div v-if="enCours.length" class="grid grid-cols-1 xl:grid-cols-2 gap-4 mb-6">
        <article v-for="row in enCours" :key="row.id" class="rounded-3xl border border-slate-100 bg-white p-4 shadow-sm">
          <div class="flex items-start justify-between gap-3 mb-3">
            <div>
              <p class="text-xs text-slate-500">Demande #{{ row.id }}</p>
              <h3 class="font-black text-slate-900">{{ row.examen_type_nom }}</h3>
              <p class="text-sm text-slate-600">{{ row.patient_nom }}</p>
            </div>
            <span class="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-blue-800">{{ row.statut }}</span>
          </div>
          <LabWorkflowSteps :steps="row.workflow || []" />
        </article>
      </div>
      <DataTable :columns="demandeCols" :rows="enCours" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'validation'" title="Validation" subtitle="Résultats en attente de validation">
      <div v-if="loading" class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div v-for="n in 2" :key="n" class="h-48 rounded-2xl bg-slate-100 animate-pulse" />
      </div>
      <div v-else-if="attenteValidation.length" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 mb-6">
        <LabExamCard
          v-for="row in attenteValidation"
          :key="row.id"
          :title="row.examen_type_nom"
          :patient-name="row.patient_nom"
          :subtitle="row.date_prescription?.slice(0, 10)"
          :status="row.statut"
        >
          <template #actions>
            <LabWorkflowSteps :steps="row.workflow || []" class="w-full" />
            <button
              v-if="row.resultat_id"
              type="button"
              class="ig-btn ig-btn-primary text-xs py-2 px-4"
              :disabled="validating === row.resultat_id"
              @click="valider(row.resultat_id)"
            >
              {{ validating === row.resultat_id ? 'Validation...' : 'Valider & publier PDF' }}
            </button>
          </template>
        </LabExamCard>
      </div>
      <DataTable :columns="validationCols" :rows="attenteValidation" :loading="loading">
        <template #cell-actions="{ row }">
          <button v-if="row.resultat_id" type="button" @click="valider(row.resultat_id)" class="ig-link" :disabled="validating === row.resultat_id">
            {{ validating === row.resultat_id ? '...' : 'Valider' }}
          </button>
        </template>
      </DataTable>
      <AlertBanner :message="validationMsg" :type="validationOk ? 'success' : 'error'" class="mt-3" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'actions'" title="Actions labo" subtitle="Affectation et saisie des résultats">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FormCard title="Affecter une demande" :image="STAT_IMAGES.examens">
          <AlertBanner :message="msgAffect" :type="msgType" />
          <form @submit.prevent="submitAffectation" class="ig-stack">
            <FormField label="Demande *" v-model="formAffect.demande_id" type="select" :options="demandeAffectOptions" required />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Affecter à moi (→ EN_COURS)</button>
          </form>
        </FormCard>

        <FormCard title="Saisir un résultat" :image="STAT_IMAGES.validation">
          <AlertBanner :message="msgResult" :type="msgType" />
          <form @submit.prevent="submitResultat" class="ig-stack">
            <FormField label="Demande *" v-model="formResult.demande_id" type="select" :options="demandeResultOptions" required />
            <FormField label="Résultats *" v-model="formResult.resultats" type="textarea" rows="5" required />
            <FormField label="Interprétation" v-model="formResult.interpretation" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Saisir (→ VALIDATION)</button>
          </form>
        </FormCard>

        <FormCard title="Modifier un résultat" :image="STAT_IMAGES.examens">
          <AlertBanner :message="msgEdit" :type="msgType" />
          <form @submit.prevent="submitEditResultat" class="ig-stack">
            <FormField label="Demande *" v-model="editDemandeId" type="select" :options="demandeValidationOptions" required />
            <FormField label="Résultats *" v-model="formEdit.resultats" type="textarea" rows="4" required />
            <FormField label="Interprétation" v-model="formEdit.interpretation" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-secondary w-full py-2.5">Mettre à jour</button>
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
import LabExamCard from '../../components/ui/LabExamCard.vue'
import LabWorkflowSteps from '../../components/ui/LabWorkflowSteps.vue'
import { laboratoryApi, getApiError } from '../../api/modules'
import { STAT_IMAGES } from '../../config/branding'

const authStore = useAuthStore()
const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble' },
  { id: 'actions', label: 'Actions labo' },
  { id: 'encours', label: 'En cours' },
  { id: 'validation', label: 'Validation' },
]

const enCours = ref([])
const attenteValidation = ref([])
const loading = ref(false)
const submitting = ref(false)
const validating = ref(null)
const validationMsg = ref('')
const validationOk = ref(false)
const msgAffect = ref(''); const msgResult = ref(''); const msgEdit = ref('')
const msgType = ref('success')

const formAffect = ref({ demande_id: '' })
const formResult = ref({ demande_id: '', resultats: '', interpretation: '' })
const editDemandeId = ref('')
const formEdit = ref({ resultats: '', interpretation: '', resultat_id: '' })

const demandeLabel = (d) => `#${d.id} — ${d.patient_nom || ''} ${d.patient_prenom || ''} · ${d.examen_type_nom || d.examen_nom}`

const demandeAffectOptions = computed(() =>
  enCours.value.filter(d => !d.affecte_a).map(d => ({ value: d.id, label: demandeLabel(d) })),
)
const demandeResultOptions = computed(() =>
  enCours.value.filter(d => d.statut === 'EN_COURS' || d.statut === 'PRELEVE').map(d => ({ value: d.id, label: demandeLabel(d) })),
)
const demandeValidationOptions = computed(() =>
  attenteValidation.value.map(d => ({ value: d.id, label: demandeLabel(d), resultat_id: d.resultat_id })),
)

const demandeCols = [
  { key: 'patient_nom', label: 'Patient' }, { key: 'examen_type_nom', label: 'Examen' },
  { key: 'statut', label: 'Statut' }, { key: 'affecte_a', label: 'Affecté à' },
]
const validationCols = [
  { key: 'patient_nom', label: 'Patient' }, { key: 'examen_type_nom', label: 'Examen' },
  { key: 'date_prescription', label: 'Date' }, { key: 'actions', label: 'Action' },
]

const load = async () => {
  loading.value = true
  try {
    const [ec, av] = await Promise.all([laboratoryApi.getDemandesEnCours(), laboratoryApi.getAttenteValidation()])
    enCours.value = ec.data.map(d => ({ ...d, patient_nom: `${d.patient_nom} ${d.patient_prenom}` }))
    attenteValidation.value = av.data.map(d => ({
      ...d, patient_nom: `${d.patient_nom} ${d.patient_prenom}`, date_prescription: d.date_prescription?.slice(0, 10),
    }))
  } finally { loading.value = false }
}

watch(editDemandeId, (id) => {
  const item = attenteValidation.value.find(d => String(d.id) === String(id))
  formEdit.value.resultat_id = item?.resultat_id || ''
  formEdit.value.resultats = item?.resultats || ''
  formEdit.value.interpretation = item?.interpretation || ''
})

const submitAffectation = async () => {
  submitting.value = true
  try {
    await laboratoryApi.affecterDemande(Number(formAffect.value.demande_id), {
      biologiste_id: authStore.user.id,
    })
    msgType.value = 'success'; msgAffect.value = 'Demande affectée'
    await load()
  } catch (e) { msgType.value = 'error'; msgAffect.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitResultat = async () => {
  submitting.value = true
  try {
    await laboratoryApi.createResultat({
      demande_id: Number(formResult.value.demande_id),
      resultats: formResult.value.resultats,
      interpretation: formResult.value.interpretation,
    })
    msgType.value = 'success'; msgResult.value = 'Résultat saisi — en attente de validation'
    await load()
  } catch (e) { msgType.value = 'error'; msgResult.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitEditResultat = async () => {
  if (!formEdit.value.resultat_id) return
  submitting.value = true
  try {
    await laboratoryApi.updateResultat(Number(formEdit.value.resultat_id), {
      resultats: formEdit.value.resultats,
      interpretation: formEdit.value.interpretation,
    })
    msgType.value = 'success'; msgEdit.value = 'Résultat mis à jour'
    await load()
  } catch (e) { msgType.value = 'error'; msgEdit.value = getApiError(e) }
  finally { submitting.value = false }
}

const valider = async (resultatId) => {
  validating.value = resultatId
  try {
    await laboratoryApi.validerResultat(resultatId)
    validationMsg.value = 'Validé — PDF généré et publié'
    validationOk.value = true
    await load()
  } catch (e) {
    validationMsg.value = getApiError(e)
    validationOk.value = false
  } finally { validating.value = null }
}

onMounted(load)
</script>
