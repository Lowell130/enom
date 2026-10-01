<template>
  <ReportSection
    id="prezzi"
    eyebrow="Quanto costa"
    title="Prezzi indicativi"
    intro="Le fasce di prezzo dei vini e il prezzo tipico per tipologia."
    :note="`Solo i ${data.wines_with_price} vini su ${data.wines_total} con un prezzo indicato (${fmtNumber(data.coverage)}%): i valori sono orientativi.`"
  >
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div class="card p-6 flex flex-col gap-4">
        <div class="flex items-baseline gap-3">
          <span class="font-serif text-[44px] font-bold leading-none text-wine-800">{{ fmtEuro(data.median) }}</span>
          <span class="text-sm text-ink-soft">prezzo tipico di una bottiglia</span>
        </div>
        <ul class="m-0 p-0 list-none flex flex-col gap-3">
          <li v-for="b in data.bands" :key="b.label" class="flex flex-col gap-1" :title="`${b.label}: ${winesLabel(b.count)}`">
            <span class="flex justify-between gap-3 text-sm">
              <span class="font-semibold">{{ b.label }}</span>
              <span class="text-ink-soft">{{ winesLabel(b.count) }} · {{ fmtNumber(b.percentage) }}%</span>
            </span>
            <span class="h-2 rounded-full bg-line-soft overflow-hidden" aria-hidden="true">
              <span class="block h-full rounded-full bg-wine-800" :style="{ width: `${Math.round((b.count / maxBand) * 100)}%` }"></span>
            </span>
          </li>
        </ul>
      </div>

      <div class="card p-6 flex flex-col gap-4">
        <h3 class="title-card text-2xl">Per tipologia</h3>
        <p class="text-[13px] text-ink-mute -mt-2">La linea va dal vino meno caro al più caro, il punto è il prezzo tipico.</p>
        <ul class="m-0 p-0 list-none flex flex-col gap-4">
          <li v-for="c in data.categories" :key="c.category" class="flex flex-col gap-1.5" :title="`${categoryPlural(c.category)}: da ${fmtEuro(c.min)} a ${fmtEuro(c.max)}, tipico ${fmtEuro(c.median)} (${winesLabel(c.wines)})`">
            <span class="flex justify-between gap-3 text-sm">
              <span class="font-semibold">{{ categoryPlural(c.category) }} <span class="text-xs font-normal text-ink-mute">{{ c.wines }}</span></span>
              <span class="text-ink-soft">{{ fmtEuro(c.median) }}</span>
            </span>
            <span class="relative h-3" aria-hidden="true">
              <span class="absolute inset-x-0 top-1/2 h-px bg-line"></span>
              <span class="absolute top-1/2 -translate-y-1/2 h-1.5 rounded-full bg-wine-800/35" :style="{ left: `${pos(c.min)}%`, width: `${Math.max(pos(c.max) - pos(c.min), 1)}%` }"></span>
              <span class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-wine-800 ring-2 ring-white" :style="{ left: `${pos(c.median)}%` }"></span>
            </span>
          </li>
        </ul>
        <span class="flex justify-between text-xs text-ink-mute"><span>0 €</span><span>{{ fmtEuro(scaleMax) }}</span></span>
      </div>
    </div>
  </ReportSection>
</template>

<script setup>
import { categoryPlural, fmtEuro, fmtNumber, winesLabel } from '~/utils/reportFormat'

const props = defineProps({
  data: { type: Object, required: true }
})

const maxBand = computed(() => Math.max(1, ...props.data.bands.map((b) => b.count)))
const scaleMax = computed(() => Math.ceil(Math.max(20, ...props.data.categories.map((c) => c.max)) / 10) * 10)
const pos = (v) => Math.min(100, (v / scaleMax.value) * 100)
</script>
