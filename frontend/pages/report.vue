<template>
  <div class="pb-6">
    <!-- INTESTAZIONE CHIARA -->
    <section class="bg-sand border-b border-line">
      <div class="page-container pt-10 pb-7 flex flex-col gap-6">
        <div class="flex flex-wrap items-end justify-between gap-5">
          <div class="flex flex-col gap-2 max-w-[700px]">
            <span class="eyebrow">Osservatorio · dati aggiornati dal catalogo</span>
            <h1 class="title-display">Il vino molisano in numeri</h1>
            <p class="text-[17px] text-ink-soft">Vitigni, denominazioni, zone e tecniche di cantina, calcolati dalle schede dei vini in catalogo.</p>
          </div>
          <div class="flex gap-2.5 no-print">
            <button type="button" class="btn-ghost btn-sm h-11" @click="printReport">
              <Printer class="w-4 h-4" aria-hidden="true" /> Stampa / PDF
            </button>
            <button type="button" class="btn-ghost btn-sm h-11" :disabled="!reportData" @click="downloadCsv">
              <Download class="w-4 h-4" aria-hidden="true" /> Esporta CSV
            </button>
          </div>
        </div>
        <div class="flex flex-wrap items-end gap-3 no-print">
          <label class="field-label text-[13px] text-ink-soft">Provincia
            <select v-model="selectedProvince" class="select h-11 text-sm min-w-[200px]">
              <option value="">Campobasso e Isernia</option>
              <option value="CB">Campobasso (CB)</option>
              <option value="IS">Isernia (IS)</option>
            </select>
          </label>
          <label class="field-label text-[13px] text-ink-soft">Denominazione
            <select v-model="selectedDenomination" class="select h-11 text-sm min-w-[200px]">
              <option value="">Tutte</option>
              <option v-for="den in (reportData?.filter_options?.denominations || ['DOC', 'DOP', 'IGP', 'IGT'])" :key="den" :value="den">{{ den }}</option>
            </select>
          </label>
          <button
            type="button"
            :aria-pressed="isOrganicOnly"
            :class="['flex items-center gap-2.5 h-11 px-3.5 rounded-[10px] border text-sm font-semibold transition-colors', isOrganicOnly ? 'border-bio bg-bio-50 text-bio-900' : 'border-line-strong bg-white text-ink']"
            @click="toggleOrganic"
          >
            <Leaf class="w-4 h-4" aria-hidden="true" /> Solo biologici
          </button>
          <button v-if="hasActiveFilters" type="button" class="h-11 px-2 text-sm font-bold text-wine-800" @click="resetFilters">Azzera filtri</button>
        </div>
      </div>
    </section>

    <div v-if="pending && !reportData" class="page-container py-16 text-center text-ink-mute">Calcolo dei dati in corso…</div>

    <template v-else-if="reportData">
      <!-- INDICATORI -->
      <section aria-label="Indicatori" class="page-container pt-8">
        <dl class="grid grid-cols-2 md:grid-cols-5 card overflow-hidden">
          <div v-for="kpi in kpis" :key="kpi.label" class="px-5 py-5 border-r border-b md:border-b-0 border-line-soft">
            <dt class="text-[13px] text-ink-soft">{{ kpi.label }}</dt>
            <dd class="mt-1 font-serif text-[44px] font-bold leading-none text-wine-800">{{ kpi.value }}</dd>
          </div>
        </dl>
      </section>

      <!-- GRAFICI -->
      <section class="page-container pt-5 pb-14 md:pb-[72px] grid grid-cols-1 lg:grid-cols-2 gap-5">
        <article v-for="panel in panels" :key="panel.title" class="card p-6 md:p-[26px] flex flex-col gap-[18px]">
          <header class="flex flex-col gap-0.5">
            <h2 class="title-card text-[28px]">{{ panel.title }}</h2>
            <span class="text-sm text-ink-mute">{{ panel.sub }}</span>
          </header>
          <ul class="m-0 p-0 list-none flex flex-col gap-3">
            <li v-for="row in panel.rows" :key="row.label" class="flex flex-col gap-[5px]">
              <div class="flex justify-between gap-3 text-sm">
                <NuxtLink v-if="row.to" :to="row.to" class="font-semibold text-ink hover:text-wine-800">{{ row.label }}</NuxtLink>
                <span v-else class="font-semibold">{{ row.label }}</span>
                <span class="text-ink-soft whitespace-nowrap">{{ row.value }}</span>
              </div>
              <div class="h-2 rounded-full bg-line-soft overflow-hidden"><div class="h-full rounded-full bg-wine-800" :style="{ width: row.width }"></div></div>
            </li>
          </ul>
        </article>

        <article v-if="reportData.wood_vs_steel" class="card p-6 md:p-[26px] flex flex-col gap-[18px]">
          <header class="flex flex-col gap-0.5">
            <h2 class="title-card text-[28px]">Legno o acciaio</h2>
            <span class="text-sm text-ink-mute">Stile di affinamento delle etichette</span>
          </header>
          <div class="flex h-11 rounded-[10px] overflow-hidden text-sm font-bold">
            <div class="bg-gold-600 text-white flex items-center pl-3" :style="{ width: `${reportData.wood_vs_steel.wood_percentage}%` }">{{ Math.round(reportData.wood_vs_steel.wood_percentage) }}%</div>
            <div class="flex-1 bg-[#DCD6CC] text-ink flex items-center justify-end pr-3">{{ Math.round(reportData.wood_vs_steel.steel_percentage) }}%</div>
          </div>
          <div class="flex flex-wrap justify-between gap-3 text-sm text-ink-soft">
            <span><strong class="text-ink">Legno</strong> (barrique, botte) · {{ reportData.wood_vs_steel.wood_count }} etichette</span>
            <span><strong class="text-ink">Acciaio inox</strong> · {{ reportData.wood_vs_steel.steel_count }} etichette</span>
          </div>
        </article>

        <article v-if="(reportData.top_pairings || []).length" class="card p-6 md:p-[26px] flex flex-col gap-[18px]">
          <header class="flex flex-col gap-0.5">
            <h2 class="title-card text-[28px]">Abbinamenti più consigliati</h2>
            <span class="text-sm text-ink-mute">Clicca per vedere i vini adatti</span>
          </header>
          <div class="flex flex-wrap gap-2">
            <NuxtLink v-for="pairing in reportData.top_pairings" :key="pairing.name" :to="`/vini?search=${encodeURIComponent(pairing.name)}`" class="chip-outline">
              {{ pairing.name }} <span class="px-[7px] py-px rounded-full bg-sand-100 text-wine-900 text-xs font-bold">{{ pairing.count }}</span>
            </NuxtLink>
          </div>
        </article>

        <article v-if="techGroups.length" class="card p-6 md:p-[26px] flex flex-col gap-[18px] lg:col-span-2">
          <header class="flex flex-col gap-0.5">
            <h2 class="title-card text-[28px]">Tecniche di cantina e vigneto</h2>
            <span class="text-sm text-ink-mute">Le voci più frequenti nelle schede tecniche</span>
          </header>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
            <div v-for="group in techGroups" :key="group.title" class="flex flex-col gap-2">
              <span class="eyebrow-sm">{{ group.title }}</span>
              <span v-for="item in group.items" :key="item.name" class="flex justify-between gap-3 text-sm border-b border-line-soft pb-1.5">
                <span class="text-ink-soft">{{ item.name }}</span><strong class="text-ink">{{ item.count }}</strong>
              </span>
            </div>
          </div>
        </article>
      </section>

      <!-- LETTURA DEI DATI -->
      <section class="bg-sand py-12 md:py-16">
        <div class="page-container grid grid-cols-1 lg:grid-cols-2 gap-10">
          <div class="flex flex-col gap-2.5">
            <span class="eyebrow">Lettura dei dati</span>
            <h2 class="title-section text-[32px] md:text-[40px]">La Tintilia guida, il territorio varia</h2>
          </div>
          <div class="flex flex-col gap-3.5 text-base text-ink-soft">
            <p><strong class="text-ink">La Tintilia come segno distintivo.</strong> È il vitigno autoctono che identifica il Molise: la sua quota nel catalogo racconta il legame con la biodiversità locale.</p>
            <p><strong class="text-ink">Microclimi diversi.</strong> Dalle colline di Campomarino vicine al mare alle quote di Castropignano e Isernia, l'escursione termica dà acidità e profumi caratteristici.</p>
            <p class="text-[13px] text-ink-mute">I conteggi per comune si riferiscono alla zona di produzione o alla sede della cantina.</p>
          </div>
        </div>
      </section>
    </template>

    <div v-else class="page-container py-16 text-center text-ink-soft">I dati dell'Osservatorio non sono disponibili in questo momento.</div>
  </div>
</template>

<script setup>
import { Printer, Download, Leaf } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()

useHead({
  title: 'Osservatorio Enologico del Molise | Report & Analisi Data Vini',
  meta: [
    { name: 'description', content: 'Report strategico e osservatorio sui vini, cantine, vitigni e denominazioni della regione Molise.' }
  ]
})

const selectedProvince = ref('')
const selectedDenomination = ref('')
const isOrganicOnly = ref(false)

const toggleOrganic = () => {
  isOrganicOnly.value = !isOrganicOnly.value
}

const hasActiveFilters = computed(() => {
  return Boolean(selectedProvince.value || selectedDenomination.value || isOrganicOnly.value)
})

const resetFilters = () => {
  selectedProvince.value = ''
  selectedDenomination.value = ''
  isOrganicOnly.value = false
}

const { data: reportData, pending } = await useAsyncData('reports_summary', async () => {
  const queryParams = new URLSearchParams()
  if (selectedProvince.value) queryParams.append('province', selectedProvince.value)
  if (selectedDenomination.value) queryParams.append('denominazione', selectedDenomination.value)
  if (isOrganicOnly.value) queryParams.append('is_organic', 'true')

  const url = `/reports/summary${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
  const res = await fetchWithAuth(url)
  return res || null
}, { 
  watch: [selectedProvince, selectedDenomination, isOrganicOnly],
  default: () => null 
})

// Print Action (PDF)
const printReport = () => {
  if (typeof window !== 'undefined') {
    window.print()
  }
}

// Download CSV Action
const downloadCsv = () => {
  if (!reportData.value) return
  
  const rows = [
    ['Osservatorio Enologico Molisano - Report Export'],
    ['Data estrazione:', new Date().toLocaleDateString('it-IT')],
    [''],
    ['KPI', 'Valore'],
    ['Totale Prodotti', reportData.value.kpis.total_products],
    ['Totale Cantine', reportData.value.kpis.total_producers],
    ['Totale Vitigni', reportData.value.kpis.total_grapes],
    ['Totale Abbinamenti', reportData.value.kpis.total_pairings],
    ['Gradazione Alcolica Media', reportData.value.kpis.avg_alcohol_degrees],
    ['Range Annate', `${reportData.value.kpis.min_vintage_year || ''} - ${reportData.value.kpis.max_vintage_year || ''}`],
    [''],
    ['Tipologia', 'Conteggio', 'Percentuale'],
    ...(reportData.value.category_breakdown || []).map(c => [getCategoryLabel(c.category), c.count, `${c.percentage}%`]),
    [''],
    ['Denominazione', 'Conteggio', 'Percentuale'],
    ...(reportData.value.denomination_breakdown || []).map(d => [d.name, d.count, `${d.percentage}%`]),
    [''],
    ['Vitigno', 'Conteggio', 'Percentuale'],
    ...(reportData.value.top_grapes || []).map(g => [g.name, g.count, `${g.percentage}%`]),
    [''],
    ['Comune Produzione', 'Conteggio Vini'],
    ...(reportData.value.zone_breakdown || []).map(z => [z.city, z.count])
  ]

  const csvContent = 'data:text/csv;charset=utf-8,' + rows.map(e => e.map(cell => `"${cell}"`).join(',')).join('\n')
  const encodedUri = encodeURI(csvContent)
  const link = document.createElement('a')
  link.setAttribute('href', encodedUri)
  link.setAttribute('download', `Osservatorio_EnotecaMolise_${new Date().toISOString().slice(0,10)}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// Helpers
const getCategoryLabel = (cat) => {
  const labels = {
    'ROSSO': 'Vini rossi',
    'VINO_ROSSO': 'Vini rossi',
    'BIANCO': 'Vini bianchi',
    'VINO_BIANCO': 'Vini bianchi',
    'ROSATO': 'Rosati',
    'PASSITO': 'Passiti e dolci',
    'SPUMANTE': 'Spumanti',
    'LIQUORE': 'Liquori e grappe',
    'ALTRO': 'Altre tipologie'
  }
  return labels[cat?.toUpperCase()] || cat
}

// Unisce voci uguali scritte in modo diverso ("75 cl" e "75 Cl", "Cordone speronato" e "Cordone Speronato")
const mergeVariants = (list = []) => {
  const map = new Map()
  for (const item of list) {
    const key = String(item.name || '').toLowerCase().replace(/\s+/g, ' ').trim()
    if (!key) continue
    const prev = map.get(key)
    if (prev) prev.count += item.count
    else map.set(key, { name: item.name, count: item.count })
  }
  return [...map.values()].sort((a, b) => b.count - a.count)
}

const fmtPct = (n) => String(n).replace('.', ',')

const toRows = (list, unit, link) => {
  const max = Math.max(1, ...list.map((x) => x.count))
  return [...list].sort((a, b) => b.count - a.count).map((x) => ({
    label: x.label,
    value: `${x.count} ${unit}${x.percentage !== undefined ? ` · ${fmtPct(x.percentage)}%` : ''}`,
    width: `${Math.round((x.count / max) * 100)}%`,
    to: link ? link(x) : ''
  }))
}

const DENOM_FILTERS = ['DOC', 'DOCG', 'DOP', 'IGT', 'IGP']

const kpis = computed(() => {
  const k = reportData.value?.kpis || {}
  return [
    { label: 'Vini in catalogo', value: k.total_products ?? 0 },
    { label: 'Cantine con vini', value: k.total_producers ?? 0 },
    { label: 'Vitigni censiti', value: k.total_grapes ?? 0 },
    { label: 'Abbinamenti', value: k.total_pairings ?? 0 },
    { label: 'Gradazione media', value: k.avg_alcohol_degrees ? `${fmtPct(k.avg_alcohol_degrees)}%` : '–' }
  ]
})

const panels = computed(() => {
  const r = reportData.value || {}
  const total = r.kpis?.total_products || 0
  return [
    {
      title: 'Tipologie',
      sub: `Ripartizione dei ${total} vini in catalogo`,
      rows: toRows((r.category_breakdown || []).map((c) => ({ ...c, label: getCategoryLabel(c.category) })), 'vini', (c) => `/vini?category=${encodeURIComponent(({ ROSSO: 'VINO_ROSSO', BIANCO: 'VINO_BIANCO' })[String(c.category).toUpperCase()] || String(c.category).toUpperCase())}`)
    },
    {
      title: 'Denominazioni',
      sub: 'Qualità certificata e tutelata',
      rows: toRows((r.denomination_breakdown || []).map((d) => ({ ...d, label: d.name })), 'vini',
        (d) => (DENOM_FILTERS.includes(d.name) ? `/vini?denominazione=${d.name}` : ''))
    },
    {
      title: 'Vitigni più diffusi',
      sub: 'Etichette che contengono il vitigno',
      rows: toRows((r.top_grapes || []).slice(0, 8).map((g) => ({ name: g.name, count: g.count, label: g.name })), 'etichette', (g) => `/vini?grape=${encodeURIComponent(g.name)}`)
    },
    {
      title: 'Comuni di produzione',
      sub: 'Dove nascono le etichette',
      rows: toRows((r.zone_breakdown || []).slice(0, 8).map((z) => ({ count: z.count, label: z.city })), 'vini', (z) => `/vini?search=${encodeURIComponent(z.label)}`)
    }
  ].filter((p) => p.rows.length)
})

const techGroups = computed(() => {
  const t = reportData.value?.technical_analytics || {}
  return [
    { title: 'Allevamento', items: mergeVariants(t.allevamento) },
    { title: 'Vinificazione', items: mergeVariants(t.vinificazione) },
    { title: 'Affinamento', items: mergeVariants(t.affinamento) },
    { title: 'Altitudine vigneti', items: mergeVariants(t.altitudine) },
    { title: 'Formato bottiglia', items: mergeVariants(t.formato) }
  ].map((g) => ({ ...g, items: g.items.slice(0, 5) })).filter((g) => g.items.length)
})
</script>

<style>
@media print {
  header, footer, nav, .no-print, button {
    display: none !important;
  }
  body {
    background: #FFFFFF !important;
  }
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
</style>
