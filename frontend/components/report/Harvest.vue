<template>
  <ReportSection
    id="vendemmia"
    eyebrow="In vigna"
    title="Calendario della vendemmia"
    intro="Quando si raccoglie ogni vitigno: ogni riquadro conta i vini vendemmiati in quel mese, più è scuro più sono."
    :note="`Dal periodo di raccolta indicato in ${data.wines_with_data} schede.`"
  >
    <div class="card p-4 md:p-6 overflow-x-auto">
      <table class="w-full min-w-[560px] border-separate border-spacing-[3px] text-sm">
        <caption class="sr-only">Numero di vini vendemmiati per vitigno e mese</caption>
        <thead>
          <tr>
            <th scope="col" class="text-left font-semibold text-ink-mute text-xs uppercase tracking-[0.08em] pb-2 pr-4 w-[200px]">Vitigno</th>
            <th v-for="m in data.months" :key="m.month" scope="col" class="font-semibold text-ink-mute text-xs uppercase tracking-[0.08em] pb-2">{{ m.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in data.grapes" :key="row.grape">
            <th scope="row" class="text-left font-semibold pr-4 py-0.5 whitespace-nowrap">
              <NuxtLink :to="`/vini?grape=${encodeURIComponent(row.grape)}`" class="text-ink hover:text-wine-800">{{ row.grape }}</NuxtLink>
              <span class="ml-1.5 text-xs font-normal text-ink-mute">{{ row.wines }}</span>
            </th>
            <td
              v-for="cell in row.months"
              :key="cell.month"
              class="h-10 rounded-md text-center text-xs font-bold"
              :style="cellStyle(cell)"
              :title="`${row.grape} · ${monthLabel(cell.month)}: ${cell.count ? winesLabel(cell.count) : 'nessun vino'}`"
            >
              <span v-if="cell.count" :class="level(cell) >= 0.45 ? 'text-white' : 'text-wine-900'">{{ cell.count }}</span>
            </td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th scope="row" class="text-left text-xs font-semibold uppercase tracking-[0.08em] text-ink-mute pt-3 pr-4">Totale vini</th>
            <td v-for="m in data.months" :key="m.month" class="pt-3 text-center font-serif text-xl font-bold text-ink">{{ m.count }}</td>
          </tr>
        </tfoot>
      </table>
      <p v-if="peak" class="mt-4 text-sm text-ink-soft">
        Il mese più intenso è <strong class="text-ink">{{ peak.label.toLowerCase() }}</strong>: {{ winesLabel(peak.count) }} su {{ data.wines_with_data }} si vendemmiano in quel periodo.
      </p>
    </div>
  </ReportSection>
</template>

<script setup>
import { winesLabel } from '~/utils/reportFormat'

const props = defineProps({
  data: { type: Object, required: true }
})

// una sola tinta (bordeaux) e una sola scala per tutta la tabella: piu' vini, riquadro piu' scuro
const maxCell = computed(() => Math.max(1, ...props.data.grapes.flatMap((g) => g.months.map((m) => m.count))))
const level = (cell) => Math.sqrt(cell.count / maxCell.value)
const cellStyle = (cell) => {
  if (!cell.count) return { background: '#F3EEE7' }
  const alpha = 0.12 + level(cell) * 0.88
  return { background: `rgba(107, 29, 47, ${alpha.toFixed(2)})` }
}

const monthLabel = (m) => props.data.months.find((x) => x.month === m)?.label || ''

const peak = computed(() => [...(props.data.months || [])].sort((a, b) => b.count - a.count)[0])
</script>
