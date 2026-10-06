<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[900px]">
    <div class="mb-6">
      <NuxtLink to="/dashboard/eventi" class="text-sm font-semibold">← Torna agli eventi</NuxtLink>
      <h1 class="font-serif text-[40px] font-semibold leading-none text-ink mt-3">Modifica evento</h1>
      <p v-if="event" class="text-sm text-ink-soft mt-1.5 mb-0">
        <NuxtLink :to="`/eventi/${event.slug}`">Vedi la pagina pubblica →</NuxtLink>
      </p>
    </div>

    <div v-if="pending" class="card p-12 text-center text-sm text-ink-mute">Caricamento dell'evento…</div>
    <div v-else-if="!event || !event.can_edit" class="card p-10 text-center flex flex-col items-center gap-3">
      <p class="text-base font-semibold text-ink m-0">{{ event ? 'Non puoi modificare questo evento' : 'Evento non trovato' }}</p>
      <p v-if="event" class="text-sm text-ink-soft m-0">Lo può modificare solo chi lo organizza.</p>
      <NuxtLink to="/dashboard/eventi" class="btn-primary btn-sm h-11">Torna agli eventi</NuxtLink>
    </div>
    <EventForm v-else :key="event.id" :initial="event" @saved="onSaved" />
  </div>
</template>

<script setup>
import EventForm from '~/components/EventForm.vue'

const route = useRoute()
const { fetchWithAuth } = useApi()
const toast = useToast()

const { data: event, pending } = await useAsyncData(`dashboard_event_${route.params.id}`, async () => {
  try { return await fetchWithAuth(`/events/${route.params.id}`) } catch (e) { return null }
}, { default: () => null })

const onSaved = (ev) => {
  toast.success(ev.status === 'DRAFT' ? 'Evento salvato come bozza.' : 'Modifiche salvate.')
  navigateTo('/dashboard/eventi')
}
</script>
