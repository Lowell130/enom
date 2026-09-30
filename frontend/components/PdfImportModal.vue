<template>
  <div class="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-xs flex items-center justify-center p-2 sm:p-4" @keydown.esc="close">
    <div class="bg-white rounded-3xl max-w-5xl w-full shadow-2xl relative border border-stone-100 max-h-[94vh] flex flex-col">

      <!-- Header -->
      <div class="flex items-start justify-between gap-4 px-6 pt-6 pb-4 border-b border-stone-100">
        <div class="flex items-center space-x-3">
          <div class="w-10 h-10 rounded-2xl bg-amber-100 flex items-center justify-center shrink-0">
            <Sparkles class="w-5 h-5 text-amber-700" />
          </div>
          <div>
            <h3 class="font-sans text-xl font-bold text-stone-900">Importa schede vino (AI)</h3>
            <p class="text-xs text-stone-500">Schede tecniche in PDF o immagine, o pagine web salvate in PDF: l'IA compila la scheda del vino, tu controlli e confermi.</p>
          </div>
        </div>
        <button type="button" class="text-stone-400 hover:text-stone-600 p-1" :disabled="busy" @click="close" aria-label="Chiudi">
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Stato IA -->
      <div v-if="aiStatus" class="px-6 pt-3">
        <div v-if="aiStatus.configured" class="text-[11px] font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-xl px-3 py-2 inline-flex items-center gap-1.5">
          <CheckCircle2 class="w-3.5 h-3.5" />
          IA attiva: {{ providerLabel }} ({{ aiStatus.model }})
        </div>
        <div v-else class="text-[11px] font-semibold text-amber-900 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2 flex items-start gap-1.5">
          <AlertTriangle class="w-3.5 h-3.5 mt-0.5 shrink-0" />
          <span>IA non configurata: si possono leggere solo PDF con testo selezionabile (non immagini, screenshot o scansioni).
            Aggiungi <code class="font-mono">GEMINI_API_KEY</code> o <code class="font-mono">ANTHROPIC_API_KEY</code> nel file <code class="font-mono">backend/.env</code> e riavvia il backend.</span>
        </div>
      </div>

      <div class="overflow-y-auto flex-1 px-6 py-4 space-y-5">

        <!-- STEP 1: selezione -->
        <template v-if="step === 'select'">
          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-1.5">1. Cantina produttrice</label>
            <select v-model="defaultProducerId" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm bg-white font-medium focus:ring-2 focus:ring-wine-800 focus:outline-none">
              <option value="">🔎 Riconosci automaticamente dal documento</option>
              <option v-for="p in producers" :key="p.id" :value="p.id">{{ p.company_name }}</option>
            </select>
            <p class="text-[11px] text-stone-500 mt-1">Potrai comunque cambiare la cantina di ogni vino nella revisione.</p>
          </div>

          <div>
            <label class="block text-xs font-bold uppercase tracking-wider text-stone-700 mb-1.5">2. Schede dei vini (PDF o immagini)</label>
            <div
              :class="['border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-colors', dragging ? 'border-wine-800 bg-wine-50' : 'border-amber-300 hover:border-amber-500 bg-amber-50/30']"
              @click="fileInput?.click()"
              @dragover.prevent="dragging = true"
              @dragleave.prevent="dragging = false"
              @drop.prevent="onDrop"
            >
              <input ref="fileInput" type="file" :accept="ACCEPT" multiple class="hidden" @change="onFilesSelected" />
              <Upload class="w-9 h-9 text-amber-600 mx-auto mb-2" />
              <p class="text-sm font-bold text-stone-800">Trascina qui i file o clicca per sceglierli</p>
              <p class="text-xs text-stone-500 mt-1">PDF, JPG, PNG o WebP · fino a {{ MAX_FILES }} file, max 15 MB ciascuno · un file può contenere uno o più vini.</p>
            </div>
            <ul v-if="files.length" class="mt-3 space-y-1.5">
              <li v-for="(f, idx) in files" :key="f.name + idx" class="flex items-center justify-between text-xs bg-stone-50 border border-stone-200 rounded-xl px-3 py-2">
                <span class="inline-flex items-center gap-2 font-medium text-stone-800 truncate"><FileText class="w-4 h-4 text-wine-800 shrink-0" />{{ f.name }}</span>
                <span class="flex items-center gap-3 shrink-0">
                  <span class="text-stone-400">{{ formatSize(f.size) }}</span>
                  <button type="button" class="text-stone-400 hover:text-rose-600" @click.stop="files.splice(idx, 1)" aria-label="Rimuovi file"><Trash2 class="w-3.5 h-3.5" /></button>
                </span>
              </li>
            </ul>
          </div>
        </template>

        <!-- STEP 2: analisi in corso -->
        <template v-else-if="step === 'analyzing'">
          <div>
            <div class="flex justify-between text-xs font-semibold text-stone-600 mb-1.5">
              <span>Analisi dei documenti…</span><span>{{ doneCount }} / {{ fileStates.length }}</span>
            </div>
            <div class="h-2 bg-stone-100 rounded-full overflow-hidden">
              <div class="h-full bg-wine-800 transition-all duration-500" :style="{ width: `${(doneCount / Math.max(fileStates.length, 1)) * 100}%` }"></div>
            </div>
          </div>
          <ul class="space-y-1.5">
            <li v-for="fs in fileStates" :key="fs.name" class="flex items-center justify-between text-xs border border-stone-200 rounded-xl px-3 py-2">
              <span class="font-medium text-stone-800 truncate">{{ fs.name }}</span>
              <span class="shrink-0 font-semibold inline-flex items-center gap-1.5"
                :class="{ 'text-stone-400': fs.state === 'queued', 'text-amber-700': fs.state === 'running', 'text-emerald-700': fs.state === 'ok', 'text-rose-700': fs.state === 'error', 'text-stone-500': fs.state === 'duplicate' }">
                <RefreshCw v-if="fs.state === 'running'" class="w-3.5 h-3.5 animate-spin" />
                {{ fileStateLabel(fs) }}
              </span>
            </li>
          </ul>
          <p class="text-[11px] text-stone-500">Ogni documento richiede in genere 10–40 secondi.</p>
        </template>

        <!-- STEP 3: revisione -->
        <template v-else-if="step === 'review'">
          <div v-for="fs in failedFiles" :key="'err-' + fs.name" class="flex items-start justify-between gap-3 bg-rose-50 border border-rose-200 rounded-2xl px-4 py-3 text-xs">
            <span class="text-rose-900"><strong>{{ fs.name }}</strong>: {{ fs.error }}</span>
            <button type="button" class="shrink-0 font-bold text-rose-800 hover:underline" @click="retryFile(fs)">Riprova</button>
          </div>
          <div v-for="fs in duplicateFiles" :key="'dup-' + fs.name" class="bg-stone-50 border border-stone-200 rounded-2xl px-4 py-3 text-xs text-stone-600">
            <strong>{{ fs.name }}</strong> è identico a <strong>{{ fs.duplicateOf }}</strong>: analizzato una sola volta.
          </div>

          <div v-if="!wines.length" class="text-center text-sm text-stone-500 py-10">Nessun vino da importare.</div>

          <template v-else>
            <div class="flex flex-wrap items-center justify-between gap-3 bg-stone-50 border border-stone-200 rounded-2xl px-4 py-3">
              <span class="text-xs font-bold text-stone-800">{{ wines.length }} {{ wines.length === 1 ? 'vino trovato' : 'vini trovati' }} · {{ selectedCount }} da importare</span>
              <div class="flex flex-wrap items-center gap-4 text-xs">
                <label class="inline-flex items-center gap-1.5 font-semibold text-stone-700">
                  Stato:
                  <select v-model="publishStatus" class="border border-stone-200 rounded-lg px-2 py-1 bg-white">
                    <option value="PUBLISHED">Pubblicato</option>
                    <option value="DRAFT">Bozza</option>
                  </select>
                </label>
                <label v-if="hasPdfWines" class="inline-flex items-center gap-1.5 font-semibold text-stone-700 cursor-pointer" title="Il PDF originale sarà scaricabile dalla scheda del vino (solo per i vini estratti da PDF)">
                  <input v-model="attachPdf" type="checkbox" class="rounded border-stone-300 text-wine-800" />
                  Allega il PDF come scheda tecnica
                </label>
              </div>
            </div>

            <article v-for="(w, idx) in wines" :key="w._key"
              :class="['border rounded-2xl transition-colors', w.action === 'skip' ? 'border-stone-200 bg-stone-50/60 opacity-70' : 'border-stone-200 bg-white shadow-2xs']">
              <!-- intestazione vino -->
              <div class="p-4 flex flex-col lg:flex-row lg:items-center gap-3">
                <div class="flex-1 min-w-0">
                  <input v-model="w.name" type="text" placeholder="Nome del vino" @change="recheckWine(w)"
                    class="w-full font-bold text-sm text-stone-900 border border-stone-200 rounded-lg px-2.5 py-1.5 focus:ring-1 focus:ring-wine-800 focus:outline-none" />
                  <div class="flex flex-wrap items-center gap-1.5 mt-1.5 text-[10px]">
                    <span class="px-2 py-0.5 rounded-full bg-stone-100 text-stone-600 font-mono">{{ w.source_file }}</span>
                    <span v-if="w._batchDupOf" class="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 font-bold"
                      :title="`Stesso vino già presente in questo import (${w._batchDupOf.source_file})`">
                      Doppione di «{{ w._batchDupOf.name }}» in {{ w._batchDupOf.source_file }}
                    </span>
                    <template v-if="w.existing_product">
                      <span v-if="w.existing_product.match === 'similar'" class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 font-bold"
                        title="Nome simile a un vino della stessa cantina già in catalogo: verifica che sia lo stesso">
                        Possibile doppione in catalogo: «{{ w.existing_product.name }}»
                      </span>
                      <span v-else class="px-2 py-0.5 rounded-full bg-sky-100 text-sky-800 font-bold">Già in catalogo: «{{ w.existing_product.name }}»</span>
                    </template>
                    <span v-if="w.action === 'update'" class="px-2 py-0.5 rounded-full bg-sky-50 text-sky-800 border border-sky-200 font-semibold">verrà aggiornato</span>
                    <span v-else-if="w.action === 'create'" class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">Nuovo vino</span>
                    <span v-for="m in w.missing_fields" :key="m" class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 font-semibold">manca: {{ m }}</span>
                    <span v-for="(wr, wi) in w.warnings" :key="'w' + wi" class="px-2 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">{{ wr }}</span>
                  </div>
                </div>
                <div class="flex flex-wrap items-center gap-2 shrink-0">
                  <select v-model="w.producer_id" @change="onProducerChange(w)"
                    :class="['border rounded-lg px-2 py-1.5 text-xs bg-white max-w-[200px]', w.producer_id ? 'border-stone-200' : 'border-rose-400 text-rose-700']">
                    <option value="">— Scegli la cantina —</option>
                    <option v-for="p in producers" :key="p.id" :value="p.id">{{ p.company_name }}</option>
                  </select>
                  <select v-model="w.action" @change="w._userAction = true" class="border border-stone-200 rounded-lg px-2 py-1.5 text-xs bg-white max-w-[220px]">
                    <option value="create">Crea nuovo</option>
                    <option v-if="w.existing_product" value="update">Aggiorna «{{ w.existing_product.name }}»</option>
                    <option value="skip">Non importare</option>
                  </select>
                  <button type="button" class="p-1.5 rounded-lg hover:bg-stone-100 text-stone-500" @click="w._open = !w._open" :aria-label="w._open ? 'Chiudi dettagli' : 'Apri dettagli'">
                    <ChevronUp v-if="w._open" class="w-4 h-4" /><ChevronDown v-else class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <!-- dettagli -->
              <div v-if="w._open" class="border-t border-stone-100 p-4 space-y-4 text-xs">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <label class="block"><span class="field-label">Tipologia</span>
                    <select v-model="w.category" class="field-input">
                      <option v-for="(label, key) in CATEGORIES" :key="key" :value="key">{{ label }}</option>
                    </select>
                  </label>
                  <label class="block"><span class="field-label">Denominazione</span>
                    <select v-model="w.denominazione" class="field-input">
                      <option value="">Nessuna</option>
                      <option v-for="d in DENOMINATIONS" :key="d" :value="d">{{ d }}</option>
                    </select>
                  </label>
                  <label class="block"><span class="field-label">Alcol (% vol)</span>
                    <input v-model.number="w.alcohol_degrees" type="number" step="0.1" min="0" max="25" class="field-input" placeholder="—" />
                  </label>
                  <label class="block"><span class="field-label">Annata</span>
                    <input v-model.number="w.vintage_year" type="number" min="1950" max="2100" class="field-input" placeholder="S.A." />
                  </label>
                  <label class="block"><span class="field-label">Temperatura servizio</span>
                    <input v-model="w.serving_temperature" type="text" class="field-input" placeholder="es. 16-18°C" />
                  </label>
                  <label class="block"><span class="field-label">Prezzo indicativo</span>
                    <input v-model="w.indicative_price" type="text" class="field-input" placeholder="es. 15,00 €" />
                  </label>
                  <label class="block col-span-2"><span class="field-label">Vitigni (separati da virgola)</span>
                    <input v-model="w._grapesText" type="text" class="field-input" placeholder="es. Tintilia, Montepulciano" />
                  </label>
                  <label class="inline-flex items-center gap-2 font-semibold text-stone-700">
                    <input v-model="w.is_riserva" type="checkbox" class="rounded border-stone-300 text-wine-800" /> Riserva
                  </label>
                </div>

                <div>
                  <span class="field-label">Abbinamenti</span>
                  <div class="flex flex-wrap gap-1.5">
                    <button v-for="p in pairingOptions" :key="p" type="button" @click="togglePairing(w, p)"
                      :class="['px-2.5 py-1 rounded-full border text-[11px] font-semibold transition-colors', w.food_pairings.includes(p) ? 'bg-emerald-600 border-emerald-600 text-white' : 'bg-white border-stone-200 text-stone-600 hover:border-emerald-400']">
                      {{ p }}
                    </button>
                  </div>
                </div>

                <label class="block"><span class="field-label">Descrizione</span>
                  <textarea v-model="w.description" rows="4" class="field-input leading-relaxed"></textarea>
                </label>

                <div class="grid md:grid-cols-3 gap-3">
                  <label class="block"><span class="field-label">Esame visivo</span><textarea v-model="w.tasting_notes.visual" rows="3" class="field-input"></textarea></label>
                  <label class="block"><span class="field-label">Esame olfattivo</span><textarea v-model="w.tasting_notes.olfactory" rows="3" class="field-input"></textarea></label>
                  <label class="block"><span class="field-label">Esame gustativo</span><textarea v-model="w.tasting_notes.taste" rows="3" class="field-input"></textarea></label>
                </div>

                <div>
                  <span class="field-label">Scheda tecnica ({{ w.custom_attributes.length }} caratteristiche)</span>
                  <div class="space-y-1.5">
                    <div v-for="(a, ai) in w.custom_attributes" :key="ai" class="flex gap-2">
                      <input v-model="a.name" type="text" list="pdf-import-attr-names" class="field-input md:w-56 w-2/5 font-semibold" placeholder="Caratteristica" />
                      <input v-model="a.value" type="text" class="field-input flex-1" placeholder="Valore" />
                      <button type="button" class="text-stone-400 hover:text-rose-600 px-1" @click="w.custom_attributes.splice(ai, 1)" aria-label="Rimuovi caratteristica"><Trash2 class="w-3.5 h-3.5" /></button>
                    </div>
                  </div>
                  <button type="button" class="mt-2 inline-flex items-center gap-1 text-[11px] font-bold text-wine-800 hover:underline" @click="w.custom_attributes.push({ name: '', value: '' })">
                    <Plus class="w-3.5 h-3.5" /> Aggiungi caratteristica
                  </button>
                </div>
              </div>
            </article>
            <datalist id="pdf-import-attr-names">
              <option v-for="n in attributeNames" :key="n" :value="n" />
            </datalist>
          </template>
        </template>

        <!-- STEP 4: esito -->
        <template v-else-if="step === 'done'">
          <div class="text-center py-8 space-y-3">
            <CheckCircle2 class="w-12 h-12 text-emerald-600 mx-auto" />
            <p class="text-lg font-bold text-stone-900">{{ result?.message }}</p>
            <ul v-if="result?.duplicates?.length" class="text-xs text-amber-900 bg-amber-50 border border-amber-200 rounded-2xl p-3 text-left max-w-xl mx-auto space-y-1">
              <li v-for="(d, i) in result.duplicates" :key="'d' + i">• {{ d }}</li>
            </ul>
            <ul v-if="result?.errors?.length" class="text-xs text-rose-800 bg-rose-50 border border-rose-200 rounded-2xl p-3 text-left max-w-xl mx-auto space-y-1">
              <li v-for="(e, i) in result.errors" :key="i">• {{ e }}</li>
            </ul>
          </div>
        </template>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 flex justify-between items-center gap-3 border-t border-stone-100">
        <button v-if="step === 'review'" type="button" class="px-4 py-2.5 text-xs text-stone-600 font-semibold hover:bg-stone-50 rounded-xl" :disabled="busy" @click="reset">
          ← Altri file
        </button>
        <button v-else type="button" class="px-4 py-2.5 text-xs text-stone-600 font-semibold hover:bg-stone-50 rounded-xl" :disabled="busy" @click="close">
          {{ step === 'done' ? 'Chiudi' : 'Annulla' }}
        </button>

        <button v-if="step === 'select'" type="button" @click="analyze" :disabled="!files.length"
          class="px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-xs font-bold shadow-xs disabled:opacity-50 inline-flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-amber-300" />
          Analizza {{ files.length || '' }} file
        </button>
        <button v-else-if="step === 'review'" type="button" @click="confirmImport" :disabled="busy || !selectedCount"
          class="px-7 py-3 bg-emerald-700 hover:bg-emerald-800 text-white rounded-xl text-xs font-bold shadow-md disabled:opacity-50 inline-flex items-center gap-2">
          <RefreshCw v-if="busy" class="w-4 h-4 animate-spin" />
          <CheckCircle2 v-else class="w-4 h-4" />
          {{ busy ? 'Importazione in corso…' : `Importa ${selectedCount} ${selectedCount === 1 ? 'vino' : 'vini'}` }}
        </button>
        <button v-else-if="step === 'done'" type="button" @click="reset"
          class="px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-xs font-bold shadow-xs">
          Importa altri PDF
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Sparkles, X, CheckCircle2, RefreshCw, Upload, FileText, AlertTriangle, ChevronDown, ChevronUp, Trash2, Plus } from 'lucide-vue-next'

const props = defineProps({
  producers: { type: Array, default: () => [] }
})
const emit = defineEmits(['close', 'imported'])

const { fetchWithAuth } = useApi()
const toast = useToast()

const MAX_FILES = 30
const MAX_BYTES = 15 * 1024 * 1024
const ACCEPT = '.pdf,.jpg,.jpeg,.png,.webp,application/pdf,image/jpeg,image/png,image/webp'
const isPdfFile = (f) => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf')
const isSupportedFile = (f) => isPdfFile(f) || /^image\/(jpeg|png|webp)$/.test(f.type) || /\.(jpe?g|png|webp)$/i.test(f.name)
const CATEGORIES = {
  VINO_ROSSO: 'Vino Rosso', VINO_BIANCO: 'Vino Bianco', ROSATO: 'Rosato',
  SPUMANTE: 'Spumante', PASSITO: 'Passito', LIQUORE: 'Liquore / Grappa'
}
const DENOMINATIONS = ['DOCG', 'DOC', 'DOP', 'IGT', 'IGP']
const DEFAULT_PAIRINGS = [
  'Antipasti & Aperitivi', 'Arrosti & Tagliate', 'Cacciagione & Selvaggina', 'Carni Rosse & Grigliate',
  'Pampanella Molisana', 'Formaggi Freschi', 'Formaggi Stagionati', 'Salumi & Affettati', 'Primi Piatti & Ragù',
  'Risotti & Tartufo', 'Pesce & Frutti di Mare', 'Piatti Vegetariani', 'Pizze & Lievitati', 'Pasticceria & Dolci',
  'Paté & Piatti Freddi'
]

const step = ref('select')
const busy = ref(false)
const dragging = ref(false)
const fileInput = ref(null)
const files = ref([])
const fileStates = ref([])
const wines = ref([])
const defaultProducerId = ref('')
const publishStatus = ref('PUBLISHED')
const attachPdf = ref(false)
const result = ref(null)
const aiStatus = ref(null)
const pairingOptions = ref([...DEFAULT_PAIRINGS])
const attributeNames = ref([])
let keySeq = 0

const providerLabel = computed(() => ({ gemini: 'Google Gemini', anthropic: 'Anthropic Claude' }[aiStatus.value?.provider] || aiStatus.value?.provider))
const doneCount = computed(() => fileStates.value.filter(f => ['ok', 'error', 'duplicate'].includes(f.state)).length)
const failedFiles = computed(() => fileStates.value.filter(f => f.state === 'error'))
const duplicateFiles = computed(() => fileStates.value.filter(f => f.state === 'duplicate'))
const selectedCount = computed(() => wines.value.filter(w => w.action !== 'skip').length)
const hasPdfWines = computed(() => wines.value.some(w => w._file && isPdfFile(w._file)))

onMounted(async () => {
  try { aiStatus.value = await fetchWithAuth('/products/import/ai-status') } catch (e) { aiStatus.value = null }
  try {
    const list = await fetchWithAuth('/pairings')
    if (Array.isArray(list) && list.length) pairingOptions.value = list.map(p => p.name)
  } catch (e) { /* elenco predefinito */ }
  try {
    const attrs = await fetchWithAuth('/attributes')
    attributeNames.value = (attrs || []).map(a => a.name)
  } catch (e) { /* facoltativo */ }
})

const formatSize = (bytes) => bytes > 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`

const addFiles = (list) => {
  for (const f of Array.from(list || [])) {
    if (!isSupportedFile(f)) { toast.error(`${f.name}: formato non supportato (usa PDF, JPG, PNG o WebP)`); continue }
    if (f.size > MAX_BYTES) { toast.error(`${f.name}: supera i 15 MB`); continue }
    if (files.value.some(x => x.name === f.name && x.size === f.size)) continue
    if (files.value.length >= MAX_FILES) { toast.error(`Massimo ${MAX_FILES} file per volta`); break }
    files.value.push(f)
  }
}
const onFilesSelected = (e) => { addFiles(e.target.files); e.target.value = '' }
const onDrop = (e) => { dragging.value = false; addFiles(e.dataTransfer?.files) }

const fileStateLabel = (fs) => ({
  queued: 'in coda',
  running: 'analisi IA…',
  ok: `${fs.count} ${fs.count === 1 ? 'vino' : 'vini'}`,
  error: 'errore',
  duplicate: `identico a ${fs.duplicateOf}`
}[fs.state])

// impronta del contenuto: riconosce lo stesso file anche se rinominato
const fileFingerprint = async (file) => {
  try {
    if (globalThis.crypto?.subtle) {
      const digest = await crypto.subtle.digest('SHA-256', await file.arrayBuffer())
      return Array.from(new Uint8Array(digest)).map(b => b.toString(16).padStart(2, '0')).join('')
    }
  } catch (e) { /* fallback sotto */ }
  return `${file.size}|${file.lastModified}`
}

// Doppioni tra i vini di questo import (stessa logica di confronto del server)
const checkBatch = async () => {
  if (!wines.value.length) return
  try {
    const res = await fetchWithAuth('/products/import/check-batch', {
      method: 'POST',
      body: { wines: wines.value.map(w => ({ producer_id: w.producer_id || '', name: w.name || '', is_riserva: !!w.is_riserva, source_file: w.source_file || '' })) }
    })
    for (const r of res?.results || []) {
      const w = wines.value[r.index]
      if (!w) continue
      const first = r.duplicate_of_index != null ? wines.value[r.duplicate_of_index] : null
      if (first) {
        const isNew = !w._batchDupOf
        w._batchDupOf = { name: first.name, source_file: first.source_file }
        if (isNew && !w._userAction) { w.action = 'skip'; w._dupAuto = true }
      } else {
        w._batchDupOf = null
        if (w._dupAuto && w.action === 'skip') w.action = w.existing_product ? 'update' : 'create'
        w._dupAuto = false
      }
    }
  } catch (e) { /* controllo facoltativo: in caso di errore la conferma ha comunque una verifica lato server */ }
}

// Ricontrolla il catalogo quando cambiano cantina o nome del vino
const recheckWine = async (w) => {
  if (w.producer_id && (w.name || '').trim()) {
    try {
      const res = await fetchWithAuth('/products/import/check-duplicate', {
        method: 'POST',
        body: { producer_id: w.producer_id, name: w.name, category: w.category || '', is_riserva: !!w.is_riserva }
      })
      w.existing_product = res?.existing_product || null
    } catch (e) { /* lascia il valore precedente */ }
  } else {
    w.existing_product = null
  }
  if (w.existing_product && w.action === 'create' && !w._userAction) w.action = 'update'
  if (!w.existing_product && w.action === 'update') w.action = 'create'
  await checkBatch()
}

const prepareWine = (w, file) => ({
  ...w,
  _key: ++keySeq,
  _open: false,
  _file: file,
  _batchDupOf: null,
  _dupAuto: false,
  _userAction: false,
  _grapesText: (w.grape_varieties || []).join(', '),
  denominazione: w.denominazione || '',
  vintage_year: w.vintage_year ?? null,
  alcohol_degrees: w.alcohol_degrees ?? null,
  tasting_notes: { visual: '', olfactory: '', taste: '', ...(w.tasting_notes || {}) },
  custom_attributes: (w.custom_attributes || []).map(a => ({ ...a })),
  food_pairings: [...(w.food_pairings || [])],
  missing_fields: w.missing_fields || [],
  warnings: w.warnings || []
})

const parseOne = async (fs) => {
  fs.state = 'running'
  fs.error = ''
  const form = new FormData()
  form.append('files', fs.file)
  if (defaultProducerId.value) form.append('producer_id', defaultProducerId.value)
  try {
    const res = await fetchWithAuth('/products/import/parse-pdfs', { method: 'POST', body: form })
    const entry = res?.files?.[0]
    if (!entry || entry.status !== 'ok') {
      fs.state = 'error'
      fs.error = entry?.error || 'Analisi non riuscita'
      return
    }
    const parsed = entry.wines.map(w => prepareWine(w, fs.file))
    fs.count = parsed.length
    fs.state = 'ok'
    if (!parsed.length) {
      fs.state = 'error'
      fs.error = (entry.warnings || []).join(' ') || 'Nessun vino riconosciuto nel documento'
    }
    wines.value.push(...parsed)
  } catch (err) {
    fs.state = 'error'
    fs.error = err?.data?.detail || 'Errore di comunicazione con il server'
  }
}

const analyze = async () => {
  if (!files.value.length) return
  busy.value = true
  step.value = 'analyzing'
  wines.value = []
  fileStates.value = files.value.map(f => ({ name: f.name, file: f, state: 'queued', count: 0, error: '', duplicateOf: '' }))
  // un file alla volta: avanzamento visibile ed errori isolati per documento
  const seen = new Map()
  for (const fs of fileStates.value) {
    const fp = await fileFingerprint(fs.file)
    if (seen.has(fp)) {
      fs.state = 'duplicate'
      fs.duplicateOf = seen.get(fp)
      continue
    }
    seen.set(fp, fs.name)
    await parseOne(fs)
  }
  await checkBatch()
  if (wines.value.length === 1) wines.value[0]._open = true
  busy.value = false
  step.value = 'review'
}

const retryFile = async (fs) => {
  busy.value = true
  await parseOne(fs)
  await checkBatch()
  busy.value = false
}

const onProducerChange = (w) => recheckWine(w)

const togglePairing = (w, p) => {
  const i = w.food_pairings.indexOf(p)
  if (i >= 0) w.food_pairings.splice(i, 1)
  else w.food_pairings.push(p)
}

const toPayload = (w, pdfUrl) => ({
  action: w.action,
  existing_id: w.action === 'update' ? w.existing_product?.id : null,
  producer_id: w.producer_id || defaultProducerId.value || null,
  name: (w.name || '').trim(),
  category: w.category,
  denominazione: w.denominazione || '',
  vintage_year: w.vintage_year || null,
  is_riserva: !!w.is_riserva,
  alcohol_degrees: w.alcohol_degrees === '' ? null : w.alcohol_degrees,
  grape_varieties: (w._grapesText || '').split(',').map(s => s.trim()).filter(Boolean),
  food_pairings: w.food_pairings,
  serving_temperature: w.serving_temperature || '',
  indicative_price: w.indicative_price || '',
  description: w.description || '',
  tasting_notes: w.tasting_notes,
  custom_attributes: w.custom_attributes.filter(a => a.name?.trim() && a.value?.trim()),
  technical_sheet_pdf: pdfUrl || ''
})

const confirmImport = async () => {
  const selected = wines.value.filter(w => w.action !== 'skip')
  const withoutProducer = selected.filter(w => !w.producer_id && !defaultProducerId.value)
  if (withoutProducer.length) {
    toast.error(`Scegli la cantina per: ${withoutProducer.map(w => w.name || 'vino senza nome').join(', ')}`)
    withoutProducer.forEach(w => { w._open = true })
    return
  }
  if (selected.some(w => !(w.name || '').trim())) {
    toast.error('Ogni vino deve avere un nome')
    return
  }

  busy.value = true
  try {
    // PDF originale come scheda tecnica scaricabile (un caricamento per file)
    const pdfUrls = new Map()
    if (attachPdf.value) {
      for (const file of new Set(selected.map(w => w._file).filter(f => f && isPdfFile(f)))) {
        const form = new FormData()
        form.append('file', file)
        try {
          const up = await fetchWithAuth('/uploads/document', { method: 'POST', body: form })
          pdfUrls.set(file, up.url)
        } catch (e) {
          toast.error(`${file.name}: impossibile allegare il PDF`)
        }
      }
    }
    const payload = {
      producer_id: defaultProducerId.value || null,
      status: publishStatus.value,
      wines: wines.value.map(w => toPayload(w, pdfUrls.get(w._file)))
    }
    result.value = await fetchWithAuth('/products/import/confirm-batch', { method: 'POST', body: payload })
    step.value = 'done'
    if (result.value.imported_count) {
      toast.success(result.value.message)
      emit('imported', result.value)
    } else {
      toast.error(result.value.message)
    }
  } catch (err) {
    const detail = err?.data?.detail
    toast.error(typeof detail === 'string' ? detail : 'Errore durante il salvataggio dei vini')
  } finally {
    busy.value = false
  }
}

const reset = () => {
  step.value = 'select'
  files.value = []
  fileStates.value = []
  wines.value = []
  result.value = null
}

const close = () => {
  if (busy.value) return
  emit('close')
}
</script>

<style scoped>
.field-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #57534e;
  margin-bottom: 4px;
}
.field-input {
  width: 100%;
  border: 1px solid #e7e5e4;
  border-radius: 0.5rem;
  padding: 0.375rem 0.625rem;
  font-size: 12px;
  background: #fff;
  color: #1c1917;
}
.field-input:focus {
  outline: none;
  box-shadow: 0 0 0 1px #9f1239;
  border-color: #9f1239;
}
</style>
