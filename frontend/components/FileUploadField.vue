<template>
  <!-- Caricamento di un'immagine o di un PDF con anteprima, sostituzione e rimozione (anche trascinando il file) -->
  <div class="flex flex-col gap-2">
    <span class="text-sm font-semibold text-ink">{{ label }}</span>
    <div
      :class="['flex items-center gap-4 p-3 rounded-xl border bg-white transition-colors',
               dragging ? 'border-wine-800 bg-wine-50' : 'border-line-input border-dashed']"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <!-- anteprima -->
      <div :class="['shrink-0 rounded-lg overflow-hidden border border-line flex items-center justify-center', previewBoxClass]">
        <template v-if="modelValue && type === 'image'">
          <img :src="fullUrl" :alt="`Anteprima: ${label}`" :class="['w-full h-full', kind === 'cover' ? 'object-cover' : 'object-contain p-1']" @error="broken = true" @load="broken = false" />
        </template>
        <FileText v-else-if="type === 'pdf'" :class="modelValue ? '' : 'opacity-40'" class="w-7 h-7 text-wine-800" aria-hidden="true" />
        <ImageIcon v-else class="w-6 h-6 text-ink-mute" aria-hidden="true" />
      </div>

      <div class="flex-1 min-w-0 flex flex-col gap-1.5">
        <p v-if="uploading" class="text-sm text-ink-soft m-0">Caricamento in corso…</p>
        <p v-else-if="broken && modelValue" class="text-sm text-wine-800 m-0">L'immagine non si apre: caricane un'altra.</p>
        <p v-else-if="modelValue && type === 'pdf'" class="text-sm text-ink-soft m-0">
          PDF caricato · <a :href="fullUrl" target="_blank" rel="noopener" class="font-semibold text-wine-800 underline">Apri</a>
        </p>
        <p v-else-if="modelValue" class="text-sm text-ink-soft m-0">Immagine caricata.</p>
        <p v-else class="text-sm text-ink-soft m-0">{{ hint }}</p>
        <div class="flex flex-wrap gap-2">
          <label :class="['btn-ghost btn-sm h-9 cursor-pointer', uploading && 'opacity-50 pointer-events-none']">
            <Upload class="w-4 h-4" aria-hidden="true" />
            {{ modelValue ? 'Sostituisci' : (type === 'pdf' ? 'Carica il PDF' : 'Carica immagine') }}
            <input type="file" :accept="type === 'pdf' ? 'application/pdf,.pdf' : 'image/*'" class="sr-only" @change="onPick" />
          </label>
          <button v-if="modelValue" type="button" class="btn-ghost btn-sm h-9 text-wine-800" @click="$emit('update:modelValue', '')">
            <Trash2 class="w-4 h-4" aria-hidden="true" /> Rimuovi
          </button>
        </div>
      </div>
    </div>
    <p v-if="error" role="alert" class="text-[13px] text-wine-800 font-semibold m-0">{{ error }}</p>
  </div>
</template>

<script setup>
import { Upload, Trash2, FileText, Image as ImageIcon } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, required: true },
  hint: { type: String, default: 'Trascina qui il file oppure usa il pulsante.' },
  type: { type: String, default: 'image' },   // 'image' | 'pdf'
  kind: { type: String, default: 'logo' }     // 'logo' | 'cover' | 'bottle': forma dell'anteprima
})
const emit = defineEmits(['update:modelValue'])

const { fetchWithAuth, mediaBase } = useApi()
const uploading = ref(false)
const dragging = ref(false)
const error = ref('')
const broken = ref(false)

const fullUrl = computed(() => {
  const url = props.modelValue || ''
  return url.startsWith('http') ? url : `${mediaBase}${url}`
})
const previewBoxClass = computed(() => ({
  cover: 'w-[120px] h-[68px] bg-sand',
  bottle: 'w-[60px] h-[84px] bg-white',
  logo: 'w-[72px] h-[72px] bg-white'
}[props.kind] || 'w-[72px] h-[72px] bg-white'))

const upload = async (file) => {
  if (!file) return
  error.value = ''
  if (props.type === 'pdf' && !/\.pdf$/i.test(file.name)) {
    error.value = 'Scegli un file PDF.'
    return
  }
  if (props.type === 'image' && !file.type.startsWith('image/')) {
    error.value = 'Scegli un\'immagine (JPG, PNG o WebP).'
    return
  }
  const formData = new FormData()
  formData.append('file', file)
  uploading.value = true
  try {
    const res = await fetchWithAuth(props.type === 'pdf' ? '/uploads/document' : '/uploads/image', { method: 'POST', body: formData })
    broken.value = false
    emit('update:modelValue', res.url)
  } catch (err) {
    error.value = apiErrorMessage(err, 'Caricamento non riuscito: riprova.')
  } finally {
    uploading.value = false
  }
}

const onPick = (e) => {
  upload(e.target.files?.[0])
  e.target.value = ''
}
const onDrop = (e) => {
  dragging.value = false
  upload(e.dataTransfer?.files?.[0])
}
</script>
