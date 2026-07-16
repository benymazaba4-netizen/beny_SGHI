<template>
  <AppLayout v-model:activeTab="activeTab" :tabs="tabs">
    <IgFeed v-if="activeTab === 'overview'">
      <AdminStatsPanel :stats="adminStats" />
    </IgFeed>

    <IgFeed v-if="activeTab === 'users'" title="Utilisateurs" subtitle="Comptes et dernières connexions">
      <p v-if="isSuperAdmin" class="mb-4 text-sm text-amber-800 bg-amber-50 border border-amber-100 rounded-xl px-4 py-3">
        Vous êtes connecté en <strong>super-administrateur</strong> — vous pouvez modifier tous les comptes, y compris les autres super-admins.
      </p>
      <p v-else class="mb-4 text-sm text-slate-600 bg-slate-50 border border-slate-100 rounded-xl px-4 py-3">
        Vous êtes connecté en <strong>administrateur</strong> — la gestion des utilisateurs est disponible, sauf pour les comptes super-admin (lecture seule).
      </p>
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <DataTable :columns="userCols" :rows="users" :loading="loading">
          <template #cell-avatar="{ row }">
            <UserAvatar
              :name="`${row.first_name || ''} ${row.last_name || ''}`.trim() || row.username"
              size="sm"
            />
          </template>
          <template #cell-niveau="{ row }">
            <span
              v-if="row.is_superuser"
              class="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-medium"
            >Super-admin</span>
            <span
              v-else-if="row.role === 'ADMIN'"
              class="text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-medium"
            >Admin</span>
            <span v-else class="text-xs text-slate-400">—</span>
          </template>
          <template #cell-actions="{ row }">
            <button v-if="canEditUser(row)" type="button" class="ig-link" @click="selectUser(row)">Modifier</button>
            <span v-else class="text-xs text-slate-400">Lecture seule</span>
          </template>
        </DataTable>
        <FormCard title="Modifier un utilisateur" :image="STAT_IMAGES.admin">
          <AlertBanner :message="userMsg" :type="userMsgType" />
          <form v-if="editUserId" @submit.prevent="submitUserUpdate" class="ig-stack">
            <p class="text-sm text-slate-600">Compte : <strong>{{ formUser.username }}</strong>
              <span v-if="formUser.is_superuser" class="ml-2 text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">Super-admin</span>
              <span v-else-if="formUser.role === 'ADMIN'" class="ml-2 text-xs px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800">Admin</span>
            </p>
            <p class="rounded-2xl border border-blue-100 bg-blue-50 px-4 py-3 text-xs font-medium text-blue-800">
              Règle RBAC : l'administrateur modifie uniquement les accès système, le rôle et l'activation du compte.
              Les informations médicales et professionnelles restent gérées par les workflows cliniques/RH.
            </p>
            <FormField label="E-mail système *" v-model="formUser.email" type="email" required />
            <FormField label="Rôle *" v-model="formUser.role" type="select" :options="roleOptions" required />
            <FormField
              label="Compte actif"
              v-model="formUser.is_active"
              type="select"
              :options="[{ value: 'true', label: 'Oui' }, { value: 'false', label: 'Non' }]"
            />
            <button type="submit" :disabled="userSubmitting" class="ig-btn ig-btn-primary w-full py-2.5">
              {{ userSubmitting ? 'Enregistrement...' : 'Enregistrer les modifications' }}
            </button>
          </form>
          <p v-else class="text-sm text-slate-500">Sélectionnez un utilisateur dans le tableau pour modifier ses informations.</p>
        </FormCard>
      </div>
    </IgFeed>

    <IgFeed v-if="activeTab === 'structure'" title="Structure hospitalière" subtitle="Bâtiments, services et lits">
      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <DataTable title="Bâtiments" :columns="batCols" :rows="batiments" :loading="loading" />
        <DataTable title="Services" :columns="svcCols" :rows="services" :loading="loading" />
        <DataTable title="Lits libres" :columns="litCols" :rows="litsLibres" :loading="loading" />
      </div>
    </IgFeed>

    <IgFeed v-if="activeTab === 'rh'" title="Ressources humaines" subtitle="Personnel et planning de garde">
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <DataTable title="Personnel" :columns="personnelCols" :rows="personnel" :loading="loading">
          <template #cell-avatar="{ row }">
            <UserAvatar :name="row.nom" size="sm" />
          </template>
        </DataTable>
        <FormCard title="Nouvelle garde" :image="STAT_IMAGES.admin">
          <AlertBanner :message="gardeMsg" :type="gardeMsgType" />
          <form @submit.prevent="submitGarde" class="ig-stack">
            <FormField label="Personnel *" v-model="formGarde.personnel_id" type="select" :options="personnelOptions" required />
            <FormField label="Service *" v-model="formGarde.service_id" type="select" :options="serviceOptions" required />
            <FormField label="Type *" v-model="formGarde.type_garde" type="select" :options="typeGardeOptions" required />
            <FormField label="Début *" v-model="formGarde.date_debut" type="datetime-local" required />
            <FormField label="Fin *" v-model="formGarde.date_fin" type="datetime-local" required />
            <FormField label="Commentaire" v-model="formGarde.commentaire" type="textarea" />
            <button type="submit" :disabled="gardeSubmitting" class="ig-btn ig-btn-primary w-full py-2.5">Planifier la garde</button>
          </form>
        </FormCard>
      </div>
      <div class="mb-6 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm">
        <h3 class="text-sm font-semibold text-slate-700 mb-3">Calendrier des gardes (7 jours)</h3>
        <div class="grid grid-cols-7 gap-2">
          <div v-for="day in gardeCalendarDays" :key="day.label" class="min-h-[88px] p-2 rounded-xl bg-slate-50 border border-slate-100">
            <p class="text-xs font-bold text-slate-600 mb-1">{{ day.label }}</p>
            <div v-for="g in day.gardes" :key="g.id" class="text-[10px] mb-1 px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 truncate" :title="`${g.personnel} — ${g.type_garde}`">
              {{ g.personnel.split(' ')[0] }} · {{ g.type_garde }}
            </div>
            <p v-if="!day.gardes.length" class="text-[10px] text-slate-400">—</p>
          </div>
        </div>
      </div>
      <DataTable title="Planning de gardes" :columns="gardeCols" :rows="gardes" :loading="loading">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="row.personnel" size="sm" />
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'governance'" title="Gouvernance des données" subtitle="Archivage, anonymisation et traçabilité des accès">
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
        <FormCard title="Archiver un dossier patient" :image="STAT_IMAGES.patients">
          <AlertBanner :message="govMsg" :type="govMsgType" />
          <form @submit.prevent="submitArchivage" class="ig-stack">
            <FormField label="Patient *" v-model="archiverPatientId" type="select" :options="patientOptions" required />
            <button type="submit" :disabled="govSubmitting" class="ig-btn ig-btn-primary w-full py-2.5">Archiver le dossier</button>
          </form>
        </FormCard>
        <FormCard title="Job d'anonymisation statistique" :image="STAT_IMAGES.admin">
          <form @submit.prevent="submitAnonymisation" class="ig-stack">
            <FormField label="Nom du job *" v-model="formAnon.nom" required />
            <FormField label="Période début *" v-model="formAnon.periode_debut" type="date" required />
            <FormField label="Période fin *" v-model="formAnon.periode_fin" type="date" required />
            <button type="submit" :disabled="govSubmitting" class="ig-btn ig-btn-secondary w-full py-2.5">Lancer l'anonymisation</button>
          </form>
        </FormCard>
      </div>
      <div class="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <DataTable title="Archives" :columns="archiveCols" :rows="archives" :loading="govLoading" />
        <DataTable title="Jobs d'anonymisation" :columns="anonCols" :rows="anonymisations" :loading="govLoading" />
      </div>
      <DataTable title="Journal d'accès aux dossiers" :columns="accesCols" :rows="accesDossiers" :loading="govLoading" class="mt-6">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="row.utilisateur" size="sm" />
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'presences'" title="Présences" subtitle="Suivi quotidien">
      <DataTable :columns="presenceCols" :rows="presences" :loading="loading">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="row.personnel" size="sm" />
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'conges'" title="Congés" subtitle="Demandes et validations">
      <DataTable :columns="congeCols" :rows="conges" :loading="loading">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="row.personnel" size="sm" />
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'security'" title="Sécurité MFA" subtitle="Authentification à deux facteurs">
      <FormCard title="Statut MFA" :image="STAT_IMAGES.admin">
        <p class="text-sm mb-4">MFA actuellement : <strong>{{ mfaStatus.mfa_enabled ? 'Activée' : 'Désactivée' }}</strong></p>
        <AlertBanner :message="mfaMsg" :type="mfaMsgType" />
        <div v-if="!mfaStatus.mfa_enabled && !mfaSetup.secret" class="ig-stack">
          <button type="button" class="ig-btn ig-btn-primary" :disabled="mfaLoading" @click="startMfaSetup">
            Configurer MFA
          </button>
        </div>
        <div v-if="mfaSetup.secret" class="ig-stack">
          <p class="text-xs text-slate-500">Scannez le QR code avec Google Authenticator ou entrez le secret manuellement.</p>
          <img v-if="mfaSetup.qr_code_base64" :src="`data:image/png;base64,${mfaSetup.qr_code_base64}`" alt="QR MFA" class="w-48 h-48 mx-auto" />
          <code class="block text-center text-sm bg-slate-100 p-2 rounded">{{ mfaSetup.secret }}</code>
          <FormField label="Code à 6 chiffres" v-model="totpCode" placeholder="000000" />
          <button type="button" class="ig-btn ig-btn-primary" :disabled="mfaLoading" @click="verifyMfa">Activer MFA</button>
        </div>
        <div v-if="mfaStatus.mfa_enabled" class="mt-4">
          <FormField label="Mot de passe pour désactiver" v-model="disablePassword" type="password" />
          <button type="button" class="ig-btn ig-btn-secondary mt-2" :disabled="mfaLoading" @click="disableMfa">Désactiver MFA</button>
        </div>
      </FormCard>
      <DataTable title="Journal des connexions" :columns="connexionCols" :rows="connexions" :loading="loading" class="mt-6">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="row.username" size="sm" />
        </template>
      </DataTable>
    </IgFeed>

    <IgFeed v-if="activeTab === 'audit'" title="Journal d'audit" subtitle="Traçabilité immuable">
      <DataTable :columns="auditCols" :rows="auditLogs" :loading="loading">
        <template #cell-avatar="{ row }">
          <UserAvatar :name="row.utilisateur_username || 'Système'" size="sm" />
        </template>
      </DataTable>
    </IgFeed>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import AppLayout from '../../components/layout/AppLayout.vue'
import IgFeed from '../../components/layout/IgFeed.vue'
import AdminStatsPanel from '../../components/ui/AdminStatsPanel.vue'
import DataTable from '../../components/ui/DataTable.vue'
import FormCard from '../../components/ui/FormCard.vue'
import FormField from '../../components/ui/FormField.vue'
import AlertBanner from '../../components/ui/AlertBanner.vue'
import UserAvatar from '../../components/ui/UserAvatar.vue'
import { useLookups } from '../../composables/useLookups'
import {
  adminApi, rhApi, auditApi, authApi, hospitalApi, mfaApi, governanceApi, getApiError,
} from '../../api/modules'
import { STAT_IMAGES } from '../../config/branding'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const isSuperAdmin = computed(() => !!authStore.user?.is_superuser)

function canEditUser(row) {
  if (!row?.is_superuser) return true
  return isSuperAdmin.value
}

const { patientOptions, serviceOptions, loadBasics } = useLookups()

const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble' },
  { id: 'users', label: 'Utilisateurs' },
  { id: 'structure', label: 'Structure' },
  { id: 'rh', label: 'RH & Gardes' },
  { id: 'presences', label: 'Présences' },
  { id: 'conges', label: 'Congés' },
  { id: 'security', label: 'Sécurité' },
  { id: 'governance', label: 'Gouvernance' },
  { id: 'audit', label: 'Audit' },
]

const adminStats = ref({
  occupation: { total_lits: 0, lits_occupes: 0, taux: 0 },
  finances: { recettes_globales: 0, factures_validees: 0 },
  laboratoire: { attente: 0, publies: 0, par_statut: {} },
  admissions: { actives: 0 },
  trends: { labels: [], recettes: [], admissions: [], examens: [] },
  cache: { hit: false, ttl_seconds: 0 },
})
const users = ref([])
const batiments = ref([])
const services = ref([])
const litsLibres = ref([])
const personnel = ref([])
const gardes = ref([])
const presences = ref([])
const conges = ref([])
const auditLogs = ref([])
const connexions = ref([])
const archives = ref([])
const anonymisations = ref([])
const accesDossiers = ref([])
const govLoading = ref(false)
const govSubmitting = ref(false)
const govMsg = ref('')
const govMsgType = ref('success')
const archiverPatientId = ref('')
const formAnon = ref({ nom: '', periode_debut: '', periode_fin: '' })
const gardeSubmitting = ref(false)
const gardeMsg = ref('')
const gardeMsgType = ref('success')
const formGarde = ref({ personnel_id: '', service_id: '', type_garde: 'JOUR', date_debut: '', date_fin: '', commentaire: '' })
const loading = ref(false)
const mfaStatus = ref({ mfa_enabled: false })
const mfaSetup = ref({})
const totpCode = ref('')
const disablePassword = ref('')
const mfaLoading = ref(false)
const mfaMsg = ref('')
const mfaMsgType = ref('success')
const editUserId = ref(null)
const userSubmitting = ref(false)
const userMsg = ref('')
const userMsgType = ref('success')
const formUser = ref({
  username: '', first_name: '', last_name: '', email: '', telephone: '', matricule: '',
  role: 'PATIENT', is_active: 'true', is_superuser: false,
})

const roleOptions = [
  { value: 'PATIENT', label: 'Patient' },
  { value: 'MEDECIN', label: 'Médecin' },
  { value: 'INFIRMIER', label: 'Infirmier' },
  { value: 'BIOLOGISTE', label: 'Biologiste' },
  { value: 'PHARMACIEN', label: 'Pharmacien' },
  { value: 'SECRETAIRE', label: 'Secrétaire' },
  { value: 'COMPTABLE', label: 'Comptable' },
  { value: 'ADMIN', label: 'Administrateur' },
]

const userCols = [
  { key: 'avatar', label: '' },
  { key: 'username', label: 'Login' },
  { key: 'role', label: 'Rôle' },
  { key: 'niveau', label: 'Niveau' },
  { key: 'first_name', label: 'Prénom' },
  { key: 'last_name', label: 'Nom' },
  { key: 'email', label: 'E-mail' },
  { key: 'is_active', label: 'Actif' },
  { key: 'date_derniere_connexion', label: 'Dernière connexion' },
  { key: 'actions', label: 'Actions' },
]
const batCols = [{ key: 'nom', label: 'Nom' }, { key: 'code', label: 'Code' }, { key: 'nombre_etages', label: 'Étages' }]
const svcCols = [{ key: 'nom', label: 'Service' }, { key: 'code', label: 'Code' }, { key: 'type_service', label: 'Type' }]
const litCols = [{ key: 'numero', label: 'Lit' }, { key: 'chambre', label: 'Chambre' }, { key: 'service', label: 'Service' }]
const personnelCols = [
  { key: 'avatar', label: '' },
  { key: 'matricule', label: 'Matricule' }, { key: 'nom', label: 'Nom' },
  { key: 'type_personnel', label: 'Type' }, { key: 'service', label: 'Service' },
]
const gardeCols = [
  { key: 'avatar', label: '' },
  { key: 'personnel', label: 'Personnel' }, { key: 'service', label: 'Service' },
  { key: 'type_garde', label: 'Type' }, { key: 'date_debut', label: 'Début' },
]
const presenceCols = [
  { key: 'avatar', label: '' },
  { key: 'personnel', label: 'Personnel' }, { key: 'date', label: 'Date' }, { key: 'statut', label: 'Statut' },
]
const congeCols = [
  { key: 'avatar', label: '' },
  { key: 'personnel', label: 'Personnel' }, { key: 'type_conge', label: 'Type' },
  { key: 'statut', label: 'Statut' }, { key: 'nb_jours', label: 'Jours' },
]
const auditCols = [
  { key: 'avatar', label: '' },
  { key: 'timestamp', label: 'Date' }, { key: 'utilisateur_username', label: 'Utilisateur' },
  { key: 'action', label: 'Action' }, { key: 'model_name', label: 'Modèle' },
]
const archiveCols = [
  { key: 'object_id', label: 'Patient ID' }, { key: 'statut', label: 'Statut' },
  { key: 'date_archivage', label: 'Archivé le' }, { key: 'date_expiration_legale', label: 'Expiration légale' },
]
const anonCols = [
  { key: 'nom', label: 'Job' }, { key: 'statut', label: 'Statut' },
  { key: 'nb_enregistrements', label: 'Enregistrements' }, { key: 'date_creation', label: 'Créé le' },
]
const accesCols = [
  { key: 'avatar', label: '' },
  { key: 'date_acces', label: 'Date' }, { key: 'utilisateur', label: 'Utilisateur' },
  { key: 'patient_id', label: 'Patient' }, { key: 'action', label: 'Action' }, { key: 'ip_address', label: 'IP' },
]
const connexionCols = [
  { key: 'avatar', label: '' },
  { key: 'date_connexion', label: 'Date' }, { key: 'username', label: 'Utilisateur' },
  { key: 'role', label: 'Rôle' }, { key: 'ip_address', label: 'IP' }, { key: 'reussie', label: 'OK' },
]
const typeGardeOptions = [
  { value: 'JOUR', label: 'Jour' }, { value: 'NUIT', label: 'Nuit' }, { value: 'ASTREINTE', label: 'Astreinte' },
]
const personnelOptions = computed(() =>
  personnel.value.map(p => ({ value: p.id, label: `${p.nom} (${p.matricule})` })),
)
const gardeCalendarDays = computed(() => {
  const days = []
  const now = new Date()
  for (let i = 0; i < 7; i += 1) {
    const d = new Date(now)
    d.setDate(now.getDate() + i)
    const key = d.toISOString().slice(0, 10)
    days.push({
      label: d.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' }),
      gardes: gardes.value.filter(g => (g.date_debut || '').slice(0, 10) === key),
    })
  }
  return days
})

async function loadGovernance() {
  govLoading.value = true
  try {
    const [archRes, anonRes, accesRes] = await Promise.all([
      governanceApi.getArchives(),
      governanceApi.getAnonymisations(),
      governanceApi.getAccesDossiers(),
    ])
    archives.value = archRes.data
    anonymisations.value = anonRes.data
    accesDossiers.value = accesRes.data
  } catch (e) {
    govMsg.value = getApiError(e)
    govMsgType.value = 'error'
  } finally {
    govLoading.value = false
  }
}

async function submitArchivage() {
  if (!archiverPatientId.value) return
  govSubmitting.value = true
  govMsg.value = ''
  try {
    const res = await governanceApi.archiverPatient(Number(archiverPatientId.value))
    govMsg.value = res.data.message || 'Dossier archivé'
    govMsgType.value = 'success'
    await loadGovernance()
  } catch (e) {
    govMsg.value = getApiError(e)
    govMsgType.value = 'error'
  } finally {
    govSubmitting.value = false
  }
}

async function submitAnonymisation() {
  govSubmitting.value = true
  govMsg.value = ''
  try {
    await governanceApi.createAnonymisation({
      nom: formAnon.value.nom,
      periode_debut: formAnon.value.periode_debut,
      periode_fin: formAnon.value.periode_fin,
    })
    govMsg.value = 'Job d\'anonymisation lancé'
    govMsgType.value = 'success'
    formAnon.value = { nom: '', periode_debut: '', periode_fin: '' }
    await loadGovernance()
  } catch (e) {
    govMsg.value = getApiError(e)
    govMsgType.value = 'error'
  } finally {
    govSubmitting.value = false
  }
}

function selectUser(row) {
  if (!canEditUser(row)) {
    userMsgType.value = 'error'
    userMsg.value = 'Seul un super-administrateur peut modifier ce compte.'
    return
  }
  editUserId.value = row.id
  formUser.value = {
    username: row.username,
    first_name: row.first_name || '',
    last_name: row.last_name || '',
    email: row.email || '',
    telephone: row.telephone || '',
    matricule: row.matricule || '',
    role: row.role || 'PATIENT',
    is_active: row.is_active ? 'true' : 'false',
    is_superuser: !!row.is_superuser,
  }
  userMsg.value = ''
}

async function submitUserUpdate() {
  if (!editUserId.value) return
  userSubmitting.value = true
  userMsg.value = ''
  try {
    const { data } = await authApi.updateUser(editUserId.value, {
      email: formUser.value.email,
      role: formUser.value.role,
      is_active: formUser.value.is_active === 'true',
    })
    userMsgType.value = 'success'
    userMsg.value = `Utilisateur ${data.username} mis à jour`
    users.value = (await authApi.getUsers()).data
    selectUser(data)
  } catch (e) {
    userMsgType.value = 'error'
    userMsg.value = getApiError(e)
  } finally {
    userSubmitting.value = false
  }
}

async function submitGarde() {
  gardeSubmitting.value = true
  gardeMsg.value = ''
  try {
    await rhApi.createPlanningGarde({
      personnel_id: Number(formGarde.value.personnel_id),
      service_id: Number(formGarde.value.service_id),
      type_garde: formGarde.value.type_garde,
      date_debut: new Date(formGarde.value.date_debut).toISOString(),
      date_fin: new Date(formGarde.value.date_fin).toISOString(),
      commentaire: formGarde.value.commentaire,
    })
    gardeMsg.value = 'Garde planifiée'
    gardeMsgType.value = 'success'
    formGarde.value = { personnel_id: '', service_id: '', type_garde: 'JOUR', date_debut: '', date_fin: '', commentaire: '' }
    gardes.value = (await rhApi.getPlanningGardes()).data
  } catch (e) {
    gardeMsg.value = getApiError(e)
    gardeMsgType.value = 'error'
  } finally {
    gardeSubmitting.value = false
  }
}

async function loadData() {
  loading.value = true
  try {
    await loadBasics()
    const [adminStatsRes, userRes, batRes, svcRes, litRes, persRes, gardeRes, presRes, congeRes, auditRes, mfaRes] = await Promise.all([
      adminApi.getStats(),
      authApi.getUsers(),
      hospitalApi.getBatiments(),
      hospitalApi.getServices(),
      hospitalApi.getLitsLibres(),
      rhApi.getPersonnel(),
      rhApi.getPlanningGardes(),
      rhApi.getPresences(),
      rhApi.getConges(),
      auditApi.getLogs(),
      mfaApi.getStatus(),
    ])
    adminStats.value = adminStatsRes.data
    users.value = userRes.data
    batiments.value = batRes.data
    services.value = svcRes.data
    litsLibres.value = (litRes.data || []).map(l => ({
      numero: l.numero, chambre: l.chambre_numero, service: l.service_nom,
    }))
    personnel.value = persRes.data
    gardes.value = gardeRes.data
    presences.value = presRes.data
    conges.value = congeRes.data
    auditLogs.value = auditRes.data
    mfaStatus.value = mfaRes.data
    try {
      connexions.value = (await authApi.getJournalConnexions()).data
    } catch (_) {}
  } catch (e) {
    console.error(getApiError(e))
  } finally {
    loading.value = false
  }
}

async function startMfaSetup() {
  mfaLoading.value = true
  mfaMsg.value = ''
  try {
    const res = await mfaApi.setup()
    mfaSetup.value = res.data
  } catch (e) {
    mfaMsg.value = getApiError(e)
    mfaMsgType.value = 'error'
  } finally {
    mfaLoading.value = false
  }
}

async function verifyMfa() {
  mfaLoading.value = true
  try {
    await mfaApi.verify(totpCode.value)
    mfaMsg.value = 'MFA activée avec succès'
    mfaMsgType.value = 'success'
    mfaSetup.value = {}
    totpCode.value = ''
    const res = await mfaApi.getStatus()
    mfaStatus.value = res.data
  } catch (e) {
    mfaMsg.value = getApiError(e)
    mfaMsgType.value = 'error'
  } finally {
    mfaLoading.value = false
  }
}

async function disableMfa() {
  mfaLoading.value = true
  try {
    await mfaApi.disable(disablePassword.value)
    mfaMsg.value = 'MFA désactivée'
    mfaMsgType.value = 'success'
    disablePassword.value = ''
    const res = await mfaApi.getStatus()
    mfaStatus.value = res.data
  } catch (e) {
    mfaMsg.value = getApiError(e)
    mfaMsgType.value = 'error'
  } finally {
    mfaLoading.value = false
  }
}

onMounted(loadData)

watch(activeTab, (tab) => {
  if (tab === 'governance') loadGovernance()
})
</script>
