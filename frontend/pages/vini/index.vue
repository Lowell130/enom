<template>
  <div class="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <!-- Header -->
    <div class="mb-12 text-center max-w-2xl mx-auto space-y-2">
      <span class="text-xs font-bold uppercase tracking-widest text-wine-800">Catalogo Ufficiale</span>
      <h1 class="font-serif text-4xl sm:text-5xl font-light text-stone-900">
        Tutti i Vini del Molise
      </h1>
      <p class="text-base text-stone-600 font-light">
        Esplora le bottiglie, le spumantizzazioni e le annate direttamente dalle cantine del Molise.
      </p>
    </div>

    <!-- Filters Bar -->
    <div class="bg-white rounded-2xl p-6 shadow-xs border border-stone-200/60 mb-12">
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-5">
        
        <!-- Search Input -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Cerca Vino o Vitigno</label>
          <div class="relative">
            <Search class="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
            <input 
              v-model="filters.search" 
              type="text" 
              placeholder="es. Tintilia, Montepulciano..." 
              class="w-full border border-stone-200/80 rounded-xl pl-10 pr-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            />
          </div>
        </div>

        <!-- Category Filter -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Tipologia</label>
          <select 
            v-model="filters.category" 
            class="w-full border border-stone-200/80 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
          >
            <option value="">Tutte le tipologie</option>
            <option value="VINO_ROSSO">Vino Rosso</option>
            <option value="VINO_BIANCO">Vino Bianco</option>
            <option value="ROSATO">Rosato</option>
            <option value="SPUMANTE">Spumante</option>
            <option value="PASSITO">Passito</option>
            <option value="LIQUORE">Liquore / Grappa</option>
          </select>
        </div>

        <!-- Denominazione Filter -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Denominazione</label>
          <select 
            v-model="filters.denominazione" 
            class="w-full border border-stone-200/80 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
          >
            <option value="">Tutte le denominazioni</option>
            <option value="DOC">DOC</option>
            <option value="DOCG">DOCG</option>
            <option value="IGT">IGT</option>
            <option value="IGP">IGP</option>
            <option value="DOP">DOP</option>
          </select>
        </div>

        <!-- Organic Filter -->
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Certificazione</label>
          <select 
            v-model="filters.organic" 
            class="w-full border border-stone-200/80 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
          >
            <option value="">Tutte</option>
            <option value="organic">Vino Biologico 🌿</option>
          </select>
        </div>

        <!-- Reset Button -->
        <div class="flex items-end">
          <button 
            @click="resetFilters" 
            class="w-full inline-flex items-center justify-center space-x-2 py-2.5 px-4 border border-stone-200 hover:bg-stone-50 text-stone-700 rounded-xl text-sm font-semibold transition-colors"
          >
            <RotateCcw class="w-4 h-4 text-stone-500" />
            <span>Azzera Filtri</span>
          </button>
        </div>

      </div>
    </div>

    <!-- Products Grid -->
    <div v-if="pending" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
      <div v-for="i in 6" :key="i" class="h-96 bg-stone-200/50 animate-pulse rounded-2xl"></div>
    </div>

    <div v-else-if="filteredProducts && filteredProducts.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
      <ProductCard v-for="product in filteredProducts" :key="product.id" :product="product" />
    </div>

    <div v-else class="text-center py-20 bg-white rounded-2xl border border-stone-200/60 p-8">
      <div class="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-3 text-stone-400">
        <Wine class="w-6 h-6" />
      </div>
      <h3 class="font-serif text-xl font-bold text-stone-800">Nessun vino trovato</h3>
      <p class="text-sm text-stone-500 mt-1 font-light">Prova a cambiare i filtri di ricerca per visualizzare altri vini.</p>
    </div>

  </div>
</template>

<script setup>
import { Search, RotateCcw, Wine } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const { fetchWithAuth } = useApi()
const { isOrganicProduct } = useOrganic()

useSeoMeta({
  title: 'Catalogo Vini del Molise - EnotecaMolise',
  description: 'Esplora il catalogo completo dei vini molisani. Filtra per tipologia, denominazione, vini biologici e cantina.'
})

const filters = reactive({
  search: '',
  category: '',
  denominazione: '',
  organic: ''
})

const syncFiltersFromRoute = () => {
  if (route.query.search !== undefined) filters.search = String(route.query.search || '')
  if (route.query.category !== undefined) filters.category = String(route.query.category || '')
  if (route.query.denominazione !== undefined) filters.denominazione = String(route.query.denominazione || '')
  if (route.query.organic !== undefined) filters.organic = String(route.query.organic || '')
}

onMounted(() => {
  syncFiltersFromRoute()
})

watch(() => route.query, () => {
  syncFiltersFromRoute()
})

const resetFilters = () => {
  filters.search = ''
  filters.category = ''
  filters.denominazione = ''
  filters.organic = ''
  router.replace({ query: {} })
}

const { data: products, pending } = await useAsyncData('catalog_products', async () => {
  const res = await fetchWithAuth('/products?status=PUBLISHED')
  return res || []
}, { default: () => [] })

const matchProductWithSearch = (p, searchQuery) => {
  if (!searchQuery || !searchQuery.trim()) return true
  
  const q = searchQuery.toLowerCase().trim()
  const words = q.split(/\s+/).filter(Boolean)
  const producerSlugSpaced = (p.producer_slug || '').replace(/-/g, ' ')
  
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
    isOrganicProduct(p) ? 'biologico bio organic' : '',
    (p.custom_attributes || []).map(a => `${a.name || ''} ${a.value || ''}`).join(' ')
  ].join(' ').toLowerCase()

  if (searchableText.includes(q)) return true
  return words.every(word => searchableText.includes(word))
}

const filteredProducts = computed(() => {
  if (!products.value) return []
  return products.value.filter(p => {
    if (filters.category && p.category !== filters.category) return false
    if (filters.denominazione && !p.denominazione.includes(filters.denominazione)) return false
    if (filters.organic === 'organic' && !isOrganicProduct(p)) return false
    if (filters.search && !matchProductWithSearch(p, filters.search)) return false
    return true
  })
})
</script>
