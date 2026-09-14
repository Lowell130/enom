<template>
  <div>
    <!-- Hero Section with Soft Muted Overlay -->
    <section class="relative bg-wine-950 text-white py-24 md:py-36 overflow-hidden">
      <!-- Background image with subtle gradient overlay -->
      <div class="absolute inset-0 z-0 opacity-25 bg-cover bg-center" style="background-image: url('https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?auto=format&fit=crop&w=1920&q=80');"></div>
      <div class="absolute inset-0 bg-gradient-to-r from-wine-950 via-wine-950/85 to-wine-950/40 z-0"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="max-w-2xl space-y-6">
          <span class="inline-flex items-center space-x-2 px-3.5 py-1.5 bg-amber-400/10 text-amber-300 rounded-full text-xs font-semibold tracking-widest uppercase border border-amber-400/20 backdrop-blur-xs">
            <Sparkles class="w-3.5 h-3.5 text-amber-300" />
            <span>Eccellenza Enologica Molisana</span>
          </span>

          <h1 class="font-serif text-4xl sm:text-6xl lg:text-7xl font-light tracking-tight leading-tight text-white">
            Scopri i Tesori dei Vigneti del Molise
          </h1>

          <p class="text-base sm:text-xl text-stone-300 leading-relaxed font-light">
            Dalla Tintilia autoctona ai grandi Rossi del Biferno e Spumanti raffinati. Il portale che connette direttamente gli appassionati con le migliori cantine del Molise.
          </p>

          <!-- Interactive Hero Search Input -->
          <div class="pt-2 max-w-xl">
            <form @submit.prevent="handleHeroSearch" class="relative flex items-center">
              <Search class="w-5 h-5 text-amber-300 absolute left-4 pointer-events-none" />
              <input 
                v-model="heroQuery"
                type="text"
                placeholder="Cerca vino, cantina, vitigno (es. Tintilia, Biferno, Biologico)..."
                class="w-full bg-white/10 hover:bg-white/15 focus:bg-white/20 text-white placeholder-stone-300 text-sm sm:text-base rounded-2xl pl-12 pr-28 py-3.5 border border-white/25 focus:border-amber-400/80 focus:outline-none backdrop-blur-md transition-all shadow-lg"
              />
              <button 
                type="submit"
                class="absolute right-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white font-semibold text-xs rounded-xl shadow-xs transition-all flex items-center space-x-1"
              >
                <span>Cerca</span>
                <ArrowRight class="w-3.5 h-3.5" />
              </button>
            </form>
          </div>

          <div class="pt-2 flex flex-wrap gap-4">
            <NuxtLink to="/vini" class="inline-flex items-center space-x-2 px-8 py-4 bg-amber-700 hover:bg-amber-800 text-white font-semibold text-sm rounded-xl shadow-md transition-all hover:scale-105">
              <span>Esplora i Vini</span>
              <ArrowRight class="w-4 h-4" />
            </NuxtLink>
            <NuxtLink to="/produttori" class="inline-flex items-center space-x-2 px-8 py-4 bg-white/10 hover:bg-white/20 text-white font-medium text-sm rounded-xl backdrop-blur-xs transition-all border border-white/20">
              <Building2 class="w-4 h-4 text-amber-200" />
              <span>Le Cantine</span>
            </NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Stats / Badges Banner -->
    <section class="bg-wine-900 border-y border-wine-800/80 text-amber-200 py-8">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div class="space-y-1">
            <div class="font-serif text-3xl font-bold text-white">Tintilia DOC</div>
            <div class="text-xs text-stone-300 uppercase tracking-widest font-medium">Vitigno Autoctono</div>
          </div>
          <div class="space-y-1">
            <div class="font-serif text-3xl font-bold text-white">Biferno DOC</div>
            <div class="text-xs text-stone-300 uppercase tracking-widest font-medium">Tradizione Millenaria</div>
          </div>
          <div class="space-y-1">
            <div class="font-serif text-3xl font-bold text-white">Pentro DOC</div>
            <div class="text-xs text-stone-300 uppercase tracking-widest font-medium">Territorio d'Isernia</div>
          </div>
          <div class="space-y-1">
            <div class="font-serif text-3xl font-bold text-white">100% Diretto</div>
            <div class="text-xs text-stone-300 uppercase tracking-widest font-medium">Contatto Cantina</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Featured Wines Section -->
    <section class="py-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex flex-col md:flex-row md:items-end justify-between mb-12">
        <div class="space-y-1">
          <span class="text-xs font-bold uppercase tracking-widest text-wine-800">Selezione del Catalogo</span>
          <h2 class="font-serif text-3xl md:text-5xl font-light text-stone-900">
            Vini in Evidenza
          </h2>
        </div>
        <NuxtLink to="/vini" class="mt-4 md:mt-0 font-semibold text-sm text-wine-800 hover:text-wine-900 inline-flex items-center space-x-1">
          <span>Vedi tutto il catalogo</span>
          <ArrowRight class="w-4 h-4" />
        </NuxtLink>
      </div>

      <div v-if="pendingProducts" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
        <div v-for="i in 3" :key="i" class="h-96 bg-stone-200/50 animate-pulse rounded-2xl"></div>
      </div>

      <div v-else-if="products && products.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
        <ProductCard v-for="prod in products.slice(0, 6)" :key="prod.id" :product="prod" />
      </div>

      <div v-else class="text-center py-16 bg-white rounded-2xl border border-stone-200/60 p-8">
        <p class="text-stone-500 font-light">Nessun vino ancora presente nel catalogo.</p>
      </div>
    </section>

    <!-- Producers Section -->
    <section class="py-20 bg-stone-100/50 border-t border-stone-200/60">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row md:items-end justify-between mb-12">
          <div class="space-y-1">
            <span class="text-xs font-bold uppercase tracking-widest text-wine-800">Territorio e Passione</span>
            <h2 class="font-serif text-3xl md:text-5xl font-light text-stone-900">
              Le Cantine Molisane
            </h2>
          </div>
          <NuxtLink to="/produttori" class="mt-4 md:mt-0 font-semibold text-sm text-wine-800 hover:text-wine-900 inline-flex items-center space-x-1">
            <span>Vedi tutte le cantine</span>
            <ArrowRight class="w-4 h-4" />
          </NuxtLink>
        </div>

        <div v-if="pendingProducers" class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div v-for="i in 2" :key="i" class="h-64 bg-stone-200/50 animate-pulse rounded-2xl"></div>
        </div>

        <div v-else-if="producers && producers.length" class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <ProducerCard v-for="producer in producers.slice(0, 4)" :key="producer.id" :producer="producer" />
        </div>
      </div>
    </section>

  </div>
</template>

<script setup>
import { Sparkles, ArrowRight, Building2, Search } from 'lucide-vue-next'

const router = useRouter()
const { fetchWithAuth } = useApi()

useSeoMeta({
  title: 'EnotecaMolise - I Grandi Vini del Molise & Le Cantine Molisane',
  description: 'Scopri i migliori vini del Molise: Tintilia, Biferno, Pentro e Spumanti. Connettiti direttamente con le cantine molisane.'
})

const heroQuery = ref('')

const handleHeroSearch = () => {
  if (heroQuery.value.trim()) {
    router.push(`/vini?search=${encodeURIComponent(heroQuery.value.trim())}`)
  } else {
    router.push('/vini')
  }
}

const { data: products, pending: pendingProducts } = await useAsyncData('home_products', () => 
  fetchWithAuth('/products?status=PUBLISHED')
)

const { data: producers, pending: pendingProducers } = await useAsyncData('home_producers', () => 
  fetchWithAuth('/producers')
)
</script>
