<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4" @click.self="close" @keydown.esc="close">
    <div class="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative border border-stone-100" role="dialog" aria-modal="true" aria-labelledby="richiesta-evento-titolo">
      <button type="button" class="absolute top-5 right-5 text-stone-400 hover:text-stone-700 p-1.5 rounded-full hover:bg-stone-100" aria-label="Chiudi" @click="close">
        <X class="w-5 h-5" aria-hidden="true" />
      </button>

      <div class="mb-5 pr-8">
        <span class="text-xs font-bold text-wine-800 uppercase tracking-widest block mb-1">Richiesta di partecipazione</span>
        <h3 id="richiesta-evento-titolo" class="font-serif text-2xl font-bold text-stone-900">{{ event.title }}</h3>
        <p class="text-sm text-stone-500 mt-1">
          Organizza {{ organizerName }}. La richiesta non è ancora una prenotazione: ti risponderanno via email per confermare.
        </p>
      </div>

      <div v-if="sent" role="status" class="py-6 flex flex-col items-center text-center gap-3">
        <span class="w-12 h-12 rounded-full bg-emerald-50 text-emerald-700 flex items-center justify-center"><CheckCircle class="w-6 h-6" aria-hidden="true" /></span>
        <p class="font-semibold text-stone-800">{{ sent }}</p>
        <p class="text-xs text-stone-500">Ti abbiamo mandato un riepilogo via email.</p>
        <button type="button" class="mt-2 px-5 py-2 rounded-xl border border-stone-200 text-sm font-semibold text-stone-700 hover:bg-stone-50" @click="close">Chiudi</button>
      </div>

      <form v-else class="space-y-4" @submit.prevent="submit">
        <div class="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_110px] gap-4">
          <label class="block">
            <span class="block text-xs font-semibold text-stone-700 mb-1">Data *</span>
            <select v-model.number="form.date_index" required class="select h-11 text-sm">
              <option v-for="d in availableDates" :key="d.index" :value="d.index">{{ d.label }}</option>
            </select>
          </label>
          <label class="block">
            <span class="block text-xs font-semibold text-stone-700 mb-1">Persone *</span>
            <input v-model.number="form.people" type="number" min="1" max="50" required class="input h-11 text-sm" />
          </label>
        </div>
        <label class="block">
          <span class="block text-xs font-semibold text-stone-700 mb-1">Nome e cognome *</span>
          <input v-model="form.user_name" type="text" required autocomplete="name" class="input h-11 text-sm" />
        </label>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="block">
            <span class="block text-xs font-semibold text-stone-700 mb-1">Email *</span>
            <input v-model="form.user_email" type="email" required autocomplete="email" class="input h-11 text-sm" />
          </label>
          <label class="block">
            <span class="block text-xs font-semibold text-stone-700 mb-1">Telefono</span>
            <input v-model="form.user_phone" type="tel" autocomplete="tel" placeholder="Facoltativo" class="input h-11 text-sm" />
          </label>
        </div>
        <label class="block">
          <span class="block text-xs font-semibold text-stone-700 mb-1">Note per l'organizzatore</span>
          <textarea v-model="form.message" rows="3" placeholder="Es. allergie o intolleranze, bambini, orario di arrivo…" class="input text-sm py-2.5 h-auto"></textarea>
        </label>
        <label class="flex items-start gap-2.5 text-xs text-stone-600 cursor-pointer">
          <input v-model="form.privacy_accepted" type="checkbox" required class="mt-0.5 w-4 h-4 accent-wine-800 shrink-0" />
          <span>
            Acconsento all'invio dei miei dati a {{ organizerName }} per organizzare la partecipazione, come descritto
            nell'<NuxtLink to="/privacy" target="_blank" class="font-semibold text-wine-800 underline underline-offset-2">informativa sulla privacy</NuxtLink>.
          </span>
        </label>

        <p v-if="error" role="alert" class="p-3.5 bg-rose-50 text-rose-800 rounded-xl text-xs font-semibold border border-rose-200 m-0">{{ error }}</p>

        <div class="pt-1 flex justify-end gap-3">
          <button type="button" class="px-4 py-2.5 text-sm text-stone-600 hover:text-stone-800 font-medium" @click="close">Annulla</button>
          <button type="submit" :disabled="submitting" class="btn-primary btn-sm h-11">
            <Send class="w-4 h-4" aria-hidden="true" />
            {{ submitting ? 'Invio in corso…' : 'Invia la richiesta' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { X, Send, CheckCircle } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

const props = defineProps({
  isOpen: Boolean,
  event: { type: Object, required: true },
  initialDate: { type: Number, default: null }
})
const emit = defineEmits(['close'])
const { fetchWithAuth } = useApi()

const availableDates = computed(() => (props.event.dates || [])
  .map((d, index) => ({ ...d, index }))
  .filter(d => !d.is_past))
const organizerName = computed(() => props.event.organizer?.name || 'l\'organizzatore')

const form = reactive({
  date_index: 0, people: 2, user_name: '', user_email: '', user_phone: '', message: '', privacy_accepted: false
})
const submitting = ref(false)
const error = ref('')
const sent = ref('')

watch(() => props.isOpen, (open) => {
  if (!open) return
  sent.value = ''
  error.value = ''
  const wanted = availableDates.value.find(d => d.index === props.initialDate)
  form.date_index = (wanted || availableDates.value[0])?.index ?? 0
}, { immediate: true })

const close = () => emit('close')

const submit = async () => {
  submitting.value = true
  error.value = ''
  try {
    const res = await fetchWithAuth(`/events/${props.event.id}/requests`, { method: 'POST', body: { ...form } })
    sent.value = res?.message || 'Richiesta inviata.'
    form.message = ''
    form.privacy_accepted = false
  } catch (err) {
    error.value = apiErrorMessage(err, 'Invio non riuscito: riprova tra poco.')
  } finally {
    submitting.value = false
  }
}
</script>
