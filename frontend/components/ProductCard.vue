<template>
  <div class="bg-white rounded-xl border border-stone-200/80 shadow-2xs hover:shadow-lg transition-all duration-300 flex flex-col overflow-hidden group">
    
    <!-- Product Image Header (Pure White Container) -->
    <div class="relative h-72 bg-white border-b border-stone-100 overflow-hidden flex items-center justify-center p-6">
      <img 
        :src="productImage" 
        :alt="product.name" 
        loading="lazy"
        class="h-full object-contain group-hover:scale-105 transition-transform duration-500"
      />
      
      <!-- Crisp Rectangular Badges (No Super Rounded Pills) -->
      <div class="absolute top-4 left-4 flex flex-wrap gap-1.5 z-10">
        <span class="px-2.5 py-1 text-xs font-bold tracking-wider uppercase rounded-md bg-wine-800 text-white shadow-2xs">
          {{ product.denominazione }}
        </span>
        <span v-if="product.is_riserva" class="px-2.5 py-1 text-xs font-bold rounded-md bg-amber-700 text-white shadow-2xs">
          Riserva
        </span>
        <span v-if="isOrganicProduct(product)" class="px-2.5 py-1 text-xs font-bold rounded-md bg-emerald-700 text-white shadow-2xs inline-flex items-center space-x-1">
          <Leaf class="w-3.5 h-3.5 text-emerald-200" />
          <span>Biologico</span>
        </span>
      </div>

      <div class="absolute top-4 right-4 z-10">
        <span :class="['px-2.5 py-1 text-xs font-semibold rounded-md border shadow-2xs transition-colors', getCategoryBadgeClass(product.category)]">
          {{ formatCategory(product.category) }}
        </span>
      </div>
    </div>

    <!-- Product Body -->
    <div class="p-6 flex-1 flex flex-col justify-between space-y-4">
      <div>
        <!-- Producer Name -->
        <NuxtLink 
          v-if="product.producer_slug" 
          :to="`/produttori/${product.producer_slug}`"
          class="inline-flex items-center space-x-1.5 text-xs font-bold text-wine-800 hover:underline uppercase tracking-wide mb-1"
        >
          <Building2 class="w-3.5 h-3.5 text-wine-800" />
          <span>{{ product.producer_name }}</span>
        </NuxtLink>

        <!-- Wine Name -->
        <h3 class="font-serif text-xl font-bold text-stone-900 line-clamp-1 group-hover:text-wine-800 transition-colors mt-0.5">
          {{ product.name }}
        </h3>

        <!-- Description -->
        <p class="text-sm text-stone-600 mt-2 line-clamp-2 leading-relaxed font-light">
          {{ product.description || 'Nessuna descrizione specificata.' }}
        </p>

        <!-- Food Pairings Pills -->
        <div v-if="product.food_pairings && product.food_pairings.length" class="mt-4 flex flex-wrap gap-1.5">
          <span 
            v-for="(pairing, idx) in product.food_pairings.slice(0, 2)" 
            :key="idx"
            class="inline-flex items-center space-x-1 text-xs bg-stone-100 text-stone-700 px-2.5 py-1 rounded-md font-medium border border-stone-200/50"
          >
            <Utensils class="w-3 h-3 text-stone-500" />
            <span>{{ pairing }}</span>
          </span>
        </div>
      </div>

      <!-- Footer action -->
      <div class="pt-4 border-t border-stone-100 flex items-center justify-between">
        <div class="text-sm text-stone-500 flex items-center space-x-1 font-medium">
          <Wine v-if="product.alcohol_degrees" class="w-4 h-4 text-wine-800" />
          <span v-if="product.alcohol_degrees">{{ product.alcohol_degrees }}% Vol</span>
        </div>

        <NuxtLink 
          :to="`/vini/${product.slug}`" 
          class="inline-flex items-center space-x-1 text-sm font-bold text-wine-800 hover:text-wine-900 group-hover:translate-x-0.5 transition-transform"
        >
          <span>Scheda Vino</span>
          <ChevronRight class="w-4 h-4" />
        </NuxtLink>
      </div>
    </div>

  </div>
</template>

<script setup>
import { Building2, Utensils, Wine, ChevronRight, Leaf } from 'lucide-vue-next'

const props = defineProps({
  product: {
    type: Object,
    required: true
  }
})

const { mediaBase } = useApi()
const { isOrganicProduct } = useOrganic()

const productImage = computed(() => {
  if (props.product.photos && props.product.photos.length > 0) {
    const url = props.product.photos[0]
    return url.startsWith('http') ? url : `${mediaBase}${url}`
  }
  return '/default_wine_bottle.jpg'
})

const { formatCategory, getCategoryBadgeClass } = useCategoryBadge()
</script>
