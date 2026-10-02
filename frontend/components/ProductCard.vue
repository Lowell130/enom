<template>
  <article class="card overflow-hidden flex flex-col group">
    <!-- Immagine cliccabile verso la scheda del vino -->
    <NuxtLink :to="detailUrl" tabindex="-1" aria-hidden="true" class="relative block h-[240px] bg-sand overflow-hidden">
      <SafeImg
        :src="productImage"
        :alt="product.name"
        loading="lazy"
        class="bottle-photo w-full h-full object-contain p-5 group-hover:scale-[1.03] transition-transform duration-500"
      >
        <span class="absolute inset-0 flex items-center justify-center"><BottleIcon /></span>
      </SafeImg>
      <span class="absolute top-3 left-3 flex flex-wrap gap-1.5">
        <span v-if="product.denominazione" class="badge-denom">{{ product.denominazione }}</span>
        <span v-if="product.is_riserva" class="badge-soft">Riserva</span>
        <span v-if="isOrganicProduct(product)" class="badge-bio">Biologico</span>
      </span>
    </NuxtLink>

    <div class="flex flex-col gap-1.5 p-[18px] pb-5 flex-1">
      <span class="eyebrow-sm tracking-[0.06em]">{{ formatCategory(product.category) }}</span>
      <h3 class="title-card text-2xl">
        <NuxtLink :to="detailUrl" class="text-ink hover:text-wine-800">{{ product.name }}</NuxtLink>
      </h3>
      <NuxtLink
        v-if="showProducer && product.producer_slug"
        :to="`/produttori/${product.producer_slug}`"
        class="text-sm font-semibold text-wine-800 hover:text-wine-900 w-fit"
      >
        {{ product.producer_name }}
      </NuxtLink>
      <p v-else-if="!showProducer && product.description" class="text-sm text-ink-soft line-clamp-2">{{ product.description }}</p>

      <div class="flex items-center justify-between gap-3 mt-auto pt-3.5 border-t border-line-soft text-[13px] text-ink-soft">
        <span class="truncate">{{ details }}</span>
        <NuxtLink :to="detailUrl" class="font-bold text-wine-800 hover:text-wine-900 shrink-0" :aria-label="`Scheda di ${product.name}`">Scheda →</NuxtLink>
      </div>
    </div>
  </article>
</template>

<script setup>
const props = defineProps({
  product: { type: Object, required: true },
  // sulla pagina della cantina il nome del produttore e' superfluo
  showProducer: { type: Boolean, default: true }
})

const { mediaBase } = useApi()
const { isOrganicProduct } = useOrganic()
const { formatCategory } = useCategoryBadge()

const detailUrl = computed(() => `/vini/${props.product.slug}`)

const productImage = computed(() => {
  const url = props.product.photos?.[0]
  if (!url) return ''
  return url.startsWith('http') ? url : `${mediaBase}${url}`
})

const details = computed(() => {
  const grape = (props.product.grape_varieties || [])[0]
  const parts = []
  if (grape) parts.push(String(grape).replace(/\s*\d+\s*%/, '').trim())
  if (props.product.alcohol_degrees) parts.push(`${String(props.product.alcohol_degrees).replace('.', ',')}% vol`)
  return parts.join(' · ')
})
</script>
