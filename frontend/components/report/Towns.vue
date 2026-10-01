<template>
  <ReportSection
    id="mappa-vino"
    eyebrow="Sul territorio"
    title="La mappa del vino molisano"
    intro="Un cerchio per ogni comune di produzione, grande quanto il numero di vini. Clicca un comune per vederne i vini."
    note="Comune indicato nella zona di produzione della scheda, altrimenti quello della cantina."
  >
    <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_340px] gap-5 items-start">
      <TownMap :towns="towns" @select="openTown" />
      <ol class="card m-0 p-4 list-none flex flex-col gap-1 lg:max-h-[520px] lg:overflow-y-auto">
        <li v-for="(town, i) in towns" :key="town.city">
          <NuxtLink
            :to="townLink(town)"
            class="grid grid-cols-[24px_minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1 px-2 py-2 rounded-[10px] text-ink hover:bg-sand-100"
          >
            <span class="text-xs font-bold text-ink-mute">{{ i + 1 }}</span>
            <span class="font-semibold truncate">{{ town.city }}</span>
            <span class="text-sm text-ink-soft whitespace-nowrap">{{ winesLabel(town.count) }}</span>
            <span></span>
            <span class="col-span-2 h-1.5 rounded-full bg-line-soft overflow-hidden" aria-hidden="true">
              <span class="block h-full rounded-full bg-wine-800" :style="{ width: `${Math.round((town.count / max) * 100)}%` }"></span>
            </span>
          </NuxtLink>
        </li>
      </ol>
    </div>
  </ReportSection>
</template>

<script setup>
import { winesLabel } from '~/utils/reportFormat'

const props = defineProps({
  towns: { type: Array, default: () => [] }
})

const router = useRouter()
const max = computed(() => Math.max(1, ...props.towns.map((t) => t.count)))

const townLink = (town) => `/vini?search=${encodeURIComponent(town.city)}`
const openTown = (town) => router.push(townLink(town))
</script>
