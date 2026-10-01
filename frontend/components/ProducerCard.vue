<template>
  <article class="card overflow-hidden flex flex-col group">
    <NuxtLink
      :to="detailUrl"
      tabindex="-1"
      aria-hidden="true"
      class="relative block h-[170px] overflow-hidden"
      :style="{ background: tone(producer.company_name) }"
    >
      <SafeImg :src="cover" alt="" loading="lazy" class="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-700" />
      <span class="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-white text-ink text-xs font-bold">{{ countLabel(producer.product_count) }}</span>
    </NuxtLink>

    <div class="relative px-5 pb-5 flex flex-col gap-2 flex-1">
      <span class="-mt-8 w-16 h-16 rounded-[14px] border-[3px] border-white bg-sand-100 overflow-hidden flex items-center justify-center font-serif text-2xl font-bold text-wine-800">
        <SafeImg :src="logo" :alt="`Logo ${producer.company_name}`" loading="lazy" class="w-full h-full object-cover">{{ initials(producer.company_name) }}</SafeImg>
      </span>
      <h3 class="title-card text-[26px] mt-1">
        <NuxtLink :to="detailUrl" class="text-ink hover:text-wine-800">{{ producer.company_name }}</NuxtLink>
      </h3>
      <span class="flex items-center gap-1.5 text-sm text-ink-soft">
        <MapPin class="w-[15px] h-[15px]" aria-hidden="true" />
        {{ place(producer) }}
      </span>
      <p v-if="producer.description" class="text-sm text-ink-soft line-clamp-2">{{ producer.description }}</p>
      <NuxtLink :to="detailUrl" class="mt-auto pt-2 text-sm font-bold text-wine-800 hover:text-wine-900 w-fit">Scopri la cantina →</NuxtLink>
    </div>
  </article>
</template>

<script setup>
import { MapPin } from 'lucide-vue-next'

const props = defineProps({
  producer: { type: Object, required: true }
})

const { coverUrl, logoUrl, initials, tone, place, countLabel } = useProducer()

const detailUrl = computed(() => `/produttori/${props.producer.slug}`)
const cover = computed(() => coverUrl(props.producer))
const logo = computed(() => logoUrl(props.producer))
</script>
