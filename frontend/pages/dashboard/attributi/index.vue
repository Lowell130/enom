<template>
  <div class="py-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <NuxtLink to="/dashboard" class="inline-flex items-center space-x-1 text-xs text-wine-800 font-semibold hover:underline mb-1">
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Torna alla Dashboard</span>
        </NuxtLink>
        <h1 class="font-sans text-3xl font-extrabold text-stone-900 tracking-tight">
          Caratteristiche Scheda Tecnica & Presets
        </h1>
        <p class="text-xs text-stone-500 mt-1">
          Gestisci il catalogo delle caratteristiche tecniche e i valori di scelta rapida memorizzati (es. Gradazione, Vinificazione, Allergeni...).
        </p>
      </div>

      <button @click="showAddModal = true" class="inline-flex items-center space-x-1.5 px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-sm rounded-xl shadow-xs transition-all">
        <Plus class="w-4 h-4 text-amber-200" />
        <span>Nuova Caratteristica</span>
      </button>
    </div>

    <!-- Master Attributes Table -->
    <div class="bg-white rounded-3xl border border-stone-200/60 shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-stone-500">
        Caricamento caratteristiche...
      </div>

      <div v-else-if="attributes && attributes.length" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-stone-700">
          <thead class="bg-stone-50 text-xs uppercase font-bold text-stone-500 border-b border-stone-100">
            <tr>
              <th class="py-4 px-6">Nome Caratteristica</th>
              <th class="py-4 px-6">Unità / Descrizione</th>
              <th class="py-4 px-6">Valori / Presets Salvati</th>
              <th class="py-4 px-6 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr v-for="attr in attributes" :key="attr.id" class="hover:bg-stone-50/50 transition-colors">
              <td class="py-4 px-6 font-sans font-bold text-stone-900 flex items-center space-x-2">
                <List class="w-4 h-4 text-wine-800" />
                <span>{{ attr.name }}</span>
              </td>
              <td class="py-4 px-6 text-xs text-stone-500 font-medium">
                {{ attr.unit_or_hint || '-' }}
              </td>
              <td class="py-4 px-6">
                <div v-if="attr.suggested_values && attr.suggested_values.length" class="flex flex-wrap gap-1 max-w-md">
                  <span 
                    v-for="(val, idx) in attr.suggested_values" 
                    :key="idx"
                    class="px-2 py-0.5 bg-stone-100 text-stone-700 rounded-md text-[11px] font-medium"
                  >
                    {{ val }}
                  </span>
                </div>
                <span v-else class="text-xs text-stone-400 font-light">Nessun valore preimpostato</span>
              </td>
              <td class="py-4 px-6 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <button @click="openEditModal(attr)" class="inline-flex items-center space-x-1 px-3 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-stone-700 rounded-lg text-xs font-semibold transition-colors">
                    <Pencil class="w-3.5 h-3.5 text-stone-500" />
                    <span>Modifica</span>
                  </button>
                  <button @click="handleDelete(attr.id)" class="inline-flex items-center space-x-1 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-semibold">
                    <Trash2 class="w-3.5 h-3.5" />
                    <span>Elimina</span>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

    </div>

    <!-- Modal Nuova Caratteristica -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl relative border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-stone-900">Aggiungi Caratteristica Tecnica</h3>
          <button @click="showAddModal = false" class="text-stone-400 hover:text-stone-600 p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleAddAttribute" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Nome Caratteristica *</label>
            <input v-model="newAttr.name" type="text" required placeholder="es. Altitudine Vigneto, Vinificazione..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Unità o Descrizione Breve</label>
            <input v-model="newAttr.unit_or_hint" type="text" placeholder="es. s.l.m., Guyot, % Vol" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Valori di Scelta Rapida (Separati da virgola)</label>
            <input v-model="suggestedValuesInput" type="text" placeholder="es. 400 m, 500 m, 600 m" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showAddModal = false" class="px-4 py-2 text-sm text-stone-600 font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Salva Caratteristica</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Modifica Caratteristica -->
    <div v-if="showEditModal && editingAttr" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl relative border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-stone-900">Modifica Caratteristica Tecnica</h3>
          <button @click="showEditModal = false" class="text-stone-400 hover:text-stone-600 p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleSaveEdit" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Nome Caratteristica *</label>
            <input v-model="editingAttr.name" type="text" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Unità o Descrizione Breve</label>
            <input v-model="editingAttr.unit_or_hint" type="text" placeholder="es. s.l.m., Guyot, % Vol" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Valori di Scelta Rapida / Presets (Separati da virgola)</label>
            <textarea v-model="editSuggestedValuesInput" rows="3" placeholder="es. 10.0%, 11.5%, 12.0%, 13.5%, 14.5%" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"></textarea>
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showEditModal = false" class="px-4 py-2 text-sm text-stone-600 font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Aggiorna Caratteristica</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Plus, List, Trash2, Pencil, X } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()
const showAddModal = ref(false)
const showEditModal = ref(false)

const suggestedValuesInput = ref('')
const editSuggestedValuesInput = ref('')

const newAttr = reactive({
  name: '',
  unit_or_hint: ''
})

const editingAttr = ref(null)

const { data: attributes, pending, refresh } = await useAsyncData('master_attributes', () => 
  fetchWithAuth('/attributes')
)

const toast = useToast()

const handleAddAttribute = async () => {
  try {
    const values = suggestedValuesInput.value 
      ? suggestedValuesInput.value.split(',').map(v => v.trim()).filter(Boolean)
      : []

    await fetchWithAuth('/attributes', {
      method: 'POST',
      body: {
        ...newAttr,
        suggested_values: values
      }
    })
    newAttr.name = ''
    newAttr.unit_or_hint = ''
    suggestedValuesInput.value = ''
    showAddModal.value = false
    toast.success('Caratteristica creata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante il salvataggio.')
  }
}

const openEditModal = (attr) => {
  editingAttr.value = {
    id: attr.id,
    name: attr.name,
    unit_or_hint: attr.unit_or_hint || ''
  }
  editSuggestedValuesInput.value = (attr.suggested_values || []).join(', ')
  showEditModal.value = true
}

const handleSaveEdit = async () => {
  if (!editingAttr.value) return
  try {
    const values = editSuggestedValuesInput.value
      ? editSuggestedValuesInput.value.split(',').map(v => v.trim()).filter(Boolean)
      : []

    await fetchWithAuth(`/attributes/${editingAttr.value.id}`, {
      method: 'PUT',
      body: {
        name: editingAttr.value.name,
        unit_or_hint: editingAttr.value.unit_or_hint,
        suggested_values: values
      }
    })
    showEditModal.value = false
    editingAttr.value = null
    toast.success('Caratteristica aggiornata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'aggiornamento.')
  }
}

const handleDelete = async (id) => {
  if (!confirm('Eliminare questa caratteristica dal catalogo master?')) return
  try {
    await fetchWithAuth(`/attributes/${id}`, { method: 'DELETE' })
    toast.success('Caratteristica eliminata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'eliminazione.')
  }
}
</script>
