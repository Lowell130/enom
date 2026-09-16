<template>
  <div class="bg-[#FAF8F5]">
    
    <!-- 1. HERO SECTION (BALANCED 2-COLUMN EDITORIAL LAYOUT) -->
    <section class="relative bg-stone-950 text-white py-20 lg:py-28 overflow-hidden">
      <!-- Background Image with Soft Gradient Mask -->
      <div class="absolute inset-0 z-0 opacity-30 bg-cover bg-center" style="background-image: url('https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=1920&q=80');"></div>
      <div class="absolute inset-0 bg-gradient-to-r from-stone-950 via-stone-950/90 to-stone-950/60 z-0"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-10 items-center">
          
          <!-- Left Column (7 cols): Main Title, Subtitle, Search & CTAs -->
          <div class="lg:col-span-7 space-y-8">
            
            <div class="space-y-4">
              <span class="text-xs font-bold uppercase tracking-[0.25em] text-amber-300 flex items-center space-x-2">
                <Sparkles class="w-4 h-4 text-amber-300" />
                <span>ECCELLENZA ENOLOGICA MOLISANA</span>
              </span>

              <h1 class="font-serif text-4xl sm:text-6xl lg:text-7xl font-light tracking-tight text-white leading-[1.06]">
                Scopri i Tesori dei Vigneti del Molise
              </h1>
            </div>

            <p class="text-base sm:text-lg text-stone-300 leading-relaxed font-light max-w-2xl">
              Dalla Tintilia autoctona ai grandi Rossi del Biferno e Spumanti raffinati. Il portale che connette direttamente gli appassionati con le migliori cantine del Molise.
            </p>

            <!-- Minimal Hero Search Input -->
            <div class="pt-2 max-w-xl space-y-4">
              <form @submit.prevent="handleHeroSearch" class="relative flex items-center border-b-2 border-white/30 hover:border-white/60 focus-within:border-amber-400 transition-colors pb-1">
                <Search class="w-5 h-5 text-stone-300 mr-3 shrink-0" />
                <input 
                  v-model="heroQuery"
                  type="text"
                  placeholder="Cerca vino, cantina, vitigno (es. Tintilia, Biferno, Biologico)..."
                  class="w-full bg-transparent text-white placeholder-stone-400 text-sm sm:text-base py-3 focus:outline-none"
                />
                <button 
                  type="submit"
                  class="px-4 py-2 bg-wine-800 hover:bg-wine-900 text-white font-bold text-xs rounded-md transition-all shrink-0 flex items-center space-x-1"
                >
                  <span>Cerca</span>
                  <ArrowRight class="w-3.5 h-3.5" />
                </button>
              </form>

              <!-- Quick Suggestions -->
              <div class="flex flex-wrap items-center gap-3 text-xs pt-1">
                <span class="text-stone-400 font-medium">Filtri rapidi:</span>
                <button 
                  v-for="pill in quickPills" 
                  :key="pill.label"
                  @click="searchPill(pill.query)"
                  class="text-amber-200 hover:text-white font-medium underline underline-offset-4 transition-colors"
                >
                  {{ pill.label }}
                </button>
              </div>
            </div>

            <!-- Hero Action Buttons -->
            <div class="pt-4 flex flex-wrap gap-4">
              <NuxtLink to="/vini" class="inline-flex items-center space-x-2 px-7 py-3.5 bg-wine-800 hover:bg-wine-900 text-white font-bold text-sm rounded-xl shadow-md transition-all hover:scale-105">
                <span>Esplora il Catalogo Vini</span>
                <ArrowRight class="w-4 h-4" />
              </NuxtLink>
              <NuxtLink to="/produttori" class="inline-flex items-center space-x-2 px-7 py-3.5 text-white hover:text-amber-200 font-semibold text-sm border border-white/30 hover:border-white/60 rounded-xl transition-all backdrop-blur-xs">
                <Building2 class="w-4 h-4 text-amber-200" />
                <span>Le Cantine Molisane</span>
              </NuxtLink>
            </div>

          </div>

          <!-- Right Column (5 cols): Visual Image, Poetic Quote & Dynamic Stats Cards -->
          <div class="lg:col-span-5 space-y-4">
            
            <!-- Dynamic Quote & Vineyard Image Hero Card -->
            <div class="relative rounded-3xl overflow-hidden border border-white/20 shadow-2xl group transition-all">
              <!-- Card Background Image -->
              <img 
                src="https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=800&q=80" 
                alt="Vigneti e Vini del Molise"
                class="w-full h-64 sm:h-72 object-cover transform group-hover:scale-105 transition-transform duration-700"
              />
              <div class="absolute inset-0 bg-gradient-to-t from-stone-950 via-stone-950/75 to-stone-950/20"></div>

              <!-- Content Overlay -->
              <div class="absolute inset-0 p-6 flex flex-col justify-between text-white z-10">
                <div class="flex items-center justify-between">
                  <span class="inline-flex items-center space-x-1.5 px-3 py-1 bg-amber-400/20 text-amber-300 border border-amber-400/30 rounded-full text-[11px] font-bold uppercase tracking-wider backdrop-blur-md">
                    <Quote class="w-3.5 h-3.5 text-amber-300" />
                    <span>Territorio e Anima</span>
                  </span>
                  <span class="text-xs text-stone-300 font-serif italic">Molise, Italia</span>
                </div>

                <div class="space-y-2">
                  <p class="font-serif italic text-base sm:text-lg text-amber-100 font-light leading-snug">
                    {{ currentQuote.text }}
                  </p>
                  <p class="text-[11px] text-stone-400 font-medium tracking-wide uppercase">
                    — {{ currentQuote.author }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Dynamic Stats Cards (Real-time numbers from API) -->
            <div class="grid grid-cols-3 gap-3">
              <NuxtLink to="/vini" class="bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 text-center hover:bg-white/20 transition-all group">
                <div class="font-serif text-2xl sm:text-3xl font-light text-white group-hover:text-amber-300 transition-colors">
                  {{ (products || []).length }}
                </div>
                <div class="text-[10px] sm:text-[11px] text-stone-300 font-medium uppercase tracking-wider mt-1">Vini in Catalogo</div>
              </NuxtLink>

              <NuxtLink to="/produttori" class="bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 text-center hover:bg-white/20 transition-all group">
                <div class="font-serif text-2xl sm:text-3xl font-light text-white group-hover:text-amber-300 transition-colors">
                  {{ (producers || []).length }}
                </div>
                <div class="text-[10px] sm:text-[11px] text-stone-300 font-medium uppercase tracking-wider mt-1">Cantine Ufficiali</div>
              </NuxtLink>

              <NuxtLink to="/produttori?view=map" class="bg-white/10 backdrop-blur-md border border-white/15 rounded-2xl p-4 text-center hover:bg-white/20 transition-all group">
                <div class="flex items-center justify-center space-x-1 font-serif text-xl sm:text-2xl font-light text-white group-hover:text-amber-300 transition-colors pt-1">
                  <MapPin class="w-4 h-4 text-amber-300 inline" />
                  <span>Mappa</span>
                </div>
                <div class="text-[10px] sm:text-[11px] text-stone-300 font-medium uppercase tracking-wider mt-1">Geolocalizzata</div>
              </NuxtLink>
            </div>

          </div>

        </div>
      </div>
    </section>

    <!-- 2. STATS & DENOMINATIONS STRIP -->
    <section class="bg-wine-950 border-y border-wine-900 text-amber-200 py-10">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center divide-x divide-wine-900/60">
          <NuxtLink to="/vini?search=Tintilia" class="space-y-1 group cursor-pointer px-2">
            <div class="font-serif text-3xl sm:text-4xl font-light text-white group-hover:text-amber-300 transition-colors">Tintilia DOC</div>
            <div class="text-[11px] text-stone-400 uppercase tracking-[0.2em] font-semibold">Vitigno Autoctono</div>
          </NuxtLink>
          <NuxtLink to="/vini?search=Biferno" class="space-y-1 group cursor-pointer px-2">
            <div class="font-serif text-3xl sm:text-4xl font-light text-white group-hover:text-amber-300 transition-colors">Biferno DOC</div>
            <div class="text-[11px] text-stone-400 uppercase tracking-[0.2em] font-semibold">Tradizione Millenaria</div>
          </NuxtLink>
          <NuxtLink to="/vini?search=Pentro" class="space-y-1 group cursor-pointer px-2">
            <div class="font-serif text-3xl sm:text-4xl font-light text-white group-hover:text-amber-300 transition-colors">Pentro DOC</div>
            <div class="text-[11px] text-stone-400 uppercase tracking-[0.2em] font-semibold">Territorio d'Isernia</div>
          </NuxtLink>
          <div class="space-y-1 px-2">
            <div class="font-serif text-3xl sm:text-4xl font-light text-white">100% Diretto</div>
            <div class="text-[11px] text-stone-400 uppercase tracking-[0.2em] font-semibold">Contatto Cantina</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 3. LE GRANDI DOC DEL MOLISE (OPEN EDITORIAL GRID - NO BOXED CARDS) -->
    <section class="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
      
      <div class="space-y-3 border-b border-stone-200/70 pb-8">
        <span class="text-xs font-bold uppercase tracking-[0.25em] text-wine-800">Eccellenze del Territorio</span>
        <h2 class="font-serif text-4xl sm:text-5xl font-light text-stone-900 tracking-tight">
          Le Grandi DOC del Molise
        </h2>
        <p class="text-stone-600 text-base font-light max-w-2xl">
          Un viaggio tra le tre storiche Denominazioni d'Origine Controllata che raccontano la biodiversità ed il terroir molisano.
        </p>
      </div>

      <!-- Open 3-Column Editorial Grid (No Boxed Containers) -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-16">
        
        <!-- Tintilia Column -->
        <div class="space-y-6 group">
          <!-- Floating Monochromatic Icon (No container box) -->
          <Wine class="w-10 h-10 text-wine-800 group-hover:scale-110 transition-transform" />
          
          <div class="space-y-2">
            <span class="text-[11px] font-bold text-stone-400 uppercase tracking-widest block">DOC dal 2011</span>
            <h3 class="font-serif text-3xl font-bold text-stone-900 group-hover:text-wine-800 transition-colors">
              Tintilia del Molise
            </h3>
          </div>

          <p class="text-sm text-stone-600 font-light leading-relaxed">
            Il vanto dell'enologia molisana. Un vitigno autoctono unico dal colore rosso rubino intenso, con marcate note speziate di pepe nero e prugna secca.
          </p>

          <NuxtLink to="/vini?search=Tintilia" class="inline-flex items-center space-x-2 text-xs font-bold text-wine-800 hover:text-wine-900 uppercase tracking-wider pt-2">
            <span>Scopri i vini Tintilia</span>
            <ArrowRight class="w-4 h-4" />
          </NuxtLink>
        </div>

        <!-- Biferno Column -->
        <div class="space-y-6 group md:border-l md:border-stone-200/80 md:pl-10 lg:pl-12">
          <!-- Floating Monochromatic Icon -->
          <Compass class="w-10 h-10 text-wine-800 group-hover:scale-110 transition-transform" />

          <div class="space-y-2">
            <span class="text-[11px] font-bold text-stone-400 uppercase tracking-widest block">DOC dal 1983</span>
            <h3 class="font-serif text-3xl font-bold text-stone-900 group-hover:text-wine-800 transition-colors">
              Biferno DOC
            </h3>
          </div>

          <p class="text-sm text-stone-600 font-light leading-relaxed">
            Nato sulle colline del fiume Biferno tra Campobasso ed il mare. Caratterizzato da Rossi strutturati ed affinati in rovere e Bianchi freschi.
          </p>

          <NuxtLink to="/vini?search=Biferno" class="inline-flex items-center space-x-2 text-xs font-bold text-wine-800 hover:text-wine-900 uppercase tracking-wider pt-2">
            <span>Scopri i vini Biferno</span>
            <ArrowRight class="w-4 h-4" />
          </NuxtLink>
        </div>

        <!-- Pentro Column -->
        <div class="space-y-6 group md:border-l md:border-stone-200/80 md:pl-10 lg:pl-12">
          <!-- Floating Monochromatic Icon -->
          <Mountain class="w-10 h-10 text-wine-800 group-hover:scale-110 transition-transform" />

          <div class="space-y-2">
            <span class="text-[11px] font-bold text-stone-400 uppercase tracking-widest block">DOC dal 1983</span>
            <h3 class="font-serif text-3xl font-bold text-stone-900 group-hover:text-wine-800 transition-colors">
              Pentro d'Isernia
            </h3>
          </div>

          <p class="text-sm text-stone-600 font-light leading-relaxed">
            Coltivato nei vigneti dell'Alto Molise e della provincia d'Isernia. Vini minerali ed eleganti nati dall'escursione termica appenninica.
          </p>

          <NuxtLink to="/vini?search=Pentro" class="inline-flex items-center space-x-2 text-xs font-bold text-wine-800 hover:text-wine-900 uppercase tracking-wider pt-2">
            <span>Scopri i vini Pentro</span>
            <ArrowRight class="w-4 h-4" />
          </NuxtLink>
        </div>

      </div>
    </section>

    <!-- 4. FEATURED WINES WITH TEXT-BASED TABS (NO BUTTON BUBBLES) -->
    <section class="py-24 bg-white border-y border-stone-200/60">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        <!-- Header & Text Tabs -->
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-stone-200/70 pb-6">
          <div class="space-y-2">
            <span class="text-xs font-bold uppercase tracking-[0.25em] text-wine-800">Selezione dal Catalogo</span>
            <h2 class="font-serif text-4xl sm:text-5xl font-light text-stone-900 tracking-tight">
              Vini in Evidenza
            </h2>
          </div>

          <!-- Clean Text Filter Tabs -->
          <div class="flex items-center gap-6 overflow-x-auto pb-2 scrollbar-none">
            <button 
              v-for="tab in productTabs" 
              :key="tab.value"
              @click="selectedTab = tab.value"
              :class="[
                'text-xs font-bold tracking-wider uppercase whitespace-nowrap transition-colors pb-1 border-b-2',
                selectedTab === tab.value
                  ? 'border-wine-800 text-wine-900 font-extrabold'
                  : 'border-transparent text-stone-400 hover:text-stone-700'
              ]"
            >
              {{ tab.label }}
            </button>
          </div>
        </div>

        <!-- Products Grid -->
        <div v-if="pendingProducts" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          <div v-for="i in 3" :key="i" class="h-96 bg-stone-200/50 animate-pulse rounded-xl"></div>
        </div>

        <div v-else-if="filteredProducts && filteredProducts.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          <ProductCard v-for="prod in filteredProducts.slice(0, 6)" :key="prod.id" :product="prod" />
        </div>

        <div v-else class="text-center py-20 bg-stone-50 rounded-xl border border-stone-200/60 p-8 space-y-2">
          <Wine class="w-8 h-8 text-stone-400 mx-auto" />
          <p class="text-stone-500 font-light text-sm">Nessun vino presente in questa categoria al momento.</p>
        </div>

      </div>
    </section>

    <!-- 5. WINERIES SPOTLIGHT & MAP TEASER -->
    <section class="py-24 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
      
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-stone-200/70 pb-6">
        <div class="space-y-2">
          <span class="text-xs font-bold uppercase tracking-[0.25em] text-wine-800">Territorio e Passione</span>
          <h2 class="font-serif text-4xl sm:text-5xl font-light text-stone-900 tracking-tight">
            Le Cantine Molisane
          </h2>
        </div>
        
        <div class="flex items-center space-x-6">
          <!-- Text View Switcher -->
          <div class="flex items-center space-x-4 text-xs font-bold uppercase tracking-wider">
            <button 
              @click="producersViewMode = 'grid'"
              :class="[
                'pb-1 border-b-2 transition-colors',
                producersViewMode === 'grid' ? 'border-wine-800 text-wine-900' : 'border-transparent text-stone-400 hover:text-stone-700'
              ]"
            >
              Griglia
            </button>

            <button 
              @click="producersViewMode = 'map'"
              :class="[
                'pb-1 border-b-2 transition-colors',
                producersViewMode === 'map' ? 'border-wine-800 text-wine-900' : 'border-transparent text-stone-400 hover:text-stone-700'
              ]"
            >
              Mappa
            </button>
          </div>

          <NuxtLink to="/produttori" class="font-bold text-xs uppercase tracking-wider text-wine-800 hover:text-wine-900 inline-flex items-center space-x-1">
            <span>Vedi tutte</span>
            <ArrowRight class="w-4 h-4" />
          </NuxtLink>
        </div>
      </div>

      <div v-if="pendingProducers" class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div v-for="i in 2" :key="i" class="h-64 bg-stone-200/50 animate-pulse rounded-xl"></div>
      </div>

      <!-- Map View -->
      <div v-else-if="producersViewMode === 'map'">
        <WineryMap 
          :producers="producers" 
          title="Mappa delle Cantine del Molise"
          subtitle="Localizzazione dei produttori molisani registrati"
          :zoom="9.5"
        />
      </div>

      <!-- Grid View -->
      <div v-else-if="producers && producers.length" class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <ProducerCard v-for="producer in producers.slice(0, 4)" :key="producer.id" :producer="producer" />
      </div>

    </section>

    <!-- 6. VALUE PROPOSITION SECTION (OPEN DARK SECTION - NO BOXED CARDS) -->
    <section class="py-24 bg-stone-900 text-white border-t border-stone-800">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16">
        
        <div class="text-center max-w-3xl mx-auto space-y-3">
          <span class="text-xs font-bold uppercase tracking-[0.25em] text-amber-300">Il Valore del Portale</span>
          <h2 class="font-serif text-4xl sm:text-5xl font-light text-white tracking-tight">
            Perché EnotecaMolise?
          </h2>
          <p class="text-stone-300 text-base font-light leading-relaxed">
            Connettiamo gli appassionati di vino ed i professionisti del settore direttamente con i viticoltori del territorio.
          </p>
        </div>

        <!-- Open 3-Column Feature Grid (No Boxed Cards) -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-16 text-center">
          
          <!-- Feature 1 -->
          <div class="space-y-4 flex flex-col items-center">
            <!-- Floating Monochromatic Icon -->
            <Wine class="w-10 h-10 text-amber-300 mb-1" />
            <h3 class="font-serif text-2xl font-bold text-white">100% Filiera Molisana</h3>
            <p class="text-xs text-stone-400 leading-relaxed font-light max-w-xs">
              Catalogo focalizzato esclusivamente sulle cantine e sui vitigni autoctoni del Molise (Tintilia, Biferno, Pentro).
            </p>
          </div>

          <!-- Feature 2 -->
          <div class="space-y-4 flex flex-col items-center md:border-l md:border-stone-800 md:pl-8">
            <!-- Floating Monochromatic Icon -->
            <MessageSquare class="w-10 h-10 text-amber-300 mb-1" />
            <h3 class="font-serif text-2xl font-bold text-white">Contatto Diretto</h3>
            <p class="text-xs text-stone-400 leading-relaxed font-light max-w-xs">
              Nessun intermediario: invia messaggi diretti o chatta su WhatsApp con la cantina per prezzi e visite.
            </p>
          </div>

          <!-- Feature 3 -->
          <div class="space-y-4 flex flex-col items-center md:border-l md:border-stone-800 md:pl-8">
            <!-- Floating Monochromatic Icon -->
            <MapPin class="w-10 h-10 text-amber-300 mb-1" />
            <h3 class="font-serif text-2xl font-bold text-white">Territorio & Visite</h3>
            <p class="text-xs text-stone-400 leading-relaxed font-light max-w-xs">
              Esplora la mappa interattiva per scoprire la posizione delle cantine ed organizzare le tue degustazioni in vigna.
            </p>
          </div>

        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { 
  Sparkles, ArrowRight, Building2, Search, Wine, LayoutGrid, 
  MapPin, Compass, Mountain, MessageSquare, Quote 
} from 'lucide-vue-next'

const router = useRouter()
const { fetchWithAuth } = useApi()
const { isOrganicProduct } = useOrganic()

useSeoMeta({
  title: 'EnotecaMolise - I Grandi Vini del Molise & Le Cantine Molisane',
  description: 'Scopri i migliori vini del Molise: Tintilia, Biferno, Pentro e Spumanti. Connettiti direttamente con le cantine molisane.'
})

const heroQuery = ref('')
const selectedTab = ref('ALL')
const producersViewMode = ref('grid')

const moliseQuotes = [
  { text: "«Il Molise existe ed è racchiuso in ogni calice: terra antica di vigne, silenzi e profumi autentici.»", author: "Passione Enologica Molisana" },
  { text: "«Dalla Tintilia al Biferno, ogni bottiglia racconta la fierezza e l'anima delle nostre colline.»", author: "I Vignaioli del Molise" },
  { text: "«Tra il mare Adriatico e le vette dell'Appennino, la vigna qui trova il suo respiro più vero.»", author: "Terroir & Tradizione Molisana" },
  { text: "«Il vino in Molise non si produce soltanto, si custodisce come una storia di famiglia.»", author: "Tradizione Molisana" },
  { text: "«Una terra piccola dal cuore grande, dove la natura parla la lingua franca del buon vino.»", author: "Eccellenze del Territorio" },
  { text: "«Assaporare una Tintilia è compiere un viaggio dove il tempo ha preservato la purezza del gusto.»", author: "Vitigni Autoctoni Molisani" }
]

const currentQuote = ref(moliseQuotes[0])

onMounted(() => {
  const randomIndex = Math.floor(Math.random() * moliseQuotes.length)
  currentQuote.value = moliseQuotes[randomIndex]
})

const quickPills = [
  { label: 'Tintilia', query: 'Tintilia' },
  { label: 'Biferno', query: 'Biferno' },
  { label: 'Vini Biologici', query: 'Biologico' },
  { label: 'Spumanti', query: 'Spumante' }
]

const productTabs = [
  { label: 'Tutti i Vini', value: 'ALL' },
  { label: 'Vini Rossi', value: 'VINO_ROSSO' },
  { label: 'Vini Bianchi', value: 'VINO_BIANCO' },
  { label: 'Vini Rosati', value: 'ROSATO' },
  { label: 'Spumanti', value: 'SPUMANTE' },
  { label: 'Biologici', value: 'ORGANIC' }
]

const handleHeroSearch = () => {
  if (heroQuery.value.trim()) {
    router.push(`/vini?search=${encodeURIComponent(heroQuery.value.trim())}`)
  } else {
    router.push('/vini')
  }
}

const searchPill = (q) => {
  router.push(`/vini?search=${encodeURIComponent(q)}`)
}

const { data: products, pending: pendingProducts } = await useAsyncData('home_products', async () => {
  const res = await fetchWithAuth('/products?status=PUBLISHED')
  return res || []
}, { default: () => [] })

const { data: producers, pending: pendingProducers } = await useAsyncData('home_producers', async () => {
  const res = await fetchWithAuth('/producers')
  return res || []
}, { default: () => [] })

const filteredProducts = computed(() => {
  const prods = products.value || []
  if (selectedTab.value === 'ALL') return prods
  if (selectedTab.value === 'ORGANIC') {
    return prods.filter(p => isOrganicProduct(p))
  }
  return prods.filter(p => p.category === selectedTab.value)
})
</script>
