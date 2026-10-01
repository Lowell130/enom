<template>
  <ReportSection
    id="vitigni-territorio"
    eyebrow="Identità"
    title="Autoctoni e internazionali"
    intro="Quanta parte del catalogo nasce dalla Tintilia, quanta dai vitigni tradizionali del Centro-Sud e quanta da vitigni internazionali."
  >
    <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] gap-5">
      <div class="card p-6 flex flex-col gap-5">
        <div class="flex items-baseline gap-3">
          <span class="font-serif text-[44px] font-bold leading-none text-wine-800">{{ fmtNumber(data.native_share) }}%</span>
          <span class="text-sm text-ink-soft">dei vini nasce da vitigni autoctoni o tradizionali</span>
        </div>

        <div class="flex h-10 gap-[2px] rounded-lg overflow-hidden" role="img" :aria-label="ariaLabel">
          <span
            v-for="g in visibleGroups"
            :key="g.group"
            class="h-full first:rounded-l-lg last:rounded-r-lg"
            :style="{ width: `${g.percentage}%`, background: COLORS[g.group] }"
            :title="`${g.label}: ${winesLabel(g.count)} (${fmtNumber(g.percentage)}%)`"
          ></span>
        </div>

        <ul class="m-0 p-0 list-none grid grid-cols-1 sm:grid-cols-2 gap-3">
          <li v-for="g in data.groups" :key="g.group" class="flex gap-2.5 text-sm">
            <span class="mt-1 w-3 h-3 rounded-sm shrink-0" :style="{ background: COLORS[g.group] }" aria-hidden="true"></span>
            <span class="flex flex-col">
              <span class="font-semibold">{{ g.label }}</span>
              <span class="text-ink-soft">{{ winesLabel(g.count) }} · {{ fmtNumber(g.percentage) }}%</span>
            </span>
          </li>
        </ul>

        <p v-if="data.international_grapes.length" class="text-sm text-ink-soft">
          Vitigni internazionali presenti:
          <template v-for="(g, i) in data.international_grapes" :key="g.name">
            <NuxtLink :to="`/vini?grape=${encodeURIComponent(g.name)}`" class="font-semibold">{{ g.name }}</NuxtLink> ({{ g.count }})<template v-if="i < data.international_grapes.length - 1">, </template>
          </template>.
        </p>
      </div>

      <div class="card p-6 flex flex-col gap-4">
        <div class="flex items-baseline gap-3">
          <span class="font-serif text-[44px] font-bold leading-none text-bio">{{ data.organic.count }}</span>
          <span class="text-sm text-ink-soft">vini biologici, il {{ fmtNumber(data.organic.percentage) }}% del catalogo</span>
        </div>
        <ul class="m-0 p-0 list-none flex flex-col gap-3">
          <li v-for="c in data.organic.categories" :key="c.category" class="flex flex-col gap-1" :title="`${categoryPlural(c.category)}: ${c.organic} biologici su ${c.total}`">
            <span class="flex justify-between gap-3 text-sm">
              <NuxtLink :to="`/vini?category=${c.category}&organic=organic`" class="font-semibold text-ink hover:text-wine-800">{{ categoryPlural(c.category) }}</NuxtLink>
              <span class="text-ink-soft">{{ c.organic }} su {{ c.total }}</span>
            </span>
            <span class="h-2 rounded-full bg-line-soft overflow-hidden" aria-hidden="true">
              <span class="block h-full rounded-full bg-bio" :style="{ width: `${c.percentage}%` }"></span>
            </span>
          </li>
        </ul>
        <NuxtLink to="/vini?organic=organic" class="text-sm font-bold">Tutti i vini biologici →</NuxtLink>
      </div>
    </div>
  </ReportSection>
</template>

<script setup>
import { categoryPlural, fmtNumber, winesLabel } from '~/utils/reportFormat'

const props = defineProps({
  data: { type: Object, required: true }
})

// tre tinte verificate per daltonismo e contrasto; "altro" resta neutro
const COLORS = {
  tintilia: '#93304A',
  traditional: '#B8823A',
  international: '#3274A6',
  other: '#D8CEC2'
}

const visibleGroups = computed(() => props.data.groups.filter((g) => g.count > 0))
const ariaLabel = computed(() => props.data.groups.map((g) => `${g.label} ${fmtNumber(g.percentage)}%`).join(', '))
</script>
