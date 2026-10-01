<template>
  <ReportSection
    id="abbinamenti"
    eyebrow="Cosa bere con…"
    title="Abbinamenti per tipologia"
    intro="I piatti più consigliati dalle cantine, le tipologie che li accompagnano meglio e qualche vino da provare."
  >
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
      <article v-for="p in items" :key="p.pairing" class="card p-5 flex flex-col gap-3">
        <header class="flex flex-col gap-0.5">
          <h3 class="title-card text-[22px]">{{ p.pairing }}</h3>
          <span class="text-[13px] text-ink-mute">consigliato per {{ winesLabel(p.wines) }}</span>
        </header>
        <ul class="m-0 p-0 list-none flex flex-col gap-1.5">
          <li v-for="c in p.categories" :key="c.category" class="flex flex-col gap-1">
            <span class="flex justify-between text-sm">
              <span>{{ categoryPlural(c.category) }}</span>
              <span class="text-ink-soft">{{ fmtNumber(c.percentage) }}%</span>
            </span>
            <span class="h-1.5 rounded-full bg-line-soft overflow-hidden" aria-hidden="true">
              <span class="block h-full rounded-full bg-wine-800" :style="{ width: `${c.percentage}%` }"></span>
            </span>
          </li>
        </ul>
        <div class="mt-auto pt-3 border-t border-line-soft flex flex-col gap-1.5">
          <span class="eyebrow-sm text-[11px]">Da provare</span>
          <NuxtLink v-for="w in p.examples" :key="w.slug" :to="`/vini/${w.slug}`" class="text-sm leading-snug text-ink hover:text-wine-800">
            <strong>{{ w.name }}</strong> <span class="text-ink-mute">· {{ w.producer }}</span>
          </NuxtLink>
          <NuxtLink :to="`/vini?search=${encodeURIComponent(p.pairing)}`" class="text-sm font-bold mt-1">Tutti i vini →</NuxtLink>
        </div>
      </article>
    </div>
  </ReportSection>
</template>

<script setup>
import { categoryPlural, fmtNumber, winesLabel } from '~/utils/reportFormat'

defineProps({
  items: { type: Array, default: () => [] }
})
</script>
