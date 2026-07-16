import { ref, computed } from 'vue'
import { clinicalApi, hospitalApi, authApi } from '../api/modules'

export function useLookups() {
  const patients = ref([])
  const admissions = ref([])
  const services = ref([])
  const users = ref([])
  const loading = ref(false)

  const patientOptions = computed(() =>
    patients.value.map((p) => ({
      value: p.id,
      label: `${p.nom} ${p.prenom} (${p.numero_dossier})`,
    })),
  )

  const admissionOptions = computed(() =>
    admissions.value.map((a) => ({
      value: a.id,
      label: `#${a.id} — ${a.patient_nom} · ${a.service_nom}`,
      version: a.version ?? 0,
      patient_id: a.patient_id,
      patient_nom: a.patient_nom,
    })),
  )

  const medecinOptions = computed(() =>
    users.value
      .filter((u) => u.role === 'MEDECIN')
      .map((u) => ({
        value: u.id,
        label: u.first_name ? `${u.first_name} ${u.last_name}` : u.username,
      })),
  )

  const serviceOptions = computed(() =>
    services.value.map((s) => ({ value: s.id, label: `${s.code} — ${s.nom}` })),
  )

  async function loadPatients() {
    patients.value = (await clinicalApi.getPatients()).data
  }

  async function loadAdmissions() {
    admissions.value = (await clinicalApi.getAdmissionsActives()).data
  }

  async function loadServices() {
    services.value = (await hospitalApi.getServices()).data
  }

  async function loadUsers() {
    users.value = (await authApi.getUsers()).data
  }

  async function loadMedecins() {
    users.value = (await authApi.getMedecins()).data.map(m => ({ ...m, role: 'MEDECIN' }))
  }

  async function loadBasics(includeMedecins = false) {
    loading.value = true
    try {
      const tasks = [loadPatients(), loadAdmissions(), loadServices()]
      if (includeMedecins) tasks.push(loadMedecins())
      await Promise.all(tasks)
    } finally {
      loading.value = false
    }
  }

  function admissionsForPatient(patientId) {
    return admissionOptions.value.filter((a) => a.patient_id === Number(patientId))
  }

  return {
    patients,
    admissions,
    services,
    users,
    loading,
    patientOptions,
    admissionOptions,
    medecinOptions,
    serviceOptions,
    loadPatients,
    loadAdmissions,
    loadServices,
    loadUsers,
    loadMedecins,
    loadBasics,
    admissionsForPatient,
  }
}
