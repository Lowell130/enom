<template>
  <div class="min-h-screen bg-stone-50 text-stone-900 pb-24">
    
    <!-- Hero Header -->
    <section class="relative bg-wine-950 text-white py-16 sm:py-20 overflow-hidden border-b border-wine-900">
      <div class="absolute inset-0 z-0 opacity-20 bg-cover bg-center" style="background-image: url('https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=1920&q=80');"></div>
      <div class="absolute inset-0 bg-gradient-to-r from-wine-950 via-wine-950/90 to-wine-900/60 z-0"></div>

      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-6">
        <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div class="max-w-3xl space-y-4">
            <div class="flex flex-wrap items-center gap-3">
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

            <div class="pt-2 flex flex-wrap items-center gap-4 text-xs text-stone-300">
              <div class="flex items-center space-x-1.5">
                <Compass class="w-4 h-4 text-amber-300" />
                <span>Copertura Regio-Territoriale (CB & IS)</span>
              </div>
              <span class="hidden sm:inline">•</span>
              <div class="flex items-center space-x-1.5">
                <Award class="w-4 h-4 text-amber-300" />
                <span>B2B Market Intelligence</span>
              </div>
            </div>
          </div>

          <!-- Hero Action Buttons (Print PDF & Export CSV) -->
          <div class="flex flex-wrap items-center gap-3 no-print shrink-0">
            <button 
              @click="printReport"
              class="inline-flex items-center space-x-2 px-4 py-2.5 bg-white/10 hover:bg-white/20 text-white font-bold text-xs rounded-xl border border-white/20 transition-all backdrop-blur-xs shadow-sm hover:scale-105"
              title="Stampa o Salva come PDF"
            >
              <Printer class="w-4 h-4 text-amber-300" />
              <span>Stampa / PDF</span>
            </button>

            <button 
              @click="downloadCsv"
              class="inline-flex items-center space-x-2 px-4 py-2.5 bg-amber-500 hover:bg-amber-600 text-stone-950 font-bold text-xs rounded-xl shadow-md transition-all hover:scale-105"
              title="Esporta i dati in formato CSV"
            >
              <Download class="w-4 h-4 text-stone-950" />
              <span>Esporta CSV</span>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Main Content Container -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 -mt-8 relative z-20 space-y-8">
      
      <!-- Interactive Dynamic Filter Bar (No Print) -->
      <div class="bg-white rounded-2xl p-4 sm:p-5 shadow-lg border border-stone-200/90 no-print flex flex-col md:flex-row items-center justify-between gap-4">
        
        <div class="flex items-center space-x-2 text-wine-900 font-bold text-xs uppercase tracking-wider shrink-0">
          <Filter class="w-4 h-4 text-wine-800" />
          <span>Filtri Osservatorio:</span>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3 w-full md:w-auto flex-1 max-w-3xl">
          <!-- Provincia Filter -->
          <div class="relative">
            <select 
              v-model="selectedProvince"
              class="w-full bg-stone-50 hover:bg-stone-100/80 focus:bg-white text-stone-800 text-xs font-semibold rounded-xl px-3 py-2.5 border border-stone-200 focus:border-wine-800 focus:outline-none transition-all cursor-pointer appearance-none pr-8"
            >
              <option value="">Tutte le Province (CB & IS)</option>
              <option value="CB">Campobasso (CB)</option>
              <option value="IS">Isernia (IS)</option>
            </select>
            <ChevronDown class="w-4 h-4 text-stone-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          <!-- Denominazione Filter -->
          <div class="relative">
            <select 
              v-model="selectedDenomination"
              class="w-full bg-stone-50 hover:bg-stone-100/80 focus:bg-white text-stone-800 text-xs font-semibold rounded-xl px-3 py-2.5 border border-stone-200 focus:border-wine-800 focus:outline-none transition-all cursor-pointer appearance-none pr-8 truncate"
            >
              <option value="">Tutte le Denominazioni</option>
              <option 
                v-for="den in (reportData?.filter_options?.denominations || ['Tintilia del Molise DOC', 'Biferno DOC', 'Pentro d\'Isernia DOC', 'Terre degli Osci IGT'])" 
                :key="den" 
                :value="den"
              >
                {{ den }}
              </option>
            </select>
            <ChevronDown class="w-4 h-4 text-stone-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          <!-- Biologico Filter Button -->
          <button 
            @click="toggleOrganic"
            :class="[
              'w-full px-3 py-2.5 rounded-xl text-xs font-bold transition-all border flex items-center justify-center space-x-2',
              isOrganicOnly 
                ? 'bg-emerald-700 text-white border-emerald-700 shadow-xs' 
                : 'bg-stone-50 text-stone-700 border-stone-200 hover:bg-stone-100'
            ]"
          >
            <Leaf class="w-3.5 h-3.5" :class="isOrganicOnly ? 'text-white' : 'text-emerald-600'" />
            <span>{{ isOrganicOnly ? 'Solo Biologici (Attivo)' : 'Filtra Biologici' }}</span>
          </button>
        </div>

        <!-- Reset Filters Button -->
        <button 
          v-if="hasActiveFilters" 
          @click="resetFilters"
          class="text-xs font-bold text-wine-800 hover:underline shrink-0"
        >
          Reset Filtri
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="pending" class="bg-white rounded-2xl shadow-xl p-12 border border-stone-200 text-center space-y-4">
        <RefreshCw class="w-8 h-8 text-wine-800 animate-spin mx-auto" />
        <p class="text-stone-500 font-medium text-sm">Elaborazione dati e analisi dell'Osservatorio in corso...</p>
      </div>

      <!-- Main Report Dashboard -->
      <div v-else-if="reportData" class="space-y-10">
        
        <!-- KPI Scorecards Grid -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <!-- Card 1: Totale Prodotti -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Prodotti</span>
              <Wine class="w-5 h-5 text-wine-800" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_products }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Vini a catalogo</div>
          </div>

          <!-- Card 2: Cantine -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Cantine</span>
              <Building2 class="w-5 h-5 text-amber-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_producers }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Produttori molisani</div>
          </div>

          <!-- Card 3: Vitigni -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Vitigni</span>
              <Sparkles class="w-5 h-5 text-purple-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_grapes }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Varietà mappate</div>
          </div>

          <!-- Card 4: Abbinamenti -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Abbinamenti</span>
              <Utensils class="w-5 h-5 text-emerald-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.total_pairings }}</div>
            <div class="text-[11px] text-stone-500 mt-1">Gusti e piatti</div>
          </div>

          <!-- Card 5: Gradazione Media -->
          <div class="bg-white rounded-2xl p-5 shadow-xs border border-stone-200/80 hover:shadow-md transition-shadow">
            <div class="flex items-center justify-between text-stone-400 mb-2">
              <span class="text-[11px] font-bold uppercase tracking-wider text-stone-500">Gradazione</span>
              <Gauge class="w-5 h-5 text-rose-700" />
            </div>
            <div class="font-serif text-3xl font-bold text-stone-900">{{ reportData.kpis.avg_alcohol_degrees }}°</div>
            <div class="text-[11px] text-stone-500 mt-1">Alcol medio (% vol)</div>
          </div>
        </div>

        <!-- Box Informativo Osservatorio -->
        <div class="bg-gradient-to-r from-amber-50 via-orange-50/40 to-wine-50/50 p-6 sm:p-7 rounded-2xl border border-amber-200/80 shadow-xs relative overflow-hidden">
          <div class="flex flex-col md:flex-row items-start md:items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-300 text-wine-900 flex items-center justify-center shrink-0">
              <Info class="w-6 h-6 text-wine-900" />
            </div>
            
            <div class="flex-1 space-y-1.5">
              <div class="flex items-center space-x-2">
                <h3 class="font-serif text-lg font-bold text-wine-950">
                  Nota Informativa sui Dati & Metodologia
                </h3>
                <span class="px-2 py-0.5 bg-wine-800 text-white rounded-md text-[10px] font-bold uppercase tracking-wider">
                  Info Osservatorio
                </span>
              </div>
              
              <p class="text-xs sm:text-sm text-stone-700 font-normal leading-relaxed">
                L'Osservatorio raccoglie e sintetizza i dati delle schede tecniche censite nel database di EnotecaMolise.
                I conteggi nella <strong class="text-wine-900">Mappa dei Comuni</strong> indicano il numero esatto di <strong>etichette/vini prodotte in ciascun comune</strong> (riferite alla <em>Zona di Produzione</em> o alla sede della cantina). I formati delle bottiglie e tutte le analisi tecniche vengono censiti e aggiornati in tempo reale.
              </p>
            </div>
          </div>
        </div>

        <!-- Section 1: Visual Breakdown con Grafici SVG Donut Charts & Barre -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          <!-- Tipologia Enologica (Rosso, Bianco, Rosato, ecc) con Donut Chart SVG -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Ripartizione per Tipologia</h2>
                <p class="text-xs text-stone-500">Distribuzione percentuale dei vini in catalogo</p>
              </div>
              <PieChart class="w-5 h-5 text-wine-800" />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-12 gap-6 items-center">
              
              <!-- Interactive SVG Donut Chart Visual -->
              <div class="sm:col-span-5 flex flex-col items-center justify-center relative py-2">
                <svg viewBox="0 0 100 100" class="w-36 h-36 transform -rotate-90">
                  <circle cx="50" cy="50" r="40" fill="transparent" stroke="#F5F5F4" stroke-width="14" />
                  <circle 
                    v-for="(segment, idx) in categorySegments" 
                    :key="segment.category"
                    cx="50" 
                    cy="50" 
                    r="40" 
                    fill="transparent" 
                    :stroke="segment.color" 
                    stroke-width="14"
                    :stroke-dasharray="`${segment.dashArray} 251.2`"
                    :stroke-dashoffset="segment.dashOffset"
                    class="transition-all duration-700 hover:opacity-80 cursor-pointer"
                  />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                  <span class="font-serif text-2xl font-bold text-stone-900">{{ reportData.kpis.total_products }}</span>
                  <span class="text-[10px] text-stone-400 font-semibold uppercase tracking-wider">Etichette</span>
                </div>
              </div>

              <!-- Legend & Breakdown List -->
              <div class="sm:col-span-7 space-y-3">
                <div v-for="item in reportData.category_breakdown" :key="item.category" class="space-y-1">
                  <div class="flex justify-between text-xs">
                    <span class="font-medium text-stone-800 flex items-center space-x-1.5">
                      <span class="w-2.5 h-2.5 rounded-full inline-block" :class="getCategoryColorClass(item.category)"></span>
                      <span>{{ getCategoryLabel(item.category) }}</span>
                    </span>
                    <span class="font-mono text-stone-600 font-semibold">{{ item.count }} vini ({{ item.percentage }}%)</span>
                  </div>
                  <div class="w-full bg-stone-100 h-2 rounded-full overflow-hidden">
                    <div 
                      class="h-full rounded-full transition-all duration-500"
                      :class="getCategoryColorClass(item.category)"
                      :style="{ width: item.percentage + '%' }"
                    ></div>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <!-- Denominazioni (DOC, IGT, DOP) con Link Interattivi -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Denominazioni di Origine</h2>
                <p class="text-xs text-stone-500">Qualità certificata e denominazioni tutelate</p>
              </div>
              <Award class="w-5 h-5 text-amber-700" />
            </div>

            <div class="space-y-3">
              <NuxtLink 
                v-for="den in reportData.denomination_breakdown" 
                :key="den.name"
                :to="`/vini?search=${encodeURIComponent(den.name)}`"
                class="p-4 bg-stone-50 hover:bg-amber-50/50 rounded-xl border border-stone-100 hover:border-amber-200 transition-all flex items-center justify-between group"
              >
                <div class="space-y-1">
                  <span class="inline-block px-2.5 py-0.5 text-xs font-bold bg-amber-100 text-amber-900 rounded-md uppercase tracking-wider group-hover:bg-amber-200 transition-colors">
                    {{ den.name }}
                  </span>
                  <div class="text-xs text-stone-500 group-hover:text-amber-900 transition-colors">
                    Vedi vini in catalogo con denominazione {{ den.name }} &rarr;
                  </div>
                </div>
                <div class="text-right">
                  <div class="font-serif text-2xl font-bold text-wine-900 group-hover:scale-105 transition-transform">{{ den.count }}</div>
                  <div class="text-xs text-stone-500 font-mono">{{ den.percentage }}% del totale</div>
                </div>
              </NuxtLink>
            </div>
          </div>

        </div>

        <!-- Section 2: Leaderboard Vitigni Autoctoni & Zone di Produzione -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <!-- Top Vitigni (2 Col) con Link al Catalogo -->
          <div class="lg:col-span-2 bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Vitigni più Diffusi & Rappresentativi</h2>
                <p class="text-xs text-stone-500">Clicca su un vitigno per esplorare le etichette in catalogo</p>
              </div>
              <Sparkles class="w-5 h-5 text-wine-800" />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <NuxtLink 
                v-for="(grape, idx) in reportData.top_grapes.slice(0, 8)" 
                :key="grape.name"
                :to="`/vini?search=${encodeURIComponent(grape.name)}`"
                class="p-4 rounded-xl border border-stone-100 bg-stone-50/60 hover:bg-wine-50/40 hover:border-wine-200 transition-all flex items-center space-x-3 group"
              >
                <div class="w-8 h-8 rounded-full bg-wine-800 text-amber-200 flex items-center justify-center font-bold text-xs shrink-0 group-hover:bg-wine-900 transition-colors">
                  #{{ idx + 1 }}
                </div>
                <div class="flex-1 min-w-0">
                  <div class="font-bold text-stone-900 text-sm truncate group-hover:text-wine-900 transition-colors">{{ grape.name }}</div>
                  <div class="text-xs text-stone-500">{{ grape.count }} etichette ({{ grape.percentage }}%)</div>
                </div>
                <ArrowRight class="w-4 h-4 text-stone-400 group-hover:text-wine-800 group-hover:translate-x-1 transition-all shrink-0" />
              </NuxtLink>
            </div>
          </div>

          <!-- Zone di Produzione / Mappa Comuni (1 Col) con Link -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Mappa dei Comuni</h2>
                <p class="text-xs text-stone-500">Concentrazione etichette per comune</p>
              </div>
              <MapPin class="w-5 h-5 text-rose-700" />
            </div>

            <div class="space-y-3 max-h-[340px] overflow-y-auto pr-1">
              <NuxtLink 
                v-for="zone in reportData.zone_breakdown" 
                :key="zone.city"
                :to="`/vini?search=${encodeURIComponent(zone.city)}`"
                class="flex items-center justify-between p-3 rounded-lg bg-stone-50 hover:bg-rose-50/50 border border-stone-100 hover:border-rose-200 transition-all text-sm group"
              >
                <div class="flex items-center space-x-2">
                  <MapPin class="w-4 h-4 text-wine-800 shrink-0 group-hover:text-rose-700 transition-colors" />
                  <span class="font-medium text-stone-800 group-hover:text-rose-900 transition-colors">{{ zone.city }}</span>
                </div>
                <span class="px-2.5 py-1 bg-stone-200/70 group-hover:bg-rose-200 group-hover:text-rose-950 text-stone-800 rounded-full font-mono text-xs font-semibold transition-colors">
                  {{ zone.count }} {{ zone.count === 1 ? 'vino' : 'vini' }}
                </span>
              </NuxtLink>
            </div>
          </div>

        </div>

        <!-- Section 3: Analisi Tecniche del Terroir & Affinamento Acciaio vs Legno -->
        <div class="space-y-8">
          
          <!-- Widget Speciale: Analisi Affinamento (Acciaio vs Legno) -->
          <div v-if="reportData.wood_vs_steel" class="bg-gradient-to-r from-amber-950 via-stone-900 to-wine-950 text-white rounded-2xl p-6 sm:p-8 shadow-xl border border-amber-500/20 space-y-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
              <div>
                <span class="text-xs font-bold uppercase tracking-widest text-amber-400 block mb-1">Tecniche di Cantina</span>
                <h3 class="font-serif text-2xl font-light text-white">Stili di Affinamento: Legno vs Acciaio</h3>
              </div>
              <div class="flex items-center space-x-3 text-xs">
                <span class="inline-flex items-center space-x-1.5 px-3 py-1 bg-amber-400/20 text-amber-300 rounded-full border border-amber-400/30">
                  <span>🪵 Legno (Barrique/Botte): {{ reportData.wood_vs_steel.wood_percentage }}%</span>
                </span>
                <span class="inline-flex items-center space-x-1.5 px-3 py-1 bg-cyan-400/20 text-cyan-300 rounded-full border border-cyan-400/30">
                  <span>🧪 Acciaio / Inox: {{ reportData.wood_vs_steel.steel_percentage }}%</span>
                </span>
              </div>
            </div>

            <div class="space-y-3">
              <div class="flex justify-between text-xs font-medium text-stone-300">
                <span>Affinamento in Legno ({{ reportData.wood_vs_steel.wood_count }} etichette)</span>
                <span>Affinamento in Acciaio ({{ reportData.wood_vs_steel.steel_count }} etichette)</span>
              </div>
              <!-- Comparison bar -->
              <div class="w-full h-4 bg-stone-800 rounded-full overflow-hidden flex border border-white/10">
                <div 
                  class="h-full bg-gradient-to-r from-amber-600 to-amber-500 transition-all duration-700" 
                  :style="{ width: reportData.wood_vs_steel.wood_percentage + '%' }"
                  title="Affinati in Legno/Barrique/Botte"
                ></div>
                <div 
                  class="h-full bg-gradient-to-r from-cyan-600 to-cyan-500 transition-all duration-700" 
                  :style="{ width: reportData.wood_vs_steel.steel_percentage + '%' }"
                  title="Affinati in Acciaio Inox"
                ></div>
              </div>
            </div>
          </div>

          <!-- Caratteristiche Tecniche (5 Col) -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-2xl font-semibold text-stone-900">Analisi Tecniche del Terroir & Enologia</h2>
                <p class="text-xs text-stone-500">Dettaglio di affinamento, vinificazione, altitudini, formati bottiglia e sistemi d'allevamento</p>
              </div>
              <Layers class="w-6 h-6 text-wine-800" />
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 sm:gap-6">
              
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
                  <li v-if="!reportData.technical_analytics.vinificazione?.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
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
                  <li v-if="!reportData.technical_analytics.affinamento?.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
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
                  <li v-if="!reportData.technical_analytics.allevamento?.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
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
                  <li v-if="!reportData.technical_analytics.altitudine?.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
                </ul>
              </div>

              <!-- Formato Bottiglia -->
              <div class="space-y-3 bg-stone-50 p-4 rounded-xl border border-stone-100">
                <div class="text-xs font-bold uppercase tracking-wider text-blue-800 flex items-center space-x-1.5">
                  <Box class="w-4 h-4" />
                  <span>Formato Bottiglia</span>
                </div>
                <ul class="space-y-2">
                  <li v-for="fmt in reportData.technical_analytics.formato" :key="fmt.name" class="flex justify-between text-xs border-b border-stone-200/40 pb-1.5">
                    <span class="text-stone-700 truncate mr-2" :title="fmt.name">{{ fmt.name }}</span>
                    <span class="font-semibold text-stone-900 shrink-0">{{ fmt.count }}</span>
                  </li>
                  <li v-if="!reportData.technical_analytics.formato?.length" class="text-xs text-stone-400 italic">Dati non pervenuti</li>
                </ul>
              </div>

            </div>
          </div>

        </div>

        <!-- Section 4: Abbinamenti Gastronomici e B2B Market Insights -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          <!-- Top Abbinamenti Gastronomici (1 Col) con Link -->
          <div class="bg-white rounded-2xl p-6 sm:p-8 shadow-xs border border-stone-200/80 space-y-6">
            <div class="flex items-center justify-between border-b border-stone-100 pb-4">
              <div>
                <h2 class="font-serif text-xl font-semibold text-stone-900">Abbinamenti di Gusto</h2>
                <p class="text-xs text-stone-500">Gastronomia tradizionale e abbinamenti consigliati</p>
              </div>
              <Utensils class="w-5 h-5 text-emerald-700" />
            </div>

            <div class="flex flex-wrap gap-2">
              <NuxtLink 
                v-for="p in reportData.top_pairings" 
                :key="p.name"
                :to="`/vini?search=${encodeURIComponent(p.name)}`"
                class="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 rounded-lg text-xs font-medium border border-emerald-100 hover:border-emerald-300 transition-all group"
              >
                <span>{{ p.name }}</span>
                <span class="px-1.5 py-0.2 bg-emerald-200 text-emerald-900 rounded text-[10px] font-mono font-bold group-hover:bg-emerald-300">{{ p.count }}</span>
              </NuxtLink>
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
        Nessun dato disponibile per i filtri selezionati.
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
  RefreshCw,
  Info,
  Box,
  Printer,
  Download,
  Filter,
  ChevronDown,
  Leaf,
  ArrowRight
} from 'lucide-vue-next'

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

// Category Donut Chart SVG Segments Computation
const categorySegments = computed(() => {
  const list = reportData.value?.category_breakdown || []
  const total = reportData.value?.kpis?.total_products || 1
  let cumulativePct = 0

  return list.map(item => {
    const pct = item.percentage || 0
    const dashArray = (pct / 100) * 251.2
    const dashOffset = -((cumulativePct / 100) * 251.2)
    cumulativePct += pct

    let color = '#78716C'
    const cat = item.category?.toUpperCase() || ''
    if (cat.includes('ROSSO')) color = '#6B1D2F'
    else if (cat.includes('BIANCO')) color = '#F59E0B'
    else if (cat.includes('ROSATO')) color = '#FB7185'
    else if (cat.includes('SPUMANTE')) color = '#06B6D4'
    else if (cat.includes('PASSITO')) color = '#D97706'

    return {
      category: item.category,
      dashArray: dashArray.toFixed(1),
      dashOffset: dashOffset.toFixed(1),
      color
    }
  })
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

<style>
/* Print Styles for PDF & Hardcopy Output */
@media print {
  /* Hide site navbar, footer and non-printable elements */
  header, footer, nav, .no-print, button {
    display: none !important;
  }
  
  body, .min-h-screen {
    background: #FFFFFF !important;
    color: #000000 !important;
    padding-bottom: 0 !important;
  }

  .max-w-7xl {
    max-width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
  }

  /* Force print background colors and graphics */
  * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }
}
</style>
