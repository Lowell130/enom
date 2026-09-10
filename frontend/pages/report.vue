<template>
  <div class="min-h-screen bg-stone-50 text-stone-900 pb-24">
    <!-- Hero Header -->
    <section class="relative bg-wine-950 text-white py-20 overflow-hidden border-b border-wine-900">
      <div class="absolute inset-0 z-0 opacity-20 bg-cover bg-center" style="background-image: url('https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=1920&q=80');"></div>
      <div class="absolute inset-0 bg-gradient-to-r from-wine-950 via-wine-950/90 to-wine-900/60 z-0"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div class="max-w-3xl space-y-4">
          <div class="flex items-center space-x-3">
            <span class="inline-flex items-center space-x-2 px-3 py-1 bg-amber-400/10 text-amber-300 rounded-full text-xs font-semibold uppercase tracking-wider border border-amber-400/20 backdrop-blur-xs">
              <BarChart3 class="w-3.5 h-3.5 text-amber-300" />
              <span>Osservatorio Enologico Molisano</span>
            </span>
            <span class="text-xs text-stone-400 font-mono">Aggiornato in Tempo Reale</span>
          </div>

          <h1 class="font-serif text-3xl sm:text-5xl lg:text-6xl font-light tracking-tight text-white leading-tight">
            Report & Analisi del Patrimonio Vitivinicolo del Molise
          </h1>

          <p class="text-base sm:text-lg text-stone-300 font-light leading-relaxed">
            Panoramica completa e dati analitici su vitigni, denominazioni, zone di produzione e profili tecnici dei vini censiti nel catalogo EnotecaMolise.
          </p>

          <div class="pt-2 flex items-center space-x-4 text-xs text-stone-300">
            <div class="flex items-center space-x-1.5">
              <Compass class="w-4 h-4 text-amber-300" />
              <span>Copertura Regio-Territoriale (CB & IS)</span>
            </div>
            <span>•</span>
            <div class="flex items-center space-x-1.5">
              <Award class="w-4 h-4 text-amber-300" />
              <span>B2B Market Intelligence</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-20">
      
      <!-- Loading State -->
      <div v-if="pending" class="bg-white rounded-2xl shadow-xl p-12 border border-stone-200 text-center space-y-4">
        <RefreshCw class="w-8 h-8 text-wine-800 animate-spin mx-auto" />
        <p class="text-stone-500 font-medium">Elaborazione dati e analisi in corso...</p>
      </div>

      <!-- Main Report Dashboard -->
      <div v-else-if="reportData" class="space-y-12">
        
        <!-- KPI Scorecards Grid -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <!-- Card 1: Totale Prodotti -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">Prodotti</span>
              <Wine class="w-5 h-5 text-wine-800" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_products }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Vini censiti a catalogo</div>
          </div>

          <!-- Card 2: Cantine -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">Cantine</span>
              <Building2 class="w-5 h-5 text-amber-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_producers }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Aziende vitivinicole</div>
          </div>

          <!-- Card 3: Vitigni -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">Vitigni</span>
              <Sparkles class="w-5 h-5 text-purple-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_grapes }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Varietà mappate</div>
          </div>

          <!-- Card 4: Abbinamenti -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">Abbinamenti</span>
              <Utensils class="w-5 h-5 text-emerald-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_pairings }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Combinazioni di gusto</div>
          </div>

          <!-- Card 5: Gradazione Media -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">Gradazione</span>
              <Gauge class="w-5 h-5 text-rose-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.avg_alcohol_degrees }}°</div>
            <div class="text-[11px] text-stone-500 mt-1">Alcol medio (% vol)</div>
          </div>

          <!-- Card 6: Annate -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-xs font-semibold uppercase tracking-wider text-stone-500">Annate</span>
              <Calendar class="w-5 h-5 text-blue-700" />
            </div>
            <div class="font-serif text-2xl font-bold text-stone-900 truncate">
              {{ reportData.kpis.min_vintage_year || 'N/D' }} - {{ reportData.kpis.max_vintage_year || 'N/D' }}
            </div>
            <div class="text-[11px] text-stone-500 mt-1">Range vendemmie</div>
          </div>
        </div>

        <!-- Section 1: Breakdown per Tipologia e Denominazione -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          <!-- Tipologia Enologica (Rosso, Bianco, Rosato, ecc) -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Ripartizione per Tipologia</h2>
                <p class="text-xs text-stone-500">Distribuzione percentuale dei vini in catalogo</p>
              </div>
              <PieChart class="w-5 h-5 text-wine-800" />
            </div>

            <div class="space-y-4">
              <div v-for="item in reportData.category_breakdown" :key="item.category" class="space-y-1.5">
                <div class="flex justify-between text-sm">
                  <span class="font-medium text-stone-800 capitalize">{{ getCategoryLabel(item.category) }}</span>
                  <span class="font-mono text-stone-600 font-semibold">{{ item.count }} vini ({{ item.percentage }}%)</span>
                </div>
                <!-- Progress bar -->
                <div class="w-full bg-stone-100 h-3 rounded-full overflow-hidden">
                  <div 
                    class="h-full rounded-full transition-all duration-500"
                    :class="getCategoryColorClass(item.category)"
                    :style="{ width: item.percentage + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- Denominazioni (DOC, IGT, DOP) -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Denominazioni di Origine</h2>
                <p class="text-xs text-stone-500">Qualità certificata e denominazioni tutelate</p>
              </div>
              <Award class="w-5 h-5 text-amber-700" />
            </div>

            <div class="space-y-4">
              <div v-for="den in reportData.denomination_breakdown" :key="den.name" class="p-4 bg-stone-50 rounded-xl border border-stone-100 flex items-center justify-between">
                <div class="space-y-1">
                  <span class="inline-block px-2.5 py-0.5 text-xs font-bold bg-amber-100 text-amber-900 rounded-md uppercase tracking-wider">
                    {{ den.name }}
                  </span>
                  <div class="text-xs text-stone-500">
                    Certificazione ufficiale del territorio
                  </div>
                </div>
                <div class="text-right">
                  <div class="font-serif text-2xl font-bold text-wine-900">{{ den.count }}</div>
                  <div class="text-xs text-stone-500 font-mono">{{ den.percentage }}% del totale</div>
                </div>
              </div>
            </div>
          </div>

        </div>

        <!-- Section 2: Leaderboard Vitigni Autoctoni & Zone di Produzione -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <!-- Top Vitigni (2 Col) -->
          <div class="lg:col-span-2 bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Vitigni più Diffusi & Rappresentativi</h2>
                <p class="text-xs text-stone-500">Presenza dei vitigni nelle schede tecniche dei vini</p>
              </div>
              <Sparkles class="w-5 h-5 text-wine-800" />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div 
                v-for="(grape, idx) in reportData.top_grapes.slice(0, 8)" 
                :key="grape.name"
                class="p-4 rounded-xl border border-stone-100 bg-stone-50/60 hover:bg-stone-50 transition-colors flex items-center space-x-3"
              >
                <div class="w-8 h-8 rounded-full bg-wine-800 text-amber-200 flex items-center justify-center font-bold text-xs shrink-0">
                  #{{ idx + 1 }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="font-medium text-stone-900 text-sm truncate">{{ grape.name }}</div>
                  <div class="text-xs text-stone-500">{{ grape.count }} etichette ({{ grape.percentage }}%)</div>
                </div>
              </div>
            </div>
          </div>

          <!-- Zone di Produzione (1 Col) -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Mappa dei Comuni</h2>
                <p class="text-xs text-stone-500">Concentrazione produttiva</p>
              </div>
              <MapPin class="w-5 h-5 text-rose-700" />
            </div>

            <div class="space-y-3 max-h-[340px] overflow-y-auto pr-1">
              <div 
                v-for="zone in reportData.zone_breakdown" 
                :key="zone.city"
                class="flex items-center justify-between p-3 rounded-lg bg-stone-50 border border-stone-100 text-sm"
              >
                <div class="flex items-center space-x-2">
                  <MapPin class="w-4 h-4 text-wine-800 shrink-0" />
                  <span class="font-medium text-stone-800">{{ zone.city }}</span>
                </div>
                <span class="px-2.5 py-1 bg-stone-200/70 text-stone-800 rounded-full font-mono text-xs font-semibold">
                  {{ zone.count }} {{ zone.count === 1 ? 'vino' : 'vini' }}
                </span>
              </div>
            </div>
          </div>

        </div>

        <!-- Section 3: Caratteristiche Tecniche (Affinamento, Vinificazione, Allevamento, Altitudine) -->
        <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
          <div class="flex items-center justify-between border-b border-stone-100 pb-4">
            <div>
              <h2 class="font-serif text-2xl font-semibold text-stone-900">Analisi Tecniche del Terroir & Enologia</h2>
              <p class="text-xs text-stone-500">Dettaglio di affinamento, vinificazione, altitudini e sistemi d'allevamento</p>
            </div>
            <Layers class="w-6 h-6 text-wine-800" />
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            
            <!-- Vinificazione -->
            <div class="space-y-3 bg-stone-50 p-4 rounded-xl border border-stone-100">
              <div class="text-xs font-bold uppercase tracking-wider text-wine-800 flex items-center space-x-1.5">
                <Wine class="w-4 h-4" />
                <span>Vinificazione</span>
              </div>
              <ul class="space-y-2">
                <li v-for="v in reportData.technical_analytics.vinificazione" :key="v.name" class="flex justify-between text-xs border-b border-stone-200/40 pb-1.5">
                  <span class="text-stone-700 truncate mr-2" :title="v.name">{{ v.name }}</span>
                  <span class="font-semibold text-stone-900 shrink-0">{{ v.count }}</span>
                </li>
                <li v-if="!reportData.technical_analytics.vinificazione.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
              </ul>
            </div>

            <!-- Affinamento -->
            <div class="space-y-3 bg-stone-50 p-4 rounded-xl border border-stone-100">
              <div class="text-xs font-bold uppercase tracking-wider text-amber-800 flex items-center space-x-1.5">
                <Layers class="w-4 h-4" />
                <span>Affinamento</span>
              </div>
              <ul class="space-y-2">
                <li v-for="a in reportData.technical_analytics.affinamento" :key="a.name" class="flex justify-between text-xs border-b border-stone-200/40 pb-1.5">
                  <span class="text-stone-700 truncate mr-2" :title="a.name">{{ a.name }}</span>
                  <span class="font-semibold text-stone-900 shrink-0">{{ a.count }}</span>
                </li>
                <li v-if="!reportData.technical_analytics.affinamento.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
              </ul>
            </div>

            <!-- Allevamento -->
            <div class="space-y-3 bg-stone-50 p-4 rounded-xl border border-stone-100">
              <div class="text-xs font-bold uppercase tracking-wider text-purple-800 flex items-center space-x-1.5">
                <Compass class="w-4 h-4" />
                <span>Allevamento</span>
              </div>
              <ul class="space-y-2">
                <li v-for="al in reportData.technical_analytics.allevamento" :key="al.name" class="flex justify-between text-xs border-b border-stone-200/40 pb-1.5">
                  <span class="text-stone-700 truncate mr-2" :title="al.name">{{ al.name }}</span>
                  <span class="font-semibold text-stone-900 shrink-0">{{ al.count }}</span>
                </li>
                <li v-if="!reportData.technical_analytics.allevamento.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
              </ul>
            </div>

            <!-- Altitudine -->
            <div class="space-y-3 bg-stone-50 p-4 rounded-xl border border-stone-100">
              <div class="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center space-x-1.5">
                <TrendingUp class="w-4 h-4" />
                <span>Altitudine Vigneti</span>
              </div>
              <ul class="space-y-2">
                <li v-for="alt in reportData.technical_analytics.altitudine" :key="alt.name" class="flex justify-between text-xs border-b border-stone-200/40 pb-1.5">
                  <span class="text-stone-700 truncate mr-2" :title="alt.name">{{ alt.name }}</span>
                  <span class="font-semibold text-stone-900 shrink-0">{{ alt.count }}</span>
                </li>
                <li v-if="!reportData.technical_analytics.altitudine.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
              </ul>
            </div>

          </div>
        </div>

        <!-- Section 4: Abbinamenti Gastronomici e B2B Market Insights -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <!-- Top Abbinamenti Gastronomici (1 Col) -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Abbinamenti di Gusto</h2>
                <p class="text-xs text-stone-500">Gastronomia tradizionale e abbinamenti consigliati</p>
              </div>
              <Utensils class="w-5 h-5 text-emerald-700" />
            </div>

            <div class="flex flex-wrap gap-2">
              <span 
                v-for="p in reportData.top_pairings" 
                :key="p.name"
                class="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-50 text-emerald-900 rounded-lg text-xs font-medium border border-emerald-100"
              >
                <span>{{ p.name }}</span>
                <span class="px-1.5 py-0.2 bg-emerald-200 text-emerald-900 rounded text-[10px] font-mono font-bold">{{ p.count }}</span>
              </span>
            </div>
          </div>

          <!-- B2B Executive Insights Narrative (2 Col) -->
          <div class="lg:col-span-2 bg-gradient-to-br from-wine-900 to-wine-950 text-white rounded-2xl p-6 sm:p-8 shadow-lg space-y-6 border border-wine-800">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-full bg-amber-400/20 flex items-center justify-center text-amber-300 border border-amber-400/30">
                <BookOpen class="w-5 h-5" />
              </div>
              <div>
                <h3 class="font-serif text-xl font-semibold text-amber-200">Analisi Strategica dell'Enologia Molisana</h3>
                <p class="text-xs text-stone-300">Executive Summary & Prospettive di Mercato</p>
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-stone-300 font-light leading-relaxed">
              <div class="space-y-2 bg-white/5 p-4 rounded-xl border border-white/10">
                <h4 class="font-semibold text-white text-base">La Tintilia come Brand Regio</h4>
                <p>
                  La Tintilia del Molise DOC rappresenta la punta di diamante e l'elemento identificativo sui mercati internazionali. La quota di vitigni autoctoni testimonia la forte identità e il legame con la biodiversità locale.
                </p>
              </div>

              <div class="space-y-2 bg-white/5 p-4 rounded-xl border border-white/10">
                <h4 class="font-semibold text-white text-base">Microclimi e Terroir Diversificati</h4>
                <p>
                  Dalle fasce collinari di Campomarino vicine al mare alle zone interne ad alta quota di Castropignano e Isernia, l'escursione termica favorisce una spiccata acidità e profili aromatici unici.
                </p>
              </div>
            </div>

            <div class="pt-2 border-t border-white/10 flex items-center justify-between text-xs text-stone-400">
              <span>Fonte: Database Unificato EnotecaMolise</span>
              <NuxtLink to="/vini" class="text-amber-300 hover:underline font-medium inline-flex items-center space-x-1">
                <span>Esplora tutti i vini in catalogo &rarr;</span>
              </NuxtLink>
            </div>
          </div>

        </div>

      </div>

      <!-- Fallback Error / Empty -->
      <div v-else class="bg-white rounded-2xl shadow-md p-12 text-center text-stone-500">
        Nessun dato disponibile al momento.
      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  BarChart3, 
  Wine, 
  Building2, 
  Sparkles, 
  Utensils, 
  Gauge, 
  Calendar, 
  PieChart, 
  Award, 
  MapPin, 
  Layers, 
  TrendingUp, 
  Compass, 
  BookOpen,
  RefreshCw
} from 'lucide-vue-next'

const { fetchWithAuth } = useApi()

useHead({
  title: 'Osservatorio Enologico del Molise | Report & Analisi Data Vini',
  meta: [
    { name: 'description', content: 'Report strategico e osservatorio sui vini, cantine, vitigni e denominazioni della regione Molise.' }
  ]
})

const { data: reportData, pending } = await useAsyncData('reports_summary', () => 
  fetchWithAuth('/reports/summary')
)

// Helpers
const getCategoryLabel = (cat) => {
  const labels = {
    'ROSSO': 'Vini Rossi',
    'VINO_ROSSO': 'Vini Rossi',
    'BIANCO': 'Vini Bianchi',
    'VINO_BIANCO': 'Vini Bianchi',
    'ROSATO': 'Vini Rosati',
    'PASSITO': 'Vini Passiti / Dolci',
    'SPUMANTE': 'Bollicine / Spumanti',
    'ALTRO': 'Altre Tipologie'
  }
  return labels[cat?.toUpperCase()] || cat
}

const getCategoryColorClass = (cat) => {
  switch (cat?.toUpperCase()) {
    case 'ROSSO':
    case 'VINO_ROSSO':
      return 'bg-wine-800'
    case 'BIANCO':
    case 'VINO_BIANCO':
      return 'bg-amber-400'
    case 'ROSATO':
      return 'bg-rose-400'
    case 'PASSITO':
      return 'bg-amber-600'
    case 'SPUMANTE':
      return 'bg-cyan-500'
    default:
      return 'bg-stone-500'
  }
}
</script>
