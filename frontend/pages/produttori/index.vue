<template>
  <div>
    <section class="bg-sand border-b border-line">
      <div class="page-container pt-10 pb-7 flex flex-col gap-6">
        <div class="flex flex-col gap-2 max-w-[680px]">
          <span class="eyebrow">Chi produce</span>
          <h1 class="title-display">Le cantine del Molise</h1>
          <p class="text-[17px] text-ink-soft">Dal litorale di Campomarino all'Alta Valle del Volturno: conosci i produttori e contattali direttamente.</p>
        </div>
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div class="flex flex-wrap items-center gap-3 flex-1">
            <div class="flex items-center gap-2 h-12 px-3.5 border border-line-strong rounded-xl bg-white flex-1 min-w-[240px] max-w-[420px] focus-within:border-wine-800">
              <Search class="w-[18px] h-[18px] text-ink-mute shrink-0" aria-hidden="true" />
              <label for="winery-search" class="sr-only">Cerca cantina</label>
              <input
                id="winery-search"
                v-model="searchQuery"
                type="search"
                placeholder="Nome della cantina o paese"
                class="flex-1 min-w-0 bg-transparent text-[15px] text-ink placeholder:text-ink-mute/70 focus:outline-none"
              />
            </div>
            <div role="group" aria-label="Provincia" class="flex gap-1.5">
              <button
                v-for="prov in provinces"
                :key="prov.value"
                type="button"
                :aria-pressed="province === prov.value"
                :class="['pill h-11', province === prov.value && 'pill-active']"
                @click="province = prov.value"
              >
                {{ prov.label }}
              </button>
            </div>
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
    </section>

    <section class="page-container pt-8 md:pt-10 pb-16 md:pb-20">
      <p class="mb-5 text-[15px] text-ink-soft" aria-live="polite">
        <strong class="text-ink">{{ filteredProducers.length }}</strong> {{ filteredProducers.length === 1 ? 'cantina' : 'cantine' }}
      </p>

      <div v-if="pending" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="i in 6" :key="i" class="h-80 rounded-2xl bg-sand animate-pulse"></div>
      </div>

      <div v-else-if="viewMode === 'map'" class="grid grid-cols-1 lg:grid-cols-[340px_minmax(0,1fr)] gap-5">
        <ul class="m-0 p-0 list-none flex flex-col gap-2 lg:max-h-[690px] lg:overflow-y-auto order-2 lg:order-1">
          <li v-for="producer in filteredProducers" :key="producer.id">
            <NuxtLink :to="`/produttori/${producer.slug}`" class="flex items-center gap-3 p-3 rounded-xl border border-line bg-white text-ink hover:border-line-strong">
              <span class="shrink-0 w-11 h-11 rounded-[10px] bg-sand-100 flex items-center justify-center font-serif text-lg font-bold text-wine-800">{{ initials(producer.company_name) }}</span>
              <span class="flex flex-col min-w-0 leading-snug">
                <span class="font-bold text-[15px] truncate">{{ producer.company_name }}</span>
                <span class="text-[13px] text-ink-mute">{{ place(producer) }} · {{ countLabel(producer.product_count) }}</span>
              </span>
            </NuxtLink>
          </li>
        </ul>
        <div class="order-1 lg:order-2">
          <WineryMap :producers="filteredProducers" title="Mappa delle cantine" subtitle="Clicca su un segnaposto per aprire la cantina" :zoom="9" tall />
        </div>
      </div>

      <div v-else-if="filteredProducers.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <ProducerCard v-for="producer in filteredProducers" :key="producer.id" :producer="producer" />
      </div>

      <div v-else class="card p-10 text-center flex flex-col items-center gap-3">
        <h2 class="title-card text-2xl">Nessuna cantina trovata</h2>
        <p class="text-ink-soft">Nessuna cantina corrisponde a “{{ searchQuery }}”.</p>
        <button type="button" class="btn-outline" @click="searchQuery = ''; province = ''">Azzera la ricerca</button>
      </div>
    </section>

    <section class="bg-white border-t border-line">
      <div class="page-container py-12 flex flex-wrap items-center justify-between gap-6">
        <div class="flex flex-col gap-1.5 max-w-[620px]">
          <span class="font-serif text-[32px] font-bold leading-tight">Hai una cantina in Molise?</span>
          <span class="text-base text-ink-soft">Registrati gratis: pubblica i tuoi vini e ricevi le richieste direttamente.</span>
        </div>
        <NuxtLink to="/login?mode=register" class="btn-outline">Registra la tua cantina</NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Search } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()
const { initials, place, countLabel } = useProducer()

useSeoMeta({
  title: 'Le Cantine Molisane - Produttori e Vigneti del Molise',
  description: 'Scopri i produttori vinicoli del Molise. Esplora le cantine di Tintilia, Biferno e Pentro a Campobasso e Isernia.'
})

const route = useRoute()
const router = useRouter()
const searchQuery = ref('')
const province = ref('')
const viewMode = ref(route.query.view === 'map' ? 'map' : 'grid')

const provinces = [
  { label: 'Tutte', value: '' },
  { label: 'Campobasso', value: 'CB' },
  { label: 'Isernia', value: 'IS' }
]
const viewModes = [
  { label: 'Griglia', value: 'grid' },
  { label: 'Mappa', value: 'map' }
]

watch(() => route.query.view, (v) => { viewMode.value = v === 'map' ? 'map' : 'grid' })

const setView = (mode) => {
  viewMode.value = mode
  router.replace({ query: { ...route.query, view: mode === 'map' ? 'map' : undefined } })
}

const { data: producers, pending } = await useAsyncData('all_producers', async () => {
  const res = await fetchWithAuth('/producers')
  return res || []
}, { default: () => [] })

const filteredProducers = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  return [...(producers.value || [])]
    .filter((p) => !province.value || (p.address?.province || '').toUpperCase() === province.value)
    .filter((p) => {
      if (!q) return true
      return [p.company_name, p.address?.city, p.address?.province].some((v) => (v || '').toLowerCase().includes(q))
    })
    .sort((a, b) => (b.product_count || 0) - (a.product_count || 0))
})
</script>
