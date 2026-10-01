<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[1040px]">
    
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">
          Gestione Vitigni & Uve (Admin)
        </h1>
        <p class="text-xs text-ink-mute mt-1">
          Gestisci il catalogo dei vitigni autoctoni molisani e internazionali utilizzabili nelle schede vino.
        </p>
      </div>

      <button @click="showAddModal = true" class="inline-flex items-center space-x-1.5 px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-sm rounded-xl shadow-xs transition-all">
        <Plus class="w-4 h-4 text-amber-200" />
        <span>Nuovo Vitigno</span>
      </button>
    </div>

    <!-- Master Grapes Table -->
    <div class="bg-white rounded-2xl border border-line shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-ink-mute">
        Caricamento vitigni in corso...
      </div>

      <div v-else-if="grapes && grapes.length" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-ink-soft">
          <thead class="bg-stone-50 text-xs uppercase font-bold text-ink-mute border-b border-stone-100">
            <tr>
              <th class="py-4 px-6">Nome Vitigno</th>
              <th class="py-4 px-6">Tipologia</th>
              <th class="py-4 px-6 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr v-for="g in grapes" :key="g.id" class="hover:bg-stone-50/50 transition-colors">
              <td class="py-4 px-6 font-sans font-bold text-ink flex items-center space-x-2">
                <Grape class="w-4 h-4 text-wine-800" />
                <span>{{ g.name }}</span>
              </td>
              <td class="py-4 px-6 text-xs font-semibold">
                <span v-if="g.category === 'AUTOCTONO'" class="px-2.5 py-1 bg-amber-50 text-amber-900 rounded-full border border-amber-200/60 inline-flex items-center space-x-1">
                  <Grape class="w-3.5 h-3.5 text-amber-700" />
                  <span>Autoctono Molisano</span>
                </span>
                <span v-else class="px-2.5 py-1 bg-stone-100 text-ink-soft rounded-full border border-line inline-flex items-center space-x-1">
                  <Globe class="w-3.5 h-3.5 text-ink-mute" />
                  <span>Nazionale / Internazionale</span>
                </span>
              </td>
              <td class="py-4 px-6 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <button @click="openEditModal(g)" class="inline-flex items-center space-x-1 px-3 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-ink-soft rounded-lg text-xs font-semibold transition-colors">
                    <Pencil class="w-3.5 h-3.5 text-ink-mute" />
                    <span>Modifica</span>
                  </button>
                  <button @click="handleDelete(g.id)" class="inline-flex items-center space-x-1 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-semibold">
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

    <!-- Modal Nuovo Vitigno -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-ink">Aggiungi Nuovo Vitigno</h3>
          <button @click="showAddModal = false" class="text-stone-400 hover:text-ink-soft p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleAddGrape" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Nome Vitigno *</label>
            <input v-model="newGrape.name" type="text" required placeholder="es. Tintilia, Falanghina, Moscato..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Tipologia Vitigno *</label>
            <select v-model="newGrape.category" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none">
              <option value="AUTOCTONO">Autoctono Molisano</option>
              <option value="INTERNAZIONALE">Nazionale / Internazionale</option>
            </select>
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showAddModal = false" class="px-4 py-2 text-sm text-ink-soft font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Salva Vitigno</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Modifica Vitigno -->
    <div v-if="showEditModal && editingGrape" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl relative border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-ink">Modifica Vitigno</h3>
          <button @click="showEditModal = false" class="text-stone-400 hover:text-ink-soft p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleSaveEdit" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Nome Vitigno *</label>
            <input v-model="editingGrape.name" type="text" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-ink-soft mb-1">Tipologia Vitigno *</label>
            <select v-model="editingGrape.category" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none">
              <option value="AUTOCTONO">Autoctono Molisano</option>
              <option value="INTERNAZIONALE">Nazionale / Internazionale</option>
            </select>
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showEditModal = false" class="px-4 py-2 text-sm text-ink-soft font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Aggiorna Vitigno</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Plus, Grape, Globe, Pencil, Trash2, X } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()
const showAddModal = ref(false)
const showEditModal = ref(false)

const newGrape = reactive({
  name: '',
  category: 'AUTOCTONO'
})

const editingGrape = ref(null)

const { data: grapes, pending, refresh } = await useAsyncData('master_grapes_admin', async () => {
  const res = await fetchWithAuth('/grapes')
  return res || []
}, { default: () => [] })

const toast = useToast()

const handleAddGrape = async () => {
  try {
    await fetchWithAuth('/grapes', {
      method: 'POST',
      body: newGrape
    })
    newGrape.name = ''
    newGrape.category = 'AUTOCTONO'
    showAddModal.value = false
    toast.success('Vitigno creato con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante il salvataggio del vitigno.')
  }
}

const openEditModal = (grape) => {
  editingGrape.value = {
    id: grape.id,
    name: grape.name,
    category: grape.category || 'AUTOCTONO'
  }
  showEditModal.value = true
}

const handleSaveEdit = async () => {
  if (!editingGrape.value) return
  try {
    await fetchWithAuth(`/grapes/${editingGrape.value.id}`, {
      method: 'PUT',
      body: {
        name: editingGrape.value.name,
        category: editingGrape.value.category
      }
    })
    showEditModal.value = false
    editingGrape.value = null
    toast.success('Vitigno aggiornato con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'aggiornamento.')
  }
}

const handleDelete = async (id) => {
  if (!confirm('Eliminare questo vitigno dal catalogo master?')) return
  try {
    await fetchWithAuth(`/grapes/${id}`, { method: 'DELETE' })
    toast.success('Vitigno eliminato con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'eliminazione.')
  }
}
</script>
