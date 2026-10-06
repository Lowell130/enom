<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[900px]">
    <div class="mb-6">
      <NuxtLink to="/dashboard/eventi" class="text-sm font-semibold">← Torna agli eventi</NuxtLink>
      <h1 class="font-serif text-[40px] font-semibold leading-none text-ink mt-3">Nuovo evento</h1>
      <p class="text-sm text-ink-soft mt-1.5 mb-0">Degustazione, visita, cena, vendemmia o festa: compila i dati e pubblicalo nel calendario del sito.</p>
    </div>
    <EventForm @saved="onSaved" />
  </div>
</template>

<script setup>
import EventForm from '~/components/EventForm.vue'

const toast = useToast()
const onSaved = (ev) => {
  toast.success(ev.status === 'DRAFT' ? 'Bozza salvata.' : 'Evento pubblicato.')
  navigateTo('/dashboard/eventi')
}
</script>
