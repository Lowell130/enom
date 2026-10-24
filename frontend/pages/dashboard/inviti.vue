<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[1000px] flex flex-col gap-6">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div class="flex flex-col gap-1.5">
        <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Contatti con le cantine</h1>
        <p class="text-sm text-ink-soft m-0 max-w-[620px]">
          Chi hai contattato, quando e come, anche per le cantine non ancora sul sito. Dopo {{ remindDays }} giorni senza
          accesso attivo una cantina torna tra quelle da sollecitare. Gli inviti mandati dal sito si registrano da soli.
        </p>
      </div>
      <button type="button" class="btn-primary btn-sm h-11" @click="openProspect()">
        <Plus class="w-4 h-4" aria-hidden="true" /> Cantina fuori dal sito
      </button>
    </div>

    <div class="flex flex-col sm:flex-row gap-3 sm:items-center">
      <div class="flex flex-wrap gap-2" role="tablist" aria-label="Filtra le cantine">
        <button v-for="f in filters" :key="f.value" type="button" role="tab" :aria-selected="filter === f.value"
                :class="['pill', filter === f.value && 'pill-active']" @click="filter = f.value">
          {{ f.label }} <span class="ml-1 opacity-70">{{ f.count }}</span>
        </button>
      </div>
      <label class="sr-only" for="cerca-cantina">Cerca</label>
      <input id="cerca-cantina" v-model="search" type="search" placeholder="Cerca per nome o comune" class="input h-10 text-sm sm:ml-auto sm:w-60" />
    </div>

    <div v-if="pending" class="card p-10 text-center text-sm text-ink-mute">Caricamento…</div>
    <div v-else-if="!visible.length" class="card p-10 text-center text-sm text-ink-mute">{{ emptyText }}</div>

    <ul v-else class="list-none m-0 p-0 flex flex-col gap-3">
      <li v-for="it in visible" :key="it.kind + it.id" class="card p-4 sm:p-5 flex flex-col gap-3">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex flex-col gap-1 min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <NuxtLink v-if="it.kind === 'producer' && it.slug" :to="`/produttori/${it.slug}`" target="_blank" class="font-bold text-ink hover:text-wine-800">{{ it.name }}</NuxtLink>
              <span v-else class="font-bold text-ink">{{ it.name }}</span>
              <span :class="['px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide', badge(it).cls]">{{ badge(it).label }}</span>
            </div>
            <span class="text-[13px] text-ink-mute">
              {{ [it.city, it.province && `(${it.province})`].filter(Boolean).join(' ') || 'Comune non indicato' }}
              <template v-if="it.kind === 'producer'"> · {{ it.wine_count === 1 ? '1 vino' : `${it.wine_count} vini` }}</template>
            </span>
          </div>
          <div class="flex flex-wrap gap-1.5">
            <a v-if="waLink(it)" :href="waLink(it)" target="_blank" rel="noopener" class="btn-ghost btn-sm h-8 px-2.5 text-xs"><MessageCircle class="w-3.5 h-3.5" aria-hidden="true" /> WhatsApp</a>
            <a v-if="it.email" :href="`mailto:${it.email}`" class="btn-ghost btn-sm h-8 px-2.5 text-xs"><Mail class="w-3.5 h-3.5" aria-hidden="true" /> Email</a>
            <a v-if="it.phone" :href="`tel:${it.phone.replace(/\s/g, '')}`" class="btn-ghost btn-sm h-8 px-2.5 text-xs"><Phone class="w-3.5 h-3.5" aria-hidden="true" /> {{ it.phone }}</a>
            <a v-if="it.facebook" :href="ext(it.facebook)" target="_blank" rel="noopener" class="btn-ghost btn-sm h-8 px-2.5 text-xs">Facebook</a>
            <a v-if="it.instagram" :href="ext(it.instagram)" target="_blank" rel="noopener" class="btn-ghost btn-sm h-8 px-2.5 text-xs">Instagram</a>
            <a v-if="it.website" :href="ext(it.website)" target="_blank" rel="noopener" class="btn-ghost btn-sm h-8 px-2.5 text-xs"><Globe class="w-3.5 h-3.5" aria-hidden="true" /> Sito</a>
          </div>
        </div>

        <p v-if="it.maybe_registered" class="m-0 p-3 rounded-[10px] bg-bio-50 border border-bio/30 text-bio-900 text-sm flex flex-wrap items-center gap-2">
          <span>Forse si è iscritta: <strong>{{ it.maybe_registered.name }}</strong>.</span>
          <button type="button" class="btn-outline btn-sm h-8 text-xs" @click="link(it, it.maybe_registered)">Sì, è lei: sposta lo storico</button>
        </p>

        <div class="flex flex-col gap-1.5 text-sm">
          <p v-if="!it.history.length" class="m-0 text-ink-mute">Mai contattata.</p>
          <ol v-else class="list-none m-0 p-0 flex flex-col gap-1.5">
            <li v-for="h in (expanded[it.id] ? it.history : it.history.slice(0, 1))" :key="h.id" class="flex items-start gap-2">
              <span class="shrink-0 text-[12px] font-semibold text-ink-soft w-[92px] pt-px">{{ day(h.contacted_at) }}</span>
              <span class="min-w-0 flex-1">
                <span class="font-semibold text-ink">{{ h.channel_label }}</span><template v-if="h.note"> · <span class="text-ink-soft whitespace-pre-line">{{ h.note }}</span></template>
              </span>
              <button v-if="!h.auto" type="button" class="shrink-0 text-ink-mute hover:text-wine-800 p-0.5" :aria-label="`Elimina il contatto del ${day(h.contacted_at)}`" @click="removeLog(it, h)">
                <X class="w-3.5 h-3.5" aria-hidden="true" />
              </button>
            </li>
          </ol>
          <button v-if="it.history.length > 1" type="button" class="self-start text-[13px] font-semibold text-wine-800" @click="expanded[it.id] = !expanded[it.id]">
            {{ expanded[it.id] ? 'Mostra solo l\'ultimo' : `Tutto lo storico (${it.history.length})` }}
          </button>
        </div>

        <div class="flex flex-wrap gap-2 pt-1 border-t border-line">
          <button type="button" class="btn-primary btn-sm h-9 mt-2" @click="openLog(it)"><Plus class="w-4 h-4" aria-hidden="true" /> Registra contatto</button>
          <template v-if="it.kind === 'producer'">
            <NuxtLink :to="`/dashboard/profilo?producer_id=${it.id}`" class="btn-ghost btn-sm h-9 mt-2">Profilo</NuxtLink>
            <button v-if="it.account !== 'active'" type="button" class="btn-ghost btn-sm h-9 mt-2" :disabled="busy === it.id" @click="invite(it)">
              <Send class="w-4 h-4" aria-hidden="true" /> {{ it.account === 'none' ? 'Invia invito' : 'Rimanda invito' }}
            </button>
          </template>
          <template v-else>
            <button type="button" class="btn-ghost btn-sm h-9 mt-2" @click="openProspect(it)">Modifica</button>
            <button type="button" class="btn-ghost btn-sm h-9 mt-2" @click="openLink(it)">Si è iscritta</button>
            <button type="button" class="btn-ghost btn-sm h-9 mt-2 text-wine-800 ml-auto" @click="removeProspect(it)"><Trash2 class="w-4 h-4" aria-hidden="true" /> Elimina</button>
          </template>
        </div>
      </li>
    </ul>

    <!-- registra un contatto -->
    <div v-if="logTarget" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="titolo-contatto" @click.self="logTarget = null">
      <form class="bg-white rounded-2xl max-w-md w-full p-6 flex flex-col gap-4 shadow-2xl" @submit.prevent="saveLog">
        <h2 id="titolo-contatto" class="font-serif text-2xl font-bold m-0">Contatto con {{ logTarget.name }}</h2>
        <div class="flex flex-col gap-1.5">
          <span class="field-label">Canale</span>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="(label, key) in channels" :key="key" type="button" :class="['pill', logForm.channel === key && 'pill-active']" @click="logForm.channel = key">{{ label }}</button>
          </div>
        </div>
        <label class="field-label">Data
          <input v-model="logForm.contacted_on" type="date" :max="today" class="input" />
        </label>
        <label class="field-label">Com'è andata (facoltativo)
          <textarea v-model="logForm.note" rows="3" maxlength="2000" class="input h-auto py-2.5 text-sm" placeholder="es. Mandato il messaggio con il link, ha risposto che ci pensa"></textarea>
        </label>
        <label v-if="logTarget.kind === 'prospect'" class="field-label">Stato
          <select v-model="logForm.status" class="select">
            <option v-for="(label, key) in prospectStatuses" :key="key" :value="key">{{ label }}</option>
          </select>
        </label>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-ghost btn-sm h-10" @click="logTarget = null">Annulla</button>
          <button type="submit" class="btn-primary btn-sm h-10" :disabled="saving">{{ saving ? 'Salvataggio…' : 'Salva' }}</button>
        </div>
      </form>
    </div>

    <!-- cantina fuori dal sito -->
    <div v-if="prospectForm" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="titolo-cantina" @click.self="prospectForm = null">
      <form class="bg-white rounded-2xl max-w-lg w-full max-h-[92vh] overflow-y-auto p-6 flex flex-col gap-4 shadow-2xl" @submit.prevent="saveProspect">
        <div class="flex flex-col gap-1">
          <h2 id="titolo-cantina" class="font-serif text-2xl font-bold m-0">{{ prospectForm.id ? 'Modifica cantina' : 'Cantina fuori dal sito' }}</h2>
          <p class="m-0 text-[13px] text-ink-soft">Solo per te: questi dati non compaiono sul sito.</p>
        </div>
        <label class="field-label">Nome *<input v-model="prospectForm.name" type="text" maxlength="150" class="input" /></label>
        <div class="grid grid-cols-[1fr_90px] gap-3">
          <label class="field-label">Comune<input v-model="prospectForm.city" type="text" maxlength="100" class="input" /></label>
          <label class="field-label">Prov.<input v-model="prospectForm.province" type="text" maxlength="4" placeholder="CB" class="input uppercase" /></label>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <label class="field-label">Email<input v-model="prospectForm.email" type="email" class="input" /></label>
          <label class="field-label">Telefono<input v-model="prospectForm.phone" type="tel" class="input" /></label>
          <label class="field-label">WhatsApp<input v-model="prospectForm.whatsapp" type="tel" class="input" /></label>
          <label class="field-label">Sito web<input v-model="prospectForm.website" type="text" class="input" /></label>
          <label class="field-label">Facebook<input v-model="prospectForm.facebook" type="text" placeholder="link alla pagina" class="input" /></label>
          <label class="field-label">Instagram<input v-model="prospectForm.instagram" type="text" class="input" /></label>
        </div>
        <label class="field-label">Note<textarea v-model="prospectForm.notes" rows="3" maxlength="3000" class="input h-auto py-2.5 text-sm" placeholder="es. Trovata su Facebook, produce Tintilia"></textarea></label>
        <label class="field-label">Stato
          <select v-model="prospectForm.status" class="select">
            <option v-for="(label, key) in prospectStatuses" :key="key" :value="key">{{ label }}</option>
          </select>
        </label>
        <p v-if="formError" role="alert" class="m-0 p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ formError }}</p>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-ghost btn-sm h-10" @click="prospectForm = null">Annulla</button>
          <button type="submit" class="btn-primary btn-sm h-10" :disabled="saving">{{ saving ? 'Salvataggio…' : 'Salva' }}</button>
        </div>
      </form>
    </div>

    <!-- si e' iscritta: collega alla cantina -->
    <div v-if="linkTarget" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="titolo-collega" @click.self="linkTarget = null">
      <form class="bg-white rounded-2xl max-w-md w-full p-6 flex flex-col gap-4 shadow-2xl" @submit.prevent="link(linkTarget, { id: linkProducer })">
        <h2 id="titolo-collega" class="font-serif text-2xl font-bold m-0">{{ linkTarget.name }} è sul sito</h2>
        <p class="m-0 text-sm text-ink-soft">Scegli la sua pagina: lo storico dei contatti passa lì e la voce «fuori dal sito» sparisce.</p>
        <select v-model="linkProducer" class="select" required>
          <option value="" disabled>Scegli la cantina</option>
          <option v-for="p in producerOptions" :key="p.id" :value="p.id">{{ p.name }}{{ p.city ? ` (${p.city})` : '' }}</option>
        </select>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-ghost btn-sm h-10" @click="linkTarget = null">Annulla</button>
          <button type="submit" class="btn-primary btn-sm h-10" :disabled="!linkProducer || saving">Collega</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { Globe, Mail, MessageCircle, Phone, Plus, Send, Trash2, X } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'
import { normalizeWhatsAppNumber } from '~/composables/useWhatsApp'

useSeoMeta({ title: 'Contatti con le cantine - EnotecaMolise', robots: 'noindex' })

const { fetchWithAuth } = useApi()
const toast = useToast()

const items = ref([])
const channels = ref({})
const prospectStatuses = ref({})
const remindDays = ref(7)
const pending = ref(true)
const filter = ref('TODO')
const search = ref('')
const expanded = reactive({})
const busy = ref('')
const saving = ref(false)

const load = async () => {
  try {
    const res = await fetchWithAuth('/outreach')
    items.value = res.items
    channels.value = res.channels
    prospectStatuses.value = res.prospect_statuses
    remindDays.value = res.remind_after_days
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    pending.value = false
  }
}
onMounted(load)

const isProspect = (i) => i.kind === 'prospect'
const groups = {
  TODO: (i) => i.to_do,
  WAITING: (i) => i.waiting,
  OUTSIDE: (i) => isProspect(i),
  ACTIVE: (i) => !isProspect(i) && i.account === 'active',
  ALL: () => true
}
const filters = computed(() => [
  { value: 'TODO', label: 'Da sollecitare' },
  { value: 'WAITING', label: 'In attesa di risposta' },
  { value: 'OUTSIDE', label: 'Fuori dal sito' },
  { value: 'ACTIVE', label: 'Con accesso' },
  { value: 'ALL', label: 'Tutte' }
].map(f => ({ ...f, count: items.value.filter(groups[f.value]).length })))

const visible = computed(() => {
  const q = search.value.trim().toLowerCase()
  return items.value.filter(groups[filter.value])
    .filter(i => !q || `${i.name} ${i.city}`.toLowerCase().includes(q))
})
const emptyText = computed(() => search.value ? 'Nessuna cantina con questa ricerca.'
  : filter.value === 'TODO' ? 'Nessuna cantina da sollecitare: ottimo lavoro.' : 'Nessuna cantina in questo elenco.')

const BADGES = {
  none: { label: 'Nessun accesso', cls: 'bg-stone-100 text-ink-mute' },
  invited: { label: 'Invitata', cls: 'bg-[#FBF5E8] text-[#5A4524]' },
  expired: { label: 'Invito scaduto', cls: 'bg-wine-50 text-wine-800' },
  active: { label: 'Accesso attivo', cls: 'bg-bio-50 text-bio-900' }
}
const PROSPECT_BADGE = {
  DA_CONTATTARE: 'bg-stone-100 text-ink-mute',
  CONTATTATA: 'bg-[#FBF5E8] text-[#5A4524]',
  INTERESSATA: 'bg-bio-50 text-bio-900',
  NON_INTERESSATA: 'bg-wine-50 text-wine-800'
}
const badge = (it) => isProspect(it)
  ? { label: `Fuori dal sito · ${it.status_label}`, cls: PROSPECT_BADGE[it.status] || PROSPECT_BADGE.DA_CONTATTARE }
  : (BADGES[it.account] || BADGES.none)

const toDate = (v) => new Date(String(v).endsWith('Z') || String(v).includes('+') ? v : `${v}Z`)
const day = (v) => (v ? toDate(v).toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' }) : '')
const ext = (u) => (/^https?:\/\//i.test(u) ? u : `https://${u}`)
const waLink = (it) => {
  const n = normalizeWhatsAppNumber(it.whatsapp)
  return n ? `https://wa.me/${n}` : ''
}
const localToday = () => {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}
const today = computed(localToday)

// --- registra contatto
const logTarget = ref(null)
const logForm = reactive({ channel: 'WHATSAPP', contacted_on: '', note: '', status: '' })
const openLog = (it) => {
  logTarget.value = it
  Object.assign(logForm, { channel: 'WHATSAPP', contacted_on: localToday(), note: '',
    status: isProspect(it) ? (it.status === 'DA_CONTATTARE' ? 'CONTATTATA' : it.status) : '' })
}
const saveLog = async () => {
  const it = logTarget.value
  saving.value = true
  try {
    await fetchWithAuth('/outreach/log', { method: 'POST', body: {
      target_type: it.kind, target_id: it.id, channel: logForm.channel,
      contacted_on: logForm.contacted_on || null, note: logForm.note } })
    if (isProspect(it) && logForm.status && logForm.status !== 'CONTATTATA') {
      await fetchWithAuth(`/outreach/prospects/${it.id}`, { method: 'PUT', body: { ...prospectBody(it), status: logForm.status } })
    }
    logTarget.value = null
    toast.success('Contatto registrato.')
    await load()
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}
const removeLog = async (it, h) => {
  if (!confirm(`Eliminare il contatto del ${day(h.contacted_at)} con ${it.name}?`)) return
  try {
    await fetchWithAuth(`/outreach/log/${h.id}`, { method: 'DELETE' })
    await load()
  } catch (err) {
    toast.error(apiErrorMessage(err))
  }
}

// --- cantine fuori dal sito
const FIELDS = ['name', 'city', 'province', 'email', 'phone', 'whatsapp', 'website', 'facebook', 'instagram', 'notes', 'status']
const prospectBody = (src) => Object.fromEntries(FIELDS.map(k => [k, src[k] ?? '']))
const prospectForm = ref(null)
const formError = ref('')
const openProspect = (it = null) => {
  formError.value = ''
  prospectForm.value = it ? { id: it.id, ...prospectBody(it) } : { id: '', ...prospectBody({ status: 'DA_CONTATTARE' }) }
}
const saveProspect = async () => {
  const f = prospectForm.value
  if ((f.name || '').trim().length < 2) { formError.value = 'Manca il nome della cantina.'; return }
  saving.value = true
  try {
    const body = prospectBody(f)
    body.province = (body.province || '').toUpperCase()
    if (f.id) await fetchWithAuth(`/outreach/prospects/${f.id}`, { method: 'PUT', body })
    else await fetchWithAuth('/outreach/prospects', { method: 'POST', body })
    prospectForm.value = null
    toast.success('Cantina salvata.')
    if (!f.id) filter.value = 'OUTSIDE'
    await load()
  } catch (err) {
    formError.value = apiErrorMessage(err)
  } finally {
    saving.value = false
  }
}
const removeProspect = async (it) => {
  if (!confirm(`Togliere ${it.name} dall'elenco, con tutto il suo storico?`)) return
  try {
    await fetchWithAuth(`/outreach/prospects/${it.id}`, { method: 'DELETE' })
    await load()
  } catch (err) {
    toast.error(apiErrorMessage(err))
  }
}

// --- si e' iscritta
const linkTarget = ref(null)
const linkProducer = ref('')
const producerOptions = computed(() => items.value.filter(i => !isProspect(i)))
const openLink = (it) => { linkTarget.value = it; linkProducer.value = it.maybe_registered?.id || '' }
const link = async (it, producer) => {
  saving.value = true
  try {
    const res = await fetchWithAuth(`/outreach/prospects/${it.id}/link`, { method: 'POST', body: { producer_id: producer.id } })
    linkTarget.value = null
    toast.success(res.message)
    await load()
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

// --- invito dal sito (stesso invio dell'elenco Cantine)
const invite = async (it) => {
  const email = it.account_email || it.email
  if (!email) {
    toast.error('Manca l\'email della cantina: aggiungila dal Profilo.')
    return
  }
  if (!confirm(`Mandare il link di accesso a ${email}?`)) return
  busy.value = it.id
  try {
    const res = await fetchWithAuth(`/producers/${it.id}/invite`, { method: 'POST', body: { email } })
    toast.success(res?.message || 'Invito mandato.')
    await load()
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    busy.value = ''
  }
}
</script>
