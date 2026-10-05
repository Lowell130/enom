<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[1240px]">
    
    <!-- Top Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">
          Vini
        </h1>
        <p class="text-sm text-ink-mute mt-2">
          Visualizza, modifica, elimina, clona, esporta e importa i vini in catalogo.
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <!-- Admin Export Dropdown -->
        <div v-if="isAdmin" class="relative group">
          <button 
            type="button"
            class="btn-ghost btn-sm h-11"
          >
            <Download class="w-4 h-4" aria-hidden="true" />
            <span>Esporta</span>
          </button>
          <div class="absolute right-0 mt-1 w-52 bg-white rounded-2xl shadow-xl border border-line py-1.5 hidden group-hover:block z-30">
            <button 
              @click="handleExport('excel')" 
              class="w-full text-left px-4 py-2.5 text-xs font-semibold text-ink-soft hover:bg-amber-50 flex items-center space-x-2 transition-colors"
            >
              <FileSpreadsheet class="w-4 h-4 text-emerald-700 shrink-0" />
              <span>Esporta Excel (.xlsx)</span>
            </button>
            <button 
              @click="handleExport('json')" 
              class="w-full text-left px-4 py-2.5 text-xs font-semibold text-ink-soft hover:bg-amber-50 flex items-center space-x-2 border-t border-stone-100 transition-colors"
            >
              <FileJson class="w-4 h-4 text-wine-800 shrink-0" />
              <span>Esporta JSON (.json)</span>
            </button>
          </div>
        </div>

        <!-- Admin Import Button -->
        <button 
          v-if="isAdmin"
          @click="showImportModal = true" 
          class="btn-ghost btn-sm h-11"
          title="Importa o aggiorna vini da file Excel o JSON"
        >
          <Upload class="w-4 h-4" aria-hidden="true" />
          <span>Importa Excel / JSON</span>
        </button>

        <!-- Admin PDF AI Import Button -->
        <button 
          v-if="isAdmin"
          @click="showPdfModal = true" 
          class="btn-ghost btn-sm h-11"
          title="Importa i vini da schede tecniche in PDF o immagine con l'IA"
        >
          <Sparkles class="w-4 h-4 text-gold-600" aria-hidden="true" />
          <span>Importa schede (AI)</span>
        </button>

        <NuxtLink to="/dashboard/prodotti/nuovo" class="btn-primary btn-sm h-11">
          <Plus class="w-4 h-4" aria-hidden="true" />
          <span>Nuovo vino</span>
        </NuxtLink>
      </div>
    </div>

    <!-- Ricerca e filtro per cantina -->
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <div class="relative flex-1 min-w-[240px] max-w-[460px]">
        <Search class="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-mute pointer-events-none" aria-hidden="true" />
        <label for="cerca-vino" class="sr-only">Cerca vino</label>
        <input
          id="cerca-vino"
          v-model="searchQuery"
          type="search"
          placeholder="Cerca per nome, cantina, vitigno, annata…"
          class="input h-10 pl-10 pr-9 text-sm [&::-webkit-search-cancel-button]:appearance-none"
          @keydown.esc="searchQuery = ''"
        />
        <button
          v-if="searchQuery"
          type="button"
          class="absolute right-2.5 top-1/2 -translate-y-1/2 p-1 rounded-md text-ink-mute hover:text-ink"
          aria-label="Cancella la ricerca"
          @click="searchQuery = ''"
        >
          <X class="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
      <template v-if="isAdmin && producers">
        <label for="filtro-cantina" class="text-sm font-semibold text-ink-soft">Cantina</label>
        <select id="filtro-cantina" v-model="selectedProducerId" class="select h-10 w-auto min-w-[220px] text-sm">
          <option value="">Tutte le cantine</option>
          <option v-for="p in producers" :key="p.id" :value="p.id">{{ p.company_name }}</option>
        </select>
      </template>
      <span v-if="!pending" class="text-sm text-ink-mute ml-auto" aria-live="polite">
        {{ visibleProducts.length === 1 ? '1 vino' : `${visibleProducts.length} vini` }}<template v-if="searchQuery"> su {{ filteredProducts.length }}</template>
      </span>
    </div>

    <!-- Products Table -->
    <div class="card overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-ink-mute">
        Caricamento vini in corso...
      </div>

      <div v-else-if="visibleProducts.length" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-ink-soft">
          <thead class="text-xs uppercase tracking-[0.08em] font-bold text-ink-mute border-b border-line">
            <tr>
              <th class="py-4 px-6">Vino</th>
              <th class="py-4 px-6">Cantina</th>
              <th class="py-4 px-6">Annata / Denom.</th>
              <th class="py-4 px-6">Stato</th>
              <th class="py-4 px-6 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr v-for="prod in visibleProducts" :key="prod.id" class="hover:bg-stone-50/50 transition-colors">
              
              <!-- Foto e nome (link alla scheda), con modifica veloce del nome -->
              <td class="py-4 px-6 min-w-[320px]">
                <div class="flex items-center gap-3.5">
                  <NuxtLink :to="`/vini/${prod.slug || prod.id}`" target="_blank" tabindex="-1" aria-hidden="true" class="group w-12 h-14 shrink-0 bg-white rounded-xl border border-line p-1 flex items-center justify-center hover:border-wine-300 transition-colors">
                    <img :src="getProductImage(prod)" alt="" class="max-h-full max-w-full object-contain group-hover:scale-105 transition-transform" />
                  </NuxtLink>

                  <form v-if="editingId === prod.id" class="flex-1 flex items-center gap-1.5" @submit.prevent="saveTitle(prod)">
                    <label :for="`titolo-${prod.id}`" class="sr-only">Nome del vino</label>
                    <input
                      :id="`titolo-${prod.id}`"
                      ref="titleInput"
                      v-model="editingName"
                      type="text"
                      maxlength="150"
                      class="input h-10 text-[15px] font-bold min-w-[280px]"
                      :disabled="savingTitle"
                      @keydown.esc.prevent="cancelEdit"
                    />
                    <button type="submit" class="shrink-0 w-9 h-9 rounded-lg bg-wine-800 text-white flex items-center justify-center hover:bg-wine-900 disabled:opacity-50" :disabled="savingTitle || !editingName.trim()" aria-label="Salva il nome">
                      <RefreshCw v-if="savingTitle" class="w-4 h-4 animate-spin" aria-hidden="true" />
                      <Check v-else class="w-4 h-4" aria-hidden="true" />
                    </button>
                    <button type="button" class="shrink-0 w-9 h-9 rounded-lg border border-line-strong bg-white text-ink-soft flex items-center justify-center hover:border-ink-mute" :disabled="savingTitle" aria-label="Annulla" @click="cancelEdit">
                      <X class="w-4 h-4" aria-hidden="true" />
                    </button>
                  </form>

                  <div v-else class="flex-1 min-w-0">
                    <div class="flex items-start gap-1.5 group/title">
                      <NuxtLink :to="`/vini/${prod.slug || prod.id}`" target="_blank" class="font-bold text-[15px] text-ink hover:text-wine-800 leading-snug transition-colors" title="Apri la scheda del vino">
                        {{ prod.name }}
                      </NuxtLink>
                      <button
                        type="button"
                        class="shrink-0 -my-1 p-1.5 rounded-md text-ink-mute hover:text-wine-800 hover:bg-sand-100 opacity-60 group-hover/title:opacity-100 focus-visible:opacity-100 transition"
                        :aria-label="`Modifica il nome di ${prod.name}`"
                        title="Modifica il nome"
                        @click="startEdit(prod)"
                      >
                        <Pencil class="w-3.5 h-3.5" aria-hidden="true" />
                      </button>
                    </div>
                    <span class="block text-[13px] text-ink-mute mt-0.5">{{ formatCategory(prod.category) }}</span>
                  </div>
                </div>
              </td>

              <!-- Cantina -->
              <td class="py-4 px-6 font-semibold text-xs text-stone-800 whitespace-nowrap">
                <span class="text-sm font-normal text-ink-soft">{{ prod.producer_name || 'N/D' }}</span>
              </td>

              <!-- Annata / Denom -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span class="font-bold text-wine-900 block text-xs">{{ prod.denominazione }}</span>
                <span class="text-ink-mute font-medium block mt-0.5">
                  {{ prod.vintage_year && prod.is_riserva ? `Annata ${prod.vintage_year} Riserva` : (prod.vintage_year ? `Annata ${prod.vintage_year}` : (prod.is_riserva ? 'Riserva' : '-')) }}
                </span>
              </td>

              <!-- Stato -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span v-if="prod.status === 'PUBLISHED'" class="px-3 py-1 bg-bio-50 text-bio-900 rounded-full font-bold border border-bio/20 inline-block">
                  Pubblicato
                </span>
                <span v-else class="px-3 py-1 bg-sand-100 text-[#5A4524] rounded-full font-bold inline-block">
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
                      class="px-3 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-ink-soft rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-line"
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
                      class="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-line"
                    >
                      <Pencil class="w-3.5 h-3.5 text-ink-mute" />
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

      <div v-else class="p-16 text-center text-ink-mute">
        <Wine class="w-8 h-8 text-stone-400 mx-auto mb-2" />
        <p v-if="searchQuery" class="text-sm">
          Nessun vino trovato per «{{ searchQuery }}».
          <button type="button" class="font-semibold text-wine-800 hover:text-wine-900" @click="searchQuery = ''">Mostra tutti</button>
        </p>
        <p v-else class="text-sm font-light">Nessun vino presente per i filtri selezionati.</p>
      </div>

    </div>

    <!-- MODAL IMPORTA CATALOGO -->
    <div v-if="showImportModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative border border-stone-100 space-y-6">
        
        <div class="flex items-center justify-between border-b border-stone-100 pb-3">
          <div class="flex items-center space-x-2.5">
            <div class="w-9 h-9 rounded-xl bg-wine-50 border border-wine-200 text-wine-800 flex items-center justify-center">
              <Upload class="w-5 h-5" />
            </div>
            <div>
              <h3 class="font-sans text-lg font-bold text-ink">Importa / Ricarica Catalogo Vini</h3>
              <p class="text-xs text-ink-mute">Formati supportati: Excel (.xlsx) e JSON (.json)</p>
            </div>
          </div>
          <button @click="showImportModal = false" class="text-stone-400 hover:text-ink-soft p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="space-y-4">
          <div 
            class="border-2 border-dashed border-stone-200 hover:border-wine-300 rounded-2xl p-6 text-center cursor-pointer transition-colors bg-stone-50/50"
            @click="triggerFileInput"
          >
            <input 
              type="file" 
              ref="fileInputRef" 
              accept=".xlsx,.xls,.json" 
              class="hidden" 
              @change="onFileSelected" 
            />
            <div v-if="selectedFile" class="space-y-1">
              <span class="inline-block px-3 py-1 bg-wine-800 text-white font-mono text-xs font-bold rounded-lg">
                {{ selectedFile.name }}
              </span>
              <p class="text-xs text-ink-mute">Dimensione: {{ (selectedFile.size / 1024).toFixed(1) }} KB</p>
              <p class="text-[11px] text-wine-800 font-semibold">Clicca per scegliere un altro file</p>
            </div>
            <div v-else class="space-y-2">
              <Upload class="w-8 h-8 text-stone-400 mx-auto" />
              <p class="text-xs font-semibold text-ink-soft">Seleziona un file .xlsx o .json dal tuo computer</p>
              <p class="text-[11px] text-ink-mute leading-relaxed">
                Se il file contiene l'<strong>ID Prodotto</strong> o corrisponde per <strong>Cantina + Nome + Annata</strong>, i vini esistenti verranno <strong>aggiornati</strong>; altrimenti verranno creati nuovi.
              </p>
            </div>
          </div>

          <!-- Import Result Summary Card -->
          <div v-if="importResult" class="p-4 bg-stone-50 rounded-2xl border border-line space-y-3">
            <div class="flex items-center space-x-2 text-xs font-bold text-ink">
              <CheckCircle2 class="w-4 h-4 text-emerald-600" />
              <span>Esito Importazione: {{ importResult.message }}</span>
            </div>
            <div class="grid grid-cols-3 gap-2 text-center text-xs">
              <div class="bg-white p-2 rounded-xl border border-emerald-200 text-emerald-800 font-bold">
                +{{ importResult.created }} Creati
              </div>
              <div class="bg-white p-2 rounded-xl border border-blue-200 text-blue-800 font-bold">
                {{ importResult.updated }} Aggiornati
              </div>
              <div class="bg-white p-2 rounded-xl border border-rose-200 text-rose-800 font-bold">
                {{ importResult.errors }} Errori
              </div>
            </div>
            <div v-if="importResult.error_details && importResult.error_details.length" class="text-xs text-rose-700 space-y-1 max-h-24 overflow-y-auto pt-1 border-t border-line">
              <div v-for="(err, idx) in importResult.error_details" :key="idx">• {{ err }}</div>
            </div>
          </div>
        </div>

        <div class="pt-2 flex justify-end space-x-3 border-t border-stone-100">
          <button type="button" @click="showImportModal = false" class="px-4 py-2.5 text-xs text-ink-soft font-semibold hover:bg-stone-50 rounded-xl">Annulla</button>
          <button 
            type="button" 
            @click="handleImport" 
            :disabled="!selectedFile || importing" 
            class="px-6 py-2.5 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-xs font-bold shadow-xs disabled:opacity-50 inline-flex items-center space-x-1.5"
          >
            <RefreshCw v-if="importing" class="w-4 h-4 animate-spin text-amber-200" />
            <span>{{ importing ? 'Importazione in corso...' : 'Avvia Importazione' }}</span>
          </button>
        </div>

      </div>
    </div>

    <!-- Importazione vini da PDF con IA (solo admin) -->
    <PdfImportModal
      v-if="showPdfModal && isAdmin"
      :producers="producers"
      @close="showPdfModal = false"
      @imported="refresh()"
    />

  </div>
</template>

<script setup>
import { 
  ArrowLeft, Plus, Building2, Copy, Pencil, Trash2, Wine, Eye, 
  Upload, Download, FileSpreadsheet, FileJson, X, CheckCircle2, RefreshCw, Sparkles, Search, Check
} from 'lucide-vue-next'

const { fetchWithAuth, mediaBase, apiBase } = useApi()
const { user, isAdmin } = useAuth()

const selectedProducerId = ref('')
const showImportModal = ref(false)
const selectedFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const fileInputRef = ref(null)

// State for PDF AI Batch Importer
const showPdfModal = ref(false)
const triggerFileInput = () => {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

const onFileSelected = (e) => {
  const file = e.target.files[0]
  if (file) {
    selectedFile.value = file
    importResult.value = null
  }
}

const { data: producers } = await useAsyncData('admin_producers_list', async () => {
  if (!isAdmin.value) return []
  const res = await fetchWithAuth('/producers?include_all=true')
  return res || []
}, { default: () => [] })

const { data: products, pending, refresh } = await useAsyncData('dashboard_products', async () => {
  let url = '/products?status=ALL'
  const myProducerId = user.value?.producer_id || user.value?.producer?.id
  if (!isAdmin.value && myProducerId) {
    url += `&producer_id=${myProducerId}`
  }
  const res = await fetchWithAuth(url)
  return res || []
}, { default: () => [] })

const filteredProducts = computed(() => {
  if (!products.value) return []
  if (isAdmin.value) {
    if (selectedProducerId.value) {
      return products.value.filter(p => String(p.producer_id) === String(selectedProducerId.value))
    }
    return products.value
  }
  const myProducerId = user.value?.producer_id || user.value?.producer?.id
  if (!myProducerId) return []
  return products.value.filter(p => String(p.producer_id) === String(myProducerId))
})

// Ricerca: nome, cantina, denominazione, tipologia, vitigni e annata, senza badare ad accenti e maiuscole.
// Resta nell'indirizzo (?q=) cosi' tornando dalla modifica di un vino la ricerca non si perde.
const route = useRoute()
const router = useRouter()
const searchQuery = ref(String(route.query.q || ''))
watch(searchQuery, (q) => {
  router.replace({ query: { ...route.query, q: q.trim() || undefined } })
})

const normalize = (text) => String(text ?? '')
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toLowerCase()

const searchText = (prod) => normalize([
  prod.name,
  prod.producer_name,
  prod.denominazione,
  formatCategory(prod.category),
  (prod.grape_varieties || []).join(' '),
  prod.vintage_year,
  prod.is_riserva ? 'riserva' : '',
  prod.status === 'PUBLISHED' ? 'pubblicato' : 'bozza'
].join(' '))

const visibleProducts = computed(() => {
  const words = normalize(searchQuery.value).split(/\s+/).filter(Boolean)
  if (!words.length) return filteredProducts.value
  return filteredProducts.value.filter(prod => {
    const text = searchText(prod)
    return words.every(w => text.includes(w))
  })
})

// Modifica veloce del nome
const editingId = ref(null)
const editingName = ref('')
const savingTitle = ref(false)
const titleInput = ref(null)

const startEdit = async (prod) => {
  editingId.value = prod.id
  editingName.value = prod.name
  await nextTick()
  const input = Array.isArray(titleInput.value) ? titleInput.value[0] : titleInput.value
  input?.focus()
  input?.select()
}

const cancelEdit = () => {
  editingId.value = null
  editingName.value = ''
}

const saveTitle = async (prod) => {
  const name = editingName.value.trim().replace(/\s+/g, ' ')
  if (!name) return
  if (name === prod.name) return cancelEdit()
  savingTitle.value = true
  try {
    const updated = await fetchWithAuth(`/products/${prod.id}`, { method: 'PUT', body: { name } })
    // aggiorna la riga senza ricaricare l'elenco (il server puo' ripulire il nome e rigenerare l'indirizzo)
    prod.name = updated?.name || name
    if (updated?.slug) prod.slug = updated.slug
    toast.success('Nome del vino aggiornato.')
    cancelEdit()
  } catch (err) {
    toast.error('Non è stato possibile salvare il nome del vino.')
  } finally {
    savingTitle.value = false
  }
}

const getProductImage = (prod) => {
  if (prod.photos && prod.photos.length > 0) {
    const url = prod.photos[0]
    return url.startsWith('http') ? url : `${mediaBase}${url}`
  }
  return '/default_wine_bottle.jpg'
}

const { formatCategory, getCategoryBadgeClass } = useCategoryBadge()

const toast = useToast()

const handleExport = async (format) => {
  try {
    const tokenCookie = useCookie('auth_token')
    const token = tokenCookie.value
    const res = await fetch(`${apiBase}/products/export/${format}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (!res.ok) throw new Error('Errore durante il download del file')
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = format === 'json' ? 'catalogo_vini.json' : 'catalogo_vini.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
    toast.success(`Catalogo esportato in formato ${format.toUpperCase()} con successo!`)
  } catch (err) {
    toast.error('Errore durante l\'esportazione del catalogo.')
  }
}

const handleImport = async () => {
  if (!selectedFile.value) return
  const filename = selectedFile.value.name.toLowerCase()
  const isExcel = filename.endsWith('.xlsx') || filename.endsWith('.xls')
  const isJson = filename.endsWith('.json')

  if (!isExcel && !isJson) {
    toast.error('Seleziona un file valido (.xlsx o .json)')
    return
  }

  const endpoint = isExcel ? '/products/import/excel' : '/products/import/json'
  const formData = new FormData()
  formData.append('file', selectedFile.value)

  importing.value = true
  importResult.value = null

  try {
    const res = await fetchWithAuth(endpoint, {
      method: 'POST',
      body: formData
    })
    importResult.value = res
    toast.success(res.message || 'Importazione completata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'importazione del file.')
  } finally {
    importing.value = false
  }
}

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
