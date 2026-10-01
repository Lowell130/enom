<template>
  <ReportSection
    id="altitudine"
    eyebrow="Vini in quota"
    title="Dal mare all'Appennino"
    intro="A che altitudine crescono le vigne: dalle colline vicine all'Adriatico ai vigneti di montagna dell'interno."
    :note="`Altitudine indicata in ${data.wines_with_data} schede.`"
  >
    <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] gap-5">
      <div class="card p-6 flex flex-col gap-4">
        <h3 class="title-card text-2xl">Vini per fascia di altitudine</h3>
        <ul class="m-0 p-0 list-none flex flex-col-reverse gap-3">
          <li v-for="band in data.bands" :key="band.label" class="grid grid-cols-[110px_minmax(0,1fr)] gap-3 items-center" :title="`${band.label}: ${winesLabel(band.count)}`">
            <span class="text-sm font-semibold">{{ band.label }}</span>
            <span class="flex flex-col gap-1">
              <span class="flex items-center gap-3">
                <span class="h-7 rounded-md bg-wine-800 min-w-[4px]" :style="{ width: `${Math.round((band.count / maxBand) * 100)}%`, opacity: 0.45 + 0.55 * ((band.min || 0) / 600) }"></span>
                <span class="text-sm text-ink-soft whitespace-nowrap">{{ band.count }} · {{ fmtNumber(band.percentage) }}%</span>
              </span>
              <span v-if="band.top_grapes.length" class="text-xs text-ink-mute">{{ band.top_grapes.join(', ') }}</span>
            </span>
          </li>
        </ul>
      </div>

      <div class="flex flex-col gap-5">
        <div class="card p-6 flex flex-col gap-1">
          <span class="text-[13px] text-ink-soft">Altitudine tipica dei vigneti</span>
          <span class="font-serif text-[48px] font-bold leading-none text-wine-800">{{ fmtNumber(data.median_altitude) }} m</span>
          <NuxtLink v-if="data.highest" :to="`/vini/${data.highest.slug}`" class="mt-3 text-sm text-ink-soft hover:text-wine-800">
            Il vigneto più alto: <strong class="text-ink">{{ data.highest.name }}</strong> di {{ data.highest.producer }}, a {{ fmtNumber(data.highest.altitude) }} m.
          </NuxtLink>
        </div>
        <div v-if="data.grapes.length" class="card p-6 flex flex-col gap-3">
          <h3 class="title-card text-2xl">Altitudine media per vitigno</h3>
          <ul class="m-0 p-0 list-none flex flex-col gap-2.5">
            <li v-for="g in data.grapes" :key="g.grape" class="flex flex-col gap-1" :title="`${g.grape}: ${g.avg_altitude} m in media su ${winesLabel(g.wines)}`">
              <span class="flex justify-between gap-3 text-sm">
                <NuxtLink :to="`/vini?grape=${encodeURIComponent(g.grape)}`" class="font-semibold text-ink hover:text-wine-800">{{ g.grape }}</NuxtLink>
                <span class="text-ink-soft">{{ fmtNumber(g.avg_altitude) }} m</span>
              </span>
              <span class="relative h-1.5 rounded-full bg-line-soft" aria-hidden="true">
                <span class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-wine-800 ring-2 ring-white" :style="{ left: `${Math.min(100, (g.avg_altitude / maxAltitude) * 100)}%` }"></span>
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </ReportSection>
</template>

<script setup>
import { fmtNumber, winesLabel } from '~/utils/reportFormat'

const props = defineProps({
  data: { type: Object, required: true }
})

const maxBand = computed(() => Math.max(1, ...props.data.bands.map((b) => b.count)))
const maxAltitude = computed(() => Math.max(800, ...props.data.grapes.map((g) => g.avg_altitude)))
</script>
