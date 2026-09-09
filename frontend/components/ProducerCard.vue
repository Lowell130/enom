<template>
  <div class="bg-white rounded-2xl border border-stone-200/60 shadow-xs hover:shadow-md transition-all duration-300 overflow-hidden flex flex-col group">
    
    <!-- Cover Image -->
    <div class="h-44 bg-wine-950 relative overflow-hidden">
      <img 
        :src="coverImage" 
        :alt="producer.company_name" 
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-75"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-stone-900/60 via-stone-900/20 to-transparent"></div>
    </div>

    <!-- Content -->
    <div class="p-6 pt-0 flex-1 flex flex-col justify-between relative z-10">
      <div>
        <div class="flex items-end space-x-4 mb-4">
          <div class="w-16 h-16 -mt-8 rounded-xl bg-white p-1 shadow-md border border-stone-100/90 overflow-hidden flex-shrink-0 relative z-10">
            <img :src="logoImage" :alt="producer.company_name" class="w-full h-full object-cover rounded-lg" />
          </div>
          <div class="pt-3 min-w-0 flex-1">
            <h3 class="font-serif text-xl font-bold text-stone-900 leading-snug group-hover:text-wine-800 transition-colors truncate">
              {{ producer.company_name }}
            </h3>
            <p class="text-xs text-stone-500 font-medium inline-flex items-center space-x-1 mt-1">
              <MapPin class="w-3.5 h-3.5 text-wine-800 flex-shrink-0" />
              <span class="truncate">{{ producer.address?.city || 'Molise' }} ({{ producer.address?.province || 'CB' }})</span>
            </p>
          </div>
        </div>

        <p class="text-sm text-stone-600 line-clamp-3 leading-relaxed mt-2 font-light">
          {{ producer.description }}
        </p>
      </div>

      <div class="mt-6 pt-4 border-t border-stone-100 flex items-center justify-between gap-2 flex-wrap">
        <div class="flex items-center space-x-2">
          <span class="inline-flex items-center space-x-1 text-xs font-semibold text-wine-800 bg-wine-50 px-3 py-1.5 rounded-full border border-wine-100">
            <Wine class="w-3.5 h-3.5 text-wine-800" />
            <span>{{ producer.product_count || 0 }} Vini</span>
          </span>

          <a 
            v-if="producer.contacts?.website"
            :href="formatWebsiteUrl(producer.contacts.website)"
            target="_blank"
            class="p-1.5 text-stone-500 hover:text-wine-800 bg-stone-100 hover:bg-wine-50 rounded-lg border border-stone-200/60 transition-colors"
            title="Visita il sito web della cantina"
          >
            <Globe class="w-3.5 h-3.5" />
          </a>

          <a 
            v-if="producer.contacts?.whatsapp_number"
            :href="getWhatsAppUrl({ number: producer.contacts.whatsapp_number, companyName: producer.company_name })"
            target="_blank"
            class="p-1.5 text-emerald-700 hover:text-emerald-800 bg-emerald-50 hover:bg-emerald-100 rounded-lg border border-emerald-200/60 transition-colors"
            title="Contatta via WhatsApp"
          >
            <MessageSquare class="w-3.5 h-3.5" />
          </a>
        </div>

        <NuxtLink 
          :to="`/produttori/${producer.slug}`" 
          class="inline-flex items-center space-x-1 text-sm font-bold text-wine-800 hover:text-wine-900 group-hover:translate-x-0.5 transition-transform"
        >
          <span>Vedi Cantina</span>
          <ChevronRight class="w-4 h-4" />
        </NuxtLink>
      </div>

    </div>

  </div>
</template>

<script setup>
import { MapPin, Wine, ChevronRight, Globe, MessageSquare } from 'lucide-vue-next'

const props = defineProps({
  producer: {
    type: Object,
    required: true
  }
})

const { mediaBase } = useApi()
const { getWhatsAppUrl, formatWebsiteUrl } = useWhatsApp()

const logoImage = computed(() => {
  if (props.producer.logo_url) {
    return props.producer.logo_url.startsWith('http') ? props.producer.logo_url : `${mediaBase}${props.producer.logo_url}`
  }
  return 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=300&q=80'
})

const coverImage = computed(() => {
  if (props.producer.cover_image_url) {
    return props.producer.cover_image_url.startsWith('http') ? props.producer.cover_image_url : `${mediaBase}${props.producer.cover_image_url}`
  }
  return 'https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb?auto=format&fit=crop&w=1200&q=80'
})
</script>
