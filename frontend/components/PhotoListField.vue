<template>
  <!-- Foto del vino: più immagini con anteprima; la prima è quella principale -->
  <div class="flex flex-col gap-2">
    <span class="text-sm font-semibold text-ink">{{ label }}</span>
    <div
      :class="['p-3 rounded-xl border bg-white transition-colors',
               dragging ? 'border-wine-800 bg-wine-50' : 'border-line-input border-dashed']"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <ul v-if="modelValue.length" class="flex flex-wrap gap-3 list-none p-0 m-0 mb-3">
        <li v-for="(url, i) in modelValue" :key="url + i" class="relative w-[84px]">
          <div :class="['w-[84px] h-[112px] rounded-lg overflow-hidden border bg-white flex items-center justify-center', i === 0 ? 'border-wine-800 ring-2 ring-wine-800/20' : 'border-line']">
            <img :src="full(url)" :alt="`Foto ${i + 1}`" class="w-full h-full object-contain p-1" />
          </div>
          <span v-if="i === 0" class="block text-[11px] font-semibold text-wine-800 text-center mt-1">Principale</span>
          <button v-else type="button" class="block w-full text-[11px] font-semibold text-ink-soft hover:text-wine-800 text-center mt-1" @click="makeMain(i)">Rendi principale</button>
          <button type="button" class="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-white border border-line shadow text-ink-soft hover:text-wine-800 flex items-center justify-center" :aria-label="`Rimuovi la foto ${i + 1}`" @click="remove(i)">
            <X class="w-3.5 h-3.5" aria-hidden="true" />
          </button>
        </li>
      </ul>
      <div class="flex flex-wrap items-center gap-3">
        <label :class="['btn-ghost btn-sm h-9 cursor-pointer', (uploading || modelValue.length >= max) && 'opacity-50 pointer-events-none']">
          <Upload class="w-4 h-4" aria-hidden="true" />
          {{ modelValue.length ? 'Aggiungi foto' : 'Carica foto' }}
          <input type="file" accept="image/*" multiple class="sr-only" @change="onPick" />
        </label>
        <span class="text-sm text-ink-soft">
          {{ uploading ? 'Caricamento in corso…' : (modelValue.length ? `${modelValue.length} di ${max} foto` : hint) }}
        </span>
      </div>
    </div>
    <p v-if="error" role="alert" class="text-[13px] text-wine-800 font-semibold m-0">{{ error }}</p>
  </div>
</template>

<script setup>
import { Upload, X } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: 'Foto della bottiglia' },
  hint: { type: String, default: 'Trascina qui le immagini (JPG, PNG o WebP): la prima sarà quella principale.' },
  max: { type: Number, default: 6 }
})
const emit = defineEmits(['update:modelValue'])

const { fetchWithAuth, mediaBase } = useApi()
const uploading = ref(false)
const dragging = ref(false)
const error = ref('')

const full = (url) => (url || '').startsWith('http') ? url : `${mediaBase}${url}`

const uploadAll = async (fileList) => {
  const files = Array.from(fileList || []).filter(f => f.type.startsWith('image/'))
  if (!files.length) { error.value = 'Scegli un\'immagine (JPG, PNG o WebP).'; return }
  error.value = ''
  const list = [...props.modelValue]
  uploading.value = true
  try {
    for (const file of files) {
      if (list.length >= props.max) { error.value = `Puoi caricare al massimo ${props.max} foto.`; break }
      const formData = new FormData()
      formData.append('file', file)
      const res = await fetchWithAuth('/uploads/image', { method: 'POST', body: formData })
      list.push(res.url)
      emit('update:modelValue', [...list])
    }
  } catch (err) {
    error.value = apiErrorMessage(err, 'Caricamento non riuscito: riprova.')
  } finally {
    uploading.value = false
  }
}

const remove = (i) => emit('update:modelValue', props.modelValue.filter((_, idx) => idx !== i))
const makeMain = (i) => {
  const list = [...props.modelValue]
  const [item] = list.splice(i, 1)
  emit('update:modelValue', [item, ...list])
}
const onPick = (e) => { uploadAll(e.target.files); e.target.value = '' }
const onDrop = (e) => { dragging.value = false; uploadAll(e.dataTransfer?.files) }
</script>
