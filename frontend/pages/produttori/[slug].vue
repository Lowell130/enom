<template>
  <div v-if="pending" class="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    <div class="h-96 bg-stone-200/50 animate-pulse rounded-2xl"></div>
  </div>

  <div v-else-if="producer" class="pb-20">
    
    <!-- Top Action Bar for Admin or Producer Owner -->
    <div v-if="canEdit" class="bg-amber-500/10 border-b border-amber-500/20 py-3 px-4 sm:px-8">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div class="flex items-center space-x-2 text-amber-900 text-xs font-semibold">
          <ShieldCheck class="w-4 h-4 text-amber-700" />
          <span>Sei autenticato come <strong class="underline">{{ isAdmin ? 'Super Admin' : 'Cantina Proprietaria' }}</strong>.</span>
        </div>
        <NuxtLink 
          :to="isAdmin ? '/dashboard/cantine' : '/dashboard/profilo'" 
          class="inline-flex items-center space-x-1 px-4 py-1.5 bg-wine-800 hover:bg-wine-900 text-white font-bold text-xs rounded-xl shadow-xs transition-all"
        >
          <Pencil class="w-3.5 h-3.5 text-amber-200" />
          <span>Modifica Dati Cantina</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Hero Header -->
    <div class="relative bg-wine-950 text-white py-24 overflow-hidden">
      <img 
        :src="coverImage" 
        :alt="producer.company_name" 
        class="absolute inset-0 w-full h-full object-cover opacity-30"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-wine-950 via-wine-950/70 to-transparent"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="flex flex-col md:flex-row items-start md:items-end space-y-4 md:space-y-0 md:space-x-6">
          <div class="w-24 h-24 rounded-2xl bg-white p-2 shadow-xl overflow-hidden flex-shrink-0 border-2 border-amber-500/50">
            <img :src="logoImage" :alt="producer.company_name" class="w-full h-full object-cover rounded-xl" />
          </div>
          <div class="space-y-1">
            <span class="text-xs font-semibold text-amber-300 uppercase tracking-widest inline-flex items-center space-x-1">
              <MapPin class="w-3.5 h-3.5" />
              <span>{{ producer.address?.city }} ({{ producer.address?.province }})</span>
            </span>
            <h1 class="font-serif text-4xl sm:text-6xl font-light tracking-tight text-white">
              {{ producer.company_name }}
            </h1>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-12">
      <div class="grid grid-cols-1 lg:grid-cols-12 gap-12">
        
        <!-- Left Sidebar: Info & Contacts -->
        <div class="lg:col-span-4 space-y-6">
          
          <div class="bg-white rounded-2xl p-6 border border-stone-200/60 shadow-xs">
            <h3 class="font-serif text-xl font-semibold text-wine-950 mb-4 border-b border-stone-100 pb-3">
              Contatti Cantina
            </h3>
            
            <ul class="space-y-3 text-sm text-stone-700 font-light">
              <li v-if="producer.address?.street || producer.address?.city" class="flex items-start space-x-2">
                <MapPin class="w-4 h-4 text-wine-800 mt-0.5 flex-shrink-0" />
                <span>{{ producer.address?.street ? producer.address.street + ', ' : '' }}{{ producer.address?.zip_code ? producer.address.zip_code + ' ' : '' }}{{ producer.address?.city || 'Molise' }} ({{ producer.address?.province || 'CB' }})</span>
              </li>
              <li v-if="producer.contacts?.phone" class="flex items-center space-x-2">
                <Phone class="w-4 h-4 text-wine-800 flex-shrink-0" />
                <a :href="`tel:${producer.contacts.phone}`" class="text-wine-800 font-medium hover:underline">
                  {{ producer.contacts.phone }}
                </a>
              </li>
              <li v-if="producer.contacts?.email_contact" class="flex items-center space-x-2">
                <Mail class="w-4 h-4 text-wine-800 flex-shrink-0" />
                <a :href="`mailto:${producer.contacts.email_contact}`" class="text-wine-800 font-medium hover:underline truncate">
                  {{ producer.contacts.email_contact }}
                </a>
              </li>
              <li v-if="producer.contacts?.website" class="flex items-center space-x-2">
                <Globe class="w-4 h-4 text-wine-800 flex-shrink-0" />
                <a :href="formatWebsiteUrl(producer.contacts.website)" target="_blank" class="text-wine-800 font-medium hover:underline truncate">
                  {{ producer.contacts.website }}
                </a>
              </li>
            </ul>

            <div class="mt-6 pt-4 border-t border-stone-100 space-y-2.5">
              <button 
                @click="isModalOpen = true" 
                class="w-full inline-flex items-center justify-center space-x-2 py-3 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-xs font-semibold transition-all shadow-xs"
              >
                <MessageSquare class="w-4 h-4 text-amber-200" />
                <span>Invia un messaggio diretto</span>
              </button>

              <a 
                v-if="producer.contacts?.whatsapp_number"
                :href="getWhatsAppUrl({ number: producer.contacts.whatsapp_number, companyName: producer.company_name })" 
                target="_blank"
                class="w-full inline-flex items-center justify-center space-x-2 py-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-semibold transition-all shadow-xs"
              >
                <MessageSquare class="w-4 h-4 text-emerald-200" />
                <span>WhatsApp Diretto</span>
              </a>
            </div>
          </div>

          <!-- Description Box -->
          <div class="bg-white rounded-2xl p-6 border border-stone-200/60 shadow-xs space-y-2">
            <h3 class="font-serif text-xl font-semibold text-wine-950 mb-3">La Nostra Storia</h3>
            <p class="text-sm text-stone-600 leading-relaxed font-light">
              {{ producer.description || 'Nessuna descrizione specificata.' }}
            </p>
          </div>


        </div>

        <!-- Right Column: Winery Wines -->
        <div class="lg:col-span-8">
          <div class="flex items-center justify-between mb-6">
            <h2 class="font-serif text-3xl font-light text-stone-900">
              Produzione Vini ({{ producerProducts.length }})
            </h2>

            <NuxtLink v-if="canEdit" to="/dashboard/prodotti/nuovo" class="inline-flex items-center space-x-1 text-xs font-bold text-wine-800 hover:underline">
              <Plus class="w-4 h-4" />
              <span>Aggiungi Vino per questa Cantina</span>
            </NuxtLink>
          </div>

          <div v-if="producerProducts && producerProducts.length" class="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <ProductCard v-for="prod in producerProducts" :key="prod.id" :product="prod" />
          </div>

          <div v-else class="text-center py-16 bg-white rounded-2xl border border-stone-200/60 p-8">
            <div class="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-3 text-stone-400">
              <Wine class="w-6 h-6" />
            </div>
            <p class="text-sm text-stone-500 font-light">Nessun vino inserito al momento per questa cantina.</p>
          </div>
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
import { ShieldCheck, Pencil, MapPin, Phone, Mail, Globe, MessageSquare, Plus, Wine } from 'lucide-vue-next'

const route = useRoute()
const { fetchWithAuth, mediaBase } = useApi()
const { user, isAdmin, isAuthenticated } = useAuth()
const { getWhatsAppUrl, formatWebsiteUrl } = useWhatsApp()

const isModalOpen = ref(false)

const { data: producer, pending } = await useAsyncData(`producer_${route.params.slug}`, () => 
  fetchWithAuth(`/producers/${route.params.slug}`)
)

const canEdit = computed(() => {
  if (!isAuthenticated.value || !producer.value) return false
  if (isAdmin.value) return true
  const userProdId = user.value?.producer_id || user.value?.producer?.id
  return userProdId && String(userProdId) === String(producer.value.id)
})

const { data: producerProducts } = await useAsyncData(`producer_products_${route.params.slug}`, async () => {
  if (!producer.value) return []
  return await fetchWithAuth(`/products?producer_id=${producer.value.id}&status=PUBLISHED`)
}, { watch: [producer] })

const logoImage = computed(() => {
  if (producer.value?.logo_url) {
    return producer.value.logo_url.startsWith('http') ? producer.value.logo_url : `${mediaBase}${producer.value.logo_url}`
  }
  return 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=300&q=80'
})

const coverImage = computed(() => {
  if (producer.value?.cover_image_url) {
    return producer.value.cover_image_url.startsWith('http') ? producer.value.cover_image_url : `${mediaBase}${producer.value.cover_image_url}`
  }
  return 'https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?auto=format&fit=crop&w=1200&q=80'
})
</script>
