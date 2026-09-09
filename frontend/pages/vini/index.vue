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
      <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-5">
        
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
            <option value="DOC">DOC (Biferno, Tintilia, Pentro)</option>
            <option value="IGT">IGT / IGP</option>
            <option value="VINO_D_TAVOLA">Vino da Tavola</option>
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

const { fetchWithAuth } = useApi()

const filters = reactive({
  search: '',
  category: '',
  denominazione: ''
})

const resetFilters = () => {
  filters.search = ''
  filters.category = ''
  filters.denominazione = ''
}

const { data: products, pending } = await useAsyncData('catalog_products', () => 
  fetchWithAuth('/products?status=PUBLISHED')
)

const filteredProducts = computed(() => {
  if (!products.value) return []
  return products.value.filter(p => {
    if (filters.category && p.category !== filters.category) return false
    if (filters.denominazione && !p.denominazione.includes(filters.denominazione)) return false
    if (filters.search) {
      const q = filters.search.toLowerCase()
      const nameMatch = p.name.toLowerCase().includes(q)
      const descMatch = (p.description || '').toLowerCase().includes(q)
      const denomMatch = (p.denominazione || '').toLowerCase().includes(q)
      const riservaMatch = p.is_riserva && 'riserva'.includes(q)
      const grapeMatch = (p.grape_varieties || []).some(g => g.toLowerCase().includes(q))
      if (!nameMatch && !descMatch && !denomMatch && !riservaMatch && !grapeMatch) return false
    }
    return true
  })
})
</script>
