<template>
  <form class="flex flex-col gap-8 card p-6 sm:p-8" novalidate @submit.prevent="save(form.status)">
    <!-- Cosa -->
    <section class="flex flex-col gap-4" aria-labelledby="ev-cosa">
      <h2 id="ev-cosa" class="font-serif text-2xl font-bold text-ink">L'evento</h2>
      <div class="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_220px] gap-4">
        <label class="field-label">Titolo *
          <input v-model="form.title" type="text" required maxlength="150" placeholder="es. Degustazione in vigna al tramonto" class="input" />
        </label>
        <label class="field-label">Tipo
          <select v-model="form.type" class="select">
            <option v-for="(label, key) in EVENT_TYPES" :key="key" :value="key">{{ label }}</option>
          </select>
        </label>
      </div>
      <label class="field-label">Descrizione
        <textarea v-model="form.description" rows="6" maxlength="8000" class="input h-auto py-3"
          placeholder="Cosa si fa, cosa si assaggia, durata, cosa portare, se è adatto ai bambini…"></textarea>
        <span class="text-[13px] font-normal text-ink-mute">Puoi andare a capo per creare paragrafi; le righe che iniziano con «- » diventano un elenco.</span>
      </label>
      <FileUploadField v-model="form.cover_image" label="Immagine di copertina" kind="cover"
        hint="Facoltativa: una foto orizzontale. Senza foto usiamo un'illustrazione." />
    </section>

    <!-- Quando -->
    <section class="flex flex-col gap-4" aria-labelledby="ev-quando">
      <div>
        <h2 id="ev-quando" class="font-serif text-2xl font-bold text-ink">Quando</h2>
        <p class="text-sm text-ink-soft mt-1 mb-0">Se l'evento si ripete (es. ogni sabato di ottobre) aggiungi più date: è un solo evento con più appuntamenti.</p>
      </div>
      <ul class="list-none m-0 p-0 flex flex-col gap-3">
        <li v-for="(d, i) in form.dates" :key="d.key" class="p-4 rounded-xl border border-line bg-cream/40 flex flex-col gap-3">
          <div class="grid grid-cols-2 sm:grid-cols-[minmax(0,1fr)_130px_130px_auto] gap-3 items-end">
            <label class="field-label col-span-2 sm:col-span-1">{{ d.multiDay ? 'Dal giorno' : 'Giorno' }} *
              <input v-model="d.date" type="date" required class="input" />
            </label>
            <label class="field-label">Inizio
              <input v-model="d.startTime" type="time" class="input" />
            </label>
            <label v-if="!d.multiDay" class="field-label">Fine
              <input v-model="d.endTime" type="time" class="input" />
            </label>
            <button v-if="form.dates.length > 1" type="button" class="btn-ghost btn-sm h-12 text-wine-800 col-span-2 sm:col-span-1" :aria-label="`Togli la data ${i + 1}`" @click="removeDate(i)">
              <Trash2 class="w-4 h-4" aria-hidden="true" /> Togli
            </button>
          </div>
          <div v-if="d.multiDay" class="grid grid-cols-2 sm:grid-cols-[minmax(0,1fr)_130px] gap-3">
            <label class="field-label">Al giorno *
              <input v-model="d.endDate" type="date" :min="d.date" class="input" />
            </label>
            <label class="field-label">Orario di chiusura
              <input v-model="d.endTime" type="time" class="input" />
            </label>
          </div>
          <label class="inline-flex items-center gap-2 text-sm text-ink-soft cursor-pointer w-fit">
            <input v-model="d.multiDay" type="checkbox" class="w-4 h-4 accent-wine-800" />
            Dura più giorni (es. una fiera dal venerdì alla domenica)
          </label>
        </li>
      </ul>
      <button type="button" class="btn-ghost btn-sm w-fit" :disabled="form.dates.length >= 40" @click="addDate">
        <Plus class="w-4 h-4" aria-hidden="true" /> Aggiungi un'altra data
      </button>
    </section>

    <!-- Chi organizza (admin) -->
    <section v-if="isAdmin" class="flex flex-col gap-4" aria-labelledby="ev-chi">
      <h2 id="ev-chi" class="font-serif text-2xl font-bold text-ink">Chi organizza</h2>
      <label class="field-label">Cantina organizzatrice
        <select v-model="form.producer_id" class="select">
          <option value="">Nessuna: evento del territorio (fiera, sagra, festival…)</option>
          <option v-for="p in producers" :key="p.id" :value="p.id">{{ p.company_name }}</option>
        </select>
      </label>
      <div class="flex flex-col gap-2">
        <span class="text-sm font-semibold text-ink">Cantine partecipanti</span>
        <p class="text-[13px] text-ink-mute m-0">Compaiono nella pagina dell'evento e l'evento compare nelle loro pagine.</p>
        <input v-model="participantSearch" type="search" placeholder="Cerca una cantina" class="input h-10 text-sm max-w-[360px]" />
        <div class="max-h-[220px] overflow-y-auto border border-line rounded-xl p-2 grid grid-cols-1 sm:grid-cols-2 gap-1">
          <label v-for="p in participantChoices" :key="p.id" class="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-sand-100 text-sm cursor-pointer">
            <input v-model="form.participant_ids" type="checkbox" :value="p.id" class="w-4 h-4 accent-wine-800" />
            <span class="truncate">{{ p.company_name }}</span>
          </label>
        </div>
        <span class="text-[13px] text-ink-mute">{{ form.participant_ids.length }} selezionate</span>
      </div>
      <label v-if="!form.producer_id" class="field-label">Email per le richieste di partecipazione
        <input v-model="form.contact_email" type="email" placeholder="es. info@prolocolarino.it" class="input" />
        <span class="text-[13px] font-normal text-ink-mute">Se la lasci vuota, le richieste arrivano agli amministratori del portale.</span>
      </label>
    </section>

    <!-- Dove -->
    <section class="flex flex-col gap-4" aria-labelledby="ev-dove">
      <h2 id="ev-dove" class="font-serif text-2xl font-bold text-ink">Dove</h2>
      <div v-if="hasOrganizer" role="radiogroup" aria-label="Luogo" class="flex flex-col sm:flex-row gap-2">
        <label :class="['flex items-center gap-2 px-4 h-12 rounded-xl border cursor-pointer text-sm font-semibold', form.use_producer_address ? 'border-wine-800 bg-wine-50 text-wine-900' : 'border-line-input bg-white text-ink']">
          <input v-model="form.use_producer_address" type="radio" :value="true" class="accent-wine-800" /> Presso la cantina
        </label>
        <label :class="['flex items-center gap-2 px-4 h-12 rounded-xl border cursor-pointer text-sm font-semibold', !form.use_producer_address ? 'border-wine-800 bg-wine-50 text-wine-900' : 'border-line-input bg-white text-ink']">
          <input v-model="form.use_producer_address" type="radio" :value="false" class="accent-wine-800" /> In un altro luogo
        </label>
      </div>
      <p v-if="hasOrganizer && form.use_producer_address" class="text-sm text-ink-soft m-0">
        Usiamo l'indirizzo e la posizione sulla mappa del profilo della cantina.
      </p>
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label class="field-label sm:col-span-2">Nome del luogo
          <input v-model="form.location.name" type="text" placeholder="es. Piazza del Municipio, Agriturismo Le Querce…" class="input" />
        </label>
        <label class="field-label">Comune *
          <input v-model="form.location.city" type="text" list="ev-comuni" class="input" />
        </label>
        <datalist id="ev-comuni"><option v-for="t in towns" :key="t" :value="t" /></datalist>
        <label class="field-label">Provincia
          <select v-model="form.location.province" class="select">
            <option value="">—</option>
            <option value="CB">Campobasso (CB)</option>
            <option value="IS">Isernia (IS)</option>
          </select>
        </label>
        <label class="field-label sm:col-span-2">Indirizzo
          <input v-model="form.location.street" type="text" class="input" />
        </label>
        <div class="sm:col-span-2 flex flex-col gap-2">
          <span class="text-sm font-semibold text-ink">Punto sulla mappa</span>
          <ClientOnly>
            <LocationPicker :lat="form.location.lat" :lng="form.location.lng" :town="form.location.city" @update="onPickLocation" />
          </ClientOnly>
        </div>
      </div>
    </section>

    <!-- Vini -->
    <section class="flex flex-col gap-3" aria-labelledby="ev-vini">
      <div>
        <h2 id="ev-vini" class="font-serif text-2xl font-bold text-ink">Vini in degustazione</h2>
        <p class="text-sm text-ink-soft mt-1 mb-0">Facoltativo: i vini scelti rimandano all'evento e viceversa.</p>
      </div>
      <p v-if="!wineChoices.length" class="text-sm text-ink-mute m-0">
        {{ hasOrganizer || form.participant_ids.length ? 'Nessun vino pubblicato da mostrare.' : 'Scegli la cantina organizzatrice o le partecipanti per vedere i loro vini.' }}
      </p>
      <div v-else class="flex flex-wrap gap-2">
        <button
          v-for="w in wineChoices"
          :key="w.id"
          type="button"
          :aria-pressed="form.product_ids.includes(w.id)"
          :class="['chip', form.product_ids.includes(w.id) ? 'bg-wine-800 text-white border-wine-800' : 'chip-outline']"
          @click="toggleWine(w.id)"
        >
          {{ w.name }}<span v-if="showWineProducer" class="opacity-70"> · {{ w.producer_name }}</span>
        </button>
      </div>
    </section>

    <!-- Costo e partecipazione -->
    <section class="flex flex-col gap-4" aria-labelledby="ev-partecipazione">
      <h2 id="ev-partecipazione" class="font-serif text-2xl font-bold text-ink">Costo e partecipazione</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label class="field-label">Costo
          <select v-model="form.price_type" class="select">
            <option value="FREE">Gratuito</option>
            <option value="PAID">A pagamento</option>
          </select>
        </label>
        <label v-if="form.price_type === 'PAID'" class="field-label">Prezzo indicativo
          <input v-model="form.price_text" type="text" maxlength="120" placeholder="es. 25 € a persona" class="input" />
        </label>
      </div>
      <fieldset class="flex flex-col gap-2 border-0 p-0 m-0">
        <legend class="text-sm font-semibold text-ink mb-1">Come si partecipa</legend>
        <label v-for="opt in bookingOptions" :key="opt.value" :class="['flex items-start gap-3 p-3 rounded-xl border cursor-pointer', form.booking_mode === opt.value ? 'border-wine-800 bg-wine-50' : 'border-line-input bg-white']">
          <input v-model="form.booking_mode" type="radio" :value="opt.value" class="mt-1 accent-wine-800" />
          <span class="flex flex-col">
            <span class="text-sm font-semibold text-ink">{{ opt.label }}</span>
            <span class="text-[13px] text-ink-mute">{{ opt.hint }}</span>
          </span>
        </label>
      </fieldset>
      <label v-if="form.booking_mode === 'EXTERNAL'" class="field-label">Link per prenotare *
        <input v-model="form.external_url" type="url" placeholder="https://…" class="input" />
      </label>
    </section>

    <!-- Pubblicazione -->
    <section class="flex flex-col gap-3 border-t border-line pt-6">
      <p v-if="error" role="alert" class="m-0 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-sm font-semibold text-rose-800">{{ error }}</p>
      <p v-if="cancelled" class="m-0 text-sm text-wine-800 font-semibold">Questo evento è annullato: puoi correggerne i dati ma resta annullato.</p>
      <div class="flex flex-wrap items-center justify-between gap-3">
        <NuxtLink to="/dashboard/eventi" class="btn-ghost">Annulla</NuxtLink>
        <div class="flex flex-wrap gap-3">
          <button type="button" class="btn-ghost" :disabled="saving" @click="save('DRAFT')">
            {{ form.status === 'PUBLISHED' && isEdit ? 'Riporta in bozza' : 'Salva come bozza' }}
          </button>
          <button type="button" class="btn-primary" :disabled="saving" @click="save('PUBLISHED')">
            {{ saving ? 'Salvataggio…' : (isEdit && form.status === 'PUBLISHED' ? 'Salva le modifiche' : 'Pubblica l\'evento') }}
          </button>
        </div>
      </div>
      <p class="m-0 text-[13px] text-ink-mute">
        Pubblicato, l'evento compare subito nel calendario del sito{{ isAdmin ? '' : ' (dopo l\'approvazione della cantina, se è ancora in attesa)' }}.
      </p>
    </section>
  </form>
</template>

<script setup>
import { Plus, Trash2 } from 'lucide-vue-next'
import FileUploadField from '~/components/FileUploadField.vue'
import LocationPicker from '~/components/LocationPicker.client.vue'
import { EVENT_TYPES, joinLocal, splitLocal } from '~/utils/events'
import { apiErrorMessage } from '~/utils/apiError'

const props = defineProps({
  initial: { type: Object, default: null }   // evento esistente (modifica) o modello di partenza
})
const emit = defineEmits(['saved'])

const { fetchWithAuth } = useApi()
const { user, isAdmin } = useAuth()

const towns = ['Acquaviva Collecroce', 'Agnone', 'Bojano', 'Campobasso', 'Campomarino', 'Casacalenda', 'Castropignano', 'Colletorto',
  'Guardialfiera', 'Guglionesi', 'Isernia', 'Larino', 'Macchia d\'Isernia', 'Mafalda', 'Montecilfone', 'Montenero di Bisaccia',
  'Monteroduni', 'Montorio nei Frentani', 'Palata', 'Petacciato', 'Petrella Tifernina', 'Portocannone', 'Pozzilli', 'Ripalimosani',
  'Rotello', 'San Felice del Molise', 'San Giacomo degli Schiavoni', 'San Martino in Pensilis', 'Santa Croce di Magliano',
  'Sesto Campano', 'Termoli', 'Ururi', 'Venafro']
const bookingOptions = [
  { value: 'REQUEST', label: 'Richiesta dal sito', hint: 'Il visitatore compila un modulo: ricevi un\'email e la trovi in «Richieste». Confermi tu rispondendo.' },
  { value: 'EXTERNAL', label: 'Prenotazione su un altro sito', hint: 'Il pulsante porta al tuo sito o a un servizio di biglietteria.' },
  { value: 'NONE', label: 'Ingresso libero', hint: 'Nessuna prenotazione: basta presentarsi.' }
]

let keySeq = 0
const dateRow = (d = {}) => {
  const start = splitLocal(d.start)
  const end = splitLocal(d.end)
  const multiDay = !!(end.date && start.date && end.date !== start.date)
  return { key: ++keySeq, date: start.date, startTime: start.time && start.time !== '00:00' ? start.time : '', endTime: end.time, endDate: multiDay ? end.date : '', multiDay }
}

const ownProducerId = computed(() => user.value?.producer_id || user.value?.producer?.id || '')
const ev = props.initial
const isEdit = !!ev?.id
const form = reactive({
  title: ev?.title || '',
  type: ev?.type || 'DEGUSTAZIONE',
  description: ev?.description || '',
  cover_image: ev?.cover_image || '',
  dates: ev?.dates?.length ? ev.dates.map(dateRow) : [dateRow()],
  use_producer_address: ev ? !!ev.use_producer_address : true,
  location: { name: '', street: '', city: '', province: '', lat: null, lng: null, ...(ev?.raw_location || {}) },
  producer_id: ev ? (ev.producer_id || '') : (isAdmin.value ? '' : ownProducerId.value),
  participant_ids: [...(ev?.participant_ids || [])],
  product_ids: [...(ev?.product_ids || [])],
  price_type: ev?.price_type || 'FREE',
  price_text: ev?.price_text || '',
  booking_mode: ev?.booking_mode || 'REQUEST',
  external_url: ev?.external_url || '',
  contact_email: ev?.contact_email || '',
  status: ev?.status === 'DRAFT' ? 'DRAFT' : 'PUBLISHED'
})
const cancelled = ev?.status === 'CANCELLED'
const saving = ref(false)
const error = ref('')
const participantSearch = ref('')

const hasOrganizer = computed(() => !!(isAdmin.value ? form.producer_id : ownProducerId.value))
watch(hasOrganizer, (has) => { if (!has) form.use_producer_address = false })

const { data: producers } = await useAsyncData('event_form_producers', async () => {
  if (!isAdmin.value) return []
  const list = (await fetchWithAuth('/producers?include_all=true')) || []
  return list.sort((a, b) => a.company_name.localeCompare(b.company_name, 'it'))
}, { default: () => [] })

const participantChoices = computed(() => {
  const q = participantSearch.value.trim().toLowerCase()
  return (producers.value || []).filter(p => p.id !== form.producer_id && (!q || p.company_name.toLowerCase().includes(q) || form.participant_ids.includes(p.id)))
})

// vini delle cantine coinvolte (pubblicati; per la propria cantina anche le bozze)
const wineProducerIds = computed(() => [...new Set([isAdmin.value ? form.producer_id : ownProducerId.value, ...form.participant_ids].filter(Boolean))])
const wineChoices = ref([])
const showWineProducer = computed(() => wineProducerIds.value.length > 1)
watch(wineProducerIds, async (ids) => {
  const lists = await Promise.all(ids.map(id => fetchWithAuth(`/products?producer_id=${id}&status=${isAdmin.value || id !== ownProducerId.value ? 'PUBLISHED' : 'ALL'}`).catch(() => [])))
  wineChoices.value = lists.flat().map(p => ({ id: p.id, name: p.name, producer_name: p.producer_name }))
    .sort((a, b) => a.name.localeCompare(b.name, 'it'))
  const allowed = new Set(wineChoices.value.map(w => w.id))
  form.product_ids = form.product_ids.filter(id => allowed.has(id))
}, { immediate: true })

const toggleWine = (id) => {
  const i = form.product_ids.indexOf(id)
  if (i >= 0) form.product_ids.splice(i, 1)
  else form.product_ids.push(id)
}

const addDate = () => {
  const last = form.dates[form.dates.length - 1]
  const row = dateRow()
  if (last?.date) {
    // proposta: una settimana dopo, stesso orario
    const [y, m, d] = last.date.split('-').map(Number)
    const next = new Date(y, m - 1, d + 7)
    row.date = `${next.getFullYear()}-${String(next.getMonth() + 1).padStart(2, '0')}-${String(next.getDate()).padStart(2, '0')}`
    row.startTime = last.startTime
    row.endTime = last.multiDay ? '' : last.endTime
  }
  form.dates.push(row)
}
const removeDate = (i) => form.dates.splice(i, 1)

const onPickLocation = ({ lat, lng }) => {
  form.location.lat = lat ?? null
  form.location.lng = lng ?? null
}

const buildDates = () => form.dates.map((d) => {
  if (!d.date) throw new Error('Indica il giorno di ogni data dell\'evento.')
  const start = joinLocal(d.date, d.startTime)
  let end = null
  if (d.multiDay) {
    if (!d.endDate) throw new Error('Indica l\'ultimo giorno dell\'evento che dura più giorni.')
    end = joinLocal(d.endDate, d.endTime || '23:59')
  } else if (d.endTime) {
    end = joinLocal(d.date, d.endTime)
  }
  return { start, end }
})

const save = async (status) => {
  error.value = ''
  if (form.title.trim().length < 3) { error.value = 'Scrivi un titolo di almeno 3 caratteri.'; return }
  let dates
  try { dates = buildDates() } catch (e) { error.value = e.message; return }
  const useProducerAddress = hasOrganizer.value && form.use_producer_address
  if (!useProducerAddress && !form.location.city?.trim() && !form.location.name?.trim()) {
    error.value = 'Indica dove si svolge l\'evento (almeno il comune).'
    return
  }
  if (form.booking_mode === 'EXTERNAL' && !form.external_url.trim()) {
    error.value = 'Inserisci il link per la prenotazione.'
    return
  }
  const body = {
    title: form.title.trim(),
    type: form.type,
    description: form.description,
    cover_image: form.cover_image || '',
    dates,
    use_producer_address: useProducerAddress,
    location: { ...form.location, lat: form.location.lat === '' ? null : form.location.lat, lng: form.location.lng === '' ? null : form.location.lng },
    producer_id: isAdmin.value ? (form.producer_id || null) : null,
    participant_ids: isAdmin.value ? form.participant_ids : [],
    product_ids: form.product_ids,
    price_type: form.price_type,
    price_text: form.price_text,
    booking_mode: form.booking_mode,
    external_url: form.booking_mode === 'EXTERNAL' ? form.external_url : '',
    contact_email: isAdmin.value && !form.producer_id && form.contact_email ? form.contact_email : null,
    status
  }
  saving.value = true
  try {
    const saved = isEdit
      ? await fetchWithAuth(`/events/${ev.id}`, { method: 'PUT', body })
      : await fetchWithAuth('/events', { method: 'POST', body })
    form.status = saved.status === 'DRAFT' ? 'DRAFT' : 'PUBLISHED'
    emit('saved', saved)
  } catch (err) {
    error.value = apiErrorMessage(err, 'Salvataggio non riuscito: controlla i dati e riprova.')
  } finally {
    saving.value = false
  }
}
</script>
