<template>
  <section aria-labelledby="richieste-stat" class="flex flex-col gap-3">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div class="flex flex-col gap-1">
        <h2 id="richieste-stat" class="eyebrow-sm tracking-[0.14em]">Richieste dei clienti</h2>
        <p class="text-sm text-ink-soft">Visibile solo nell'area riservata.</p>
      </div>
      <NuxtLink to="/dashboard/messaggi" class="text-sm font-bold">Leggi le richieste →</NuxtLink>
    </div>

    <p v-if="!data.total" class="card p-5 text-sm text-ink-soft">Non sono ancora arrivate richieste.</p>

    <div v-else class="grid grid-cols-1 xl:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] gap-3">
      <div class="card p-5 flex flex-col gap-4">
        <dl class="grid grid-cols-3 gap-3">
          <div><dt class="text-[13px] text-ink-soft">Ricevute</dt><dd class="font-serif text-[32px] font-bold leading-tight">{{ data.total }}</dd></div>
          <div><dt class="text-[13px] text-ink-soft">Da leggere</dt><dd class="font-serif text-[32px] font-bold leading-tight text-wine-800">{{ data.unread }}</dd></div>
          <div><dt class="text-[13px] text-ink-soft">Su un vino</dt><dd class="font-serif text-[32px] font-bold leading-tight">{{ data.about_a_wine }}</dd></div>
        </dl>
        <ul class="m-0 p-0 list-none flex flex-col gap-2.5">
          <li v-for="t in data.types" :key="t.type" class="flex flex-col gap-1">
            <span class="flex justify-between gap-3 text-sm">
              <span class="font-semibold">{{ TYPE_LABELS[t.type] || t.type }}</span>
              <span class="text-ink-soft">{{ t.count }}</span>
            </span>
            <span class="h-1.5 rounded-full bg-line-soft overflow-hidden" aria-hidden="true">
              <span class="block h-full rounded-full bg-wine-800" :style="{ width: `${Math.round((t.count / data.total) * 100)}%` }"></span>
            </span>
          </li>
        </ul>
        <div v-if="showProducers && data.top_producers.length" class="pt-3 border-t border-line-soft flex flex-col gap-1.5">
          <span class="eyebrow-sm text-[11px]">Cantine più contattate</span>
          <span v-for="p in data.top_producers" :key="p.id" class="flex justify-between text-sm">
            <span>{{ p.name }}</span><span class="text-ink-soft">{{ p.requests }}</span>
          </span>
        </div>
      </div>

      <div class="card overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-line font-bold">Vini più richiesti</div>
        <p v-if="!data.top_wines.length" class="p-5 text-sm text-ink-soft">Nessuna richiesta riguarda ancora un vino specifico.</p>
        <ol v-else class="m-0 p-0 list-none divide-y divide-line-soft">
          <li v-for="(w, i) in data.top_wines" :key="w.id" class="px-5 py-3 flex items-center gap-4">
            <span class="w-6 text-sm font-bold text-ink-mute">{{ i + 1 }}</span>
            <span class="flex flex-col min-w-0 flex-1">
              <NuxtLink :to="`/vini/${w.slug}`" class="font-semibold text-ink hover:text-wine-800 truncate">{{ w.name }}</NuxtLink>
              <span class="text-[13px] text-ink-mute truncate">{{ showProducers ? `${w.producer} · ` : '' }}ultima richiesta {{ formatDate(w.last_request) }}</span>
            </span>
            <span class="font-serif text-2xl font-bold">{{ w.requests }}</span>
          </li>
        </ol>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  data: { type: Object, required: true },
  showProducers: { type: Boolean, default: false }
})

const TYPE_LABELS = {
  INFO_PREZZI: 'Prezzi e listino',
  DISPONIBILITA: 'Disponibilità e spedizione',
  VISITA_CANTINA: 'Visita o degustazione',
  ALTRO: 'Altro'
}

const formatDate = (value) => {
  if (!value) return '–'
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? '–' : d.toLocaleDateString('it-IT', { day: 'numeric', month: 'short', year: 'numeric' })
}
</script>
