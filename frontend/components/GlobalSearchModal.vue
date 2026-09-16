<template>
  <ClientOnly>
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div 
          v-if="isOpen" 
          class="fixed inset-0 z-50 bg-stone-900/60 backdrop-blur-xs flex items-start justify-center pt-16 sm:pt-24 px-4 pb-6 overflow-y-auto"
          @click.self="close"
        >
          <div class="bg-white rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden border border-stone-200/80 flex flex-col max-h-[80vh]">
            
            <!-- Search Header -->
            <div class="p-4 sm:p-5 border-b border-stone-100 flex items-center space-x-3 bg-stone-50/50">
              <Search class="w-5 h-5 text-wine-800 shrink-0" />
              <input 
                ref="searchInputRef"
                v-model="query"
                type="text"
                placeholder="Cerca vino, cantina, vitigno o 'biologico'..."
                class="w-full bg-transparent border-0 text-stone-900 font-medium placeholder-stone-400 text-base sm:text-lg focus:outline-none focus:ring-0"
                @keydown.esc="close"
                @keydown.enter="handleEnterKey"
              />
              <button v-if="query" @click="query = ''" class="text-stone-400 hover:text-stone-600 p-1">
                <X class="w-4 h-4" />
              </button>
              <kbd class="hidden sm:inline-block px-2 py-1 text-[10px] font-mono text-stone-400 bg-stone-100 border border-stone-200 rounded-md">ESC</kbd>
            </div>

            <!-- Search Results Content -->
            <div class="overflow-y-auto p-4 sm:p-6 space-y-6 flex-1">
              
              <!-- Initial state when query is empty -->
              <div v-if="!query.trim()" class="space-y-4 py-2">
                <div class="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-stone-400">
                  <Sparkles class="w-3.5 h-3.5 text-amber-500" />
                  <span>Ricerche Popolari & Suggerimenti</span>
                </div>
                <div class="flex flex-wrap gap-2">
                  <button 
                    v-for="sug in popularSearches" 
                    :key="sug.label"
                    @click="applySuggestion(sug)"
                    class="px-3.5 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-stone-700 text-xs font-semibold rounded-xl border border-stone-200/60 transition-colors flex items-center space-x-1.5"
                  >
                    <span>{{ sug.icon }}</span>
                    <span>{{ sug.label }}</span>
                  </button>
                </div>
              </div>

              <!-- Loading state -->
              <div v-else-if="loading" class="py-12 text-center text-stone-400 text-sm font-medium animate-pulse">
                Ricerca nel catalogo in corso...
              </div>

              <!-- Results list -->
              <div v-else-if="hasResults" class="space-y-6">
                
                <!-- Matching Wines -->
                <div v-if="matchingProducts.length" class="space-y-3">
                  <div class="flex items-center justify-between">
                    <span class="text-xs font-bold uppercase tracking-wider text-stone-400">
                      Vini Trovati ({{ matchingProducts.length }})
                    </span>
                    <button 
                      @click="goToCatalogWithSearch" 
                      class="text-xs font-bold text-wine-800 hover:underline"
                    >
                      Vedi tutti
                    </button>
                  </div>

                  <div class="divide-y divide-stone-100 rounded-2xl border border-stone-100 overflow-hidden bg-stone-50/40">
                    <NuxtLink 
                      v-for="prod in matchingProducts.slice(0, 5)" 
                      :key="prod.id"
                      :to="`/vini/${prod.slug}`"
                      @click="close"
                      class="p-3.5 flex items-center space-x-4 hover:bg-white transition-colors group"
                    >
                      <!-- Wine Photo -->
                      <div class="w-12 h-12 rounded-xl bg-white border border-stone-200/60 flex items-center justify-center overflow-hidden shrink-0">
                        <img 
                          :src="getProductImage(prod)" 
                          :alt="prod.name"
                          class="h-full object-contain group-hover:scale-105 transition-transform"
                        />
                      </div>
                      
                      <!-- Wine Info -->
                      <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-2">
                          <h4 class="text-sm font-bold text-stone-900 group-hover:text-wine-800 truncate transition-colors">
                            {{ prod.name }}
                          </h4>
                          <span v-if="isOrganicProduct(prod)" class="px-2 py-0.5 text-[10px] font-bold rounded-full bg-emerald-700 text-white shrink-0 inline-flex items-center space-x-0.5">
                            <Leaf class="w-2.5 h-2.5" />
                            <span>BIO</span>
                          </span>
                        </div>
                        <p class="text-xs text-stone-500 font-medium truncate mt-0.5">
                          <span v-if="prod.producer_name" class="text-wine-800 font-semibold">{{ prod.producer_name }}</span>
                          <span v-if="prod.denominazione"> • {{ prod.denominazione }}</span>
                          <span v-if="prod.vintage_year"> ({{ prod.vintage_year }})</span>
                        </p>
                      </div>

                      <ChevronRight class="w-4 h-4 text-stone-400 group-hover:text-wine-800 group-hover:translate-x-0.5 transition-all shrink-0" />
                    </NuxtLink>
                  </div>
                </div>

                <!-- Matching Producers -->
                <div v-if="matchingProducers.length" class="space-y-3">
                  <span class="text-xs font-bold uppercase tracking-wider text-stone-400">
                    Cantine e Produttori ({{ matchingProducers.length }})
                  </span>

                  <div class="divide-y divide-stone-100 rounded-2xl border border-stone-100 overflow-hidden bg-stone-50/40">
                    <NuxtLink 
                      v-for="p in matchingProducers.slice(0, 3)" 
                      :key="p.id"
                      :to="`/produttori/${p.slug}`"
                      @click="close"
                      class="p-3.5 flex items-center space-x-4 hover:bg-white transition-colors group"
                    >
                      <div class="w-10 h-10 rounded-xl bg-wine-50 border border-wine-100 flex items-center justify-center shrink-0">
                        <Building2 class="w-5 h-5 text-wine-800" />
                      </div>
                      <div class="flex-1 min-w-0">
                        <h4 class="text-sm font-bold text-stone-900 group-hover:text-wine-800 transition-colors">
                          {{ p.name }}
                        </h4>
                        <p class="text-xs text-stone-500 font-medium">
                          {{ p.municipality }}{{ p.province ? ` (${p.province})` : '' }}
                        </p>
                      </div>
                      <ChevronRight class="w-4 h-4 text-stone-400 group-hover:text-wine-800 group-hover:translate-x-0.5 transition-all shrink-0" />
                    </NuxtLink>
                  </div>
                </div>

              </div>

              <!-- No results state -->
              <div v-else-if="query.trim()" class="py-12 text-center space-y-2">
                <Wine class="w-8 h-8 text-stone-300 mx-auto" />
                <p class="text-sm font-bold text-stone-700">Nessun risultato per "{{ query }}"</p>
                <p class="text-xs text-stone-500 font-light max-w-sm mx-auto">
                  Prova a cercare per vitigno (es. Tintilia, Montepulciano), o digita "biologico" per i vini biologici.
                </p>
              </div>

            </div>

            <!-- Footer bar -->
            <div class="p-4 bg-stone-50 border-t border-stone-100 flex items-center justify-between text-xs text-stone-500">
              <div class="flex items-center space-x-2">
                <span>Premi <kbd class="px-1.5 py-0.5 bg-white border rounded text-[10px]">INVIO</kbd> per vedere tutti i risultati</span>
              </div>
              <button 
                @click="goToCatalogWithSearch"
                class="font-bold text-wine-800 hover:underline inline-flex items-center space-x-1"
              >
                <span>Tutto il Catalogo</span>
                <ChevronRight class="w-3.5 h-3.5" />
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>
  </ClientOnly>
</template>

<script setup>
import { Search, X, Wine, Building2, ChevronRight, Leaf, Sparkles } from 'lucide-vue-next'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  initialQuery: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['close'])

const router = useRouter()
const { fetchWithAuth, mediaBase } = useApi()
const { isOrganicProduct } = useOrganic()

const query = ref('')
const searchInputRef = ref(null)
const loading = ref(false)

const products = ref([])
const producers = ref([])

const popularSearches = [
  { label: 'Tintilia', icon: '🍇', search: 'Tintilia' },
  { label: 'Vini Biologici', icon: '🌿', organic: 'organic' },
  { label: 'Biferno Rosso', icon: '🍷', search: 'Biferno' },
  { label: 'Falanghina', icon: '🥂', search: 'Falanghina' },
  { label: 'DOC Molise', icon: '🏷️', denominazione: 'DOC' }
]

watch(() => props.isOpen, async (val) => {
  if (val) {
    if (props.initialQuery) {
      query.value = props.initialQuery
    }
    nextTick(() => {
      searchInputRef.value?.focus()
    })
    if (!products.value.length) {
      loading.value = true
      try {
        const [prodsRes, prodcsRes] = await Promise.all([
          fetchWithAuth('/products?status=PUBLISHED'),
          fetchWithAuth('/producers')
        ])
        products.value = prodsRes || []
        producers.value = prodcsRes || []
      } catch (err) {
        console.error('Errore caricamento motore di ricerca:', err)
      } finally {
        loading.value = false
      }
    }
  }
})

const matchProductWithSearch = (p, rawQuery) => {
  if (!rawQuery || !rawQuery.trim()) return true
  const q = rawQuery.toLowerCase().trim()
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

const matchingProducts = computed(() => {
  if (!query.value.trim() || !products.value) return []
  return products.value.filter(p => matchProductWithSearch(p, query.value))
})

const matchingProducers = computed(() => {
  if (!query.value.trim() || !producers.value) return []
  const q = query.value.toLowerCase().trim()
  const words = q.split(/\s+/).filter(Boolean)
  return producers.value.filter(p => {
    const slugSpaced = (p.slug || '').replace(/-/g, ' ')
    const searchableText = [
      p.company_name || '',
      p.name || '',
      slugSpaced,
      p.address?.city || p.municipality || '',
      p.address?.province || p.province || '',
      p.description || ''
    ].join(' ').toLowerCase()

    if (searchableText.includes(q)) return true
    return words.every(w => searchableText.includes(w))
  })
})

const hasResults = computed(() => {
  return matchingProducts.value.length > 0 || matchingProducers.value.length > 0
})

const close = () => {
  emit('close')
}

const getProductImage = (prod) => {
  if (prod.photos && prod.photos.length > 0) {
    const url = prod.photos[0]
    return url.startsWith('http') ? url : `${mediaBase}${url}`
  }
  return '/default_wine_bottle.jpg'
}

const applySuggestion = (sug) => {
  if (sug.search) {
    query.value = sug.search
  } else if (sug.organic) {
    router.push('/vini?organic=organic')
    close()
  } else if (sug.denominazione) {
    router.push(`/vini?denominazione=${sug.denominazione}`)
    close()
  }
}

const goToCatalogWithSearch = () => {
  if (query.value.trim()) {
    router.push(`/vini?search=${encodeURIComponent(query.value.trim())}`)
  } else {
    router.push('/vini')
  }
  close()
}

const handleEnterKey = () => {
  goToCatalogWithSearch()
}
</script>
