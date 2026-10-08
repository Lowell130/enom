<template>
  <div class="pb-6">
    <!-- INTESTAZIONE -->
    <section class="bg-sand border-b border-line">
      <div class="page-container pt-10 md:pt-12 pb-8 flex flex-col gap-7">
        <div class="flex flex-col gap-3 max-w-[760px]">
          <span class="eyebrow">Osservatorio</span>
          <h1 class="title-display">Il vino molisano in numeri</h1>
          <p class="text-[17px] leading-relaxed text-ink-soft m-0">
            Vitigni, denominazioni, zone e tecniche di cantina: una fotografia del catalogo, calcolata dalle schede dei vini.
          </p>
          <p class="flex items-start gap-2.5 m-0 mt-1 px-3.5 py-2.5 rounded-xl bg-white/70 border border-line text-[13px] leading-relaxed text-ink-soft">
            <Info class="w-4 h-4 mt-0.5 shrink-0 text-wine-800" aria-hidden="true" />
            <span>
              I dati vengono dalle schede pubblicate sul sito, ricavate dalle schede tecniche dei produttori:
              descrivono il catalogo di EnotecaMolise, non l'intera produzione del Molise.
              <a href="#fonte-dati" class="font-semibold text-wine-800 underline underline-offset-2 whitespace-nowrap no-print">Come sono calcolati</a>
            </span>
          </p>
        </div>

        <div role="group" aria-labelledby="report-filters-title" class="no-print card p-4 sm:p-5 flex flex-col gap-3">
          <div class="flex items-center justify-between gap-3">
            <span id="report-filters-title" class="text-[13px] font-bold uppercase tracking-[0.08em] text-ink-mute">Filtra i dati</span>
            <button v-if="hasActiveFilters" type="button" class="text-sm font-bold text-wine-800 hover:underline underline-offset-2" @click="resetFilters">Azzera filtri</button>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-[repeat(2,minmax(0,240px))_auto] gap-3 items-end">
            <label class="field-label text-[13px] text-ink-soft">Provincia
              <select v-model="selectedProvince" class="select h-11 text-sm w-full">
                <option value="">Campobasso e Isernia</option>
                <option value="CB">Campobasso (CB)</option>
                <option value="IS">Isernia (IS)</option>
              </select>
            </label>
            <label class="field-label text-[13px] text-ink-soft">Denominazione
              <select v-model="selectedDenomination" class="select h-11 text-sm w-full">
                <option value="">Tutte</option>
                <option v-for="den in (reportData?.filter_options?.denominations || ['DOC', 'DOP', 'IGP', 'IGT'])" :key="den" :value="den">{{ den }}</option>
              </select>
            </label>
            <button
              type="button"
              :aria-pressed="isOrganicOnly"
              :class="['flex items-center justify-center sm:justify-start gap-2.5 h-11 px-4 rounded-[10px] border text-sm font-semibold transition-colors sm:col-span-2 lg:col-span-1', isOrganicOnly ? 'border-bio bg-bio-50 text-bio-900' : 'border-line-strong bg-white text-ink hover:border-ink-mute']"
              @click="toggleOrganic"
            >
              <Leaf class="w-4 h-4" aria-hidden="true" /> Solo biologici
            </button>
          </div>
        </div>
        <!-- in stampa: quali filtri erano attivi -->
        <p v-if="hasActiveFilters" class="hidden print:block m-0 text-sm text-ink-soft">Filtri: {{ filtersLabel }}</p>
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

      <nav v-if="insights" aria-label="In questa pagina" class="page-container pt-5 no-print">
        <ul class="m-0 p-0 list-none flex flex-wrap gap-2">
          <li v-for="link in pageLinks" :key="link.id"><a :href="`#${link.id}`" class="chip">{{ link.label }}</a></li>
        </ul>
      </nav>

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


      </section>

      <!-- APPROFONDIMENTI -->
      <div v-if="insights" class="page-container pb-16 md:pb-20 flex flex-col gap-14 md:gap-[72px]">
        <ReportHarvest v-if="insights.harvest?.grapes?.length" :data="insights.harvest" />
        <ReportTowns v-if="insights.towns?.length" :towns="insights.towns" />
        <ReportAltitude v-if="insights.altitude?.wines_with_data" :data="insights.altitude" />
        <ReportSoils v-if="insights.soils?.soils?.length" :data="insights.soils" />
        <ReportServing v-if="insights.serving?.length" :rows="insights.serving" />
        <ReportPrices v-if="insights.prices?.wines_with_price" :data="insights.prices" />
        <ReportHeritage v-if="insights.heritage" :data="insights.heritage" />
        <ReportPairings v-if="insights.pairings?.length" :items="insights.pairings" />
      </div>

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
          </div>
        </div>
      </section>

      <!-- FONTE DEI DATI -->
      <section id="fonte-dati" aria-labelledby="fonte-dati-title" class="page-container pt-10 md:pt-12 pb-6 scroll-mt-24">
        <div class="card p-6 md:p-8 grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)] gap-6 lg:gap-10">
          <div class="flex flex-col gap-2">
            <span class="eyebrow">Nota sui dati</span>
            <h2 id="fonte-dati-title" class="font-serif text-[28px] font-bold leading-tight m-0">Da dove vengono i numeri</h2>
          </div>
          <ul class="m-0 pl-5 list-disc flex flex-col gap-2.5 text-[15px] leading-relaxed text-ink-soft marker:text-wine-800">
            <li><strong class="text-ink">Fonte.</strong> Le statistiche sono calcolate in automatico dalle schede dei vini presenti su EnotecaMolise, compilate dalle cantine o ricavate dalle schede tecniche che i produttori pubblicano sui propri siti.</li>
            <li><strong class="text-ink">Cosa descrivono.</strong> Contano solo i vini e le cantine in catalogo: non sono statistiche ufficiali e non riguardano superfici vitate, bottiglie prodotte o vendite.</li>
            <li><strong class="text-ink">Possibili differenze.</strong> Le schede possono essere incomplete o non aggiornate e i numeri cambiano ogni volta che il catalogo si aggiorna. Prezzi e temperature sono quelli indicati dai produttori.</li>
            <li><strong class="text-ink">Come si contano.</strong> Ogni vino conta una volta, per il suo vitigno principale (quello con la percentuale più alta). I conteggi per comune si riferiscono alla zona di produzione o alla sede della cantina.</li>
            <li><strong class="text-ink">Hai notato un errore?</strong> Scrivici a <a href="mailto:info@enotecamolise.it" class="font-semibold text-wine-800 underline underline-offset-2">info@enotecamolise.it</a>: le cantine possono anche correggere le proprie schede dall'area riservata.</li>
          </ul>
        </div>
      </section>

      <!-- SCARICA -->
      <section aria-labelledby="scarica-title" class="page-container pb-8 no-print">
        <div class="rounded-2xl bg-sand border border-line p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-5">
          <div class="flex flex-col gap-1.5 max-w-[560px]">
            <h2 id="scarica-title" class="font-serif text-[26px] font-bold leading-tight m-0">Porta con te i dati</h2>
            <p class="m-0 text-[15px] text-ink-soft">
              Salva l'Osservatorio in PDF o scarica i numeri in CSV per aprirli con Excel.
              {{ hasActiveFilters ? `Il file contiene solo i dati filtrati (${filtersLabel}).` : 'Il file contiene tutto il catalogo.' }}
            </p>
          </div>
          <div class="flex flex-wrap gap-2.5 shrink-0">
            <button type="button" class="btn-outline btn-sm h-11" @click="printReport">
              <Printer class="w-4 h-4" aria-hidden="true" /> Stampa o salva PDF
            </button>
            <button type="button" class="btn-primary btn-sm h-11" :disabled="!reportData" @click="downloadCsv">
              <Download class="w-4 h-4" aria-hidden="true" /> Scarica CSV
            </button>
          </div>
        </div>
      </section>
    </template>

    <div v-else class="page-container py-16 text-center text-ink-soft">I dati dell'Osservatorio non sono disponibili in questo momento.</div>
  </div>
</template>

<script setup>
import { Printer, Download, Leaf, Info } from 'lucide-vue-next'

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

const filtersLabel = computed(() => [
  selectedProvince.value && `provincia di ${selectedProvince.value === 'CB' ? 'Campobasso' : 'Isernia'}`,
  selectedDenomination.value,
  isOrganicOnly.value && 'solo biologici'
].filter(Boolean).join(', '))

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

const { data: insights } = await useAsyncData('reports_insights', async () => {
  const queryParams = new URLSearchParams()
  if (selectedProvince.value) queryParams.append('province', selectedProvince.value)
  if (selectedDenomination.value) queryParams.append('denominazione', selectedDenomination.value)
  if (isOrganicOnly.value) queryParams.append('is_organic', 'true')
  try {
    return (await fetchWithAuth(`/reports/insights${queryParams.toString() ? `?${queryParams.toString()}` : ''}`)) || null
  } catch (err) {
    return null
  }
}, {
  watch: [selectedProvince, selectedDenomination, isOrganicOnly],
  default: () => null
})

const pageLinks = [
  { id: 'vendemmia', label: 'Vendemmia' },
  { id: 'mappa-vino', label: 'Mappa' },
  { id: 'altitudine', label: 'Altitudine' },
  { id: 'terreni', label: 'Terreni' },
  { id: 'servizio', label: 'Servizio' },
  { id: 'prezzi', label: 'Prezzi' },
  { id: 'vitigni-territorio', label: 'Autoctoni e bio' },
  { id: 'abbinamenti', label: 'Abbinamenti' }
]

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
    ['Osservatorio EnotecaMolise'],
    ['Data estrazione', new Date().toLocaleDateString('it-IT')],
    ['Filtri', filtersLabel.value || 'nessuno'],
    ['Fonte', 'Schede dei vini pubblicate su EnotecaMolise, ricavate dalle schede tecniche dei produttori. Non sono statistiche ufficiali.'],
    [''],
    ['KPI', 'Valore'],
    ['Totale Prodotti', reportData.value.kpis.total_products],
    ['Totale Cantine', reportData.value.kpis.total_producers],
    ['Totale Vitigni', reportData.value.kpis.total_grapes],
    ['Totale Abbinamenti', reportData.value.kpis.total_pairings],
    ['Gradazione Alcolica Media', fmtPct(reportData.value.kpis.avg_alcohol_degrees ?? '')],
    ['Range Annate', `${reportData.value.kpis.min_vintage_year || ''} - ${reportData.value.kpis.max_vintage_year || ''}`],
    [''],
    ['Tipologia', 'Conteggio', 'Percentuale'],
    ...(reportData.value.category_breakdown || []).map(c => [getCategoryLabel(c.category), c.count, `${fmtPct(c.percentage)}%`]),
    [''],
    ['Denominazione', 'Conteggio', 'Percentuale'],
    ...(reportData.value.denomination_breakdown || []).map(d => [d.name, d.count, `${fmtPct(d.percentage)}%`]),
    [''],
    ['Vitigno principale', 'Conteggio', 'Percentuale'],
    ...(reportData.value.top_grapes || []).map(g => [g.name, g.count, `${fmtPct(g.percentage)}%`]),
    [''],
    ['Comune Produzione', 'Conteggio Vini'],
    ...(reportData.value.zone_breakdown || []).map(z => [z.city, z.count])
  ]

  // ";" e BOM: Excel in italiano apre il file con colonne e accenti giusti
  const cell = (v) => `"${String(v ?? '').replace(/"/g, '""')}"`
  const csv = '\uFEFF' + rows.map(r => r.map(cell).join(';')).join('\r\n')
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.setAttribute('href', url)
  link.setAttribute('download', `Osservatorio_EnotecaMolise_${new Date().toISOString().slice(0,10)}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  setTimeout(() => URL.revokeObjectURL(url), 1000)
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
    }
  ].filter((p) => p.rows.length)
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
