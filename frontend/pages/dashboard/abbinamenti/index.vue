<template>
  <div class="py-10 max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <NuxtLink to="/dashboard" class="inline-flex items-center space-x-1 text-xs text-wine-800 font-semibold hover:underline mb-1">
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Torna alla Dashboard</span>
        </NuxtLink>
        <h1 class="font-sans text-3xl font-extrabold text-stone-900 tracking-tight">
          Gestione Abbinamenti Culinari (Admin)
        </h1>
        <p class="text-xs text-stone-500 mt-1">
          Gestisci il catalogo master degli abbinamenti gastronomici selezionabili nelle schede vino.
        </p>
      </div>

      <button @click="showAddModal = true" class="inline-flex items-center space-x-1.5 px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-sm rounded-xl shadow-xs transition-all">
        <Plus class="w-4 h-4 text-amber-200" />
        <span>Nuovo Abbinamento</span>
      </button>
    </div>

    <!-- Master Pairings Table -->
    <div class="bg-white rounded-3xl border border-stone-200/60 shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-stone-500">
        Caricamento abbinamenti in corso...
      </div>

      <div v-else-if="pairings && pairings.length" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-stone-700">
          <thead class="bg-stone-50 text-xs uppercase font-bold text-stone-500 border-b border-stone-100">
            <tr>
              <th class="py-4 px-6">Abbinamento Gastronomico</th>
              <th class="py-4 px-6">Categoria</th>
              <th class="py-4 px-6 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr v-for="item in pairings" :key="item.id" class="hover:bg-stone-50/50 transition-colors">
              <td class="py-4 px-6 font-sans font-bold text-stone-900 flex items-center space-x-2">
                <Utensils class="w-4 h-4 text-wine-800" />
                <span>{{ item.name }}</span>
              </td>
              <td class="py-4 px-6 text-xs font-semibold">
                <span class="px-2.5 py-1 bg-stone-100 text-stone-700 rounded-full border border-stone-200/60 uppercase text-[10px] tracking-wider">
                  {{ item.category || 'GENERALE' }}
                </span>
              </td>
              <td class="py-4 px-6 text-right">
                <div class="flex items-center justify-end space-x-2">
                  <button @click="openEditModal(item)" class="inline-flex items-center space-x-1 px-3 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-stone-700 rounded-lg text-xs font-semibold transition-colors">
                    <Pencil class="w-3.5 h-3.5 text-stone-500" />
                    <span>Modifica</span>
                  </button>
                  <button @click="handleDelete(item.id)" class="inline-flex items-center space-x-1 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded-lg text-xs font-semibold">
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

    <!-- Modal Nuovo Abbinamento -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl relative border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-stone-900">Aggiungi Nuovo Abbinamento</h3>
          <button @click="showAddModal = false" class="text-stone-400 hover:text-stone-600 p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleAddPairing" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Nome Abbinamento *</label>
            <input v-model="newPairing.name" type="text" required placeholder="es. Carne Rossa alla Griglia, Formaggi Stagionati..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Categoria</label>
            <select v-model="newPairing.category" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none">
              <option value="CARNI">Carni & Arrosti</option>
              <option value="FORMAGGI">Formaggi</option>
              <option value="PRIMI">Primi Piatti & Zuppe</option>
              <option value="PESCE">Pesce & Frutti di Mare</option>
              <option value="SALUMI">Salumi & Antipasti</option>
              <option value="APERITIVI">Aperitivi & Finger Food</option>
              <option value="DOLCI">Dolci & Pasticceria</option>
              <option value="GENERALE">Generale / Altro</option>
            </select>
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showAddModal = false" class="px-4 py-2 text-sm text-stone-600 font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Salva Abbinamento</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Modifica Abbinamento -->
    <div v-if="showEditModal && editingPairing" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl relative border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-stone-900">Modifica Abbinamento</h3>
          <button @click="showEditModal = false" class="text-stone-400 hover:text-stone-600 p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleSaveEdit" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Nome Abbinamento *</label>
            <input v-model="editingPairing.name" type="text" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Categoria</label>
            <select v-model="editingPairing.category" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none">
              <option value="CARNI">Carni & Arrosti</option>
              <option value="FORMAGGI">Formaggi</option>
              <option value="PRIMI">Primi Piatti & Zuppe</option>
              <option value="PESCE">Pesce & Frutti di Mare</option>
              <option value="SALUMI">Salumi & Antipasti</option>
              <option value="APERITIVI">Aperitivi & Finger Food</option>
              <option value="DOLCI">Dolci & Pasticceria</option>
              <option value="GENERALE">Generale / Altro</option>
            </select>
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showEditModal = false" class="px-4 py-2 text-sm text-stone-600 font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Aggiorna Abbinamento</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Plus, Utensils, Pencil, Trash2, X } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()
const showAddModal = ref(false)
const showEditModal = ref(false)

const newPairing = reactive({
  name: '',
  category: 'CARNI'
})

const editingPairing = ref(null)

const { data: pairings, pending, refresh } = await useAsyncData('master_pairings_admin', () => 
  fetchWithAuth('/pairings')
)

const toast = useToast()

const handleAddPairing = async () => {
  try {
    await fetchWithAuth('/pairings', {
      method: 'POST',
      body: newPairing
    })
    newPairing.name = ''
    newPairing.category = 'CARNI'
    showAddModal.value = false
    toast.success('Abbinamento creato con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante il salvataggio.')
  }
}

const openEditModal = (item) => {
  editingPairing.value = {
    id: item.id,
    name: item.name,
    category: item.category || 'GENERALE'
  }
  showEditModal.value = true
}

const handleSaveEdit = async () => {
  if (!editingPairing.value) return
  try {
    await fetchWithAuth(`/pairings/${editingPairing.value.id}`, {
      method: 'PUT',
      body: {
        name: editingPairing.value.name,
        category: editingPairing.value.category
      }
    })
    showEditModal.value = false
    editingPairing.value = null
    toast.success('Abbinamento aggiornato con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'aggiornamento.')
  }
}

const handleDelete = async (id) => {
  if (!confirm('Eliminare questo abbinamento dal catalogo master?')) return
  try {
    await fetchWithAuth(`/pairings/${id}`, { method: 'DELETE' })
    toast.success('Abbinamento eliminato con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'eliminazione.')
  }
}
</script>
