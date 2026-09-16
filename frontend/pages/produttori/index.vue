<template>
  <div class="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
    
    <!-- Header Hero -->
    <div class="text-center max-w-3xl mx-auto space-y-3">
      <span class="inline-flex items-center space-x-1.5 px-3.5 py-1 bg-wine-50 text-wine-800 border border-wine-100 rounded-full text-xs font-bold uppercase tracking-widest">
        <Building2 class="w-3.5 h-3.5 text-wine-800" />
        <span>I Custodi del Territorio</span>
      </span>

      <h1 class="font-serif text-4xl sm:text-6xl font-light text-stone-900 tracking-tight">
        Le Cantine del Molise
      </h1>

      <p class="text-base sm:text-lg text-stone-600 font-light leading-relaxed">
        Scopri i produttori vinicoli che tramandano la passione enologica molisana tra Campobasso, Isernia ed il litorale adriatico.
      </p>
    </div>

    <!-- Search & Filter Controls Bar -->
    <div class="bg-white rounded-xl p-4 sm:p-5 border border-stone-200/80 shadow-xs flex flex-col md:flex-row items-center justify-between gap-4">
      
      <!-- Search Input -->
      <div class="relative w-full md:w-96">
        <Search class="w-4 h-4 text-stone-400 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
        <input 
          v-model="searchQuery"
          type="text" 
          placeholder="Cerca cantina per nome o città (es. Colle Tinto, Castropignano)..."
          class="w-full bg-stone-50 hover:bg-stone-100/80 focus:bg-white text-stone-800 text-xs sm:text-sm rounded-lg pl-11 pr-4 py-3 border border-stone-200 focus:border-wine-800 focus:outline-none transition-all"
        />
        <button 
          v-if="searchQuery" 
          @click="searchQuery = ''"
          class="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-stone-400 hover:text-stone-600 font-bold"
        >
          ✕
        </button>
      </div>

      <!-- View Switcher & Counter -->
      <div class="flex items-center justify-between w-full md:w-auto gap-4">
        <span class="text-xs font-semibold text-stone-500 whitespace-nowrap">
          <strong class="text-stone-900">{{ (filteredProducers || []).length }}</strong> {{ (filteredProducers || []).length === 1 ? 'Cantina Trovata' : 'Cantine Trovate' }}
        </span>

        <!-- Grid vs Map Switcher -->
        <div class="bg-stone-100 p-1 rounded-lg border border-stone-200/70 flex items-center gap-1">
          <button 
            @click="viewMode = 'grid'"
            :class="[
              'px-3 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 transition-all',
              viewMode === 'grid' 
                ? 'bg-white text-wine-900 shadow-xs border border-stone-200/60 font-bold' 
                : 'text-stone-500 hover:text-stone-800'
            ]"
          >
            <LayoutGrid class="w-3.5 h-3.5" />
            <span>Griglia</span>
          </button>

          <button 
            @click="viewMode = 'map'"
            :class="[
              'px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all',
              viewMode === 'map' 
                ? 'bg-white text-wine-900 shadow-xs border border-stone-200/60 font-bold' 
                : 'text-stone-500 hover:text-stone-800'
            ]"
          >
            <MapPin class="w-3.5 h-3.5 text-wine-800" />
            <span>Mappa Interattiva</span>
          </button>
        </div>
      </div>

    </div>

    <!-- Loading Skeleton -->
    <div v-if="pending" class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div v-for="i in 4" :key="i" class="h-72 bg-stone-200/50 animate-pulse rounded-xl"></div>
    </div>

    <!-- Map View -->
    <div v-else-if="viewMode === 'map'">
      <WineryMap 
        :producers="filteredProducers" 
        title="Mappa delle Cantine Molisane"
        subtitle="Localizzazione geografica dei produttori registrati"
        :zoom="9.5"
      />
    </div>

    <!-- Grid View -->
    <div v-else-if="filteredProducers && filteredProducers.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
      <ProducerCard v-for="producer in filteredProducers" :key="producer.id" :producer="producer" />
    </div>

    <!-- Empty State -->
    <div v-else class="text-center py-20 bg-white rounded-xl border border-stone-200/60 p-8 space-y-3">
      <div class="w-14 h-14 rounded-lg bg-stone-100 flex items-center justify-center mx-auto text-stone-400">
        <Building2 class="w-7 h-7" />
      </div>
      <h3 class="font-serif text-xl font-bold text-stone-800">Nessuna cantina trovata</h3>
      <p class="text-sm text-stone-500 font-light max-w-md mx-auto">
        Non ci sono cantine registrate corrispondenti alla ricerca "<strong class="text-stone-700">{{ searchQuery }}</strong>".
      </p>
      <button 
        @click="searchQuery = ''"
        class="mt-2 inline-flex items-center px-4 py-2 bg-stone-100 hover:bg-stone-200 text-stone-700 font-semibold text-xs rounded-xl transition-all"
      >
        Resetta ricerca
      </button>
    </div>

  </div>
</template>

<script setup>
import { Building2, Search, LayoutGrid, MapPin } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()

useSeoMeta({
  title: 'Le Cantine Molisane - Produttori e Vigneti del Molise',
  description: 'Scopri i migliori produttori vinicoli del Molise. Esplora le cantine di Tintilia, Biferno e Pentro a Campobasso ed Isernia.'
})

const route = useRoute()
const searchQuery = ref('')
const viewMode = ref(route.query.view === 'map' ? 'map' : 'grid')

watch(() => route.query.view, (newView) => {
  if (newView === 'map') {
    viewMode.value = 'map'
  } else if (newView === 'grid') {
    viewMode.value = 'grid'
  }
})

const { data: producers, pending } = await useAsyncData('all_producers', async () => {
  const res = await fetchWithAuth('/producers')
  return res || []
}, { default: () => [] })

const filteredProducers = computed(() => {
  const list = producers.value || []
  if (!searchQuery.value.trim()) return list
  
  const q = searchQuery.value.toLowerCase().trim()
  return list.filter(p => {
    const nameMatch = (p.company_name || '').toLowerCase().includes(q)
    const cityMatch = (p.address?.city || '').toLowerCase().includes(q)
    const provMatch = (p.address?.province || '').toLowerCase().includes(q)
    return nameMatch || cityMatch || provMatch
  })
})
</script>
