<template>
  <div v-if="pending" class="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="h-96 bg-stone-200/50 animate-pulse rounded-2xl"></div>
  </div>

  <div v-else-if="product" class="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <!-- Top Action Bar for Logged-In Admin / Owner Producer -->
    <div v-if="canEdit" class="mb-8 p-4 bg-amber-500/10 border border-amber-500/20 rounded-2xl flex items-center justify-between shadow-xs">
      <div class="flex items-center space-x-2.5 text-amber-900 text-sm font-medium">
        <ShieldCheck class="w-5 h-5 text-amber-700" />
        <span>Stai visualizzando questo vino come <strong class="font-bold underline">{{ isAdmin ? 'Super Admin' : 'Produttore Proprietario' }}</strong>.</span>
      </div>
      <NuxtLink 
        :to="`/dashboard/prodotti/edit-${product.id}`" 
        class="inline-flex items-center space-x-1.5 px-5 py-2.5 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-xs rounded-xl shadow-xs transition-all"
      >
        <Pencil class="w-3.5 h-3.5 text-amber-200" />
        <span>Modifica Scheda Vino</span>
      </NuxtLink>
    </div>

    <!-- Breadcrumbs -->
    <nav class="flex items-center space-x-2 text-xs text-stone-500 mb-8 font-medium">
      <NuxtLink to="/" class="hover:text-wine-800 transition-colors">Home</NuxtLink>
      <span>/</span>
      <NuxtLink to="/vini" class="hover:text-wine-800 transition-colors">Vini</NuxtLink>
      <span>/</span>
      <span class="text-stone-900 font-semibold truncate">{{ product.name }}</span>
    </nav>

    <!-- Main Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
      
      <!-- Left Column: Bottle Image Gallery (Clean White Container) -->
      <div class="lg:col-span-5">
        <div class="bg-white rounded-3xl p-8 border border-stone-200/60 shadow-xs flex items-center justify-center relative overflow-hidden">
          <img 
            :src="mainImage" 
            :alt="product.name" 
            class="max-h-[500px] object-contain hover:scale-105 transition-transform duration-500"
          />
          <div class="absolute top-4 left-4 flex flex-wrap gap-2 z-10">
            <span class="px-3 py-1 text-xs font-bold rounded-full bg-wine-800 text-white shadow-xs">
              {{ product.denominazione }}
            </span>
            <span v-if="product.is_riserva" class="px-3 py-1 text-xs font-bold rounded-full bg-amber-700 text-white shadow-xs">
              Riserva
            </span>
            <span v-if="isOrganicProduct(product)" class="px-3 py-1 text-xs font-bold rounded-full bg-emerald-700 text-white shadow-xs inline-flex items-center space-x-1">
              <Leaf class="w-3.5 h-3.5 text-emerald-200" />
              <span>Vino Biologico</span>
            </span>
          </div>
          <div class="absolute top-4 right-4 z-10">
            <span :class="['px-3 py-1 text-xs font-semibold rounded-lg border shadow-xs', getCategoryBadgeClass(product.category)]">
              {{ formatCategory(product.category) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Right Column: Details & Specs -->
      <div class="lg:col-span-7 flex flex-col justify-between">
        <div>
          <!-- Producer Link -->
          <div class="flex items-center justify-between mb-3">
            <NuxtLink 
              v-if="product.producer_slug"
              :to="`/produttori/${product.producer_slug}`" 
              class="inline-flex items-center space-x-1.5 text-xs font-bold text-wine-800 uppercase tracking-widest hover:underline"
            >
              <Building2 class="w-4 h-4 text-wine-800" />
              <span>Cantina: {{ product.producer_name }}</span>
            </NuxtLink>

            <NuxtLink 
              v-if="canEdit" 
              :to="`/dashboard/prodotti/edit-${product.id}`" 
              class="inline-flex items-center space-x-1 text-xs font-bold text-wine-800 hover:text-wine-900 underline"
            >
              <Pencil class="w-3.5 h-3.5" />
              <span>Modifica veloce</span>
            </NuxtLink>
          </div>

          <h1 class="font-serif text-4xl sm:text-5xl font-light text-stone-900 leading-tight">
            {{ product.name }}
          </h1>

          <!-- Quick Badges -->
          <div class="mt-6 flex flex-wrap items-center gap-3 text-sm font-medium text-stone-700 border-b border-stone-200/60 pb-6">
            <span v-if="isOrganicProduct(product)" class="inline-flex items-center space-x-1.5 bg-emerald-50 text-emerald-900 px-3.5 py-1.5 rounded-xl border border-emerald-200 font-semibold shadow-2xs">
              <Leaf class="w-4 h-4 text-emerald-700" />
              <span>Vino Biologico</span>
            </span>

            <span v-if="product.alcohol_degrees" class="inline-flex items-center space-x-1.5 bg-wine-50 text-wine-900 px-3.5 py-1.5 rounded-xl border border-wine-100 font-semibold">
              <Wine class="w-4 h-4 text-wine-800" />
              <span>{{ product.alcohol_degrees }}% Vol.</span>
            </span>

            <span v-if="product.serving_temperature" class="inline-flex items-center space-x-1.5 bg-amber-50 text-amber-900 px-3.5 py-1.5 rounded-xl border border-amber-100 font-semibold">
              <Thermometer class="w-4 h-4 text-amber-700" />
              <span>Servire a {{ product.serving_temperature }}</span>
            </span>

            <span v-if="product.indicative_price" class="inline-flex items-center space-x-1.5 bg-emerald-50 text-emerald-900 px-3.5 py-1.5 rounded-xl border border-emerald-100 font-bold">
              <Tag class="w-4 h-4 text-emerald-700" />
              <span>{{ product.indicative_price }}</span>
            </span>
          </div>

          <!-- Description -->
          <div class="mt-6 space-y-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400">Descrizione</h3>
            <p class="text-base text-stone-700 leading-relaxed font-light">
              {{ product.description || 'Nessuna descrizione specificata.' }}
            </p>
          </div>

          <!-- Vitigni / Grape Varieties -->
          <div v-if="product.grape_varieties && product.grape_varieties.length" class="mt-6 space-y-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400">Vitigni</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="(v, i) in product.grape_varieties" :key="i" class="px-3.5 py-1.5 bg-stone-100 text-stone-800 rounded-xl text-xs font-semibold border border-stone-200/50">
                🍇 {{ v }}
              </span>
            </div>
          </div>

          <!-- Tasting Notes (Stacked Full-Width Vertical Rows - No Outer Container) -->
          <div v-if="product.tasting_notes" class="mt-8 space-y-3">
            <div class="flex items-center space-x-2 text-stone-900 mb-3">
              <Sparkles class="w-4 h-4 text-wine-800" />
              <h3 class="font-sans text-xs font-bold uppercase tracking-wider text-stone-400">Profilo Organolettico</h3>
            </div>
            
            <div class="space-y-3">
              
              <!-- Esame Visivo -->
              <div v-if="product.tasting_notes.visual" class="bg-gradient-to-r from-amber-50/60 via-amber-50/20 to-transparent p-4 sm:p-4.5 rounded-2xl border border-amber-200/60 shadow-2xs">
                <div class="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                  <div class="flex items-center space-x-2 text-amber-900 font-bold text-xs uppercase tracking-wider shrink-0 md:w-36">
                    <div class="w-6 h-6 rounded-lg bg-amber-100/90 flex items-center justify-center text-amber-800 shrink-0">
                      <Eye class="w-3.5 h-3.5" />
                    </div>
                    <span>Esame Visivo</span>
                  </div>
                  <p class="text-stone-800 text-xs sm:text-sm font-medium leading-relaxed flex-1">
                    {{ product.tasting_notes.visual }}
                  </p>
                </div>
              </div>

              <!-- Esame Olfattivo -->
              <div v-if="product.tasting_notes.olfactory" class="bg-gradient-to-r from-purple-50/60 via-purple-50/20 to-transparent p-4 sm:p-4.5 rounded-2xl border border-purple-200/60 shadow-2xs">
                <div class="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                  <div class="flex items-center space-x-2 text-purple-900 font-bold text-xs uppercase tracking-wider shrink-0 md:w-36">
                    <div class="w-6 h-6 rounded-lg bg-purple-100/90 flex items-center justify-center text-purple-800 shrink-0">
                      <Sparkles class="w-3.5 h-3.5" />
                    </div>
                    <span>Esame Olfattivo</span>
                  </div>
                  <p class="text-stone-800 text-xs sm:text-sm font-medium leading-relaxed flex-1">
                    {{ product.tasting_notes.olfactory }}
                  </p>
                </div>
              </div>

              <!-- Esame Gustativo -->
              <div v-if="product.tasting_notes.taste" class="bg-gradient-to-r from-rose-50/60 via-rose-50/20 to-transparent p-4 sm:p-4.5 rounded-2xl border border-rose-200/60 shadow-2xs">
                <div class="flex flex-col md:flex-row md:items-center gap-2 md:gap-4">
                  <div class="flex items-center space-x-2 text-rose-900 font-bold text-xs uppercase tracking-wider shrink-0 md:w-36">
                    <div class="w-6 h-6 rounded-lg bg-rose-100/90 flex items-center justify-center text-rose-800 shrink-0">
                      <GlassWater class="w-3.5 h-3.5" />
                    </div>
                    <span>Esame Gustativo</span>
                  </div>
                  <p class="text-stone-800 text-xs sm:text-sm font-medium leading-relaxed flex-1">
                    {{ product.tasting_notes.taste }}
                  </p>
                </div>
              </div>

            </div>
          </div>

          <!-- Abbinamenti Culinari -->
          <div v-if="product.food_pairings && product.food_pairings.length" class="mt-6 space-y-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-stone-400">Abbinamenti Consigliati</h3>
            <div class="flex flex-wrap gap-2">
              <span v-for="(pairing, i) in product.food_pairings" :key="i" class="inline-flex items-center space-x-1.5 px-3.5 py-1.5 bg-stone-100 text-stone-800 rounded-xl text-xs font-semibold border border-stone-200/50">
                <Utensils class="w-3.5 h-3.5 text-stone-500" />
                <span>{{ pairing }}</span>
              </span>
            </div>
          </div>

        </div>

        <!-- Action Buttons -->
        <div class="mt-10 pt-6 border-t border-stone-200/60 flex flex-wrap gap-4 items-center">
          <button 
            @click="isModalOpen = true" 
            class="inline-flex items-center justify-center space-x-2 px-8 py-4 bg-wine-800 hover:bg-wine-900 text-white font-semibold rounded-2xl shadow-md transition-all hover:scale-105 flex-1 text-center text-sm"
          >
            <MessageSquare class="w-4 h-4 text-amber-200" />
            <span>Chiedi Info / Disponibilità / Prezzi</span>
          </button>

          <a 
            v-if="product.technical_sheet_pdf" 
            :href="pdfUrl" 
            target="_blank" 
            class="inline-flex items-center justify-center space-x-2 px-6 py-4 border border-wine-800 text-wine-800 hover:bg-wine-50 font-semibold rounded-2xl text-xs transition-colors"
          >
            <FileDown class="w-4 h-4" />
            <span>Scarica Scheda Tecnica PDF</span>
          </a>
        </div>

      </div>

    </div>

    <!-- SEZIONE SCHEDA TECNICA (EXACT REFERENCE DESIGN) -->
    <div class="mt-16 bg-white rounded-3xl p-8 sm:p-12 border border-stone-200/60 shadow-xs">
      <h2 class="font-serif text-3xl font-light text-stone-900 mb-8">
        Scheda Tecnica
      </h2>

      <!-- 2-Column Technical Specification Grid -->
      <div v-if="displaySpecs && displaySpecs.length" class="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-5">
        <div 
          v-for="(item, idx) in displaySpecs" 
          :key="idx" 
          class="flex items-center justify-between border-b border-stone-200/60 pb-3"
        >
          <span class="text-sm text-stone-500 font-medium">{{ item.name }}</span>
          <span class="text-sm font-bold text-stone-900 text-right ml-4">{{ item.value }}</span>
        </div>
      </div>
    </div>

    <!-- SEZIONE ALTRI VINI DELLA STESSA CANTINA -->
    <div v-if="otherWineryProducts && otherWineryProducts.length" class="mt-16 pt-12 border-t border-stone-200/60">
      <div class="flex flex-col sm:flex-row sm:items-end justify-between mb-8 gap-4">
        <div>
          <span class="text-xs font-bold text-wine-800 uppercase tracking-widest block mb-1">
            Dalla stessa cantina
          </span>
          <h2 class="font-serif text-3xl font-light text-stone-900">
            Altri vini prodotti da {{ product.producer_name }}
          </h2>
        </div>
        
        <NuxtLink 
          v-if="product.producer_slug"
          :to="`/produttori/${product.producer_slug}`"
          class="inline-flex items-center space-x-1 text-sm font-bold text-wine-800 hover:text-wine-900 underline shrink-0"
        >
          <span>Vedi tutti i vini della cantina</span>
          <ChevronRight class="w-4 h-4" />
        </NuxtLink>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <ProductCard 
          v-for="otherProd in otherWineryProducts" 
          :key="otherProd.id" 
          :product="otherProd" 
        />
      </div>
    </div>

    <!-- Contact Modal -->
    <InquiryModal 
      :is-open="isModalOpen" 
      :producer-id="product.producer_id"
      :producer-name="product.producer_name"
      :product-id="product.id"
      :product-name="product.name"
      @close="isModalOpen = false"
    />

  </div>

  <!-- Fallback if Product Not Found (404) -->
  <div v-else class="py-24 max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
    <div class="w-16 h-16 rounded-2xl bg-wine-50 text-wine-800 flex items-center justify-center mx-auto mb-4 border border-wine-100 shadow-2xs">
      <Wine class="w-8 h-8" />
    </div>
    <h1 class="font-serif text-3xl sm:text-4xl font-bold text-stone-900 mb-2">Vino non trovato</h1>
    <p class="text-stone-600 mb-8 font-light text-base max-w-md mx-auto">
      La scheda del vino richiesta potrebbe non essere ancora presente nel catalogo o lo slug specificato non è corretto.
    </p>
    <NuxtLink to="/vini" class="inline-flex items-center space-x-2 px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-sm rounded-xl transition-all shadow-xs">
      <span>Torna al catalogo vini</span>
    </NuxtLink>
  </div>
</template>

<script setup>
import { ShieldCheck, Pencil, Building2, Wine, Thermometer, Tag, Utensils, MessageSquare, FileDown, Eye, Sparkles, GlassWater, ChevronRight, Leaf } from 'lucide-vue-next'

const route = useRoute()
const { fetchWithAuth, mediaBase } = useApi()
const { user, isAdmin, isAuthenticated } = useAuth()
const { formatCategory, getCategoryBadgeClass } = useCategoryBadge()
const { isOrganicProduct } = useOrganic()

const isModalOpen = ref(false)

const { data: product, pending } = await useAsyncData(`product_${route.params.slug}`, async () => {
  try {
    return await fetchWithAuth(`/products/${route.params.slug}`)
  } catch (err) {
    if (err?.statusCode === 404 || err?.status === 404 || err?.response?.status === 404) {
      return null
    }
    throw err
  }
})

watchEffect(() => {
  if (product.value) {
    useSeoMeta({
      title: `${product.value.name} - ${product.value.producer_name || 'EnotecaMolise'}`,
      description: product.value.description || `Scopri ${product.value.name} prodotto da ${product.value.producer_name}. Scheda tecnica e dettagli enologici su EnotecaMolise.`
    })
  }
})

const { data: wineryProducts } = await useAsyncData(`winery_products_${route.params.slug}`, async () => {
  if (!product.value?.producer_id) return []
  return await fetchWithAuth(`/products?producer_id=${product.value.producer_id}`)
})

const otherWineryProducts = computed(() => {
  if (!wineryProducts.value || !product.value) return []
  return wineryProducts.value.filter(p => String(p.id) !== String(product.value.id))
})

const canEdit = computed(() => {
  if (!isAuthenticated.value || !product.value) return false
  if (isAdmin.value) return true
  const userProdId = user.value?.producer_id || user.value?.producer?.id
  return userProdId && String(userProdId) === String(product.value.producer_id)
})

const displaySpecs = computed(() => {
  if (!product.value) return []
  
  const list = []
  const customMap = new Set()
  
  if (product.value.custom_attributes && product.value.custom_attributes.length > 0) {
    for (const attr of product.value.custom_attributes) {
      if (attr.name) {
        customMap.add(attr.name.toLowerCase().trim())
      }
    }
  }

  // Auto-include standard fields if not explicitly specified in custom_attributes
  if (product.value.denominazione && !customMap.has('denominazione')) {
    list.push({ name: 'Denominazione', value: product.value.denominazione })
  }
  if (product.value.is_riserva && !customMap.has('menzione') && !customMap.has('riserva')) {
    list.push({ name: 'Menzione', value: 'Riserva' })
  }
  if (product.value.grape_varieties && product.value.grape_varieties.length && !customMap.has('uvaggio') && !customMap.has('vitigni')) {
    list.push({ name: 'Uvaggio', value: product.value.grape_varieties.join(', ') })
  }
  if (product.value.alcohol_degrees && !customMap.has('grado alcolico') && !customMap.has('gradazione alcolica')) {
    list.push({ name: 'Gradazione Alcolica', value: `${product.value.alcohol_degrees}% vol` })
  }
  if (product.value.serving_temperature && !customMap.has('temperatura di servizio')) {
    list.push({ name: 'Temperatura di Servizio', value: product.value.serving_temperature })
  }
  if (product.value.indicative_price && !customMap.has('fascia di prezzo') && !customMap.has('prezzo') && !customMap.has('prezzo indicativo')) {
    list.push({ name: 'Fascia di Prezzo', value: product.value.indicative_price })
  }

  // Append any extra custom attributes
  if (product.value.custom_attributes && product.value.custom_attributes.length > 0) {
    for (const attr of product.value.custom_attributes) {
      if (attr.name && attr.value) {
        list.push({ name: attr.name, value: attr.value })
      }
    }
  }

  return list
})

const mainImage = computed(() => {
  if (product.value?.photos && product.value.photos.length > 0) {
    const url = product.value.photos[0]
    return url.startsWith('http') ? url : `${mediaBase}${url}`
  }
  return 'https://images.unsplash.com/photo-1586370434639-0fe43b2d32e6?auto=format&fit=crop&w=600&q=80'
})

const pdfUrl = computed(() => {
  if (!product.value?.technical_sheet_pdf) return '#'
  const url = product.value.technical_sheet_pdf
  return url.startsWith('http') ? url : `${mediaBase}${url}`
})
</script>
