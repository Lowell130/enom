<template>
  <ReportSection
    id="servizio"
    eyebrow="A tavola"
    title="Guida al servizio"
    intro="A che temperatura servire ogni tipologia e quanto è alcolica, in media, secondo le schede delle cantine."
  >
    <div class="card p-6 flex flex-col gap-4">
      <div class="hidden sm:grid grid-cols-[150px_minmax(0,1fr)_110px] gap-4 text-xs font-semibold uppercase tracking-[0.08em] text-ink-mute">
        <span>Tipologia</span>
        <span class="flex justify-between"><span>{{ SCALE_MIN }} °C</span><span>{{ SCALE_MAX }} °C</span></span>
        <span class="text-right">Alcol medio</span>
      </div>
      <ul class="m-0 p-0 list-none flex flex-col gap-3">
        <li
          v-for="row in rows"
          :key="row.category"
          class="grid grid-cols-[minmax(0,1fr)_auto] sm:grid-cols-[150px_minmax(0,1fr)_110px] gap-x-4 gap-y-1.5 items-center"
          :title="row.title"
        >
          <NuxtLink :to="`/vini?category=${row.category}`" class="font-semibold text-ink hover:text-wine-800">
            {{ categoryPlural(row.category) }}
            <span class="text-xs font-normal text-ink-mute">{{ row.wines }}</span>
          </NuxtLink>
          <span class="sm:order-last text-right text-sm text-ink-soft">{{ row.avg_alcohol ? `${fmtNumber(row.avg_alcohol, 1)}% vol` : '–' }}</span>
          <span class="col-span-2 sm:col-span-1 relative h-8 rounded-md bg-[linear-gradient(90deg,#E4EBF0,#F6F1EA_50%,#F3E3DC)]" aria-hidden="true">
            <span
              v-if="row.temp_min !== null"
              class="absolute top-1 bottom-1 rounded bg-wine-800 text-white text-xs font-bold flex items-center justify-center min-w-[52px]"
              :style="{ left: `${pos(row.temp_min)}%`, width: `${Math.max(pos(row.temp_max) - pos(row.temp_min), 0)}%` }"
            >{{ row.range }}</span>
          </span>
        </li>
      </ul>
      <p class="text-[13px] text-ink-mute">Valori tipici (mediana) delle temperature indicate dalle cantine.</p>
    </div>
  </ReportSection>
</template>

<script setup>
import { categoryPlural, fmtNumber } from '~/utils/reportFormat'

const props = defineProps({
  rows: { type: Array, default: () => [] }
})

const SCALE_MIN = 4
const SCALE_MAX = 20

const pos = (t) => Math.min(100, Math.max(0, ((t - SCALE_MIN) / (SCALE_MAX - SCALE_MIN)) * 100))

const rows = computed(() => props.rows.map((r) => {
  const range = r.temp_min === null ? '' : (r.temp_min === r.temp_max ? `${r.temp_min} °C` : `${r.temp_min}–${r.temp_max} °C`)
  return {
    ...r,
    range,
    title: `${categoryPlural(r.category)}: ${range || 'temperatura non indicata'}${r.avg_alcohol ? `, ${fmtNumber(r.avg_alcohol, 1)}% vol in media` : ''}`
  }
}))
</script>
