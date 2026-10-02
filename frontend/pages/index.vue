<template>
  <div>
    <!-- HERO: luminoso, ricerca come azione principale -->
    <section class="page-container pt-10 md:pt-14 pb-10 grid grid-cols-1 gap-10 lg:gap-12 lg:grid-cols-2 items-center">
      <div class="flex flex-col gap-6">
        <span class="eyebrow">Il portale delle cantine molisane</span>
        <h1 class="font-serif font-semibold text-ink text-[44px] md:text-[68px] leading-[1.02] text-balance">Scopri i tesori dei vigneti del Molise</h1>
        <p class="text-lg text-ink-soft max-w-[520px]">
          Dalla Tintilia autoctona ai rossi del Biferno: {{ productCount }} vini di {{ producerCount }} cantine, da conoscere e da contattare direttamente.
        </p>
        <form role="search" class="flex flex-col gap-3 max-w-[560px]" @submit.prevent="handleHeroSearch">
          <label for="home-search" class="text-[13px] font-semibold text-ink-soft">Cerca nel catalogo</label>
          <div class="flex gap-2 p-1.5 border border-line-strong rounded-[14px] bg-white focus-within:border-wine-800">
            <input
              id="home-search"
              v-model="heroQuery"
              type="search"
              placeholder="Vino, cantina o vitigno"
              class="flex-1 min-w-0 px-3 bg-transparent text-base text-ink placeholder:text-ink-mute/70 focus:outline-none"
            />
            <button type="submit" class="btn-primary h-12 px-[22px]">Cerca</button>
          </div>
          <div class="flex flex-wrap gap-2">
            <NuxtLink v-for="pill in quickPills" :key="pill.label" :to="pill.to" class="chip">{{ pill.label }}</NuxtLink>
          </div>
        </form>
      </div>
      <figure class="m-0">
        <img
          src="https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=1400&q=80"
          alt="Filari di vigneto in collina"
          class="w-full aspect-[5/4] object-cover rounded-[20px] bg-sand-300"
        />
      </figure>
    </section>

    <!-- NUMERI -->
    <section aria-label="Il catalogo in numeri" class="border-y border-line bg-white">
      <div class="page-container py-6 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div v-for="stat in stats" :key="stat.label" class="flex items-baseline gap-2.5">
          <span class="font-serif text-[40px] font-bold text-wine-800 leading-none">{{ stat.value }}</span>
          <span class="text-sm text-ink-soft">{{ stat.label }}</span>
        </div>
      </div>
    </section>

    <!-- VINI IN EVIDENZA: un vino per cantina -->
    <section class="page-container py-14 md:py-20">
      <div class="flex flex-wrap items-end justify-between gap-5 mb-7">
        <div class="flex flex-col gap-2">
          <span class="eyebrow">Selezione dal catalogo</span>
          <h2 class="title-section">Vini in evidenza</h2>
        </div>
        <div role="tablist" aria-label="Filtra per tipologia" class="flex flex-wrap gap-1.5">
          <button
            v-for="tab in productTabs"
            :key="tab.value"
            type="button"
            role="tab"
            :aria-selected="selectedTab === tab.value"
            :class="['pill', selectedTab === tab.value && 'pill-active']"
            @click="selectedTab = tab.value"
          >
            {{ tab.label }}
          </button>
        </div>
      </div>

      <div v-if="pendingProducts" class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div v-for="i in 4" :key="i" class="h-96 rounded-2xl bg-sand animate-pulse"></div>
      </div>
      <div v-else-if="featuredProducts.length" class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <ProductCard v-for="prod in featuredProducts" :key="prod.id" :product="prod" />
      </div>
      <p v-else class="card p-8 text-center text-ink-soft">Nessun vino in questa tipologia, per ora.</p>

      <div class="flex justify-center mt-8">
        <NuxtLink to="/vini" class="btn-primary">Esplora tutti i {{ productCount }} vini</NuxtLink>
      </div>
    </section>

    <!-- LE DENOMINAZIONI -->
    <section class="bg-sand py-14 md:py-20">
      <div class="page-container flex flex-col gap-7">
        <div class="flex flex-col gap-2 max-w-[640px]">
          <span class="eyebrow">Il territorio</span>
          <h2 class="title-section">Le grandi denominazioni</h2>
        </div>
        <div class="grid grid-cols-1 gap-5 md:grid-cols-3">
          <NuxtLink v-for="doc in denominations" :key="doc.name" :to="doc.to" class="group flex flex-col rounded-2xl overflow-hidden bg-white text-ink">
            <div class="h-[140px] overflow-hidden" :style="{ background: doc.tone }">
              <DenomArt :variant="doc.art" class="group-hover:scale-[1.03] transition-transform duration-700" />
            </div>
            <div class="p-[22px] flex flex-col gap-2">
              <span class="text-xs font-bold text-gold-600">{{ doc.since }}</span>
              <span class="font-serif text-[28px] font-bold leading-tight">{{ doc.name }}</span>
              <span class="text-[15px] text-ink-soft">{{ doc.text }}</span>
              <span class="text-sm font-bold text-wine-800 mt-1.5 group-hover:text-wine-900">Vedi i vini →</span>
            </div>
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- LE CANTINE -->
    <section class="page-container py-14 md:py-20">
      <div class="flex flex-wrap items-end justify-between gap-5 mb-7">
        <div class="flex flex-col gap-2">
          <span class="eyebrow">Chi produce</span>
          <h2 class="title-section">Le cantine molisane</h2>
        </div>
        <NuxtLink to="/produttori" class="text-[15px] font-bold">Tutte le {{ producerCount }} cantine →</NuxtLink>
      </div>
      <div v-if="pendingProducers" class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in 3" :key="i" class="h-80 rounded-2xl bg-sand animate-pulse"></div>
      </div>
      <div v-else class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        <ProducerCard v-for="producer in topProducers" :key="producer.id" :producer="producer" />
      </div>
    </section>

    <!-- MAPPA -->
    <section class="bg-white border-t border-line py-14 md:py-20">
      <div class="page-container grid grid-cols-1 gap-10 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] items-center">
        <div class="flex flex-col gap-4">
          <span class="eyebrow">Sul territorio</span>
          <h2 class="title-section">Trova le cantine vicino a te</h2>
          <p class="text-[17px] text-ink-soft max-w-[460px]">Da Campomarino a Monteroduni: guarda dove nascono i vini e organizza una visita in cantina.</p>
          <div class="flex flex-wrap gap-3">
            <NuxtLink to="/produttori?view=map" class="btn-primary">Apri la mappa</NuxtLink>
            <NuxtLink to="/produttori" class="btn-outline">Elenco delle cantine</NuxtLink>
          </div>
        </div>
        <WineryMap :producers="producers" title="Le cantine del Molise" :subtitle="`${producerCount} produttori sulla mappa`" :zoom="9" />
      </div>
    </section>

    <!-- PERCHE' ENOTECAMOLISE -->
    <section class="page-container py-14 md:py-20 grid grid-cols-1 gap-8 md:grid-cols-3">
      <div v-for="point in reasons" :key="point.title" class="flex flex-col gap-2.5">
        <span class="font-serif text-[26px] font-bold">{{ point.title }}</span>
        <span class="text-[15px] text-ink-soft">{{ point.text }}</span>
      </div>
    </section>
  </div>
</template>

<script setup>
import DenomArt from '~/components/DenomArt.vue'

const router = useRouter()
const { fetchWithAuth } = useApi()
const { isOrganicProduct } = useOrganic()

useSeoMeta({
  title: 'EnotecaMolise - I vini e le cantine del Molise',
  description: 'Scopri i vini del Molise: Tintilia, Biferno, Pentro e spumanti. Contatta direttamente le cantine molisane.'
})

const heroQuery = ref('')
const selectedTab = ref('ALL')

const quickPills = [
  { label: 'Tintilia', to: '/vini?search=Tintilia' },
  { label: 'Biferno', to: '/vini?search=Biferno' },
  { label: 'Biologici', to: '/vini?organic=organic' },
  { label: 'Spumanti', to: '/vini?category=SPUMANTE' },
  { label: 'Vicino a me', to: '/produttori?view=map' }
]

const productTabs = [
  { label: 'Tutti', value: 'ALL' },
  { label: 'Rossi', value: 'VINO_ROSSO' },
  { label: 'Bianchi', value: 'VINO_BIANCO' },
  { label: 'Rosati', value: 'ROSATO' },
  { label: 'Spumanti', value: 'SPUMANTE' },
  { label: 'Biologici', value: 'ORGANIC' }
]

const denominations = [
  { name: 'Tintilia del Molise', since: 'DOC dal 2011', to: '/vini?search=Tintilia', art: 'tintilia', tone: '#8C5A5F', text: 'Il vitigno autoctono simbolo della regione: rosso rubino, pepe nero e prugna secca.' },
  { name: 'Biferno', since: 'DOC dal 1983', to: '/vini?search=Biferno', art: 'biferno', tone: '#9A8F6C', text: 'Lungo il fiume, tra Campobasso e il mare: rossi strutturati, rosati e bianchi freschi.' },
  { name: "Pentro d'Isernia", since: 'DOC dal 1983', to: '/vini?search=Pentro', art: 'pentro', tone: '#7F8B80', text: "L'Alto Molise e l'escursione termica appenninica: vini minerali ed eleganti." }
]

const reasons = [
  { title: 'Solo vino molisano', text: 'Un catalogo dedicato alle cantine e ai vitigni del Molise: Tintilia, Biferno, Pentro.' },
  { title: 'Contatto diretto', text: 'Nessun intermediario: scrivi alla cantina per prezzi, disponibilità e visite.' },
  { title: 'Territorio e visite', text: 'La mappa delle cantine per conoscere il Molise del vino da vicino.' }
]

const handleHeroSearch = () => {
  const q = heroQuery.value.trim()
  router.push(q ? `/vini?search=${encodeURIComponent(q)}` : '/vini')
}

const { data: products, pending: pendingProducts } = await useAsyncData('home_products', async () => {
  const res = await fetchWithAuth('/products?status=PUBLISHED')
  return res || []
}, { default: () => [] })

const { data: producers, pending: pendingProducers } = await useAsyncData('home_producers', async () => {
  const res = await fetchWithAuth('/producers')
  return res || []
}, { default: () => [] })

const productCount = computed(() => (products.value || []).length)
const producerCount = computed(() => (producers.value || []).length)

const stats = computed(() => [
  { value: productCount.value, label: 'vini in catalogo' },
  { value: producerCount.value, label: 'cantine' },
  { value: 3, label: 'grandi DOC' },
  { value: 0, label: 'intermediari: contatti diretti' }
])

// un vino per cantina, cosi' la vetrina non e' dominata da un solo produttore
const featuredProducts = computed(() => {
  const prods = (products.value || []).filter((p) => {
    if (selectedTab.value === 'ALL') return p.category !== 'LIQUORE'
    if (selectedTab.value === 'ORGANIC') return isOrganicProduct(p)
    return p.category === selectedTab.value
  })
  const seen = new Set()
  const picked = []
  for (const p of prods) {
    const key = p.producer_id || p.producer_name
    if (seen.has(key)) continue
    seen.add(key)
    picked.push(p)
    if (picked.length === 4) break
  }
  return picked
})

const topProducers = computed(() =>
  [...(producers.value || [])].sort((a, b) => (b.product_count || 0) - (a.product_count || 0)).slice(0, 6)
)
</script>
