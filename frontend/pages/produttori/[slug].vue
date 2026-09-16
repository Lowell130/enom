<template>
  <div v-if="pending" class="py-16 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="h-96 bg-stone-200/50 animate-pulse rounded-3xl"></div>
  </div>

  <div v-else-if="producer" class="pb-24 bg-stone-50/40">
    
    <!-- Top Action Bar for Admin or Producer Owner -->
    <div v-if="canEdit" class="bg-amber-500/10 border-b border-amber-500/20 py-3 px-4 sm:px-8">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center space-x-2 text-amber-900 text-xs font-semibold">
          <ShieldCheck class="w-4 h-4 text-amber-700" />
          <span>Sei autenticato come <strong class="underline">{{ isAdmin ? 'Super Admin' : 'Cantina Proprietaria' }}</strong>.</span>
        </div>
        <NuxtLink 
          :to="isAdmin ? `/dashboard/profilo?producer_id=${producer.id}` : '/dashboard/profilo'" 
          class="inline-flex items-center space-x-1.5 px-4 py-1.5 bg-wine-800 hover:bg-wine-900 text-white font-bold text-xs rounded-xl shadow-xs transition-all"
        >
          <Pencil class="w-3.5 h-3.5 text-amber-200" />
          <span>Modifica Dati Cantina</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Hero Header -->
    <div class="relative bg-wine-950 text-white py-20 lg:py-28 overflow-hidden">
      <!-- Background Image Overlay -->
      <img 
        :src="coverImage" 
        :alt="producer.company_name" 
        class="absolute inset-0 w-full h-full object-cover opacity-35"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-wine-950 via-wine-950/75 to-stone-950/50"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        
        <!-- Breadcrumb -->
        <nav class="flex items-center space-x-2 text-xs text-stone-300 font-medium mb-8">
          <NuxtLink to="/" class="hover:text-white transition-colors">Home</NuxtLink>
          <ChevronRight class="w-3.5 h-3.5 text-stone-500" />
          <NuxtLink to="/produttori" class="hover:text-white transition-colors">Cantine Molisane</NuxtLink>
          <ChevronRight class="w-3.5 h-3.5 text-stone-500" />
          <span class="text-amber-300 truncate">{{ producer.company_name }}</span>
        </nav>

        <div class="flex flex-col md:flex-row items-start md:items-end justify-between gap-6">
          <div class="flex flex-col sm:flex-row items-start sm:items-end space-y-4 sm:space-y-0 sm:space-x-6">
            <div class="w-28 h-28 sm:w-36 sm:h-36 rounded-3xl bg-white p-2 shadow-2xl overflow-hidden flex-shrink-0 border-2 border-amber-400/40">
              <img :src="logoImage" :alt="producer.company_name" class="w-full h-full object-cover rounded-2xl" />
            </div>
            <div class="space-y-2">
              <div class="flex flex-wrap items-center gap-2">
                <span class="inline-flex items-center space-x-1 px-3 py-1 bg-amber-400/10 text-amber-300 border border-amber-400/20 text-xs font-semibold uppercase tracking-wider rounded-full backdrop-blur-xs">
                  <MapPin class="w-3.5 h-3.5 text-amber-400" />
                  <span>{{ producer.address?.city || 'Molise' }} ({{ producer.address?.province || 'CB' }})</span>
                </span>
                <span class="inline-flex items-center space-x-1 px-3 py-1 bg-white/10 text-stone-200 border border-white/20 text-xs font-semibold rounded-full backdrop-blur-xs">
                  <Wine class="w-3.5 h-3.5 text-amber-300" />
                  <span>{{ (producerProducts || []).length }} Vini in Catalogo</span>
                </span>
              </div>

              <h1 class="font-serif text-4xl sm:text-6xl font-light tracking-tight text-white leading-tight">
                {{ producer.company_name }}
              </h1>

              <p v-if="producer.address?.street" class="text-stone-300 text-sm font-light flex items-center space-x-1.5">
                <MapPin class="w-4 h-4 text-amber-400 flex-shrink-0" />
                <span>{{ producer.address.street }}{{ producer.address.zip_code ? `, ${producer.address.zip_code}` : '' }} {{ producer.address.city }}</span>
              </p>
            </div>
          </div>

          <!-- Hero Action Buttons -->
          <div class="flex flex-wrap items-center gap-3 w-full md:w-auto pt-4 md:pt-0">
            <button 
              @click="isModalOpen = true" 
              class="flex-1 md:flex-initial inline-flex items-center justify-center space-x-2 px-6 py-3.5 bg-amber-600 hover:bg-amber-700 text-white rounded-2xl text-xs font-bold transition-all shadow-lg hover:scale-105"
            >
              <MessageSquare class="w-4 h-4 text-amber-100" />
              <span>Contatta la Cantina</span>
            </button>

            <a 
              v-if="producer.contacts?.whatsapp_number"
              :href="getWhatsAppUrl({ number: producer.contacts.whatsapp_number, companyName: producer.company_name })" 
              target="_blank"
              class="inline-flex items-center justify-center space-x-2 px-5 py-3.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-2xl text-xs font-bold transition-all shadow-md hover:scale-105"
              title="Chatta su WhatsApp"
            >
              <MessageSquare class="w-4 h-4 text-emerald-100" />
              <span>WhatsApp</span>
            </a>

            <a 
              v-if="producer.contacts?.website"
              :href="formatWebsiteUrl(producer.contacts.website)" 
              target="_blank"
              class="inline-flex items-center justify-center p-3.5 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-2xl transition-all backdrop-blur-xs hover:scale-105"
              title="Sito Web Ufficiale"
            >
              <Globe class="w-4 h-4 text-amber-200" />
            </a>
          </div>
        </div>

      </div>
    </div>

    <!-- Main Content Container -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12 space-y-16">
      
      <!-- Section 1: Story & Location Details -->
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
        
        <!-- Story Column (7 cols) -->
        <div class="lg:col-span-7 space-y-6">
          <div class="bg-white rounded-3xl p-8 border border-stone-200/70 shadow-xs relative overflow-hidden">
            <div class="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
              <Building2 class="w-48 h-48 text-wine-900" />
            </div>

            <span class="text-xs font-bold uppercase tracking-widest text-wine-800 block mb-2">Identità e Passione</span>
            <h2 class="font-serif text-3xl font-light text-stone-900 mb-6">
              La Nostra Storia
            </h2>

            <div class="prose prose-stone text-stone-600 font-light leading-relaxed text-base space-y-4">
              <p v-if="producer.description" class="whitespace-pre-line">
                {{ producer.description }}
              </p>
              <p v-else class="italic text-stone-400">
                La cantina {{ producer.company_name }} rappresenta una delle realtà enologiche del territorio molisano, custode di tradizione e passione per la vite.
              </p>
            </div>

            <!-- Contact pills bar inside story container -->
            <div class="mt-8 pt-6 border-t border-stone-100 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm font-light">
              <div v-if="producer.contacts?.phone" class="flex items-center space-x-3 p-3 bg-stone-50 rounded-2xl border border-stone-100">
                <div class="w-9 h-9 rounded-xl bg-wine-50 text-wine-800 flex items-center justify-center flex-shrink-0">
                  <Phone class="w-4 h-4" />
                </div>
                <div>
                  <div class="text-xs text-stone-400 font-medium">Telefono</div>
                  <a :href="`tel:${producer.contacts.phone}`" class="text-stone-800 font-semibold hover:text-wine-800">
                    {{ producer.contacts.phone }}
                  </a>
                </div>
              </div>

              <div v-if="producer.contacts?.email_contact" class="flex items-center space-x-3 p-3 bg-stone-50 rounded-2xl border border-stone-100">
                <div class="w-9 h-9 rounded-xl bg-wine-50 text-wine-800 flex items-center justify-center flex-shrink-0">
                  <Mail class="w-4 h-4" />
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-xs text-stone-400 font-medium">Email</div>
                  <a :href="`mailto:${producer.contacts.email_contact}`" class="text-stone-800 font-semibold hover:text-wine-800 truncate block">
                    {{ producer.contacts.email_contact }}
                  </a>
                </div>
              </div>

              <div v-if="producer.contacts?.website" class="flex items-center space-x-3 p-3 bg-stone-50 rounded-2xl border border-stone-100">
                <div class="w-9 h-9 rounded-xl bg-wine-50 text-wine-800 flex items-center justify-center flex-shrink-0">
                  <Globe class="w-4 h-4" />
                </div>
                <div class="min-w-0 flex-1">
                  <div class="text-xs text-stone-400 font-medium">Sito Web</div>
                  <a :href="formatWebsiteUrl(producer.contacts.website)" target="_blank" class="text-wine-800 font-semibold hover:underline truncate block">
                    {{ producer.contacts.website }}
                  </a>
                </div>
              </div>

              <div v-if="producer.contacts?.instagram || producer.contacts?.facebook" class="flex items-center space-x-3 p-3 bg-stone-50 rounded-2xl border border-stone-100">
                <div class="w-9 h-9 rounded-xl bg-wine-50 text-wine-800 flex items-center justify-center flex-shrink-0">
                  <Share2 class="w-4 h-4" />
                </div>
                <div class="flex items-center space-x-3">
                  <a v-if="producer.contacts?.instagram" :href="formatSocialUrl(producer.contacts.instagram, 'instagram')" target="_blank" class="text-pink-700 font-semibold hover:underline text-xs flex items-center gap-1">
                    <Instagram class="w-3.5 h-3.5" /> Instagram
                  </a>
                  <a v-if="producer.contacts?.facebook" :href="formatSocialUrl(producer.contacts.facebook, 'facebook')" target="_blank" class="text-blue-700 font-semibold hover:underline text-xs flex items-center gap-1">
                    <Facebook class="w-3.5 h-3.5" /> Facebook
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Location & Map Column (5 cols) -->
        <div class="lg:col-span-5 space-y-6">
          <WineryMap 
            :producers="[producer]" 
            :title="`Dove trovarci: ${producer.company_name}`"
            :subtitle="`${producer.address?.city || 'Molise'} (${producer.address?.province || 'CB'})`"
            :zoom="13"
          />

          <!-- Quick Contact Callout -->
          <div class="bg-gradient-to-br from-wine-950 to-stone-900 rounded-3xl p-6 text-white shadow-md space-y-4">
            <h3 class="font-serif text-xl font-semibold text-amber-200">
              Vuoi contattare direttamente la cantina?
            </h3>
            <p class="text-xs text-stone-300 leading-relaxed font-light">
              Puoi inviare una richiesta diretta per informazioni sui vini, visite in cantina o degustazioni.
            </p>

            <div class="pt-2 flex flex-col sm:flex-row gap-3">
              <button 
                @click="isModalOpen = true"
                class="w-full py-3 bg-amber-600 hover:bg-amber-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center justify-center space-x-2"
              >
                <MessageSquare class="w-4 h-4 text-amber-100" />
                <span>Richiedi Info o Visita</span>
              </button>
            </div>
          </div>
        </div>

      </div>

      <!-- Section 2: Winery Wines Catalogue -->
      <div class="pt-8 border-t border-stone-200/80 space-y-8">
        
        <!-- Catalogue Header & Category Filter Tabs -->
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div class="space-y-1">
            <span class="text-xs font-bold uppercase tracking-widest text-wine-800">Selezione della Cantina</span>
            <h2 class="font-serif text-3xl sm:text-4xl font-light text-stone-900">
              Catalogo Vini ({{ (filteredProducts || []).length }})
            </h2>
          </div>

          <div class="flex items-center space-x-4">
            <NuxtLink v-if="canEdit" to="/dashboard/prodotti/nuovo" class="inline-flex items-center space-x-1.5 px-4 py-2 bg-wine-800 hover:bg-wine-900 text-white text-xs font-bold rounded-xl shadow-xs transition-all">
              <Plus class="w-4 h-4 text-amber-200" />
              <span>Aggiungi Vino</span>
            </NuxtLink>
          </div>
        </div>

        <!-- Category Filter Pills -->
        <div class="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
          <button 
            v-for="cat in categoryTabs" 
            :key="cat.value"
            @click="selectedCategory = cat.value"
            :class="[
              'px-4 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all border',
              selectedCategory === cat.value
                ? 'bg-wine-900 text-white border-wine-900 shadow-xs'
                : 'bg-white text-stone-600 border-stone-200 hover:bg-stone-50'
            ]"
          >
            {{ cat.label }} ({{ cat.count }})
          </button>
        </div>

        <!-- Wines Grid -->
        <div v-if="filteredProducts && filteredProducts.length" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8">
          <ProductCard v-for="prod in filteredProducts" :key="prod.id" :product="prod" />
        </div>

        <div v-else class="text-center py-20 bg-white rounded-3xl border border-stone-200/60 p-8 space-y-3">
          <div class="w-14 h-14 rounded-2xl bg-stone-100 flex items-center justify-center mx-auto text-stone-400">
            <Wine class="w-7 h-7" />
          </div>
          <h3 class="font-serif text-xl font-bold text-stone-800">Nessun vino trovato in questa categoria</h3>
          <p class="text-sm text-stone-500 font-light max-w-md mx-auto">
            Seleziona una categoria differente per visualizzare i vini del catalogo di {{ producer.company_name }}.
          </p>
        </div>

      </div>

    </div>

    <!-- Contact Modal -->
    <InquiryModal 
      :is-open="isModalOpen" 
      :producer-id="producer.id"
      :producer-name="producer.company_name"
      :whatsapp-number="producer.contacts?.whatsapp_number"
      @close="isModalOpen = false"
    />

  </div>
</template>

<script setup>
import { 
  ShieldCheck, Pencil, MapPin, Phone, Mail, Globe, MessageSquare, 
  Plus, Wine, ChevronRight, Building2, Share2, Instagram, Facebook 
} from 'lucide-vue-next'

const route = useRoute()
const { fetchWithAuth, mediaBase } = useApi()
const { user, isAdmin, isAuthenticated } = useAuth()
const { getWhatsAppUrl, formatWebsiteUrl } = useWhatsApp()

const isModalOpen = ref(false)
const selectedCategory = ref('ALL')

const { data: producer, pending } = await useAsyncData(`producer_${route.params.slug}`, async () => {
  try {
    const res = await fetchWithAuth(`/producers/${route.params.slug}`)
    return res || null
  } catch (err) {
    return null
  }
}, { default: () => null })

watchEffect(() => {
  if (producer.value) {
    useSeoMeta({
      title: `${producer.value.company_name} - Cantina del Molise`,
      description: producer.value.description || `Scopri la cantina ${producer.value.company_name} a ${producer.value.address?.city || 'Molise'}. Vini, storia e contatti su EnotecaMolise.`
    })
  }
})

const canEdit = computed(() => {
  if (!isAuthenticated.value || !producer.value) return false
  if (isAdmin.value) return true
  const userProdId = user.value?.producer_id || user.value?.producer?.id
  return userProdId && String(userProdId) === String(producer.value.id)
})

const { data: producerProducts } = await useAsyncData(`producer_products_${route.params.slug}`, async () => {
  if (!producer.value?.id) return []
  const res = await fetchWithAuth(`/products?producer_id=${producer.value.id}&status=PUBLISHED`)
  return res || []
}, { watch: [producer], default: () => [] })

const categoryTabs = computed(() => {
  const prods = producerProducts.value || []
  return [
    { label: 'Tutti i Vini', value: 'ALL', count: prods.length },
    { label: 'Vini Rossi', value: 'VINO_ROSSO', count: prods.filter(p => p.category === 'VINO_ROSSO').length },
    { label: 'Vini Bianchi', value: 'VINO_BIANCO', count: prods.filter(p => p.category === 'VINO_BIANCO').length },
    { label: 'Vini Rosati', value: 'ROSATO', count: prods.filter(p => p.category === 'ROSATO').length },
    { label: 'Spumanti', value: 'SPUMANTE', count: prods.filter(p => p.category === 'SPUMANTE').length },
    { label: 'Dolci / Passiti', value: 'PASSITO', count: prods.filter(p => p.category === 'PASSITO').length }
  ].filter(tab => tab.value === 'ALL' || tab.count > 0)
})

const filteredProducts = computed(() => {
  const prods = producerProducts.value || []
  if (selectedCategory.value === 'ALL') return prods
  return prods.filter(p => p.category === selectedCategory.value)
})

const formatSocialUrl = (handleOrUrl, platform) => {
  if (!handleOrUrl) return '#'
  if (handleOrUrl.startsWith('http')) return handleOrUrl
  const clean = handleOrUrl.replace('@', '')
  return platform === 'instagram' 
    ? `https://instagram.com/${clean}` 
    : `https://facebook.com/${clean}`
}

const logoImage = computed(() => {
  if (producer.value?.logo_url) {
    return producer.value.logo_url.startsWith('http') ? producer.value.logo_url : `${mediaBase}${producer.value.logo_url}`
  }
  return 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=300&q=80'
})

const coverImage = computed(() => {
  if (producer.value?.cover_image_url && !producer.value.cover_image_url.includes('photo-1506377247377')) {
    return producer.value.cover_image_url.startsWith('http') ? producer.value.cover_image_url : `${mediaBase}${producer.value.cover_image_url}`
  }
  return 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=1600&q=80'
})
</script>
