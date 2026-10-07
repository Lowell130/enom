<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[1240px]">
    
    <div class="mb-8">
      <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">
        Richieste di Contatto Utenti
      </h1>
      <p class="text-xs text-ink-mute mt-1">
        Messaggi inviati dagli utenti del portale per informazioni su prezzi, disponibilità, degustazioni ed eventi.
      </p>
    </div>

    <div class="mb-4 flex flex-wrap items-center gap-2">
      <button v-for="f in filters" :key="f.value" type="button" :aria-pressed="filter === f.value"
        :class="['pill h-10', filter === f.value && 'pill-active']" @click="setFilter(f.value)">
        {{ f.label }}
      </button>
      <span v-if="eventFilter" class="inline-flex items-center gap-2 h-10 px-3.5 rounded-xl bg-wine-50 border border-wine-200 text-sm text-wine-900">
        Evento: <strong>{{ eventFilterTitle }}</strong>
        <button type="button" class="font-bold" aria-label="Mostra tutte le richieste" @click="clearEvent">✕</button>
      </span>
    </div>

    <div class="bg-white rounded-2xl border border-line shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-ink-mute">
        Caricamento messaggi...
      </div>

      <div v-else-if="shown.length" class="divide-y divide-stone-100">
        <div 
          v-for="msg in shown" 
          :key="msg.id" 
          class="p-6 transition-colors hover:bg-stone-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4"
          :class="{ 'bg-wine-50/20': !msg.is_read }"
        >
          <div class="space-y-2">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-bold text-ink text-sm">{{ msg.user_name }}</span>
              <span class="text-xs text-stone-400 font-light">&lt;{{ msg.user_email }}&gt;</span>
              <span v-if="msg.user_phone" class="inline-flex items-center space-x-1 text-xs text-ink-mute font-medium">
                <Phone class="w-3 h-3 text-stone-400" />
                <span>{{ msg.user_phone }}</span>
              </span>
              <span v-if="!msg.is_read" class="px-2.5 py-0.5 bg-wine-800 text-white rounded-full text-[10px] font-bold tracking-wider uppercase">NUOVO</span>
            </div>
            <p class="text-xs text-ink-mute m-0">
              <time :datetime="msg.created_at">{{ formatWhen(msg.created_at) }}</time>
              · {{ typeLabel(msg.message_type) }}
            </p>

            <div v-if="msg.message_type === 'EVENTO'" class="text-xs font-semibold text-wine-900 flex flex-wrap items-center gap-x-1.5 gap-y-1">
              <CalendarDays class="w-3.5 h-3.5 text-wine-800" />
              <NuxtLink v-if="msg.event_slug" :to="`/eventi/${msg.event_slug}`" class="text-wine-900">{{ msg.event_title }}</NuxtLink>
              <span v-else>{{ msg.event_title }}</span>
              <span class="text-ink-soft font-normal">· {{ msg.event_date }} · <strong>{{ msg.people }} {{ msg.people === 1 ? 'persona' : 'persone' }}</strong></span>
              <span v-if="isAdmin && msg.producer_name" class="text-ink-soft font-normal">· {{ msg.producer_name }}</span>
            </div>
            <div v-else class="text-xs font-semibold text-wine-900 flex items-center space-x-1.5">
              <Building2 class="w-3.5 h-3.5 text-wine-800" />
              <span>Cantina: {{ msg.producer_name }}</span>
              <span v-if="msg.product_name" class="ml-2 text-ink-soft font-normal">| Vino: <strong>{{ msg.product_name }}</strong></span>
            </div>

            <p class="text-sm text-ink-soft bg-stone-50/80 p-4 rounded-2xl border border-stone-200/50 leading-relaxed max-w-3xl font-light">
              "{{ msg.message }}"
            </p>
          </div>

          <div class="flex items-center space-x-3 flex-shrink-0">
            <a 
              :href="replyLink(msg)"
              class="inline-flex items-center space-x-1.5 px-4 py-2.5 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-xs font-semibold transition-all shadow-xs"
            >
              <Mail class="w-3.5 h-3.5" />
              <span>Rispondi via Email</span>
            </a>
            
            <button 
              v-if="!msg.is_read" 
              @click="markRead(msg.id)" 
              class="inline-flex items-center space-x-1 px-3 py-2.5 bg-stone-100 hover:bg-stone-200 text-ink-soft rounded-xl text-xs font-semibold"
            >
              <CheckCircle class="w-3.5 h-3.5 text-ink-mute" />
              <span>Segna letto</span>
            </button>

            <button
              type="button"
              :disabled="deleting === msg.id"
              :aria-label="`Elimina il messaggio di ${msg.user_name}`"
              title="Elimina il messaggio"
              class="inline-flex items-center space-x-1 px-3 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-xl text-xs font-semibold border border-rose-200/50 disabled:opacity-50"
              @click="removeInquiry(msg)"
            >
              <Trash2 class="w-3.5 h-3.5" />
              <span>Elimina</span>
            </button>
          </div>
        </div>
      </div>

      <div v-else class="p-16 text-center text-ink-mute">
        <MessageSquare class="w-8 h-8 text-stone-400 mx-auto mb-2" />
        <p class="text-sm font-light">{{ inquiries.length ? 'Nessuna richiesta con questo filtro.' : 'Nessuna richiesta di contatto ricevuta.' }}</p>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Phone, Building2, Mail, CheckCircle, MessageSquare, CalendarDays, Trash2 } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()
const { isAdmin } = useAuth()
const route = useRoute()
const router = useRouter()

const { data: inquiries, pending, refresh } = await useAsyncData('user_inquiries', async () => {
  const res = await fetchWithAuth('/inquiries')
  return res || []
}, { default: () => [] })

const toast = useToast()

// filtri: tutte, solo eventi, solo messaggi; dalla pagina Eventi si arriva con ?evento=<id>
const filters = [
  { value: 'ALL', label: 'Tutte' },
  { value: 'EVENTS', label: 'Prenotazioni eventi' },
  { value: 'MESSAGES', label: 'Messaggi' }
]
const eventFilter = ref(typeof route.query.evento === 'string' ? route.query.evento : '')
const filter = ref(eventFilter.value ? 'EVENTS' : 'ALL')
const setFilter = (value) => { filter.value = value; if (value !== 'EVENTS') clearEvent() }
const clearEvent = () => { eventFilter.value = ''; router.replace({ query: {} }) }
const eventFilterTitle = computed(() => (inquiries.value || []).find(m => m.event_id === eventFilter.value)?.event_title || 'selezionato')
const shown = computed(() => (inquiries.value || []).filter((m) => {
  if (eventFilter.value) return m.event_id === eventFilter.value
  if (filter.value === 'EVENTS') return m.message_type === 'EVENTO'
  if (filter.value === 'MESSAGES') return m.message_type !== 'EVENTO'
  return true
}))

const TYPES = { INFO_PREZZI: 'Prezzi e listino', DISPONIBILITA: 'Disponibilità e acquisto', VISITA_CANTINA: 'Visita in cantina', EVENTO: 'Prenotazione evento', ALTRO: 'Altro' }
const typeLabel = (t) => TYPES[t] || 'Richiesta'

// "oggi alle 15:30", "ieri alle 9:12", oppure la data
const formatWhen = (value) => {
  if (!value) return ''
  const d = new Date(String(value).endsWith('Z') ? value : `${value}Z`)
  const now = new Date()
  const time = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
  const days = Math.floor((new Date(now.toDateString()) - new Date(d.toDateString())) / 86400000)
  if (days === 0) return `Oggi alle ${time}`
  if (days === 1) return `Ieri alle ${time}`
  return `${d.toLocaleDateString('it-IT', { day: 'numeric', month: 'long', year: d.getFullYear() === now.getFullYear() ? undefined : 'numeric' })} alle ${time}`
}

const replyLink = (msg) => {
  if (msg.message_type === 'EVENTO') {
    const subject = `Re: ${msg.event_title} - ${msg.event_date}`
    const body = `Gentile ${msg.user_name},\n\ngrazie per la richiesta di partecipazione a «${msg.event_title}» (${msg.event_date}, ${msg.people} ${msg.people === 1 ? 'persona' : 'persone'}).\n\n\n---\nLe tue note:\n${msg.message}`
    return `mailto:${msg.user_email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
  }
  const subject = msg.product_name
    ? `Re: ${msg.product_name} - ${msg.producer_name}`
    : `Re: la tua richiesta a ${msg.producer_name}`
  const body = `Gentile ${msg.user_name},\n\ngrazie per averci scritto.\n\n\n---\nIl tuo messaggio:\n${msg.message}`
  return `mailto:${msg.user_email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
}

// eliminazione definitiva, dopo conferma
const deleting = ref(null)
const removeInquiry = async (msg) => {
  if (!window.confirm(`Eliminare definitivamente il messaggio di ${msg.user_name}? Non si potrà recuperare.`)) return
  deleting.value = msg.id
  try {
    await fetchWithAuth(`/inquiries/${msg.id}`, { method: 'DELETE' })
    toast.success('Messaggio eliminato.')
    await refresh()
  } catch (err) {
    toast.error('Non è stato possibile eliminare il messaggio.')
  } finally {
    deleting.value = null
  }
}

const markRead = async (id) => {
  try {
    await fetchWithAuth(`/inquiries/${id}/read`, { method: 'PUT' })
    toast.success('Messaggio segnato come letto.')
    await refresh()
  } catch (err) {
    toast.error('Errore aggiornamento stato.')
  }
}
</script>
