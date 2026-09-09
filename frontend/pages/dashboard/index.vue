<template>
  <div class="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <!-- Dashboard Header -->
    <div class="bg-white rounded-3xl p-8 border border-stone-200/70 shadow-xs mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
      <div>
        <div class="flex items-center space-x-2">
          <span v-if="isAdmin" class="px-3 py-1 bg-wine-800 text-amber-200 font-bold text-xs rounded-full uppercase tracking-wider inline-flex items-center space-x-1">
            <ShieldCheck class="w-3.5 h-3.5" />
            <span>Super Admin</span>
          </span>
          <span v-else class="px-3 py-1 bg-emerald-800 text-emerald-100 font-bold text-xs rounded-full uppercase tracking-wider inline-flex items-center space-x-1">
            <Building2 class="w-3.5 h-3.5" />
            <span>Produttore Cantina</span>
          </span>
          <span class="text-xs text-stone-400">• {{ user?.email }}</span>
        </div>
        <h1 class="font-sans text-3xl font-extrabold text-stone-900 mt-3 tracking-tight">
          Benvenuto nella tua Dashboard
        </h1>
        <p class="text-xs text-stone-500 mt-1 leading-relaxed">
          <span v-if="isAdmin">Gestisci l'intero catalogo, le cantine, i campi della scheda tecnica e l'associazione vini del Molise.</span>
          <span v-else>Gestisci la produzione vini e il profilo della tua cantina ({{ user?.producer?.company_name || 'Cantina' }}).</span>
        </p>
      </div>

      <div class="mt-2 md:mt-0 flex gap-3">
        <NuxtLink to="/dashboard/prodotti/nuovo" class="px-5 py-3 bg-wine-800 hover:bg-wine-900 text-white font-bold text-sm rounded-xl shadow-xs transition-all inline-flex items-center space-x-2">
          <Plus class="w-4 h-4 text-amber-200" />
          <span>Inserisci Nuovo Vino</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Quick Navigation Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6 mb-10">
      
      <!-- Card Prodotti -->
      <NuxtLink to="/dashboard/prodotti" class="bg-white p-6 rounded-2xl border border-stone-200/70 shadow-2xs hover:shadow-md hover:border-wine-200 transition-all group flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="w-11 h-11 rounded-xl bg-wine-50 text-wine-800 flex items-center justify-center transition-colors">
              <Wine class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold text-wine-800 inline-flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
              <span>Gestisci</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </div>
          <h3 class="font-sans text-base font-bold text-stone-900 mt-4 group-hover:text-wine-900 transition-colors">Catalogo Prodotti</h3>
          <p class="text-xs text-stone-500 mt-1 leading-relaxed">Aggiungi, modifica e clona i vini in 1-Click.</p>
        </div>
      </NuxtLink>

      <!-- Card Profilo Cantina (For Producer) -->
      <NuxtLink v-if="isProducer" to="/dashboard/profilo" class="bg-white p-6 rounded-2xl border border-stone-200/70 shadow-2xs hover:shadow-md hover:border-amber-200 transition-all group flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="w-11 h-11 rounded-xl bg-amber-50 text-amber-800 flex items-center justify-center transition-colors">
              <Store class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold text-amber-800 inline-flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
              <span>Profilo</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </div>
          <h3 class="font-sans text-base font-bold text-stone-900 mt-4 group-hover:text-amber-900 transition-colors">Profilo Cantina</h3>
          <p class="text-xs text-stone-500 mt-1 leading-relaxed">Modifica storia, foto copertina e contatti.</p>
        </div>
      </NuxtLink>

      <!-- Card Messaggi -->
      <NuxtLink to="/dashboard/messaggi" class="bg-white p-6 rounded-2xl border border-stone-200/70 shadow-2xs hover:shadow-md hover:border-emerald-200 transition-all group flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="w-11 h-11 rounded-xl bg-emerald-50 text-emerald-800 flex items-center justify-center transition-colors">
              <Mail class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold text-emerald-800 inline-flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
              <span>Leggi</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </div>
          <h3 class="font-sans text-base font-bold text-stone-900 mt-4 group-hover:text-emerald-900 transition-colors">Richieste Contatto</h3>
          <p class="text-xs text-stone-500 mt-1 leading-relaxed">Messaggi degli utenti su prezzi e disponibilità.</p>
        </div>
      </NuxtLink>

      <!-- Card Admin Cantine (Only for Admin) -->
      <NuxtLink v-if="isAdmin" to="/dashboard/cantine" class="bg-white p-6 rounded-2xl border border-stone-200/70 shadow-2xs hover:shadow-md hover:border-amber-200 transition-all group flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="w-11 h-11 rounded-xl bg-amber-50 text-amber-800 flex items-center justify-center transition-colors">
              <Building2 class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold text-amber-800 inline-flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
              <span>Amministra</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </div>
          <h3 class="font-sans text-base font-bold text-stone-900 mt-4 group-hover:text-amber-900 transition-colors">Gestione Cantine</h3>
          <p class="text-xs text-stone-500 mt-1 leading-relaxed">Aggiungi, modifica e gestisci tutte le cantine.</p>
        </div>
      </NuxtLink>

      <!-- Card Admin Attributi Scheda Tecnica (Only for Admin) -->
      <NuxtLink v-if="isAdmin" to="/dashboard/attributi" class="bg-white p-6 rounded-2xl border border-stone-200/70 shadow-2xs hover:shadow-md hover:border-indigo-200 transition-all group flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="w-11 h-11 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center transition-colors">
              <Sliders class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold text-indigo-700 inline-flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
              <span>Modifica</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </div>
          <h3 class="font-sans text-base font-bold text-stone-900 mt-4 group-hover:text-indigo-900 transition-colors">Campi Scheda Tecnica</h3>
          <p class="text-xs text-stone-500 mt-1 leading-relaxed">Gestisci le caratteristiche disponibili (Vinificazione, Allevamento...).</p>
        </div>
      </NuxtLink>

      <!-- Card Admin Vitigni (Only for Admin) -->
      <NuxtLink v-if="isAdmin" to="/dashboard/vitigni" class="bg-white p-6 rounded-2xl border border-stone-200/70 shadow-2xs hover:shadow-md hover:border-purple-200 transition-all group flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="w-11 h-11 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center transition-colors">
              <Grape class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold text-purple-700 inline-flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
              <span>Gestisci</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </div>
          <h3 class="font-sans text-base font-bold text-stone-900 mt-4 group-hover:text-purple-900 transition-colors">Gestione Vitigni</h3>
          <p class="text-xs text-stone-500 mt-1 leading-relaxed">Gestisci l'elenco delle uve (Tintilia, Montepulciano...).</p>
        </div>
      </NuxtLink>

      <!-- Card Admin Abbinamenti (Only for Admin) -->
      <NuxtLink v-if="isAdmin" to="/dashboard/abbinamenti" class="bg-white p-6 rounded-2xl border border-stone-200/70 shadow-2xs hover:shadow-md hover:border-rose-200 transition-all group flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between">
            <div class="w-11 h-11 rounded-xl bg-rose-50 text-rose-700 flex items-center justify-center transition-colors">
              <Utensils class="w-5 h-5" />
            </div>
            <span class="text-xs font-bold text-rose-700 inline-flex items-center space-x-1 group-hover:translate-x-1 transition-transform">
              <span>Gestisci</span>
              <ArrowRight class="w-3.5 h-3.5" />
            </span>
          </div>
          <h3 class="font-sans text-base font-bold text-stone-900 mt-4 group-hover:text-rose-900 transition-colors">Abbinamenti Culinari</h3>
          <p class="text-xs text-stone-500 mt-1 leading-relaxed">Gestisci il catalogo master degli abbinamenti cibo/vino.</p>
        </div>
      </NuxtLink>

    </div>

    <!-- Admin Stats Widget -->
    <div v-if="isAdmin && stats" class="bg-stone-900 text-white rounded-3xl p-8 shadow-xl border border-stone-800">
      <div class="flex items-center space-x-2 text-amber-400 mb-6">
        <BarChart3 class="w-5 h-5" />
        <h3 class="font-sans text-base font-bold tracking-tight">Panoramica Statistiche Piattaforma</h3>
      </div>
      <div class="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
        <div class="p-4 bg-white/5 rounded-2xl border border-white/10">
          <span class="text-3xl font-sans font-extrabold text-white block tracking-tight">{{ stats.total_producers }}</span>
          <span class="text-xs font-medium text-stone-400 mt-1 block">Cantine Totali</span>
        </div>
        <div class="p-4 bg-white/5 rounded-2xl border border-white/10">
          <span class="text-3xl font-sans font-extrabold text-white block tracking-tight">{{ stats.total_products }}</span>
          <span class="text-xs font-medium text-stone-400 mt-1 block">Vini Inseriti</span>
        </div>
        <div class="p-4 bg-white/5 rounded-2xl border border-white/10">
          <span class="text-3xl font-sans font-extrabold text-white block tracking-tight">{{ stats.published_products }}</span>
          <span class="text-xs font-medium text-stone-400 mt-1 block">Vini Pubblicati</span>
        </div>
        <div class="p-4 bg-white/5 rounded-2xl border border-white/10">
          <span class="text-3xl font-sans font-extrabold text-white block tracking-tight">{{ stats.total_inquiries }}</span>
          <span class="text-xs font-medium text-stone-400 mt-1 block">Contatti Ricevuti</span>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { Wine, Building2, Mail, Sliders, Grape, Plus, ArrowRight, ShieldCheck, BarChart3, Store, Utensils } from 'lucide-vue-next'

const { user, isAdmin, isProducer, isAuthenticated } = useAuth()
const { fetchWithAuth } = useApi()

onMounted(() => {
  if (!isAuthenticated.value) {
    navigateTo('/login')
  }
})

const { data: stats } = await useAsyncData('admin_stats', async () => {
  if (!isAdmin.value) return null
  return await fetchWithAuth('/admin/stats')
})
</script>
