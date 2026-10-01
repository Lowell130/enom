<template>
  <div>
    <!-- INTESTAZIONE -->
    <section class="bg-sand border-b border-line">
      <div class="page-container pt-10 pb-8 flex flex-wrap items-end justify-between gap-6">
        <div class="flex flex-col gap-2 max-w-[640px]">
          <span class="eyebrow">Catalogo</span>
          <h1 class="title-display">Tutti i vini del Molise</h1>
          <p class="text-[17px] text-ink-soft">{{ (products || []).length }} etichette di {{ producerOptions.length }} cantine. Filtra per tipologia, denominazione o vitigno.</p>
        </div>
        <div role="search" class="flex gap-2 p-1.5 border border-line-strong rounded-[14px] bg-white flex-1 min-w-[260px] max-w-[460px] focus-within:border-wine-800">
          <label for="catalog-search" class="sr-only">Cerca nel catalogo</label>
          <Search class="w-[18px] h-[18px] text-ink-mute self-center ml-2 shrink-0" aria-hidden="true" />
          <input
            id="catalog-search"
            v-model="filters.search"
            type="search"
            placeholder="Nome, vitigno, abbinamento…"
            class="flex-1 min-w-0 px-2 h-11 bg-transparent text-[15px] text-ink placeholder:text-ink-mute/70 focus:outline-none"
          />
        </div>
      </div>
    </section>

    <section class="page-container pt-8 md:pt-10 pb-16 md:pb-20 grid grid-cols-1 lg:grid-cols-[260px_minmax(0,1fr)] gap-8 lg:gap-10 items-start">
      <!-- FILTRI -->
      <div class="lg:sticky lg:top-24">
        <button
          type="button"
          class="lg:hidden btn-ghost w-full mb-4"
          :aria-expanded="showFilters"
          aria-controls="catalog-filters"
          @click="showFilters = !showFilters"
        >
          <SlidersHorizontal class="w-[18px] h-[18px]" aria-hidden="true" />
          {{ showFilters ? 'Nascondi filtri' : 'Mostra filtri' }}<template v-if="activeFilters.length"> ({{ activeFilters.length }})</template>
        </button>

        <aside id="catalog-filters" aria-label="Filtri" :class="['flex-col gap-7', showFilters ? 'flex' : 'hidden lg:flex']">
          <div class="flex flex-col gap-1">
            <span class="eyebrow-sm tracking-[0.12em] mb-1.5">Tipologia</span>
            <button
              v-for="cat in categoryOptions"
              :key="cat.value"
              type="button"
              :aria-pressed="filters.category === cat.value"
              :class="[
                'flex justify-between items-center min-h-[40px] px-3 rounded-[10px] text-[15px] text-left border transition-colors',
                filters.category === cat.value ? 'border-wine-800 bg-wine-50 text-wine-900 font-bold' : 'border-transparent text-ink hover:bg-sand-100'
              ]"
              @click="filters.category = cat.value"
            >
              <span>{{ cat.label }}</span>
              <span class="text-[13px] text-ink-mute font-normal">{{ cat.count }}</span>
            </button>
          </div>

          <div class="flex flex-col gap-2.5">
            <span class="eyebrow-sm tracking-[0.12em]">Denominazione</span>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="den in denominationOptions"
                :key="den.value"
                type="button"
                :aria-pressed="filters.denominazione === den.value"
                :class="['inline-flex items-center px-3 py-[7px] rounded-full border text-[13px] font-semibold transition-colors', filters.denominazione === den.value ? 'border-wine-800 bg-wine-800 text-white' : 'border-line-strong bg-white text-ink-soft hover:border-ink-mute']"
                @click="filters.denominazione = filters.denominazione === den.value ? '' : den.value"
              >
                {{ den.value }} · {{ den.count }}
              </button>
            </div>
          </div>

          <div class="flex flex-col gap-2.5">
            <span class="eyebrow-sm tracking-[0.12em]">Vitigno</span>
            <div class="flex flex-wrap gap-1.5">
              <button
                v-for="grape in visibleGrapes"
                :key="grape.name"
                type="button"
                :aria-pressed="filters.grape === grape.name"
                :class="['inline-flex items-center px-3 py-[7px] rounded-full border text-[13px] font-semibold transition-colors', filters.grape === grape.name ? 'border-wine-800 bg-wine-800 text-white' : 'border-line-strong bg-white text-ink-soft hover:border-ink-mute']"
                @click="filters.grape = filters.grape === grape.name ? '' : grape.name"
              >
                {{ grape.name }} · {{ grape.count }}
              </button>
              <button
                v-if="grapeOptions.length > 6"
                type="button"
                class="px-2 py-[7px] text-[13px] font-bold text-wine-800"
                :aria-expanded="showAllGrapes"
                @click="showAllGrapes = !showAllGrapes"
              >
                {{ showAllGrapes ? 'Meno' : `Tutti i ${grapeOptions.length} →` }}
              </button>
            </div>
          </div>

          <button
            type="button"
            :aria-pressed="filters.organic === 'organic'"
            :class="['flex items-center gap-2.5 min-h-[48px] px-3.5 rounded-xl border text-[15px] font-semibold transition-colors', filters.organic === 'organic' ? 'border-bio bg-bio-50 text-bio-900' : 'border-line-strong bg-white text-ink']"
            @click="filters.organic = filters.organic === 'organic' ? '' : 'organic'"
          >
            <Leaf class="w-[18px] h-[18px]" aria-hidden="true" />
            <span class="flex-1 text-left">Solo vini biologici</span>
            <span :class="['relative w-9 h-5 rounded-full shrink-0 transition-colors', filters.organic === 'organic' ? 'bg-bio' : 'bg-[#D8CEC2]']">
              <span :class="['absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all', filters.organic === 'organic' ? 'left-[18px]' : 'left-0.5']"></span>
            </span>
          </button>

          <label class="field-label">
            <span class="eyebrow-sm tracking-[0.12em]">Cantina</span>
            <select v-model="filters.producer" class="select h-11 text-sm">
              <option value="">Tutte le cantine</option>
              <option v-for="p in producerOptions" :key="p" :value="p">{{ p }}</option>
            </select>
          </label>
        </aside>
      </div>

      <!-- RISULTATI -->
      <div class="min-w-0 flex flex-col gap-5">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-[15px] text-ink-soft" aria-live="polite"><strong class="text-ink">{{ filteredProducts.length }}</strong> {{ filteredProducts.length === 1 ? 'vino' : 'vini' }}</span>
            <button
              v-for="f in activeFilters"
              :key="f.key"
              type="button"
              class="inline-flex items-center gap-1.5 h-8 px-2.5 rounded-full bg-sand-100 text-wine-900 text-[13px] font-semibold hover:bg-sand-200"
              :aria-label="`Rimuovi filtro ${f.label}`"
              @click="f.clear()"
            >
              {{ f.label }} <X class="w-3.5 h-3.5" aria-hidden="true" />
            </button>
            <button v-if="activeFilters.length" type="button" class="h-8 px-1.5 text-[13px] font-bold text-wine-800" @click="resetFilters">Azzera</button>
          </div>
          <label class="flex items-center gap-2 text-sm text-ink-soft">
            Ordina
            <select v-model="sortBy" class="h-10 px-2.5 border border-line-strong rounded-[10px] bg-white text-sm text-ink">
              <option value="featured">In evidenza</option>
              <option value="name">Nome A–Z</option>
              <option value="alcohol">Gradazione</option>
            </select>
          </label>
        </div>

        <div v-if="pending" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
          <div v-for="i in 6" :key="i" class="h-96 rounded-2xl bg-sand animate-pulse"></div>
        </div>

        <template v-else-if="filteredProducts.length">
          <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5">
            <ProductCard v-for="product in visibleProducts" :key="product.id" :product="product" />
          </div>
          <div v-if="visibleProducts.length < filteredProducts.length" class="flex flex-col items-center gap-2.5 mt-3">
            <span class="text-sm text-ink-mute">Mostrati {{ visibleProducts.length }} di {{ filteredProducts.length }}</span>
            <button type="button" class="btn-outline bg-white" @click="limit += PAGE_SIZE">Mostra altri vini</button>
          </div>
        </template>

        <div v-else class="card p-10 text-center flex flex-col items-center gap-3">
          <h2 class="title-card text-2xl">Nessun vino trovato</h2>
          <p class="text-ink-soft">Prova a togliere qualche filtro o a cercare un altro vitigno.</p>
          <button type="button" class="btn-outline" @click="resetFilters">Azzera i filtri</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Search, Leaf, X, SlidersHorizontal } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { fetchWithAuth } = useApi()
const { isOrganicProduct } = useOrganic()
const { formatCategory } = useCategoryBadge()

useSeoMeta({
  title: 'Catalogo Vini del Molise - EnotecaMolise',
  description: 'Esplora il catalogo completo dei vini molisani. Filtra per tipologia, denominazione, vitigno, vini biologici e cantina.'
})

const PAGE_SIZE = 24
const limit = ref(PAGE_SIZE)
const sortBy = ref('featured')
const showFilters = ref(false)
const showAllGrapes = ref(false)

const filters = reactive({
  search: '',
  category: '',
  denominazione: '',
  organic: '',
  grape: '',
  producer: ''
})

const syncFiltersFromRoute = () => {
  for (const key of Object.keys(filters)) {
    if (route.query[key] !== undefined) filters[key] = String(route.query[key] || '')
  }
}

syncFiltersFromRoute()
watch(() => route.query, syncFiltersFromRoute)
watch(filters, () => { limit.value = PAGE_SIZE })

const resetFilters = () => {
  for (const key of Object.keys(filters)) filters[key] = ''
  router.replace({ query: {} })
}

const { data: products, pending } = await useAsyncData('catalog_products', async () => {
  const res = await fetchWithAuth('/products?status=PUBLISHED')
  return res || []
}, { default: () => [] })

const cleanGrape = (g) => String(g || '').replace(/\s*\d+([.,]\d+)?\s*%/g, '').trim()

const matchProductWithSearch = (p, searchQuery) => {
  if (!searchQuery || !searchQuery.trim()) return true

  const q = searchQuery.toLowerCase().trim()
  const words = q.split(/\s+/).filter(w => w.length > 2)
  const producerSlugSpaced = (p.producer_slug || '').replace(/-/g, ' ')

  const pairingsText = (p.food_pairings || []).join(' ').toLowerCase()
  const searchableText = [
    p.name || '',
    p.producer_name || '',
    producerSlugSpaced,
    p.denominazione || '',
    p.category || '',
    p.description || '',
    p.vintage_year ? String(p.vintage_year) : '',
    p.is_riserva ? 'riserva' : '',
    (p.grape_varieties || []).join(' '),
    pairingsText,
    isOrganicProduct(p) ? 'biologico bio organic' : '',
    (p.custom_attributes || []).map(a => `${a.name || ''} ${a.value || ''}`).join(' ')
  ].join(' ').toLowerCase()

  if (searchableText.includes(q)) return true
  if (words.length === 0) return searchableText.includes(q)

  if (words.every(word => searchableText.includes(word))) return true

  if (p.food_pairings && p.food_pairings.length > 0) {
    const matchingPairingWords = words.filter(word => pairingsText.includes(word))
    if (matchingPairingWords.length >= Math.min(2, words.length)) return true
  }

  return false
}

// Ogni filtro escluso a turno, cosi' i conteggi mostrano quanti vini si otterrebbero scegliendolo
const passes = (p, skip = '') => {
  if (skip !== 'category' && filters.category && p.category !== filters.category) return false
  if (skip !== 'denominazione' && filters.denominazione && !(p.denominazione || '').includes(filters.denominazione)) return false
  if (skip !== 'organic' && filters.organic === 'organic' && !isOrganicProduct(p)) return false
  if (skip !== 'grape' && filters.grape && !(p.grape_varieties || []).some(g => cleanGrape(g).toLowerCase() === filters.grape.toLowerCase())) return false
  if (skip !== 'producer' && filters.producer && p.producer_name !== filters.producer) return false
  if (skip !== 'search' && filters.search && !matchProductWithSearch(p, filters.search)) return false
  return true
}

const filteredProducts = computed(() => {
  const list = (products.value || []).filter(p => passes(p))
  if (sortBy.value === 'name') return [...list].sort((a, b) => (a.name || '').localeCompare(b.name || '', 'it'))
  if (sortBy.value === 'alcohol') return [...list].sort((a, b) => (Number(b.alcohol_degrees) || 0) - (Number(a.alcohol_degrees) || 0))
  return list
})

const visibleProducts = computed(() => filteredProducts.value.slice(0, limit.value))

const CATEGORIES = ['VINO_ROSSO', 'VINO_BIANCO', 'ROSATO', 'SPUMANTE', 'PASSITO', 'LIQUORE']
const categoryOptions = computed(() => {
  const base = (products.value || []).filter(p => passes(p, 'category'))
  return [
    { value: '', label: 'Tutte', count: base.length },
    ...CATEGORIES.map(c => ({ value: c, label: formatCategory(c), count: base.filter(p => p.category === c).length })).filter(o => o.count)
  ]
})

const denominationOptions = computed(() => {
  const base = (products.value || []).filter(p => passes(p, 'denominazione'))
  return ['DOC', 'DOCG', 'DOP', 'IGT', 'IGP']
    .map(d => ({ value: d, count: base.filter(p => (p.denominazione || '').includes(d)).length }))
    .filter(o => o.count || filters.denominazione === o.value)
})

const grapeOptions = computed(() => {
  const counts = new Map()
  for (const p of (products.value || []).filter(p => passes(p, 'grape'))) {
    const names = new Set((p.grape_varieties || []).map(cleanGrape).filter(Boolean))
    for (const n of names) counts.set(n, (counts.get(n) || 0) + 1)
  }
  return [...counts.entries()].map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count)
})

const visibleGrapes = computed(() => {
  const list = showAllGrapes.value ? grapeOptions.value : grapeOptions.value.slice(0, 6)
  if (filters.grape && !list.some(g => g.name === filters.grape)) return [...list, { name: filters.grape, count: 0 }]
  return list
})

const producerOptions = computed(() => [...new Set((products.value || []).map(p => p.producer_name).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'it')))

const activeFilters = computed(() => {
  const list = []
  if (filters.search) list.push({ key: 'search', label: `“${filters.search}”`, clear: () => { filters.search = '' } })
  if (filters.category) list.push({ key: 'category', label: formatCategory(filters.category), clear: () => { filters.category = '' } })
  if (filters.denominazione) list.push({ key: 'den', label: filters.denominazione, clear: () => { filters.denominazione = '' } })
  if (filters.grape) list.push({ key: 'grape', label: filters.grape, clear: () => { filters.grape = '' } })
  if (filters.organic) list.push({ key: 'organic', label: 'Biologici', clear: () => { filters.organic = '' } })
  if (filters.producer) list.push({ key: 'producer', label: filters.producer, clear: () => { filters.producer = '' } })
  return list
})
</script>
