<template>
  <div v-if="pending" class="page-container py-16">
    <div class="h-96 rounded-[20px] bg-sand animate-pulse"></div>
  </div>

  <div v-else-if="producer">
    <!-- Barra per amministratore o cantina proprietaria -->
    <div v-if="canEdit" class="bg-sand-100 border-b border-line">
      <div class="page-container py-2.5 flex flex-wrap items-center justify-between gap-3 text-sm">
        <span class="text-ink-soft">
          Stai vedendo la pagina pubblica come <strong class="text-ink">{{ isAdmin ? 'amministratore' : 'cantina proprietaria' }}</strong>.
          <strong v-if="producer.status === 'PENDING_APPROVAL'" class="text-[#7A5A1E]"> Non è ancora visibile ai visitatori: la cantina è in attesa di approvazione.</strong>
          <strong v-else-if="producer.status === 'SUSPENDED'" class="text-wine-800"> Non è visibile ai visitatori: la cantina è sospesa.</strong>
        </span>
        <NuxtLink :to="isAdmin ? `/dashboard/profilo?producer_id=${producer.id}` : '/dashboard/profilo'" class="btn-ghost btn-sm">
          <Pencil class="w-4 h-4" aria-hidden="true" /> Modifica dati cantina
        </NuxtLink>
      </div>
    </div>

    <nav aria-label="Percorso" class="page-container pt-4 flex flex-wrap gap-2 text-[13px] text-ink-mute">
      <NuxtLink to="/" class="text-ink-mute hover:text-wine-800">Home</NuxtLink><span aria-hidden="true">/</span>
      <NuxtLink to="/produttori" class="text-ink-mute hover:text-wine-800">Cantine</NuxtLink><span aria-hidden="true">/</span>
      <span class="text-ink font-semibold">{{ producer.company_name }}</span>
    </nav>

    <!-- COPERTINA + LOGO SOVRAPPOSTO -->
    <section class="page-container pt-4">
      <div class="h-[220px] md:h-[340px] rounded-[20px] overflow-hidden" :style="{ background: tone(producer.company_name) }">
        <SafeImg :src="cover" :alt="`Copertina di ${producer.company_name}`" class="w-full h-full object-cover">
          <CoverArt :seed="producer.company_name" :place="place(producer)" />
        </SafeImg>
      </div>
      <div class="flex flex-wrap items-end justify-between gap-6 px-2">
        <div class="flex flex-wrap items-end gap-5">
          <span class="relative z-10 self-start -mt-[44px] md:-mt-[60px] w-[120px] h-[120px] rounded-[22px] border-4 border-cream shadow-[0_6px_20px_rgba(42,8,18,0.10)] logo-box text-[40px]">
            <SafeImg :src="logo" :alt="`Logo ${producer.company_name}`" class="logo-img p-2.5">{{ initials(producer.company_name) }}</SafeImg>
          </span>
          <div class="flex flex-col gap-1.5 pt-4">
            <span class="eyebrow">Cantina</span>
            <h1 class="title-display">{{ producer.company_name }}</h1>
            <span class="flex items-center gap-1.5 text-[15px] text-ink-soft">
              <MapPin class="w-4 h-4" aria-hidden="true" /> {{ place(producer) }} · Molise
            </span>
          </div>
        </div>
        <div class="flex flex-wrap gap-2.5 pt-4 w-full sm:w-auto">
          <button type="button" class="btn-primary flex-1 sm:flex-none" @click="isModalOpen = true">
            <Mail class="w-[18px] h-[18px]" aria-hidden="true" /> Contatta la cantina
          </button>
          <a
            v-if="producer.contacts?.whatsapp_number"
            :href="getWhatsAppUrl({ number: producer.contacts.whatsapp_number, companyName: producer.company_name })"
            target="_blank"
            rel="noopener"
            class="btn-ghost"
          >
            <MessageCircle class="w-[18px] h-[18px]" aria-hidden="true" /> WhatsApp
          </a>
          <a v-if="producer.contacts?.website" :href="websiteUrl(producer.contacts.website)" target="_blank" rel="noopener" class="btn-ghost">
            <Globe class="w-[18px] h-[18px]" aria-hidden="true" /> Sito web
          </a>
        </div>
      </div>
    </section>

    <!-- DATI RAPIDI -->
    <section v-if="facts.length" aria-label="In breve" class="page-container mt-8">
      <dl class="grid grid-cols-2 md:grid-cols-[repeat(auto-fit,minmax(160px,1fr))] card overflow-hidden">
        <div v-for="fact in facts" :key="fact.label" class="px-5 py-4 border-r border-b md:border-b-0 border-line-soft flex flex-col gap-1">
          <dt class="eyebrow-sm tracking-[0.08em]">{{ fact.label }}</dt>
          <dd class="font-serif text-lg md:text-xl font-bold leading-snug text-ink">{{ fact.value }}</dd>
        </div>
      </dl>
    </section>

    <!-- I VINI -->
    <section class="page-container py-12 md:py-16">
      <div class="flex flex-wrap items-end justify-between gap-5 mb-6">
        <div class="flex flex-col gap-2">
          <span class="eyebrow">In catalogo</span>
          <h2 class="title-section">I vini della cantina</h2>
        </div>
        <div class="flex flex-wrap items-center gap-1.5">
          <div v-if="categoryTabs.length > 2" role="tablist" aria-label="Filtra per tipologia" class="flex flex-wrap gap-1.5">
            <button
              v-for="cat in categoryTabs"
              :key="cat.value"
              type="button"
              role="tab"
              :aria-selected="selectedCategory === cat.value"
              :class="['pill', selectedCategory === cat.value && 'pill-active']"
              @click="selectedCategory = cat.value"
            >
              {{ cat.label }} <span class="ml-1.5 opacity-70">{{ cat.count }}</span>
            </button>
          </div>
          <NuxtLink v-if="canEdit" to="/dashboard/prodotti/nuovo" class="btn-ghost btn-sm ml-2">
            <Plus class="w-4 h-4" aria-hidden="true" /> Aggiungi vino
          </NuxtLink>
        </div>
      </div>
      <div v-if="filteredProducts.length" class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
        <ProductCard v-for="prod in filteredProducts" :key="prod.id" :product="prod" :show-producer="false" />
      </div>
      <p v-else class="card p-8 text-center text-ink-soft">I vini di questa cantina saranno presto in catalogo.</p>
    </section>

    <!-- PROSSIMI EVENTI -->
    <section v-if="producerEvents.length || canEdit" class="page-container pb-12 md:pb-16">
      <div class="flex flex-wrap items-end justify-between gap-4 mb-6">
        <div class="flex flex-col gap-2">
          <span class="eyebrow">In programma</span>
          <h2 class="title-section text-[32px] md:text-[40px]">Prossimi eventi</h2>
        </div>
        <NuxtLink v-if="canEdit" to="/dashboard/eventi/nuovo" class="btn-ghost btn-sm">
          <Plus class="w-4 h-4" aria-hidden="true" /> Nuovo evento
        </NuxtLink>
      </div>
      <div v-if="producerEvents.length" class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <EventCard v-for="ev in producerEvents.slice(0, 4)" :key="ev.id" :event="ev" compact />
      </div>
      <p v-else class="m-0 text-ink-soft">Nessun evento in programma: pubblica una degustazione o una visita, comparirà qui e nel calendario del sito.</p>
    </section>

    <!-- STORIA + VISITA E CONTATTI -->
    <section id="contatti" class="bg-sand py-12 md:py-[72px]">
      <div class="page-container grid grid-cols-1 gap-10 lg:grid-cols-2 items-start">
        <div class="flex flex-col gap-4">
          <span class="eyebrow">La storia</span>
          <h2 class="title-section">Chi è {{ producer.company_name }}</h2>
          <div v-if="producer.description" class="text-[17px] text-ink-soft whitespace-pre-line text-pretty">
            <p class="m-0">{{ shownDescription }}</p>
            <button v-if="isLongDescription" type="button" class="mt-3 font-bold text-wine-800 hover:text-wine-900" :aria-expanded="showFullStory" @click="showFullStory = !showFullStory">
              {{ showFullStory ? 'Mostra meno' : 'Leggi tutta la storia' }}
            </button>
          </div>
          <p v-else class="text-[17px] text-ink-soft">La cantina non ha ancora inserito la sua presentazione.</p>
        </div>

        <aside aria-label="Visita e contatti" class="card overflow-hidden flex flex-col">
          <WineryMap :producers="mapProducers" :zoom="13" bare class="border-b border-line" />
          <div class="p-6 flex flex-col gap-5">
            <span class="font-serif text-[28px] font-bold leading-tight">Visita e contatti</span>
            <ul class="m-0 p-0 list-none flex flex-col gap-3.5 text-[15px]">
              <li v-if="addressLine" class="flex gap-3">
                <MapPin class="w-5 h-5 text-gold-600 shrink-0" aria-hidden="true" /><span>{{ addressLine }}</span>
              </li>
              <li v-if="producer.contacts?.phone" class="flex gap-3">
                <Phone class="w-5 h-5 text-gold-600 shrink-0" aria-hidden="true" />
                <a :href="`tel:${producer.contacts.phone}`" class="font-semibold">{{ producer.contacts.phone }}</a>
              </li>
              <li v-if="producer.contacts?.email_contact" class="flex gap-3 min-w-0">
                <Mail class="w-5 h-5 text-gold-600 shrink-0" aria-hidden="true" />
                <a :href="`mailto:${producer.contacts.email_contact}`" class="font-semibold truncate">{{ producer.contacts.email_contact }}</a>
              </li>
              <li v-if="producer.contacts?.website" class="flex gap-3 min-w-0">
                <Globe class="w-5 h-5 text-gold-600 shrink-0" aria-hidden="true" />
                <a :href="websiteUrl(producer.contacts.website)" target="_blank" rel="noopener" class="font-semibold truncate">{{ producer.contacts.website.replace(/^https?:\/\//, '') }}</a>
              </li>
              <li v-if="producer.contacts?.instagram || producer.contacts?.facebook" class="flex gap-3">
                <AtSign class="w-5 h-5 text-gold-600 shrink-0" aria-hidden="true" />
                <span class="flex flex-wrap gap-x-4">
                  <a v-if="producer.contacts?.instagram" :href="socialUrl(producer.contacts.instagram, 'instagram')" target="_blank" rel="noopener" class="font-semibold">Instagram</a>
                  <a v-if="producer.contacts?.facebook" :href="socialUrl(producer.contacts.facebook, 'facebook')" target="_blank" rel="noopener" class="font-semibold">Facebook</a>
                </span>
              </li>
            </ul>
            <div class="flex flex-wrap gap-2.5">
              <button type="button" class="btn-primary" @click="isModalOpen = true">Scrivi alla cantina</button>
              <a v-if="directionsUrl" :href="directionsUrl" target="_blank" rel="noopener" class="btn-outline">Indicazioni stradali</a>
            </div>
          </div>
        </aside>
      </div>
    </section>

    <!-- CANTINE NEI DINTORNI -->
    <section v-if="nearby.length" class="bg-white border-t border-line py-12 md:py-16">
      <div class="page-container">
        <div class="flex flex-wrap items-end justify-between gap-5 mb-6">
          <h2 class="title-section text-[32px] md:text-[40px]">Cantine nei dintorni</h2>
          <NuxtLink to="/produttori?view=map" class="text-[15px] font-bold">Vedi sulla mappa →</NuxtLink>
        </div>
        <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
          <NuxtLink
            v-for="near in nearby"
            :key="near.id"
            :to="`/produttori/${near.slug}`"
            class="flex items-center gap-4 p-4 rounded-2xl border border-line bg-cream text-ink hover:border-line-strong"
          >
            <span class="logo-box shrink-0 w-14 h-14 rounded-xl border border-line text-[22px]">
              <SafeImg :src="logoUrl(near)" alt="" class="logo-img p-1">{{ initials(near.company_name) }}</SafeImg>
            </span>
            <span class="flex flex-col gap-0.5 min-w-0">
              <span class="font-serif text-[22px] font-bold leading-tight">{{ near.company_name }}</span>
              <span class="text-sm text-ink-soft">{{ place(near) }}<template v-if="near.km"> · {{ near.km }} km</template></span>
            </span>
          </NuxtLink>
        </div>
      </div>
    </section>

    <InquiryModal
      :is-open="isModalOpen"
      :producer-id="producer.id"
      :producer-name="producer.company_name"
      :whatsapp-number="producer.contacts?.whatsapp_number"
      @close="isModalOpen = false"
    />
  </div>

  <div v-else class="page-container py-24 text-center flex flex-col items-center gap-4">
    <h1 class="title-section">Cantina non trovata</h1>
    <p class="text-ink-soft">La cantina cercata non è presente o non è ancora pubblica.</p>
    <NuxtLink to="/produttori" class="btn-primary">Tutte le cantine</NuxtLink>
  </div>
</template>

<script setup>
import CoverArt from '~/components/CoverArt.vue'
import EventCard from '~/components/EventCard.vue'
import { primaryGrape } from '~/utils/grapes'
import { Pencil, MapPin, Phone, Mail, Globe, MessageCircle, Plus, AtSign } from 'lucide-vue-next'

const route = useRoute()
const { fetchWithAuth } = useApi()
const { user, isAdmin, isAuthenticated } = useAuth()
const { getWhatsAppUrl } = useWhatsApp()
const { coverUrl, logoUrl, initials, tone, place, websiteUrl, socialUrl } = useProducer()
const { formatCategory } = useCategoryBadge()
const { isOrganicProduct } = useOrganic()

const isModalOpen = ref(false)
const selectedCategory = ref('ALL')
const showFullStory = ref(false)

const { data: producer, pending } = await useAsyncData(`producer_${route.params.slug}`, async () => {
  try {
    return (await fetchWithAuth(`/producers/${route.params.slug}`)) || null
  } catch (err) {
    return null
  }
}, { default: () => null })

// pagina "non trovato" con il codice giusto (404), anche per i motori di ricerca
if (!producer.value) setResponseStatus(useRequestEvent(), 404)

watchEffect(() => {
  if (producer.value) {
    useSeoMeta({
      title: `${producer.value.company_name} - Cantina del Molise`,
      description: producer.value.description || `Scopri la cantina ${producer.value.company_name} a ${producer.value.address?.city || 'Molise'}. Vini, storia e contatti su EnotecaMolise.`
    })
  }
})

const canEdit = computed(() => {
  if (!isAuthenticated.value || !producer.value) return false
  if (isAdmin.value) return true
  const userProdId = user.value?.producer_id || user.value?.producer?.id
  return userProdId && String(userProdId) === String(producer.value.id)
})

const { data: producerProducts } = await useAsyncData(`producer_products_${route.params.slug}`, async () => {
  if (!producer.value?.id) return []
  return (await fetchWithAuth(`/products?producer_id=${producer.value.id}&status=PUBLISHED`)) || []
}, { watch: [producer], default: () => [] })

const { data: producerEvents } = await useAsyncData(`producer_events_${route.params.slug}`, async () => {
  if (!producer.value?.id) return []
  try { return (await fetchWithAuth(`/events?producer=${producer.value.id}`)) || [] } catch (e) { return [] }
}, { watch: [producer], default: () => [] })

const { data: allProducers } = await useAsyncData('all_producers', async () => {
  return (await fetchWithAuth('/producers')) || []
}, { default: () => [] })

const mapProducers = computed(() => (producer.value ? [producer.value] : []))
const cover = computed(() => coverUrl(producer.value))
const logo = computed(() => logoUrl(producer.value))

const CATEGORY_ORDER = ['VINO_ROSSO', 'VINO_BIANCO', 'ROSATO', 'SPUMANTE', 'PASSITO', 'LIQUORE']
const categoryTabs = computed(() => {
  const prods = producerProducts.value || []
  const tabs = [{ label: 'Tutti', value: 'ALL', count: prods.length }]
  for (const cat of CATEGORY_ORDER) {
    const count = prods.filter((p) => p.category === cat).length
    if (count) tabs.push({ label: formatCategory(cat), value: cat, count })
  }
  return tabs
})

const filteredProducts = computed(() => {
  const prods = producerProducts.value || []
  return selectedCategory.value === 'ALL' ? prods : prods.filter((p) => p.category === selectedCategory.value)
})

// Dati rapidi ricavati dalle schede dei vini (solo quelli disponibili)
const facts = computed(() => {
  const prods = producerProducts.value || []
  const list = []
  if (prods.length) list.push({ label: 'Vini in catalogo', value: prods.length })
  const grapes = new Map()
  for (const p of prods) {
    const name = primaryGrape(p)
    if (name) grapes.set(name, (grapes.get(name) || 0) + 1)
  }
  const topGrapes = [...grapes.entries()].sort((a, b) => b[1] - a[1]).slice(0, 2).map(([n]) => n)
  if (topGrapes.length) list.push({ label: 'Vitigni', value: topGrapes.join(', ') })
  list.push({ label: 'Zona', value: place(producer.value) })
  const denoms = [...new Set(prods.map((p) => p.denominazione).filter(Boolean))]
  if (denoms.length) list.push({ label: 'Denominazioni', value: denoms.slice(0, 3).join(', ') })
  const altitude = prods
    .flatMap((p) => p.custom_attributes || [])
    .find((a) => /altitudin/i.test(a?.name || '') && a?.value)
  if (altitude) list.push({ label: 'Altitudine', value: String(altitude.value).replace(/\s*(mt|m)\.?\s*(s\.?l\.?m\.?)?$/i, ' m') })
  const organic = prods.filter((p) => isOrganicProduct(p)).length
  if (organic) list.push({ label: 'Biologici', value: organic === prods.length ? 'Tutti i vini' : `${organic} vini` })
  return list
})

const STORY_LIMIT = 700
const isLongDescription = computed(() => (producer.value?.description || '').length > STORY_LIMIT + 100)
const shownDescription = computed(() => {
  const text = producer.value?.description || ''
  if (!isLongDescription.value || showFullStory.value) return text
  const cut = text.slice(0, STORY_LIMIT)
  return cut.slice(0, cut.lastIndexOf(' ')) + '…'
})

const addressLine = computed(() => {
  const a = producer.value?.address || {}
  const second = [a.zip_code, a.city].filter(Boolean).join(' ') + (a.province ? ` (${a.province})` : '')
  return [a.street, second.trim()].filter(Boolean).join(', ')
})

const coords = (p) => {
  if (!p) return null
  const [lat, lng] = getProducerCoordinatesSync(p, 0)
  return { lat, lng }
}

const directionsUrl = computed(() => {
  const c = coords(producer.value)
  if (c) return `https://www.google.com/maps/dir/?api=1&destination=${c.lat},${c.lng}`
  return addressLine.value ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(addressLine.value)}` : ''
})

// Le tre cantine piu' vicine (in linea d'aria), se le coordinate sono disponibili
const nearby = computed(() => {
  const here = coords(producer.value)
  const others = (allProducers.value || []).filter((p) => p.id !== producer.value?.id)
  if (!here) return []
  const toRad = (d) => (d * Math.PI) / 180
  return others
    .map((p) => {
      const c = coords(p)
      if (!c) return null
      const dLat = toRad(c.lat - here.lat)
      const dLng = toRad(c.lng - here.lng)
      const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(here.lat)) * Math.cos(toRad(c.lat)) * Math.sin(dLng / 2) ** 2
      return { ...p, km: Math.round(6371 * 2 * Math.asin(Math.sqrt(h))) }
    })
    .filter(Boolean)
    .sort((a, b) => a.km - b.km)
    .slice(0, 3)
})
</script>
