<template>
  <!-- Unisce una voce duplicata in un'altra: i vini passano al nome scelto e il doppione sparisce -->
  <div class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" :aria-label="`Unisci ${item.name}`" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-line space-y-4">
      <div class="flex items-start justify-between gap-3">
        <div>
          <h3 class="font-sans text-lg font-bold text-ink m-0">Unisci «{{ item.name }}»</h3>
          <p class="text-sm text-ink-mute mt-1 mb-0">
            Scegli la voce corretta: tutti i vini che usano «{{ item.name }}» passeranno a quella e «{{ item.name }}» verrà eliminata.
          </p>
        </div>
        <button type="button" class="p-1 text-ink-mute hover:text-ink" aria-label="Chiudi" @click="$emit('close')"><X class="w-5 h-5" aria-hidden="true" /></button>
      </div>

      <div>
        <label for="merge-filter" class="block text-sm font-semibold text-ink mb-1">Unisci in…</label>
        <input id="merge-filter" v-model="query" type="search" placeholder="Cerca la voce di destinazione" class="input h-10 text-sm" />
        <ul class="mt-2 max-h-[260px] overflow-y-auto border border-line rounded-xl divide-y divide-stone-100 list-none p-0 m-0">
          <li v-for="t in candidates" :key="t.id">
            <button type="button"
              :class="['w-full text-left px-3 py-2 text-sm', targetId === t.id ? 'bg-wine-800 text-white font-semibold' : 'hover:bg-stone-50 text-ink']"
              @click="targetId = t.id">
              {{ t.name }}
            </button>
          </li>
          <li v-if="!candidates.length" class="px-3 py-3 text-sm text-ink-mute">Nessuna voce trovata.</li>
        </ul>
      </div>

      <p v-if="error" role="alert" class="text-sm text-wine-800 font-semibold m-0">{{ error }}</p>

      <div class="flex justify-end gap-3">
        <button type="button" class="btn-ghost btn-sm h-10" @click="$emit('close')">Annulla</button>
        <button type="button" class="btn-primary btn-sm h-10" :disabled="!targetId || busy" @click="merge">
          {{ busy ? 'Unione in corso…' : `Unisci in «${targetName}»` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { X } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

const props = defineProps({
  endpoint: { type: String, required: true },   // es. '/grapes'
  item: { type: Object, required: true },
  items: { type: Array, default: () => [] }
})
const emit = defineEmits(['close', 'merged'])

const { fetchWithAuth } = useApi()
const toast = useToast()
const query = ref('')
const targetId = ref('')
const busy = ref(false)
const error = ref('')

const norm = (s) => (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
const candidates = computed(() => {
  const q = norm(query.value.trim())
  return props.items
    .filter(t => t.id !== props.item.id)
    .filter(t => !q || norm(t.name).includes(q))
    .sort((a, b) => a.name.localeCompare(b.name, 'it'))
})
const targetName = computed(() => props.items.find(t => t.id === targetId.value)?.name || '…')

const merge = async () => {
  busy.value = true
  error.value = ''
  try {
    const res = await fetchWithAuth(`${props.endpoint}/${props.item.id}/merge`, { method: 'POST', body: { target_id: targetId.value } })
    const n = res?.products_updated || 0
    toast.success(`${res?.message || 'Voci unite'}${n ? ` · ${n === 1 ? '1 vino aggiornato' : `${n} vini aggiornati`}` : ''}`)
    emit('merged')
  } catch (err) {
    error.value = apiErrorMessage(err, 'Unione non riuscita: riprova.')
  } finally {
    busy.value = false
  }
}
</script>
