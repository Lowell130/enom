<template>
  <ReportSection
    id="terreni"
    eyebrow="Il suolo"
    title="Su quali terreni"
    intro="I tipi di terreno citati nelle schede e i vitigni che ci crescono più spesso. Un vigneto può avere più tipi di suolo."
    :note="`Tipologia di terreno indicata in ${data.wines_with_data} schede.`"
  >
    <div class="card p-6 flex flex-col gap-4">
      <p v-if="data.most_common_combo" class="text-base text-ink-soft">
        La combinazione più frequente è il terreno <strong class="text-ink">{{ data.most_common_combo }}</strong>.
      </p>
      <ul class="m-0 p-0 list-none grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-3.5">
        <li v-for="s in data.soils" :key="s.soil" class="flex flex-col gap-1" :title="`${s.soil}: ${winesLabel(s.count)}`">
          <span class="flex justify-between gap-3 text-sm">
            <span class="font-semibold">{{ s.soil }}</span>
            <span class="text-ink-soft whitespace-nowrap">{{ winesLabel(s.count) }} · {{ fmtNumber(s.percentage) }}%</span>
          </span>
          <span class="h-2 rounded-full bg-line-soft overflow-hidden" aria-hidden="true">
            <span class="block h-full rounded-full bg-gold-600" :style="{ width: `${Math.round((s.count / max) * 100)}%` }"></span>
          </span>
          <span v-if="s.top_grapes.length" class="text-xs text-ink-mute">{{ s.top_grapes.join(', ') }}</span>
        </li>
      </ul>
    </div>
  </ReportSection>
</template>

<script setup>
import { fmtNumber, winesLabel } from '~/utils/reportFormat'

const props = defineProps({
  data: { type: Object, required: true }
})

const max = computed(() => Math.max(1, ...props.data.soils.map((s) => s.count)))
</script>
