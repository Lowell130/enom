<template>
  <!-- Pagina di errore del sito (indirizzo inesistente o errore imprevisto), nella grafica del sito -->
  <NuxtLayout>
    <section class="page-container py-12 md:py-20 grid grid-cols-1 gap-10 lg:grid-cols-2 lg:gap-14 items-center">
      <div class="flex flex-col gap-5">
        <span class="eyebrow">{{ notFound ? 'Errore 404' : `Errore ${statusCode}` }}</span>
        <h1 class="font-serif font-semibold text-ink text-[40px] md:text-[56px] leading-[1.04] text-balance">
          {{ notFound ? 'Questa pagina non esiste' : 'Qualcosa è andato storto' }}
        </h1>
        <p class="text-lg text-ink-soft max-w-[520px]">
          <template v-if="notFound">
            L'indirizzo potrebbe essere sbagliato oppure la pagina è stata spostata. Prova a cercare il vino o la cantina che ti interessa.
          </template>
          <template v-else>
            Si è verificato un problema imprevisto. Riprova tra qualche istante: se il problema continua, torna alla home.
          </template>
        </p>

        <form v-if="notFound" role="search" class="flex flex-col gap-2 max-w-[520px]" @submit.prevent="search">
          <label for="error-search" class="text-[13px] font-semibold text-ink-soft">Cerca nel catalogo</label>
          <div class="flex gap-2 p-1.5 border border-line-strong rounded-[14px] bg-white focus-within:border-wine-800">
            <input
              id="error-search"
              v-model="query"
              type="search"
              placeholder="Vino, cantina o vitigno"
              class="flex-1 min-w-0 px-3 bg-transparent text-base text-ink placeholder:text-ink-mute/70 focus:outline-none [&::-webkit-search-cancel-button]:appearance-none"
            />
            <button type="submit" class="btn-primary h-11 px-5">Cerca</button>
          </div>
        </form>

        <div class="flex flex-wrap gap-2.5 pt-1">
          <button type="button" class="btn-outline btn-sm h-11" @click="goTo('/')">Torna alla home</button>
          <button type="button" class="btn-ghost btn-sm h-11" @click="goTo('/vini')">Tutti i vini</button>
          <button type="button" class="btn-ghost btn-sm h-11" @click="goTo('/produttori')">Le cantine</button>
          <button v-if="!notFound" type="button" class="btn-ghost btn-sm h-11" @click="reload">Riprova</button>
        </div>

        <p v-if="showDetails" class="text-xs text-ink-mute font-mono break-all">{{ error?.message }}</p>
      </div>

      <figure class="m-0 w-full aspect-[5/4] rounded-[20px] overflow-hidden bg-sand-300 hidden sm:block">
        <HeroArt />
      </figure>
    </section>
  </NuxtLayout>
</template>

<script setup>
import HeroArt from '~/components/HeroArt.vue'

const props = defineProps({
  error: { type: Object, default: null }
})

const statusCode = computed(() => Number(props.error?.statusCode || props.error?.status) || 500)
const notFound = computed(() => statusCode.value === 404)
// il dettaglio tecnico serve solo in sviluppo
const showDetails = computed(() => import.meta.dev && !notFound.value && props.error?.message)

useSeoMeta({
  title: () => (notFound.value ? 'Pagina non trovata' : 'Errore') + ' - EnotecaMolise',
  robots: 'noindex'
})

const query = ref('')
const goTo = (path) => clearError({ redirect: path })
const search = () => {
  const q = query.value.trim()
  clearError({ redirect: q ? `/vini?search=${encodeURIComponent(q)}` : '/vini' })
}
const reload = () => {
  if (import.meta.client) window.location.reload()
}
</script>
