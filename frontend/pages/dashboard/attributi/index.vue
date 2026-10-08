<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[1040px] flex flex-col gap-6">
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div class="flex flex-col gap-1.5">
        <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Campi della scheda tecnica</h1>
        <p class="text-sm text-ink-soft m-0 max-w-[620px]">
          Le voci che compaiono nelle schede dei vini (vinificazione, affinamento, allergeni…) e i valori pronti
          da scegliere quando si compila una scheda.
        </p>
      </div>
      <button type="button" class="btn-primary btn-sm h-11 shrink-0" @click="openAdd">
        <Plus class="w-4 h-4" aria-hidden="true" /> Nuovo campo
      </button>
    </div>

    <div v-if="(attributes || []).length" class="flex flex-wrap items-center gap-3">
      <label class="relative flex-1 min-w-[220px] max-w-[360px]">
        <span class="sr-only">Cerca un campo o un valore</span>
        <Search class="w-4 h-4 text-ink-mute absolute left-3.5 top-1/2 -translate-y-1/2" aria-hidden="true" />
        <input v-model="query" type="search" placeholder="Cerca un campo o un valore" class="input h-11 pl-10 text-sm" />
      </label>
      <span class="text-sm text-ink-mute">{{ filtered.length }} {{ filtered.length === 1 ? 'campo' : 'campi' }}</span>
    </div>

    <div v-if="pending" class="card p-8 text-center text-sm text-ink-mute">Caricamento…</div>

    <div v-else-if="!(attributes || []).length" class="card p-10 text-center text-sm text-ink-soft">
      Nessun campo ancora: aggiungine uno con "Nuovo campo".
    </div>

    <p v-else-if="!filtered.length" class="card p-8 text-center text-sm text-ink-soft m-0">Nessun campo corrisponde a "{{ query }}".</p>

    <div v-else class="flex flex-col gap-4">
      <article v-for="attr in filtered" :key="attr.id" class="card p-5 flex flex-col gap-4">
        <header class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex flex-col gap-0.5 min-w-0">
            <h2 class="text-[17px] font-bold text-ink m-0">{{ attr.name }}</h2>
            <p class="text-[13px] text-ink-mute m-0">
              {{ countLabel(attr) }}<template v-if="attr.unit_or_hint"> · {{ attr.unit_or_hint }}</template>
            </p>
          </div>
          <div class="flex flex-wrap gap-1.5">
            <button type="button" :class="actBtn" @click="openEdit(attr)">
              <Pencil class="w-3.5 h-3.5" aria-hidden="true" /> Modifica
            </button>
            <button type="button" :class="actBtn" title="Unisci questo doppione in un'altra voce" @click="mergeItem = attr">
              <Merge class="w-3.5 h-3.5" aria-hidden="true" /> Unisci in…
            </button>
            <button type="button" :class="[actBtn, '!text-rose-700 hover:!bg-rose-50']" @click="handleDelete(attr)">
              <Trash2 class="w-3.5 h-3.5" aria-hidden="true" /> Elimina
            </button>
          </div>
        </header>

        <template v-if="values(attr).length">
          <!-- valori brevi: etichette affiancate -->
          <ul v-if="!isLong(attr)" class="list-none m-0 p-0 flex flex-wrap gap-1.5">
            <li v-for="v in shown(attr)" :key="v" :class="valueChip">
              <span :class="matches(v) && 'bg-amber-100 rounded px-0.5'">{{ v }}</span>
              <button type="button" :class="valueX" :aria-label="`Togli il valore ${v}`" title="Togli questo valore" @click="removeValue(attr, v)">
                <X class="w-3 h-3" aria-hidden="true" />
              </button>
            </li>
          </ul>
          <!-- frasi lunghe: un valore per riga, su due colonne -->
          <ol v-else class="list-none m-0 p-0 grid grid-cols-1 md:grid-cols-2 gap-2">
            <li v-for="v in shown(attr)" :key="v" class="group flex items-start gap-2 px-3 py-2.5 rounded-xl bg-stone-50 border border-stone-100 text-[13px] leading-snug text-ink-soft">
              <span :class="['flex-1', matches(v) && 'bg-amber-100 rounded px-0.5']">{{ v }}</span>
              <button type="button" :class="[valueX, 'mt-px']" :aria-label="`Togli il valore ${v}`" title="Togli questo valore" @click="removeValue(attr, v)">
                <X class="w-3 h-3" aria-hidden="true" />
              </button>
            </li>
          </ol>
          <button
            v-if="values(attr).length > LIMIT"
            type="button"
            class="self-start text-sm font-semibold text-wine-800 hover:underline underline-offset-2"
            :aria-expanded="!!expanded[attr.id]"
            @click="expanded[attr.id] = !expanded[attr.id]"
          >
            {{ expanded[attr.id] ? 'Mostra meno' : `Mostra tutti (${values(attr).length})` }}
          </button>
        </template>
        <p v-else class="text-[13px] text-ink-mute m-0">Nessun valore pronto: nelle schede si scrive a mano.</p>
      </article>
    </div>

    <!-- Nuovo / Modifica -->
    <div v-if="form" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" @click.self="form = null">
      <div role="dialog" aria-modal="true" aria-labelledby="attr-form-title" class="bg-white rounded-2xl w-full max-w-[560px] max-h-[92vh] overflow-y-auto p-6 shadow-2xl">
        <div class="flex items-center justify-between mb-4">
          <h3 id="attr-form-title" class="text-xl font-bold text-ink m-0">{{ form.id ? 'Modifica campo' : 'Nuovo campo' }}</h3>
          <button type="button" class="p-1 text-stone-400 hover:text-ink-soft" aria-label="Chiudi" @click="form = null"><X class="w-5 h-5" /></button>
        </div>
        <form class="flex flex-col gap-4" @submit.prevent="save">
          <label class="field-label">Nome del campo *
            <input v-model="form.name" type="text" required placeholder="es. Affinamento, Allergeni" class="input" />
          </label>
          <label class="field-label">Unità o suggerimento
            <input v-model="form.unit_or_hint" type="text" placeholder="es. mesi, m s.l.m., % vol" class="input" />
          </label>
          <label class="field-label">Valori pronti
            <textarea v-model="form.values" rows="10" placeholder="Un valore per riga, es.&#10;Acciaio&#10;Barrique&#10;Botte grande" class="input h-auto py-3 text-[14px] leading-relaxed"></textarea>
            <span class="text-[13px] font-normal text-ink-mute">Un valore per riga: le virgole dentro un valore restano come sono. {{ formCount }}</span>
          </label>
          <div class="flex justify-end gap-2.5 pt-1">
            <button type="button" class="btn-ghost btn-sm" @click="form = null">Annulla</button>
            <button type="submit" class="btn-primary btn-sm" :disabled="saving">{{ saving ? 'Salvataggio…' : 'Salva' }}</button>
          </div>
        </form>
      </div>
    </div>

    <MergeDialog v-if="mergeItem" endpoint="/attributes" :item="mergeItem" :items="attributes || []" @close="mergeItem = null" @merged="mergeItem = null; refresh()" />
  </div>
</template>

<script setup>
import { Plus, Trash2, Pencil, X, Merge, Search } from 'lucide-vue-next'
import MergeDialog from '~/components/MergeDialog.vue'

useSeoMeta({ title: 'Campi della scheda tecnica - EnotecaMolise' })

const { fetchWithAuth } = useApi()
const toast = useToast()

const LIMIT = 8          // valori visibili prima di "Mostra tutti"
const LONG_TEXT = 40     // oltre questa lunghezza un valore e' una frase: si mostra in elenco

// stili ripetuti
const actBtn = 'inline-flex items-center gap-1 h-8 px-3 rounded-lg bg-stone-100 text-ink-soft text-xs font-semibold transition-colors hover:bg-wine-50 hover:text-wine-900'
const valueChip = 'inline-flex items-center gap-1 pl-2.5 pr-1 py-1 rounded-lg bg-stone-100 text-[13px] text-ink-soft'
const valueX = 'shrink-0 p-0.5 rounded text-stone-400 hover:text-rose-700 hover:bg-rose-50'

const mergeItem = ref(null)
const query = ref('')
const expanded = reactive({})
const form = ref(null)
const saving = ref(false)

const { data: attributes, pending, refresh } = await useAsyncData('master_attributes', async () => {
  return (await fetchWithAuth('/attributes')) || []
}, { default: () => [] })

const norm = (s) => String(s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '')
const values = (attr) => attr.suggested_values || []
const isLong = (attr) => values(attr).some(v => String(v).length > LONG_TEXT)
const matches = (v) => !!query.value.trim() && norm(v).includes(norm(query.value.trim()))
const countLabel = (attr) => {
  const n = values(attr).length
  return n ? `${n} ${n === 1 ? 'valore pronto' : 'valori pronti'}` : 'Testo libero'
}

const filtered = computed(() => {
  const q = norm(query.value.trim())
  const list = [...(attributes.value || [])].sort((a, b) => a.name.localeCompare(b.name, 'it'))
  if (!q) return list
  return list.filter(a => norm(a.name).includes(q) || norm(a.unit_or_hint).includes(q) || values(a).some(v => norm(v).includes(q)))
})

// cercando un valore si apre tutto l'elenco, cosi' il valore trovato si vede
const shown = (attr) => {
  const all = values(attr)
  if (expanded[attr.id] || all.length <= LIMIT) return all
  if (query.value.trim() && all.some(matches)) return all
  return all.slice(0, LIMIT)
}

const splitLines = (text) => {
  const seen = new Set()
  return String(text || '').split('\n').map(v => v.trim()).filter(v => v && !seen.has(v.toLowerCase()) && seen.add(v.toLowerCase()))
}
const formCount = computed(() => {
  const n = form.value ? splitLines(form.value.values).length : 0
  return n ? `(${n} ${n === 1 ? 'valore' : 'valori'})` : ''
})

const openAdd = () => { form.value = { id: '', name: '', unit_or_hint: '', values: '' } }
const openEdit = (attr) => {
  form.value = { id: attr.id, name: attr.name, unit_or_hint: attr.unit_or_hint || '', values: values(attr).join('\n') }
}

const save = async () => {
  if (!form.value) return
  saving.value = true
  const body = { name: form.value.name.trim(), unit_or_hint: form.value.unit_or_hint.trim(), suggested_values: splitLines(form.value.values) }
  try {
    if (form.value.id) {
      const saved = await fetchWithAuth(`/attributes/${form.value.id}`, { method: 'PUT', body })
      const n = saved?.products_updated || 0
      toast.success(n ? `Campo aggiornato: nuovo nome applicato anche a ${n === 1 ? '1 vino' : `${n} vini`}.` : 'Campo aggiornato.')
    } else {
      await fetchWithAuth('/attributes', { method: 'POST', body })
      toast.success('Campo creato.')
    }
    form.value = null
    await refresh()
  } catch (err) {
    // es. 409: esiste gia' una voce con lo stesso nome
    toast.error(err?.data?.detail || 'Salvataggio non riuscito.')
  } finally {
    saving.value = false
  }
}

const removeValue = async (attr, value) => {
  try {
    await fetchWithAuth(`/attributes/${attr.id}`, {
      method: 'PUT',
      body: { name: attr.name, unit_or_hint: attr.unit_or_hint || '', suggested_values: values(attr).filter(v => v !== value) }
    })
    toast.success('Valore tolto dai valori pronti (le schede dei vini non cambiano).')
    await refresh()
  } catch (err) {
    toast.error(err?.data?.detail || 'Operazione non riuscita.')
  }
}

const handleDelete = async (attr) => {
  if (!confirm(`Eliminare il campo "${attr.name}"?`)) return
  try {
    await fetchWithAuth(`/attributes/${attr.id}`, { method: 'DELETE' })
    toast.success('Campo eliminato.')
    await refresh()
  } catch (err) {
    toast.error('Eliminazione non riuscita.')
  }
}
</script>
