<template>
  <div class="space-y-4">
    <!-- Zone upload drag & drop -->
    <div
      @drop.prevent="handleDrop"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      :class="[
        'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition',
        isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
      ]"
    >
      <input
        type="file"
        ref="fileInput"
        @change="handleFileSelect"
        :accept="acceptedMimes"
        multiple
        class="hidden"
      />
      
      <div @click="fileInput.$el.click()" class="cursor-pointer">
        <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
          <path d="M28 8H12a4 4 0 00-4 4v20a4 4 0 004 4h24a4 4 0 004-4V20m-8-12l-4-4m0 0l-4 4m4-4v12m-8 8h8m-8 4h8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <p class="mt-2 text-sm font-medium text-gray-900">
          Glissez-déposez les images ici ou <span class="text-blue-600">parcourez</span>
        </p>
        <p class="mt-1 text-xs text-gray-500">
          PNG, JPG, GIF, WebP jusqu'à 5 MB
        </p>
      </div>
    </div>

    <!-- Liste uploads en cours -->
    <div v-if="uploads.length > 0" class="space-y-2">
      <p class="text-sm font-medium text-gray-700">Uploads en cours</p>
      <div v-for="(upload, idx) in uploads" :key="idx" class="flex items-center justify-between p-3 bg-gray-50 rounded">
        <div class="flex-1">
          <p class="text-sm font-medium">{{ upload.name }}</p>
          <div class="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div
              class="bg-blue-600 h-2 rounded-full transition"
              :style="{ width: upload.progress + '%' }"
            />
          </div>
        </div>
        <span v-if="upload.progress === 100" class="text-green-600 ml-3">✓</span>
        <span v-else class="text-gray-500 ml-3">{{ upload.progress }}%</span>
      </div>
    </div>

    <!-- Erreurs -->
    <div v-if="error" class="p-4 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- Succès -->
    <div v-if="successMessage" class="p-4 bg-green-50 border border-green-200 rounded text-green-700 text-sm">
      {{ successMessage }}
    </div>

    <!-- Images uploadées -->
    <div v-if="uploadedImages.length > 0" class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div v-for="img in uploadedImages" :key="img.id" class="relative group">
        <img
          :src="img.url"
          :alt="img.nom_original"
          class="w-full h-24 object-cover rounded border border-gray-200 group-hover:shadow-md transition"
        />
        <button
          @click="deleteImage(img.id)"
          class="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition"
        >
          ✕
        </button>
        <p class="text-xs text-gray-500 mt-1 truncate">{{ img.nom_original }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import apiClient from '@/api/client'

const props = defineProps({
  contenuType: {
    type: String,
    default: 'general'
  },
  contenuId: {
    type: Number,
    default: null
  },
  acceptedMimes: {
    type: String,
    default: 'image/jpeg,image/png,image/webp,image/gif'
  }
})

const emit = defineEmits(['upload-success', 'delete-success'])

const fileInput = ref(null)
const isDragging = ref(false)
const uploads = ref([])
const uploadedImages = ref([])
const error = ref(null)
const successMessage = ref(null)

const handleFileSelect = async (event) => {
  const files = Array.from(event.target.files)
  await uploadFiles(files)
}

const handleDrop = async (event) => {
  isDragging.value = false
  const files = Array.from(event.dataTransfer.files)
  await uploadFiles(files)
}

const uploadFiles = async (files) => {
  error.value = null
  successMessage.value = null

  for (const file of files) {
    const uploadId = Date.now() + Math.random()
    const upload = {
      name: file.name,
      progress: 0,
      id: uploadId
    }
    uploads.value.push(upload)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('contenu_type', props.contenuType)
      if (props.contenuId) {
        formData.append('contenu_id', props.contenuId)
      }

      // Endpoint pour les images
      const response = await apiClient.post('/files/upload/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100)
          upload.progress = progress
        }
      })

      uploadedImages.value.push(response.data)
      upload.progress = 100
      successMessage.value = `${file.name} uploadé avec succès`
      emit('upload-success', response.data)

      // Effacer après 3 secondes
      setTimeout(() => {
        uploads.value = uploads.value.filter(u => u.id !== uploadId)
      }, 2000)
    } catch (err) {
      error.value = `Erreur upload ${file.name}: ${err.response?.data?.detail || err.message}`
      uploads.value = uploads.value.filter(u => u.id !== uploadId)
    }
  }

  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const deleteImage = async (imageId) => {
  try {
    await apiClient.delete(`/files/uploads/${imageId}`)
    uploadedImages.value = uploadedImages.value.filter(img => img.id !== imageId)
    emit('delete-success', imageId)
  } catch (err) {
    error.value = `Erreur suppression: ${err.message}`
  }
}

// Charger les images uploadées au montage
const loadUploadedImages = async () => {
  try {
    const response = await apiClient.get('/files/uploads', {
      params: {
        contenu_type: props.contenuType,
        contenu_id: props.contenuId,
        limit: 20
      }
    })
    uploadedImages.value = response.data
  } catch (err) {
    console.error('Erreur chargement images:', err)
  }
}

// Charger les images au montage
const { onMounted } = await import('vue')
onMounted(loadUploadedImages)
</script>
