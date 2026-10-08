<template>
  <section class="page-container pt-10 md:pt-14 pb-20">
    <div class="max-w-[760px] flex flex-col gap-6">
      <nav aria-label="Percorso" class="text-[13px] text-ink-mute">
        <NuxtLink to="/" class="hover:text-wine-800">Home</NuxtLink> / <span class="text-ink font-semibold">Cookie policy</span>
      </nav>
      <h1 class="title-display">{{ page?.title || 'Cookie policy' }}</h1>
      <RichText v-if="page" :text="page.body" />
      <p v-else class="text-ink-soft">Il testo non è al momento disponibile.</p>
      <div class="card p-5 flex flex-wrap items-center justify-between gap-4">
        <p class="m-0 text-sm text-ink-soft">
          La tua scelta attuale: <strong class="text-ink">{{ choiceLabel }}</strong>
        </p>
        <button type="button" class="btn-outline btn-sm" @click="openPreferences">Cambia le preferenze</button>
      </div>
    </div>
  </section>
</template>

<script setup>
import RichText from '~/components/RichText.vue'

const { fetchWithAuth } = useApi()
const { decided, allows, openPreferences } = useCookieConsent()
// scelta letta solo nel browser, per non mostrare un testo diverso tra server e pagina
const mounted = ref(false)
onMounted(() => { mounted.value = true })
const choiceLabel = computed(() => {
  if (!mounted.value) return '…'
  if (!decided.value) return 'nessuna scelta ancora'
  return allows('statistiche') ? 'cookie tecnici e di statistica' : 'solo cookie tecnici'
})
const { data: page } = await useAsyncData('site_page_cookie', () => fetchWithAuth('/site/pages/cookie').catch(() => null))

useSeoMeta({ title: 'Cookie policy - EnotecaMolise', robots: 'noindex' })
</script>
