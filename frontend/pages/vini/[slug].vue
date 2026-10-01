<template>
  <div v-if="pending" class="page-container py-12">
    <div class="h-96 rounded-[22px] bg-sand animate-pulse"></div>
  </div>

  <div v-else-if="product">
    <!-- Barra per amministratore o cantina proprietaria -->
    <div v-if="canEdit" class="bg-sand-100 border-b border-line">
      <div class="page-container py-2.5 flex flex-wrap items-center justify-between gap-3 text-sm">
        <span class="text-ink-soft">Stai vedendo la scheda pubblica come <strong class="text-ink">{{ isAdmin ? 'amministratore' : 'cantina proprietaria' }}</strong>.</span>
        <NuxtLink :to="`/dashboard/prodotti/edit-${product.id}`" class="btn-ghost btn-sm">
          <Pencil class="w-4 h-4" aria-hidden="true" /> Modifica scheda vino
        </NuxtLink>
      </div>
    </div>

    <nav aria-label="Percorso" class="page-container pt-4 flex flex-wrap gap-2 text-[13px] text-ink-mute">
      <NuxtLink to="/" class="text-ink-mute hover:text-wine-800">Home</NuxtLink><span aria-hidden="true">/</span>
      <NuxtLink to="/vini" class="text-ink-mute hover:text-wine-800">Vini</NuxtLink><span aria-hidden="true">/</span>
      <span class="text-ink font-semibold">{{ product.name }}</span>
    </nav>

    <!-- PRODOTTO -->
    <section class="page-container pt-6 pb-14 md:pb-16 grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-12 items-start">
      <div class="relative rounded-[22px] bg-sand min-h-[420px] lg:min-h-[600px] flex items-center justify-center lg:sticky lg:top-24">
        <SafeImg :src="mainImage" :alt="product.name" class="max-h-[540px] w-full object-contain p-8"><BottleIcon :size="256" /></SafeImg>
        <span class="absolute top-4 left-4 flex flex-wrap gap-1.5">
          <span v-if="product.is_riserva" class="badge-soft">Riserva</span>
          <span v-if="isOrganicProduct(product)" class="badge-bio"><Leaf class="w-3.5 h-3.5" aria-hidden="true" /> Biologico</span>
        </span>
      </div>

      <div class="flex flex-col gap-[22px]">
        <NuxtLink v-if="product.producer_slug" :to="`/produttori/${product.producer_slug}`" class="flex items-center gap-3 text-ink w-fit">
          <span class="w-11 h-11 rounded-xl bg-sand-100 overflow-hidden flex items-center justify-center font-serif text-lg font-bold text-wine-800">
            <SafeImg :src="producerLogo" alt="" class="w-full h-full object-cover">{{ initials(product.producer_name) }}</SafeImg>
          </span>
          <span class="flex flex-col leading-tight">
            <span class="text-[15px] font-bold">{{ product.producer_name }}</span>
            <span class="text-[13px] text-ink-mute">{{ producer ? place(producer) + ' · ' : '' }}vedi la cantina</span>
          </span>
        </NuxtLink>

        <div class="flex flex-col gap-3">
          <div class="flex flex-wrap gap-1.5">
            <span v-if="product.denominazione" class="badge-denom text-xs px-2.5 py-1">{{ product.denominazione }}</span>
            <span class="badge-soft text-xs px-2.5 py-1">{{ formatCategory(product.category) }}</span>
            <span v-if="product.vintage_year" class="badge-soft text-xs px-2.5 py-1">Annata {{ product.vintage_year }}</span>
          </div>
          <h1 class="font-serif font-semibold text-ink text-[42px] md:text-[60px] leading-none">{{ product.name }}</h1>
        </div>

        <dl v-if="keyFacts.length" class="grid grid-cols-2 sm:grid-cols-4 gap-x-4 border-y border-line">
          <div v-for="fact in keyFacts" :key="fact.label" class="py-3.5 flex flex-col gap-0.5">
            <dt class="eyebrow-sm tracking-[0.08em]">{{ fact.label }}</dt>
            <dd class="text-[17px] font-semibold text-ink">{{ fact.value }}</dd>
          </div>
        </dl>

        <p v-if="product.description" class="text-[17px] text-ink-soft text-pretty whitespace-pre-line">{{ product.description }}</p>

        <div class="flex flex-col gap-2.5 p-5 rounded-2xl bg-white border border-line">
          <div class="flex flex-wrap gap-2.5">
            <button type="button" class="btn-primary h-[52px] flex-1 text-base" @click="isModalOpen = true">
              <Mail class="w-[18px] h-[18px]" aria-hidden="true" /> Chiedi prezzo e disponibilità
            </button>
            <a v-if="product.technical_sheet_pdf" :href="pdfUrl" target="_blank" rel="noopener" class="btn-ghost h-[52px]">
              <FileDown class="w-[18px] h-[18px]" aria-hidden="true" /> Scheda tecnica PDF
            </a>
          </div>
          <span class="text-[13px] text-ink-mute">Risponde direttamente {{ product.producer_name || 'la cantina' }}, senza intermediari.</span>
        </div>
      </div>
    </section>

    <!-- DEGUSTAZIONE E ABBINAMENTI -->
    <section v-if="tastingNotes.length || (product.food_pairings || []).length" class="bg-sand py-12 md:py-16">
      <div class="page-container flex flex-col gap-6">
        <template v-if="tastingNotes.length">
          <h2 class="title-section text-[32px] md:text-[40px]">Note di degustazione</h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div v-for="note in tastingNotes" :key="note.label" class="p-6 rounded-2xl bg-white flex flex-col gap-2.5">
              <span class="flex items-center gap-2.5 eyebrow-sm text-[13px]">
                <component :is="note.icon" class="w-5 h-5" aria-hidden="true" /> {{ note.label }}
              </span>
              <p class="text-base text-ink">{{ note.text }}</p>
            </div>
          </div>
        </template>
        <div v-if="(product.food_pairings || []).length" class="flex flex-col gap-2.5 mt-2">
          <span class="eyebrow-sm text-[13px]">Abbinamenti</span>
          <div class="flex flex-wrap gap-2">
            <NuxtLink v-for="pairing in product.food_pairings" :key="pairing" :to="`/vini?search=${encodeURIComponent(pairing)}`" class="chip-outline">{{ pairing }}</NuxtLink>
          </div>
        </div>
      </div>
    </section>

    <!-- SCHEDA TECNICA -->
    <section v-if="displaySpecs.length" class="page-container py-12 md:py-16 flex flex-col gap-6">
      <h2 class="title-section text-[32px] md:text-[40px]">Scheda tecnica</h2>
      <dl class="grid grid-cols-1 lg:grid-cols-2 gap-x-12">
        <div v-for="(item, idx) in displaySpecs" :key="idx" class="flex justify-between gap-4 py-[13px] border-b border-line text-[15px]">
          <dt class="text-ink-mute">{{ item.name }}</dt>
          <dd class="font-semibold text-right">{{ item.value }}</dd>
        </div>
      </dl>
    </section>

    <!-- ALTRI VINI DELLA CANTINA -->
    <section v-if="otherWineryProducts.length" class="bg-white border-t border-line py-12 md:py-16">
      <div class="page-container">
        <div class="flex flex-wrap items-end justify-between gap-5 mb-6">
          <div class="flex flex-col gap-2">
            <span class="eyebrow">Dalla stessa cantina</span>
            <h2 class="title-section text-[32px] md:text-[40px]">Altri vini di {{ product.producer_name }}</h2>
          </div>
          <NuxtLink v-if="product.producer_slug" :to="`/produttori/${product.producer_slug}`" class="text-[15px] font-bold">Tutti i {{ (wineryProducts || []).length }} vini →</NuxtLink>
        </div>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <ProductCard v-for="otherProd in otherWineryProducts.slice(0, 4)" :key="otherProd.id" :product="otherProd" :show-producer="false" />
        </div>
      </div>
    </section>

    <InquiryModal
      :is-open="isModalOpen"
      :producer-id="product.producer_id"
      :producer-name="product.producer_name"
      :product-id="product.id"
      :product-name="product.name"
      @close="isModalOpen = false"
    />
  </div>

  <div v-else class="page-container py-24 text-center flex flex-col items-center gap-4">
    <h1 class="title-section">Vino non trovato</h1>
    <p class="text-ink-soft max-w-md">La scheda richiesta non è ancora nel catalogo oppure l'indirizzo non è corretto.</p>
    <NuxtLink to="/vini" class="btn-primary">Torna al catalogo</NuxtLink>
  </div>
</template>

<script setup>
import { Pencil, Mail, FileDown, Eye, Droplet, Wine, Leaf } from 'lucide-vue-next'

const route = useRoute()
const { fetchWithAuth, mediaBase } = useApi()
const { user, isAdmin, isAuthenticated } = useAuth()
const { formatCategory } = useCategoryBadge()
const { logoUrl, initials, place } = useProducer()
const { isOrganicProduct } = useOrganic()

const isModalOpen = ref(false)


const { data: product, pending } = await useAsyncData(`product_${route.params.slug}`, async () => {
  try {
    const res = await fetchWithAuth(`/products/${route.params.slug}`)
    return res || null
  } catch (err) {
    return null
  }
}, { default: () => null })

// pagina "non trovato" con il codice giusto (404), anche per i motori di ricerca
if (!product.value) setResponseStatus(useRequestEvent(), 404)

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
  return ''
})

const pdfUrl = computed(() => {
  if (!product.value?.technical_sheet_pdf) return '#'
  const url = product.value.technical_sheet_pdf
  return url.startsWith('http') ? url : `${mediaBase}${url}`
})

const { data: producer } = await useAsyncData(`wine_producer_${route.params.slug}`, async () => {
  if (!product.value?.producer_slug) return null
  try {
    return await fetchWithAuth(`/producers/${product.value.producer_slug}`)
  } catch (err) {
    return null
  }
}, { default: () => null })

const producerLogo = computed(() => logoUrl(producer.value))

const findAttr = (re) => (product.value?.custom_attributes || []).find((a) => re.test(a?.name || '') && a?.value)?.value

const keyFacts = computed(() => {
  const p = product.value
  if (!p) return []
  const list = []
  if (p.grape_varieties?.length) list.push({ label: (p.grape_varieties.length > 1 ? 'Vitigni' : 'Vitigno'), value: p.grape_varieties.join(', ') })
  if (p.alcohol_degrees) list.push({ label: 'Gradazione', value: `${String(p.alcohol_degrees).replace('.', ',')}% vol` })
  if (p.serving_temperature) list.push({ label: 'Servizio', value: String(p.serving_temperature).replace(/\s*°?\s*C?\s*$/i, ' °C').replace(/-/g, '–') })
  const formato = findAttr(/^formato/i)
  if (formato) list.push({ label: 'Formato', value: formato })
  else if (p.indicative_price) list.push({ label: 'Prezzo indicativo', value: p.indicative_price })
  return list.slice(0, 4)
})

const tastingNotes = computed(() => {
  const n = product.value?.tasting_notes || {}
  return [
    { label: 'Vista', text: n.visual, icon: Eye },
    { label: 'Olfatto', text: n.olfactory, icon: Droplet },
    { label: 'Gusto', text: n.taste, icon: Wine }
  ].filter((x) => x.text)
})
</script>
