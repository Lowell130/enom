<template>
  <section class="page-container pt-10 md:pt-14 pb-20">
    <div class="max-w-[760px] flex flex-col gap-6">
      <nav aria-label="Percorso" class="text-[13px] text-ink-mute">
        <NuxtLink to="/" class="hover:text-wine-800">Home</NuxtLink> / <span class="text-ink font-semibold">Chi siamo</span>
      </nav>
      <h1 class="title-display">{{ page?.title || 'Chi siamo' }}</h1>
      <RichText v-if="page" :text="page.body" />
      <p v-else class="text-ink-soft">Il testo non è al momento disponibile.</p>
      <div class="flex flex-wrap gap-3 pt-2">
        <NuxtLink to="/vini" class="btn-primary">Scopri i vini</NuxtLink>
        <NuxtLink to="/produttori" class="btn-outline">Le cantine</NuxtLink>
      </div>
    </div>
  </section>
</template>

<script setup>
import RichText from '~/components/RichText.vue'

const { fetchWithAuth } = useApi()
const { data: page } = await useAsyncData('site_page_chi_siamo', () => fetchWithAuth('/site/pages/chi-siamo').catch(() => null))

useSeoMeta({ title: 'Chi siamo - EnotecaMolise', robots: 'noindex' })
</script>
