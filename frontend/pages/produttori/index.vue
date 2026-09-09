<template>
  <div class="py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="mb-12 text-center max-w-2xl mx-auto space-y-2">
      <span class="text-xs font-bold uppercase tracking-widest text-wine-800">I Custodi del Territorio</span>
      <h1 class="font-serif text-4xl sm:text-5xl font-light text-stone-900">
        Le Cantine del Molise
      </h1>
      <p class="text-base text-stone-600 font-light">
        Scopri i produttori che mantengono viva la tradizione enologica molisana tra Campobasso ed Isernia.
      </p>
    </div>


    <div v-if="pending" class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <div v-for="i in 4" :key="i" class="h-64 bg-stone-200/50 animate-pulse rounded-2xl"></div>
    </div>

    <div v-else-if="producers && producers.length" class="grid grid-cols-1 md:grid-cols-2 gap-8">
      <ProducerCard v-for="producer in producers" :key="producer.id" :producer="producer" />
    </div>

    <div v-else class="text-center py-20 bg-white rounded-2xl border border-stone-200/60 p-8">
      <div class="w-12 h-12 rounded-full bg-stone-100 flex items-center justify-center mx-auto mb-3 text-stone-400">
        <Building2 class="w-6 h-6" />
      </div>
      <h3 class="font-serif text-xl font-bold text-stone-800">Nessuna cantina registrata</h3>
    </div>

  </div>
</template>

<script setup>
import { Building2 } from 'lucide-vue-next'
const { fetchWithAuth } = useApi()

const { data: producers, pending } = await useAsyncData('all_producers', () => 
  fetchWithAuth('/producers')
)
</script>
