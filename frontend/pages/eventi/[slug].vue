<template>
  <div v-if="pending" class="page-container py-16">
    <div class="h-96 rounded-[20px] bg-sand animate-pulse"></div>
  </div>

  <div v-else-if="event">
    <div v-if="event.can_edit" class="bg-sand-100 border-b border-line">
      <div class="page-container py-2.5 flex flex-wrap items-center justify-between gap-3 text-sm">
        <span class="text-ink-soft">
          Stai vedendo la pagina pubblica dell'evento come organizzatore.
          <strong v-if="event.status === 'DRAFT'" class="text-[#7A5A1E]"> È una bozza: i visitatori non la vedono.</strong>
          <strong v-else-if="event.hidden" class="text-wine-800"> È nascosto dall'amministratore.</strong>
          <strong v-else-if="event.organizer && event.organizer.status !== 'APPROVED'" class="text-[#7A5A1E]"> Sarà visibile quando la cantina verrà approvata.</strong>
        </span>
        <NuxtLink :to="`/dashboard/eventi/${event.id}`" class="btn-ghost btn-sm">
          <Pencil class="w-4 h-4" aria-hidden="true" /> Modifica evento
        </NuxtLink>
      </div>
    </div>

    <nav aria-label="Percorso" class="page-container pt-4 flex flex-wrap gap-2 text-[13px] text-ink-mute">
      <NuxtLink to="/" class="text-ink-mute hover:text-wine-800">Home</NuxtLink><span aria-hidden="true">/</span>
      <NuxtLink to="/eventi" class="text-ink-mute hover:text-wine-800">Eventi</NuxtLink><span aria-hidden="true">/</span>
      <span class="text-ink font-semibold">{{ event.title }}</span>
    </nav>

    <section class="page-container pt-4">
      <div class="h-[220px] md:h-[340px] rounded-[20px] overflow-hidden" :style="{ background: tone(event.title) }">
        <SafeImg :src="mediaUrl(event.cover_image)" :alt="`Immagine dell'evento ${event.title}`" class="w-full h-full object-cover">
          <CoverArt :seed="event.title" :place="placeLabel(event)" />
        </SafeImg>
      </div>
    </section>

    <div v-if="event.status === 'CANCELLED'" class="page-container mt-6">
      <p class="m-0 p-4 rounded-2xl bg-wine-50 border border-wine-200 text-wine-900">
        <strong>Questo evento è stato annullato.</strong>
        <span v-if="event.cancel_message"> {{ event.cancel_message }}</span>
      </p>
    </div>
    <div v-else-if="event.is_past" class="page-container mt-6">
      <p class="m-0 p-4 rounded-2xl bg-sand-100 border border-line text-ink-soft"><strong class="text-ink">Evento concluso.</strong> Guarda gli <NuxtLink to="/eventi" class="font-semibold">eventi in programma</NuxtLink>.</p>
    </div>

    <section class="page-container pt-6 pb-14 grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_380px] gap-10 items-start">
      <div class="flex flex-col gap-6 min-w-0">
        <div class="flex flex-col gap-2">
          <span class="eyebrow">{{ event.type_label }}</span>
          <h1 class="title-display">{{ event.title }}</h1>
          <p class="text-[17px] text-ink-soft m-0">
            <template v-if="event.organizer">
              Organizza <NuxtLink :to="`/produttori/${event.organizer.slug}`" class="font-semibold">{{ event.organizer.name }}</NuxtLink>
            </template>
            <template v-else>Evento del territorio</template>
            · {{ placeLabel(event) }}
          </p>
        </div>

        <RichText v-if="event.description" :text="event.description" class="text-[17px] text-ink-soft leading-relaxed" />

        <div v-if="event.participants.length" class="flex flex-col gap-3">
          <h2 class="font-serif text-[28px] font-bold">Cantine partecipanti</h2>
          <ul class="list-none m-0 p-0 grid grid-cols-1 sm:grid-cols-2 gap-2">
            <li v-for="p in event.participants" :key="p.id">
              <NuxtLink :to="`/produttori/${p.slug}`" class="flex items-center gap-3 p-3 rounded-xl border border-line bg-white text-ink hover:border-line-strong">
                <span class="logo-box w-11 h-11 rounded-[10px] text-lg shrink-0">
                  <SafeImg :src="mediaUrl(p.logo_url)" :alt="`Logo ${p.name}`" class="logo-img p-1">{{ initials(p.name) }}</SafeImg>
                </span>
                <span class="flex flex-col min-w-0 leading-snug">
                  <span class="font-bold text-[15px] truncate">{{ p.name }}</span>
                  <span class="text-[13px] text-ink-mute">{{ p.city }}{{ p.province ? ` (${p.province})` : '' }}</span>
                </span>
              </NuxtLink>
            </li>
          </ul>
        </div>

        <div v-if="event.wines.length" class="flex flex-col gap-3">
          <h2 class="font-serif text-[28px] font-bold">I vini in degustazione</h2>
          <ul class="list-none m-0 p-0 grid grid-cols-1 sm:grid-cols-2 gap-2">
            <li v-for="w in event.wines" :key="w.id">
              <NuxtLink :to="`/vini/${w.slug}`" class="flex items-center gap-3 p-3 rounded-xl border border-line bg-white text-ink hover:border-line-strong">
                <span class="w-11 h-14 shrink-0 flex items-center justify-center">
                  <SafeImg :src="mediaUrl(w.photo)" :alt="w.name" class="max-h-14 object-contain"><BottleIcon :size="52" /></SafeImg>
                </span>
                <span class="flex flex-col min-w-0 leading-snug">
                  <span class="font-bold text-[15px] truncate">{{ w.name }}</span>
                  <span class="text-[13px] text-ink-mute truncate">{{ w.producer_name }}</span>
                </span>
              </NuxtLink>
            </li>
          </ul>
        </div>
      </div>

      <aside class="card p-6 flex flex-col gap-5 lg:sticky lg:top-[96px]" aria-label="Date e partecipazione">
        <div class="flex flex-col gap-2">
          <h2 class="eyebrow-sm">{{ upcoming.length > 1 ? 'Date in programma' : 'Quando' }}</h2>
          <ul class="list-none m-0 p-0 flex flex-col gap-1.5">
            <li v-for="d in shownDates" :key="d.start" :class="['flex items-start gap-2 text-[15px]', d.is_past ? 'text-ink-mute line-through' : 'text-ink']">
              <CalendarDays class="w-4 h-4 mt-1 shrink-0" aria-hidden="true" />
              <span>{{ d.label }}</span>
            </li>
          </ul>
        </div>
        <div class="flex flex-col gap-1.5">
          <h2 class="eyebrow-sm">Dove</h2>
          <p class="m-0 flex items-start gap-2 text-[15px] text-ink">
            <MapPin class="w-4 h-4 mt-1 shrink-0" aria-hidden="true" />
            <span>
              <template v-if="event.location.name">{{ event.location.name }}<br /></template>
              <template v-if="event.location.street">{{ event.location.street }}<br /></template>
              {{ event.location.city }}<template v-if="event.location.province"> ({{ event.location.province }})</template>
            </span>
          </p>
          <a :href="directionsUrl" target="_blank" rel="noopener" class="text-sm font-semibold w-fit">Indicazioni stradali →</a>
        </div>
        <div class="flex flex-col gap-1.5">
          <h2 class="eyebrow-sm">Costo</h2>
          <p class="m-0 text-[15px] font-semibold" :class="event.price_type === 'PAID' ? 'text-ink' : 'text-bio-900'">{{ priceLabel(event) }}</p>
        </div>

        <template v-if="bookable">
          <button v-if="event.booking_mode === 'REQUEST'" type="button" class="btn-primary w-full" @click="requestOpen = true">
            <Mail class="w-[18px] h-[18px]" aria-hidden="true" /> Chiedi di partecipare
          </button>
          <a v-else-if="event.booking_mode === 'EXTERNAL'" :href="event.external_url" target="_blank" rel="noopener" class="btn-primary w-full">
            <ExternalLink class="w-[18px] h-[18px]" aria-hidden="true" /> Prenota sul sito dell'organizzatore
          </a>
          <p v-else class="m-0 text-sm text-ink-soft">Partecipazione libera, senza prenotazione.</p>
          <p v-if="event.booking_mode === 'REQUEST'" class="m-0 -mt-2 text-xs text-ink-mute">Nessun pagamento online: l'organizzatore ti risponde via email per confermare.</p>
        </template>

        <ClientOnly>
          <EventMap :events="[event]" />
        </ClientOnly>
      </aside>
    </section>

    <section v-if="related.length" class="bg-white border-t border-line py-12 md:py-16">
      <div class="page-container">
        <h2 class="title-section text-[32px] md:text-[40px] mb-6">Altri eventi in programma</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <EventCard v-for="ev in related" :key="ev.id" :event="ev" />
        </div>
      </div>
    </section>

    <EventRequestModal :is-open="requestOpen" :event="event" @close="requestOpen = false" />
  </div>

  <div v-else class="page-container py-24 text-center flex flex-col items-center gap-4">
    <h1 class="title-section">Evento non trovato</h1>
    <p class="text-ink-soft">L'evento cercato non esiste o non è più pubblico.</p>
    <NuxtLink to="/eventi" class="btn-primary">Tutti gli eventi</NuxtLink>
  </div>
</template>

<script setup>
import { CalendarDays, MapPin, Mail, ExternalLink, Pencil } from 'lucide-vue-next'
import CoverArt from '~/components/CoverArt.vue'
import EventCard from '~/components/EventCard.vue'
import EventMap from '~/components/EventMap.client.vue'
import EventRequestModal from '~/components/EventRequestModal.vue'
import { placeLabel, priceLabel } from '~/utils/events'

const route = useRoute()
const { fetchWithAuth } = useApi()
const { mediaUrl, tone, initials } = useProducer()
const origin = useRequestURL().origin
const requestOpen = ref(false)

const { data: event, pending } = await useAsyncData(`event_${route.params.slug}`, async () => {
  try {
    return (await fetchWithAuth(`/events/${route.params.slug}`)) || null
  } catch (err) {
    return null
  }
}, { default: () => null })

if (!event.value) setResponseStatus(useRequestEvent(), 404)

const { data: others } = await useAsyncData(`event_others_${route.params.slug}`, async () => {
  try { return (await fetchWithAuth('/events?limit=12')) || [] } catch (e) { return [] }
}, { default: () => [] })

const upcoming = computed(() => (event.value?.dates || []).filter(d => !d.is_past))
// eventi ricorrenti: le date passate non servono piu', tranne per un evento gia' concluso
const shownDates = computed(() => (upcoming.value.length ? upcoming.value : event.value?.dates || []))
const bookable = computed(() => event.value && event.value.status === 'PUBLISHED' && !event.value.is_past)
const related = computed(() => (others.value || []).filter(e => e.id !== event.value?.id).slice(0, 3))

const directionsUrl = computed(() => {
  const loc = event.value?.location || {}
  if (loc.lat != null && loc.lng != null) return `https://www.google.com/maps/dir/?api=1&destination=${loc.lat},${loc.lng}`
  const q = [loc.name, loc.street, loc.city, loc.province, 'Molise'].filter(Boolean).join(', ')
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`
})

watchEffect(() => {
  const ev = event.value
  if (!ev) return
  const when = ev.next_date?.label || ev.dates?.[0]?.label || ''
  useSeoMeta({
    title: `${ev.title} - ${when} | Eventi in Molise`,
    description: (ev.description || `${ev.type_label} a ${placeLabel(ev)}, ${when}.`).slice(0, 160),
    ogImage: ev.cover_image ? mediaUrl(ev.cover_image) : undefined
  })
})

// dati strutturati: Google puo' mostrare l'evento con data e luogo nei risultati di ricerca
useHead(() => {
  const ev = event.value
  if (!ev) return {}
  const base = origin
  const loc = ev.location || {}
  const toIso = (v) => (v ? `${String(v).slice(0, 16)}:00` : undefined)
  const date = ev.next_date || ev.dates?.[0] || {}
  const data = {
    '@context': 'https://schema.org',
    '@type': 'Event',
    name: ev.title,
    description: ev.description || undefined,
    startDate: toIso(date.start),
    endDate: toIso(date.end),
    eventStatus: ev.status === 'CANCELLED' ? 'https://schema.org/EventCancelled' : 'https://schema.org/EventScheduled',
    eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode',
    location: {
      '@type': 'Place',
      name: loc.name || loc.city || 'Molise',
      address: { '@type': 'PostalAddress', streetAddress: loc.street || undefined, addressLocality: loc.city || undefined, addressRegion: 'Molise', addressCountry: 'IT' },
      geo: loc.lat != null && loc.lng != null ? { '@type': 'GeoCoordinates', latitude: loc.lat, longitude: loc.lng } : undefined
    },
    image: ev.cover_image ? [mediaUrl(ev.cover_image)] : undefined,
    organizer: ev.organizer ? { '@type': 'Organization', name: ev.organizer.name, url: base ? `${base}/produttori/${ev.organizer.slug}` : undefined } : undefined,
    isAccessibleForFree: ev.price_type === 'FREE',
    url: base ? `${base}/eventi/${ev.slug}` : undefined
  }
  return { script: [{ type: 'application/ld+json', innerHTML: JSON.stringify(data) }] }
})
</script>
