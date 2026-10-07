<template>
  <div>
    <section class="bg-sand border-b border-line">
      <div class="page-container pt-10 pb-7 flex flex-col gap-6">
        <div class="flex flex-col gap-2 max-w-[680px]">
          <span class="eyebrow">In programma</span>
          <h1 class="title-display">Eventi nelle cantine del Molise</h1>
          <p class="text-[17px] text-ink-soft">Degustazioni, visite in vigna, cene e feste del vino: scegli una data e chiedi alla cantina di partecipare.</p>
        </div>

        <div class="flex flex-col gap-3">
          <div v-if="viewMode !== 'calendar'" role="group" aria-label="Periodo" class="flex flex-wrap gap-1.5">
            <button
              v-for="p in periods"
              :key="p.value"
              type="button"
              :aria-pressed="!past && period === p.value"
              :class="['pill h-11', !past && period === p.value && 'pill-active']"
              @click="setPeriod(p.value)"
            >
              {{ p.label }}
            </button>
            <button type="button" :aria-pressed="past" :class="['pill h-11', past && 'pill-active']" @click="setPast(!past)">
              Eventi passati
            </button>
          </div>
          <div class="flex flex-wrap items-center justify-between gap-3">
            <div class="flex flex-wrap items-center gap-3">
              <label class="sr-only" for="event-type">Tipo di evento</label>
              <select id="event-type" v-model="type" class="select h-11 w-auto min-w-[190px] text-sm">
                <option value="">Tutti i tipi</option>
                <option v-for="(label, key) in EVENT_TYPES" :key="key" :value="key">{{ label }}</option>
              </select>
              <label class="sr-only" for="event-city">Comune</label>
              <select id="event-city" v-model="city" class="select h-11 w-auto min-w-[170px] text-sm">
                <option value="">Tutti i comuni</option>
                <option v-for="c in cities" :key="c" :value="c">{{ c }}</option>
              </select>
              <label class="inline-flex items-center gap-2 h-11 px-3.5 rounded-xl border border-line-strong bg-white text-sm font-semibold text-ink cursor-pointer">
                <input v-model="freeOnly" type="checkbox" class="w-4 h-4 accent-wine-800" />
                Solo gratuiti
              </label>
            </div>
            <div role="tablist" aria-label="Vista" class="segmented">
              <button
                v-for="mode in viewModes"
                :key="mode.value"
                type="button"
                role="tab"
                :aria-selected="viewMode === mode.value"
                :class="['segmented-item', viewMode === mode.value && 'segmented-item-active']"
                @click="setView(mode.value)"
              >
                {{ mode.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="page-container pt-8 md:pt-10 pb-16 md:pb-20">
      <p v-if="viewMode !== 'calendar'" class="mb-5 text-[15px] text-ink-soft" aria-live="polite">
        <strong class="text-ink">{{ visible.length }}</strong> {{ visible.length === 1 ? 'evento' : 'eventi' }}{{ past ? ' passati' : '' }}
      </p>

      <div v-if="pending" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="i in 6" :key="i" class="h-80 rounded-2xl bg-sand animate-pulse"></div>
      </div>

      <ClientOnly v-else-if="viewMode === 'calendar'">
        <EventCalendar v-model:month="calendarMonth" :events="visible" />
        <template #fallback><div class="h-[640px] rounded-2xl bg-sand animate-pulse"></div></template>
      </ClientOnly>

      <div v-else-if="!visible.length" class="card p-10 text-center flex flex-col items-center gap-3">
        <CalendarDays class="w-9 h-9 text-ink-mute" aria-hidden="true" />
        <h2 class="title-card text-2xl">{{ hasFilters ? 'Nessun evento con questi filtri' : (past ? 'Nessun evento passato' : 'Nessun evento in programma') }}</h2>
        <p class="text-ink-soft max-w-[460px]">
          {{ hasFilters ? 'Prova a cambiare periodo, tipo o comune.' : 'Le cantine pubblicano qui degustazioni, visite e feste: torna a trovarci presto.' }}
        </p>
        <button v-if="hasFilters" type="button" class="btn-outline" @click="resetFilters">Azzera i filtri</button>
      </div>

      <ClientOnly v-else-if="viewMode === 'map'">
        <EventMap :events="visible" tall />
      </ClientOnly>

      <div v-else class="flex flex-col gap-10">
        <section v-for="group in groups" :key="group.title" :aria-labelledby="`mese-${group.key}`">
          <h2 :id="`mese-${group.key}`" class="font-serif text-[30px] font-bold mb-4">{{ group.title }}</h2>
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <EventCard v-for="ev in group.events" :key="ev.id" :event="ev" />
          </div>
        </section>
      </div>
    </section>

    <section class="bg-white border-t border-line">
      <div class="page-container py-12 flex flex-wrap items-center justify-between gap-6">
        <div class="flex flex-col gap-1.5 max-w-[620px]">
          <span class="font-serif text-[32px] font-bold leading-tight">Organizzi un evento in cantina?</span>
          <span class="text-base text-ink-soft">Pubblicalo gratis dall'area riservata: le richieste di partecipazione ti arrivano via email.</span>
        </div>
        <NuxtLink :to="isAuthenticated ? '/dashboard/eventi/nuovo' : '/login?mode=register'" class="btn-outline">
          {{ isAuthenticated ? 'Pubblica un evento' : 'Registra la tua cantina' }}
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup>
import { CalendarDays } from 'lucide-vue-next'
import EventCard from '~/components/EventCard.vue'
import EventMap from '~/components/EventMap.client.vue'
import EventCalendar from '~/components/EventCalendar.vue'
import { EVENT_TYPES, eventWhen, monthTitle } from '~/utils/events'

const { fetchWithAuth } = useApi()
const { isAuthenticated } = useAuth()
const route = useRoute()
const router = useRouter()

useSeoMeta({
  title: 'Eventi del vino in Molise - Degustazioni, visite e feste in cantina',
  description: 'Calendario degli eventi nelle cantine del Molise: degustazioni, visite in vigna, cene, vendemmia e feste del vino.'
})

const periods = [
  { label: 'Tutti', value: '' },
  { label: 'Questo fine settimana', value: 'weekend' },
  { label: 'Questo mese', value: 'month' },
  { label: 'Prossimi 30 giorni', value: 'next30' }
]
const viewModes = [
  { label: 'Elenco', value: 'list' },
  { label: 'Calendario', value: 'calendar' },
  { label: 'Mappa', value: 'map' }
]

const period = ref(['weekend', 'month', 'next30'].includes(route.query.periodo) ? route.query.periodo : '')
const past = ref(route.query.passati === '1')
const type = ref(EVENT_TYPES[route.query.tipo] ? route.query.tipo : '')
const city = ref(typeof route.query.comune === 'string' ? route.query.comune : '')
const freeOnly = ref(route.query.gratuiti === '1')
// nell'indirizzo: ?vista=calendario o ?vista=mappa
const VIEW_SLUGS = { calendar: 'calendario', map: 'mappa' }
const viewMode = ref(Object.keys(VIEW_SLUGS).find(k => VIEW_SLUGS[k] === route.query.vista) || 'list')
const calendarMonth = ref(typeof route.query.mese === 'string' && /^\d{4}-\d{2}$/.test(route.query.mese) ? route.query.mese : '')
const setView = (mode) => { viewMode.value = mode }

const { data: events, pending } = await useAsyncData('public_events', async () => {
  // calendario: tutti gli eventi, anche quelli gia' passati (si sfogliano i mesi)
  if (viewMode.value === 'calendar') {
    const params = new URLSearchParams()
    if (type.value) params.set('type', type.value)
    if (freeOnly.value) params.set('free', 'true')
    const [upcoming, done] = await Promise.all([
      fetchWithAuth(`/events?${params.toString()}&limit=300`),
      fetchWithAuth(`/events?${params.toString()}&past=true&limit=300`)
    ])
    const seen = new Set()
    return [...(upcoming || []), ...(done || [])].filter(e => !seen.has(e.id) && seen.add(e.id))
  }
  const params = new URLSearchParams()
  if (past.value) params.set('past', 'true')
  else if (period.value) params.set('period', period.value)
  if (type.value) params.set('type', type.value)
  if (freeOnly.value) params.set('free', 'true')
  return fetchWithAuth(`/events?${params.toString()}`)
}, { default: () => [], watch: [period, past, type, freeOnly, viewMode] })

// i filtri restano nell'indirizzo: la pagina si puo' condividere gia' filtrata
watch([period, past, type, city, freeOnly, viewMode, calendarMonth], () => {
  const calendar = viewMode.value === 'calendar'
  router.replace({
    query: {
      vista: VIEW_SLUGS[viewMode.value],
      mese: calendar && calendarMonth.value ? calendarMonth.value : undefined,
      periodo: !calendar && !past.value && period.value ? period.value : undefined,
      passati: !calendar && past.value ? '1' : undefined,
      tipo: type.value || undefined,
      comune: city.value || undefined,
      gratuiti: freeOnly.value ? '1' : undefined
    }
  })
})

const cities = computed(() => [...new Set((events.value || []).map(e => e.location?.city).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'it')))
const visible = computed(() => (events.value || []).filter(e => !city.value || (e.location?.city || '').toLowerCase() === city.value.toLowerCase()))
const hasFilters = computed(() => !!((viewMode.value !== 'calendar' && period.value) || type.value || city.value || freeOnly.value))

const groups = computed(() => {
  const out = []
  for (const ev of visible.value) {
    const start = eventWhen(ev)?.start || ev.starts_at
    const key = String(start || '').slice(0, 7)
    let group = out.find(g => g.key === key)
    if (!group) {
      group = { key, title: monthTitle(start), events: [] }
      out.push(group)
    }
    group.events.push(ev)
  }
  return out
})

const setPeriod = (value) => { past.value = false; period.value = value }
const setPast = (value) => { past.value = value; if (value) period.value = '' }
const resetFilters = () => { period.value = ''; type.value = ''; city.value = ''; freeOnly.value = false }
</script>
