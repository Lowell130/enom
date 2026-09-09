<template>
  <div class="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <!-- Top Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <NuxtLink to="/dashboard" class="inline-flex items-center space-x-1 text-xs text-wine-800 font-semibold hover:underline mb-1">
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Torna alla Dashboard</span>
        </NuxtLink>
        <h1 class="font-sans text-3xl font-extrabold text-stone-900 tracking-tight">
          Gestione Prodotti
        </h1>
        <p class="text-xs text-stone-500 mt-1">
          Visualizza, modifica, elimina e clona i vini in catalogo in 1-Click.
        </p>
      </div>

      <div class="flex gap-3">
        <NuxtLink to="/dashboard/prodotti/nuovo" class="inline-flex items-center space-x-2 px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-sm rounded-xl shadow-xs transition-all">
          <Plus class="w-4 h-4 text-amber-200" />
          <span>Inserisci Nuovo Vino</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Admin Filter by Producer if Admin -->
    <div v-if="isAdmin && producers" class="bg-white p-4 rounded-2xl border border-stone-200/60 mb-6 flex items-center space-x-4">
      <span class="text-xs font-bold uppercase tracking-wider text-stone-600">Filtra per Cantina (Admin):</span>
      <select v-model="selectedProducerId" class="border border-stone-200 rounded-xl px-3.5 py-2 text-xs font-medium focus:ring-2 focus:ring-wine-800 focus:outline-none">
        <option value="">Tutte le cantine</option>
        <option v-for="p in producers" :key="p.id" :value="p.id">{{ p.company_name }}</option>
      </select>
    </div>

    <!-- Products Table -->
    <div class="bg-white rounded-3xl border border-stone-200/60 shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-stone-500">
        Caricamento vini in corso...
      </div>

      <div v-else-if="filteredProducts && filteredProducts.length" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-stone-700">
          <thead class="bg-stone-50 text-xs uppercase font-bold text-stone-500 border-b border-stone-100">
            <tr>
              <th class="py-4 px-6">Vino</th>
              <th class="py-4 px-6">Cantina</th>
              <th class="py-4 px-6">Annata / Denom.</th>
              <th class="py-4 px-6">Stato</th>
              <th class="py-4 px-6 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr v-for="prod in filteredProducts" :key="prod.id" class="hover:bg-stone-50/50 transition-colors">
              
              <!-- Vino Name & Photo (Clickable Link to Product Detail Sheet) -->
              <td class="py-4 px-6 min-w-[240px]">
                <NuxtLink :to="`/vini/${prod.slug || prod.id}`" target="_blank" class="flex items-center space-x-3.5 group cursor-pointer" title="Clicca per visualizzare la scheda tecnica del vino">
                  <div class="w-12 h-14 shrink-0 bg-white rounded-xl border border-stone-200/70 p-1 flex items-center justify-center group-hover:border-wine-300 transition-colors">
                    <img :src="getProductImage(prod)" class="max-h-full max-w-full object-contain group-hover:scale-105 transition-transform" />
                  </div>
                  <div>
                    <span class="font-sans font-bold text-sm text-stone-900 group-hover:text-wine-800 leading-snug block transition-colors">{{ prod.name }}</span>
                    <span :class="['inline-block px-2 py-0.5 text-[11px] font-semibold rounded-md border mt-0.5', getCategoryBadgeClass(prod.category)]">{{ formatCategory(prod.category) }}</span>
                  </div>
                </NuxtLink>
              </td>

              <!-- Cantina -->
              <td class="py-4 px-6 font-semibold text-xs text-stone-800 whitespace-nowrap">
                <span class="inline-flex items-center space-x-1.5 bg-stone-50 px-2.5 py-1 rounded-lg border border-stone-200/50">
                  <Building2 class="w-3.5 h-3.5 text-stone-400" />
                  <span>{{ prod.producer_name || 'N/D' }}</span>
                </span>
              </td>

              <!-- Annata / Denom -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span class="font-bold text-wine-900 block text-xs">{{ prod.denominazione }}</span>
                <span class="text-stone-500 font-medium block mt-0.5">
                  {{ prod.vintage_year && prod.is_riserva ? `Annata ${prod.vintage_year} Riserva` : (prod.vintage_year ? `Annata ${prod.vintage_year}` : (prod.is_riserva ? 'Riserva' : '-')) }}
                </span>
              </td>

              <!-- Stato -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span v-if="prod.status === 'PUBLISHED'" class="px-3 py-1 bg-emerald-50 text-emerald-800 rounded-full font-bold border border-emerald-200/60 inline-block">
                  Pubblicato
                </span>
                <span v-else class="px-3 py-1 bg-amber-50 text-amber-800 rounded-full font-bold border border-amber-200/60 inline-block">
                  Bozza
                </span>
              </td>

              <!-- Actions: 2 Aligned Rows (No forced single icon wrap) -->
              <td class="py-4 px-6 text-right whitespace-nowrap">
                <div class="flex flex-col items-end space-y-1.5">
                  <!-- Row 1: Vedi Scheda & Clona 1-Click -->
                  <div class="flex items-center space-x-2">
                    <NuxtLink 
                      :to="`/vini/${prod.slug || prod.id}`"
                      target="_blank"
                      class="px-3 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-stone-700 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-stone-200/60"
                      title="Visualizza Scheda Tecnica Vino"
                    >
                      <Eye class="w-3.5 h-3.5 text-wine-800" />
                      <span>Vedi Scheda</span>
                    </NuxtLink>

                    <button 
                      @click="handleClone(prod)" 
                      title="Clona questo vino per creare una variante o nuova annata"
                      class="px-3 py-1.5 bg-amber-700 hover:bg-amber-800 text-white rounded-xl text-xs font-bold transition-all shadow-2xs inline-flex items-center space-x-1"
                    >
                      <Copy class="w-3.5 h-3.5 text-amber-200" />
                      <span>Clona 1-Click</span>
                    </button>
                  </div>

                  <!-- Row 2: Modifica & Elimina -->
                  <div class="flex items-center space-x-2">
                    <NuxtLink 
                      :to="`/dashboard/prodotti/edit-${prod.id}`" 
                      class="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-stone-200/60"
                    >
                      <Pencil class="w-3.5 h-3.5 text-stone-500" />
                      <span>Modifica</span>
                    </NuxtLink>

                    <button 
                      @click="handleDelete(prod.id)" 
                      class="px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-rose-200/50"
                      title="Elimina definitivo"
                    >
                      <Trash2 class="w-3.5 h-3.5 text-rose-600" />
                      <span>Elimina</span>
                    </button>
                  </div>
                </div>
              </td>

            </tr>
          </tbody>
        </table>
      </div>

      <div v-else class="p-16 text-center text-stone-500">
        <Wine class="w-8 h-8 text-stone-400 mx-auto mb-2" />
        <p class="text-sm font-light">Nessun vino presente per i filtri selezionati.</p>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Plus, Building2, Copy, Pencil, Trash2, Wine, Eye } from 'lucide-vue-next'

const { fetchWithAuth, mediaBase } = useApi()
const { isAdmin } = useAuth()

const selectedProducerId = ref('')

const { data: producers } = await useAsyncData('admin_producers_list', async () => {
  if (!isAdmin.value) return null
  return await fetchWithAuth('/producers')
})

const { data: products, pending, refresh } = await useAsyncData('dashboard_products', () => 
  fetchWithAuth('/products?status=ALL')
)

const filteredProducts = computed(() => {
  if (!products.value) return []
  if (isAdmin.value && selectedProducerId.value) {
    return products.value.filter(p => p.producer_id === selectedProducerId.value)
  }
  return products.value
})

const getProductImage = (prod) => {
  if (prod.photos && prod.photos.length > 0) {
    const url = prod.photos[0]
    return url.startsWith('http') ? url : `${mediaBase}${url}`
  }
  return 'https://images.unsplash.com/photo-1586370434639-0fe43b2d32e6?auto=format&fit=crop&w=600&q=80'
}

const { formatCategory, getCategoryBadgeClass } = useCategoryBadge()

const toast = useToast()

const handleClone = async (prod) => {
  if (!confirm(`Vuoi clonare il vino "${prod.name}"? Verrà creata una copia in bozza che potrai modificare subito.`)) return
  try {
    const cloned = await fetchWithAuth(`/products/${prod.id}/clone`, { method: 'POST' })
    toast.success(`Vino duplicato con successo come "${cloned.name}"! Reindirizzamento...`)
    await refresh()
    navigateTo(`/dashboard/prodotti/edit-${cloned.id}`)
  } catch (err) {
    toast.error('Errore durante la clonazione del vino.')
  }
}

const handleDelete = async (id) => {
  if (!confirm('Sei sicuro di voler eliminare definitivamente questo vino?')) return
  try {
    await fetchWithAuth(`/products/${id}`, { method: 'DELETE' })
    toast.success('Vino eliminato con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'eliminazione del vino.')
  }
}
</script>
