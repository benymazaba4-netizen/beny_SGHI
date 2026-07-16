<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <IgFeed v-if="activeTab === 'overview'">
      <StatGrid>
        <StatCard label="Références" :value="stocks.length" :image="STAT_IMAGES.stocks" />
        <StatCard label="Alertes" :value="alertes.length" :image="STAT_IMAGES.alertes" />
        <StatCard label="Stocks critiques" :value="stocksCritiques" :image="STAT_IMAGES.prescriptions" />
      </StatGrid>
    </IgFeed>

    <IgFeed v-if="activeTab === 'stocks'" title="Stocks" subtitle="Inventaire en temps réel">
      <DataTable :columns="stockCols" :rows="stocks" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'alertes'" title="Alertes" subtitle="Seuils et péremption">
      <DataTable :columns="alerteCols" :rows="alertes" :loading="loading" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'actions'" title="Réception & mouvements" subtitle="Lots et ajustements de stock">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <FormCard title="Réception d'un lot" :image="STAT_IMAGES.stocks">
          <AlertBanner :message="msgLot" :type="msgType" />
          <form @submit.prevent="submitLot" class="ig-stack">
            <FormField label="Médicament *" v-model="formLot.medicament_id" type="select" :options="medicamentOptions" required />
            <FormField label="N° lot *" v-model="formLot.numero_lot" required />
            <FormField label="Quantité *" v-model="formLot.quantite_initiale" type="number" required />
            <FormField label="Date fabrication *" v-model="formLot.date_fabrication" type="date" required />
            <FormField label="Date péremption *" v-model="formLot.date_peremption" type="date" required />
            <FormField label="Fournisseur" v-model="formLot.fournisseur" />
            <FormField label="Prix achat" v-model="formLot.prix_achat" type="number" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Enregistrer lot</button>
          </form>
        </FormCard>

        <FormCard title="Mouvement de stock" :image="STAT_IMAGES.stocks">
          <AlertBanner :message="msgMvt" :type="msgType" />
          <form @submit.prevent="submitMouvement" class="ig-stack">
            <FormField label="Médicament *" v-model="formMvt.medicament_id" type="select" :options="medicamentOptions" required />
            <FormField label="Type *" v-model="formMvt.type_mouvement" type="select" :options="typeMvtOptions" required />
            <FormField label="Quantité *" v-model="formMvt.quantite" type="number" required />
            <FormField label="Référence" v-model="formMvt.reference" />
            <FormField label="Commentaire" v-model="formMvt.commentaire" type="textarea" />
            <button type="submit" :disabled="submitting" class="ig-btn ig-btn-primary w-full py-2.5">Enregistrer mouvement</button>
          </form>
        </FormCard>
      </div>
    </IgFeed>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import IgFeed from '../../components/layout/IgFeed.vue'
import StatGrid from '../../components/ui/StatGrid.vue'
import StatCard from '../../components/ui/StatCard.vue'
import DataTable from '../../components/ui/DataTable.vue'
import FormCard from '../../components/ui/FormCard.vue'
import FormField from '../../components/ui/FormField.vue'
import AlertBanner from '../../components/ui/AlertBanner.vue'
import { pharmacyApi, prescriptionsApi, getApiError } from '../../api/modules'
import { STAT_IMAGES } from '../../config/branding'

const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble' },
  { id: 'actions', label: 'Réception / Mouvements' },
  { id: 'stocks', label: 'Stocks' },
  { id: 'alertes', label: 'Alertes' },
]

const stocks = ref([])
const alertes = ref([])
const medicaments = ref([])
const loading = ref(false)
const submitting = ref(false)
const msgLot = ref(''); const msgMvt = ref('')
const msgType = ref('success')

const formLot = ref({ medicament_id: '', numero_lot: '', quantite_initiale: '', date_fabrication: '', date_peremption: '', fournisseur: '', prix_achat: 0 })
const formMvt = ref({ medicament_id: '', type_mouvement: 'ENTREE', quantite: '', reference: '', commentaire: '' })

const typeMvtOptions = [
  { value: 'ENTREE', label: 'Entrée' }, { value: 'SORTIE', label: 'Sortie' },
  { value: 'PERTE', label: 'Perte' }, { value: 'AJUSTEMENT', label: 'Ajustement' },
]

const stocksCritiques = computed(() => stocks.value.filter(s => s.quantite_totale <= s.seuil_alerte).length)
const medicamentOptions = computed(() => medicaments.value.map(m => ({ value: m.id, label: `${m.nom} (${m.code})` })))

const stockCols = [
  { key: 'medicament__code', label: 'Code' }, { key: 'medicament__nom', label: 'Nom' },
  { key: 'quantite_totale', label: 'Qté' }, { key: 'seuil_alerte', label: 'Seuil' },
]
const alerteCols = [
  { key: 'medicament__nom', label: 'Médicament' }, { key: 'type_alerte', label: 'Type' },
  { key: 'message', label: 'Message' },
]

const load = async () => {
  loading.value = true
  try {
    const [s, a] = await Promise.all([pharmacyApi.getStocks(), pharmacyApi.getAlertes()])
    stocks.value = s.data
    alertes.value = a.data
  } finally { loading.value = false }
}

watch(activeTab, async (tab) => {
  if (tab === 'actions' && !medicaments.value.length) {
    medicaments.value = (await prescriptionsApi.getMedicaments()).data
  }
})

const submitLot = async () => {
  submitting.value = true
  try {
    await pharmacyApi.createLot({
      ...formLot.value,
      medicament_id: Number(formLot.value.medicament_id),
      quantite_initiale: Number(formLot.value.quantite_initiale),
      prix_achat: Number(formLot.value.prix_achat) || 0,
    })
    msgType.value = 'success'; msgLot.value = 'Lot enregistré — stock mis à jour'
    await load()
  } catch (e) { msgType.value = 'error'; msgLot.value = getApiError(e) }
  finally { submitting.value = false }
}

const submitMouvement = async () => {
  submitting.value = true
  try {
    await pharmacyApi.createMouvement({
      ...formMvt.value,
      medicament_id: Number(formMvt.value.medicament_id),
      quantite: Number(formMvt.value.quantite),
    })
    msgType.value = 'success'; msgMvt.value = 'Mouvement enregistré'
    await load()
  } catch (e) { msgType.value = 'error'; msgMvt.value = getApiError(e) }
  finally { submitting.value = false }
}

onMounted(load)
</script>
