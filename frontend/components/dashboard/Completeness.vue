<template>
  <section aria-labelledby="completezza" class="flex flex-col gap-3">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div class="flex flex-col gap-1">
        <h2 id="completezza" class="eyebrow-sm tracking-[0.14em]">Completezza delle schede</h2>
        <p class="text-sm text-ink-soft">Le schede complete si trovano meglio nella ricerca e nei filtri del catalogo.</p>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] gap-3">
      <div class="card p-5 flex flex-col gap-4">
        <div class="flex items-baseline gap-3">
          <span class="font-serif text-[44px] font-bold leading-none text-wine-800">{{ data.average_score }}%</span>
          <span class="text-sm text-ink-soft">completezza media · {{ data.complete }} schede complete su {{ data.wines }}</span>
        </div>
        <ul class="m-0 p-0 list-none flex flex-col gap-2.5">
          <li v-for="f in data.fields" :key="f.field" class="flex flex-col gap-1" :title="`${f.label}: presente in ${f.filled} schede su ${data.wines}`">
            <span class="flex justify-between gap-3 text-sm">
              <span class="font-semibold">{{ f.label }}</span>
              <span class="text-ink-soft">{{ f.filled }} su {{ data.wines }}</span>
            </span>
            <span class="h-1.5 rounded-full bg-line-soft overflow-hidden" aria-hidden="true">
              <span class="block h-full rounded-full" :class="f.percentage >= 80 ? 'bg-bio' : 'bg-wine-800'" :style="{ width: `${f.percentage}%` }"></span>
            </span>
          </li>
        </ul>
      </div>

      <div class="card overflow-hidden flex flex-col">
        <div class="px-5 py-4 border-b border-line flex flex-wrap justify-between gap-2">
          <span class="font-bold">Da completare per prime</span>
          <span class="text-sm text-ink-mute">le schede con più informazioni mancanti</span>
        </div>
        <p v-if="!data.to_improve.length" class="p-5 text-sm text-ink-soft">Tutte le schede sono complete.</p>
        <ul v-else class="m-0 p-0 list-none divide-y divide-line-soft">
          <li v-for="w in data.to_improve" :key="w.id" class="px-5 py-3 flex flex-wrap items-center gap-x-4 gap-y-1.5">
            <span class="w-12 shrink-0 font-serif text-xl font-bold" :class="w.score < 50 ? 'text-wine-800' : 'text-ink'">{{ w.score }}%</span>
            <span class="flex flex-col min-w-0 flex-1">
              <span class="font-semibold truncate">{{ w.name }}</span>
              <span class="text-[13px] text-ink-mute truncate">{{ showProducer ? `${w.producer} · ` : '' }}manca: {{ w.missing.join(', ').toLowerCase() }}</span>
            </span>
            <NuxtLink :to="`/dashboard/prodotti/edit-${w.id}`" class="btn-ghost btn-sm h-9 shrink-0">Completa</NuxtLink>
          </li>
        </ul>
      </div>
    </div>
  </section>
</template>

<script setup>
defineProps({
  data: { type: Object, required: true },
  showProducer: { type: Boolean, default: false }
})
</script>
