<template>
  <div class="bg-white rounded-xl border border-stone-200/80 shadow-2xs hover:shadow-lg transition-all duration-300 overflow-hidden flex flex-col group">
    
    <!-- Cover Header -->
    <div class="h-48 sm:h-52 bg-stone-950 relative overflow-hidden">
      <img 
        :src="coverImage" 
        :alt="producer.company_name" 
        loading="lazy"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 opacity-80"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-stone-950/80 via-stone-950/30 to-transparent"></div>

      <!-- Top Badges Overlay (Crisp Badges, No Super Rounded Pills) -->
      <div class="absolute top-4 left-4 right-4 flex items-center justify-between z-10 gap-2">
        <span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-stone-950/80 backdrop-blur-md text-amber-200 border border-amber-400/30 text-xs font-semibold">
          <MapPin class="w-3.5 h-3.5 text-amber-400" />
          <span>{{ producer.address?.city || 'Molise' }} ({{ producer.address?.province || 'CB' }})</span>
        </span>

        <span class="inline-flex items-center space-x-1 px-2.5 py-1 rounded-md bg-wine-900/90 backdrop-blur-md text-white border border-wine-400/30 text-xs font-bold">
          <Wine class="w-3.5 h-3.5 text-amber-300" />
          <span>{{ producer.product_count || 0 }} {{ producer.product_count === 1 ? 'Vino' : 'Vini' }}</span>
        </span>
      </div>

      <!-- Bottom-Right Contact Icons on Cover -->
      <div class="absolute bottom-3 right-4 flex items-center space-x-1.5 z-10">
        <a 
          v-if="producer.contacts?.website"
          :href="formatWebsiteUrl(producer.contacts.website)"
          target="_blank"
          class="p-2 text-stone-200 hover:text-white bg-stone-900/70 hover:bg-wine-800 backdrop-blur-md rounded-md border border-white/20 transition-all"
          title="Sito Web Cantina"
        >
          <Globe class="w-3.5 h-3.5" />
        </a>

        <a 
          v-if="producer.contacts?.whatsapp_number"
          :href="getWhatsAppUrl({ number: producer.contacts.whatsapp_number, companyName: producer.company_name })"
          target="_blank"
          class="p-2 text-emerald-300 hover:text-white bg-emerald-950/70 hover:bg-emerald-700 backdrop-blur-md rounded-md border border-emerald-400/30 transition-all"
          title="WhatsApp Diretto"
        >
          <MessageSquare class="w-3.5 h-3.5" />
        </a>

        <a 
          v-if="producer.contacts?.instagram"
          :href="formatSocialUrl(producer.contacts.instagram, 'instagram')"
          target="_blank"
          class="p-2 text-pink-300 hover:text-white bg-stone-900/70 hover:bg-pink-700 backdrop-blur-md rounded-md border border-white/20 transition-all"
          title="Instagram Cantina"
        >
          <Instagram class="w-3.5 h-3.5" />
        </a>

        <a 
          v-if="producer.contacts?.facebook"
          :href="formatSocialUrl(producer.contacts.facebook, 'facebook')"
          target="_blank"
          class="p-2 text-blue-300 hover:text-white bg-stone-900/70 hover:bg-blue-700 backdrop-blur-md rounded-md border border-white/20 transition-all"
          title="Facebook Cantina"
        >
          <Facebook class="w-3.5 h-3.5" />
        </a>
      </div>
    </div>

    <!-- Card Content -->
    <div class="px-6 pb-6 pt-0 flex-1 flex flex-col justify-between relative z-10">
      <div>
        <!-- Logo overlapping cover image -->
        <div class="-mt-10 mb-3 relative z-10 flex items-end">
          <div class="w-20 h-20 rounded-xl bg-white p-1.5 shadow-md border border-stone-200 overflow-hidden flex-shrink-0 group-hover:border-wine-800 transition-colors">
            <img :src="logoImage" :alt="producer.company_name" loading="lazy" class="w-full h-full object-cover rounded-lg" />
          </div>
        </div>

        <!-- Winery Name -->
        <NuxtLink :to="`/produttori/${producer.slug}`" class="block">
          <h3 class="font-serif text-2xl font-bold text-stone-900 group-hover:text-wine-800 transition-colors leading-tight">
            {{ producer.company_name }}
          </h3>
        </NuxtLink>

        <!-- Description -->
        <p class="text-sm text-stone-600 line-clamp-3 leading-relaxed mt-2.5 font-light">
          {{ producer.description || 'Cantina vinicola d\'eccellenza nel cuore del territorio molisano.' }}
        </p>
      </div>

      <!-- Action Footer -->
      <div class="mt-6 pt-4 border-t border-stone-100 flex items-center justify-between">
        <div class="text-xs font-semibold text-stone-500 uppercase tracking-wider flex items-center space-x-1">
          <Building2 class="w-3.5 h-3.5 text-wine-800" />
          <span>{{ producer.address?.city || 'Molise' }}</span>
        </div>

        <NuxtLink 
          :to="`/produttori/${producer.slug}`" 
          class="inline-flex items-center space-x-2 px-4 py-2 bg-wine-800 hover:bg-wine-900 text-white rounded-md text-xs font-bold transition-all shadow-2xs group-hover:bg-wine-900"
        >
          <span>Scopri Cantina</span>
          <ChevronRight class="w-3.5 h-3.5" />
        </NuxtLink>
      </div>

    </div>

  </div>
</template>

<script setup>
import { MapPin, Wine, ChevronRight, Globe, MessageSquare, Building2, Instagram, Facebook } from 'lucide-vue-next'

const props = defineProps({
  producer: {
    type: Object,
    required: true
  }
})

const { mediaBase } = useApi()
const { getWhatsAppUrl, formatWebsiteUrl } = useWhatsApp()

const formatSocialUrl = (handleOrUrl, platform) => {
  if (!handleOrUrl) return '#'
  if (handleOrUrl.startsWith('http')) return handleOrUrl
  const clean = handleOrUrl.replace('@', '')
  return platform === 'instagram' 
    ? `https://instagram.com/${clean}` 
    : `https://facebook.com/${clean}`
}

const logoImage = computed(() => {
  if (props.producer.logo_url) {
    return props.producer.logo_url.startsWith('http') ? props.producer.logo_url : `${mediaBase}${props.producer.logo_url}`
  }
  return 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=300&q=80'
})

const coverImage = computed(() => {
  if (props.producer.cover_image_url && !props.producer.cover_image_url.includes('photo-1506377247377')) {
    return props.producer.cover_image_url.startsWith('http') ? props.producer.cover_image_url : `${mediaBase}${props.producer.cover_image_url}`
  }
  return 'https://images.unsplash.com/photo-1560493676-04071c5f467b?auto=format&fit=crop&w=1600&q=80'
})
</script>
