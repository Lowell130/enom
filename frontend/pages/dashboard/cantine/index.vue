<template>
  <div class="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="flex flex-col md:flex-row md:items-center justify-between mb-8 gap-4">
      <div>
        <NuxtLink to="/dashboard" class="inline-flex items-center space-x-1 text-xs text-wine-800 font-semibold hover:underline mb-1">
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Torna alla Dashboard</span>
        </NuxtLink>
        <h1 class="font-sans text-3xl font-extrabold text-stone-900 tracking-tight">
          Gestione Cantine & Produttori (Admin)
        </h1>
        <p class="text-xs text-stone-500 mt-1">
          Aggiungi nuove cantine molisane, modifica i loro dati e contatti o gestisci quelle esistenti.
        </p>
      </div>

      <button @click="showAddModal = true" class="inline-flex items-center space-x-1.5 px-6 py-3 bg-wine-800 hover:bg-wine-900 text-white font-semibold text-sm rounded-xl shadow-xs transition-all">
        <Plus class="w-4 h-4 text-amber-200" />
        <span>Aggiungi Nuova Cantina</span>
      </button>
    </div>

    <!-- Producers Table -->
    <div class="bg-white rounded-3xl border border-stone-200/60 shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-stone-500">
        Caricamento cantine in corso...
      </div>

      <div v-else-if="producers && producers.length" class="overflow-x-auto">
        <table class="w-full text-left text-sm text-stone-700">
          <thead class="bg-stone-50 text-xs uppercase font-bold text-stone-500 border-b border-stone-100">
            <tr>
              <th class="py-4 px-6">Cantina</th>
              <th class="py-4 px-6">Città / Prov.</th>
              <th class="py-4 px-6">Contatti</th>
              <th class="py-4 px-6">Vini a Catalogo</th>
              <th class="py-4 px-6 text-right">Azioni</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-stone-100">
            <tr v-for="p in producers" :key="p.id" class="hover:bg-stone-50/50 transition-colors">
              
              <!-- Cantina Name & Logo (Clickable Link to Producer Page) -->
              <td class="py-4 px-6 min-w-[240px]">
                <NuxtLink :to="`/produttori/${p.slug}`" target="_blank" class="flex items-center space-x-3.5 group cursor-pointer" title="Clicca per visualizzare la pagina della cantina">
                  <div class="w-12 h-12 shrink-0 bg-white rounded-xl border border-stone-200/70 p-1 flex items-center justify-center group-hover:border-wine-300 transition-colors">
                    <img :src="getLogo(p)" class="max-h-full max-w-full object-cover rounded-lg group-hover:scale-105 transition-transform" />
                  </div>
                  <div>
                    <span class="font-sans font-bold text-sm text-stone-900 group-hover:text-wine-800 leading-snug block transition-colors">{{ p.company_name }}</span>
                    <span class="text-xs text-stone-500 font-medium block mt-0.5">slug: {{ p.slug }}</span>
                  </div>
                </NuxtLink>
              </td>

              <!-- Città / Prov -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span class="font-bold text-stone-900 block text-xs">{{ p.address?.city || 'Molise' }}</span>
                <span class="text-stone-500 font-medium block mt-0.5">Prov. {{ p.address?.province || 'CB' }}</span>
              </td>

              <!-- Contatti -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span v-if="p.contacts?.email_contact" class="font-medium text-stone-700 block text-xs flex items-center space-x-1">
                  <Mail class="w-3.5 h-3.5 text-stone-400 shrink-0" />
                  <span>{{ p.contacts.email_contact }}</span>
                </span>
                <div class="flex items-center space-x-3 mt-1 text-stone-500 font-medium text-[11px]">
                  <span v-if="p.contacts?.phone" class="inline-flex items-center space-x-1">
                    <Phone class="w-3 h-3 text-stone-400" />
                    <span>{{ p.contacts.phone }}</span>
                  </span>
                  <span v-if="p.contacts?.whatsapp_number" class="inline-flex items-center space-x-1 text-emerald-700 font-semibold">
                    <MessageSquare class="w-3 h-3 text-emerald-600" />
                    <span>WA: {{ p.contacts.whatsapp_number }}</span>
                  </span>
                </div>
              </td>

              <!-- Vini a Catalogo -->
              <td class="py-4 px-6 text-xs whitespace-nowrap">
                <span class="px-3 py-1 bg-wine-50 text-wine-900 rounded-full font-bold border border-wine-200/60 inline-flex items-center space-x-1.5">
                  <Wine class="w-3.5 h-3.5 text-wine-800" />
                  <span>{{ p.product_count || 0 }} Vini</span>
                </span>
              </td>

              <!-- Azioni (Aligned 2-Row Layout matching Gestione Prodotti) -->
              <td class="py-4 px-6 text-right whitespace-nowrap">
                <div class="flex flex-col items-end space-y-1.5">
                  
                  <!-- Row 1: Vedi Pagina & Modifica -->
                  <div class="flex items-center space-x-2">
                    <NuxtLink 
                      :to="`/produttori/${p.slug}`"
                      target="_blank"
                      class="px-3 py-1.5 bg-stone-100 hover:bg-wine-50 hover:text-wine-900 text-stone-700 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-stone-200/60"
                      title="Visualizza Pagina Cantina"
                    >
                      <Eye class="w-3.5 h-3.5 text-wine-800" />
                      <span>Vedi</span>
                    </NuxtLink>

                    <button 
                      @click="openEditModal(p)" 
                      class="px-3 py-1.5 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded-xl text-xs font-semibold transition-all inline-flex items-center space-x-1 border border-stone-200/60"
                    >
                      <Pencil class="w-3.5 h-3.5 text-stone-500" />
                      <span>Modifica</span>
                    </button>
                  </div>

                  <!-- Row 2: Elimina -->
                  <div class="flex items-center space-x-2">
                    <button 
                      @click="handleDelete(p.id)" 
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

    </div>

    <!-- MODAL NUOVA CANTINA -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto border border-stone-100">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-sans text-xl font-bold text-stone-900">Aggiungi Nuova Cantina</h3>
          <button @click="showAddModal = false" class="text-stone-400 hover:text-stone-600 p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleAddProducer" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Nome Cantina *</label>
            <input v-model="newProducer.company_name" type="text" required placeholder="es. Cantine del Molise" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Città *</label>
              <input v-model="newProducer.city" type="text" required placeholder="Campobasso" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">CAP</label>
              <input v-model="newProducer.zip_code" type="text" placeholder="86010" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Provincia</label>
              <input v-model="newProducer.province" type="text" placeholder="CB" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Indirizzo (Via/Contrada)</label>
            <input v-model="newProducer.street" type="text" placeholder="Via Matese 10" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Email Contatto</label>
              <input v-model="newProducer.email_contact" type="email" placeholder="info@cantina.it" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Telefono</label>
              <input v-model="newProducer.phone" type="text" placeholder="+39 0874 12345" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Numero WhatsApp (es. 393331234567)</label>
              <input v-model="newProducer.whatsapp_number" type="text" placeholder="393331234567" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Sito Web Ufficiale</label>
              <input v-model="newProducer.website" type="text" placeholder="https://..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">URL Logo Cantina</label>
            <input v-model="newProducer.logo_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'logo', 'new')" class="text-xs text-stone-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">URL Foto Copertina Cantina</label>
            <input v-model="newProducer.cover_image_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'cover', 'new')" class="text-xs text-stone-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Descrizione / Storia</label>
            <textarea v-model="newProducer.description" rows="3" placeholder="Breve descrizione della cantina..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm"></textarea>
          </div>

          <div class="pt-2 flex justify-end space-x-3">
            <button type="button" @click="showAddModal = false" class="px-4 py-2 text-sm text-stone-600 font-semibold">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs">Crea Cantina</button>
          </div>
        </form>
      </div>
    </div>

    <!-- MODAL MODIFICA CANTINA -->
    <div v-if="showEditModal" class="fixed inset-0 z-50 bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-3xl max-w-xl w-full p-6 sm:p-8 shadow-2xl relative max-h-[90vh] overflow-y-auto border border-stone-100">
        <div class="flex items-center justify-between mb-4 border-b border-stone-100 pb-3">
          <h3 class="font-sans text-xl font-bold text-stone-900">Modifica Cantina: {{ editProducer.company_name }}</h3>
          <button @click="showEditModal = false" class="text-stone-400 hover:text-stone-600 p-1">
            <X class="w-5 h-5" />
          </button>
        </div>

        <form @submit.prevent="handleUpdateProducer" class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Nome Cantina / Azienda *</label>
            <input v-model="editProducer.company_name" type="text" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <div class="grid grid-cols-3 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Città *</label>
              <input v-model="editProducer.city" type="text" required class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">CAP</label>
              <input v-model="editProducer.zip_code" type="text" placeholder="86010" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Provincia</label>
              <input v-model="editProducer.province" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Indirizzo (Via/Contrada)</label>
            <input v-model="editProducer.street" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Email Contatto</label>
              <input v-model="editProducer.email_contact" type="email" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Telefono</label>
              <input v-model="editProducer.phone" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">WhatsApp (es. 393331234567)</label>
              <input v-model="editProducer.whatsapp_number" type="text" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
            <div>
              <label class="block text-xs font-semibold text-stone-700 mb-1">Sito Web</label>
              <input v-model="editProducer.website" type="text" placeholder="https://..." class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">URL Logo Cantina</label>
            <input v-model="editProducer.logo_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'logo')" class="text-xs text-stone-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">URL Foto Copertina Cantina</label>
            <input v-model="editProducer.cover_image_url" type="text" placeholder="https://... o carica" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUploadMedia(e, 'cover')" class="text-xs text-stone-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Descrizione / Storia Cantina</label>
            <textarea v-model="editProducer.description" rows="4" class="w-full border border-stone-200 rounded-xl px-3.5 py-2.5 text-sm"></textarea>
          </div>

          <div class="pt-4 flex justify-end space-x-3 border-t border-stone-100">
            <button type="button" @click="showEditModal = false" class="px-4 py-2.5 text-sm text-stone-600 font-semibold hover:bg-stone-50 rounded-xl">Annulla</button>
            <button type="submit" class="px-6 py-2.5 bg-wine-800 text-white rounded-xl text-sm font-semibold shadow-xs hover:bg-wine-900">Salva Modifiche</button>
          </div>
        </form>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Plus, Pencil, Eye, Trash2, X, Mail, Phone, MessageSquare, Wine } from 'lucide-vue-next'

const { fetchWithAuth, mediaBase } = useApi()
const toast = useToast()

const showAddModal = ref(false)
const showEditModal = ref(false)

const { data: producers, pending, refresh } = await useAsyncData('admin_producers_manage', () => 
  fetchWithAuth('/producers')
)

const newProducer = reactive({
  company_name: '',
  city: 'Campobasso',
  province: 'CB',
  zip_code: '',
  street: '',
  email_contact: '',
  phone: '',
  whatsapp_number: '',
  website: '',
  logo_url: '',
  cover_image_url: '',
  description: ''
})

const editProducer = reactive({
  id: '',
  company_name: '',
  city: '',
  province: '',
  zip_code: '',
  street: '',
  email_contact: '',
  phone: '',
  whatsapp_number: '',
  website: '',
  logo_url: '',
  cover_image_url: '',
  description: ''
})

const getLogo = (p) => {
  if (p.logo_url) {
    return p.logo_url.startsWith('http') ? p.logo_url : `${mediaBase}${p.logo_url}`
  }
  return 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=300&q=80'
}

const openEditModal = (p) => {
  editProducer.id = p.id
  editProducer.company_name = p.company_name
  editProducer.city = p.address?.city || ''
  editProducer.province = p.address?.province || ''
  editProducer.zip_code = p.address?.zip_code || ''
  editProducer.street = p.address?.street || ''
  editProducer.email_contact = p.contacts?.email_contact || ''
  editProducer.phone = p.contacts?.phone || ''
  editProducer.whatsapp_number = p.contacts?.whatsapp_number || ''
  editProducer.website = p.contacts?.website || ''
  editProducer.logo_url = p.logo_url || ''
  editProducer.cover_image_url = p.cover_image_url || ''
  editProducer.description = p.description || ''
  showEditModal.value = true
}

const handleFileUpload = async (event, target, type) => {
  const file = event.target.files[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const res = await fetchWithAuth('/upload', {
      method: 'POST',
      body: formData
    })
    const targetObj = target === 'new' ? newProducer : editProducer
    if (type === 'logo') targetObj.logo_url = res.url
    if (type === 'cover') targetObj.cover_image_url = res.url
    toast.success('Immagine caricata con successo!')
  } catch (err) {
    toast.error('Errore durante l\'upload dell\'immagine.')
  }
}

const handleAddProducer = async () => {
  try {
    await fetchWithAuth('/producers', {
      method: 'POST',
      body: {
        company_name: newProducer.company_name,
        description: newProducer.description,
        logo_url: newProducer.logo_url,
        cover_image_url: newProducer.cover_image_url,
        address: { 
          street: newProducer.street, 
          city: newProducer.city, 
          province: newProducer.province,
          zip_code: newProducer.zip_code
        },
        contacts: { 
          email_contact: newProducer.email_contact, 
          phone: newProducer.phone, 
          whatsapp_number: newProducer.whatsapp_number,
          website: newProducer.website
        }
      }
    })
    showAddModal.value = false
    // Reset form fields
    newProducer.company_name = ''
    newProducer.street = ''
    newProducer.zip_code = ''
    newProducer.email_contact = ''
    newProducer.phone = ''
    newProducer.whatsapp_number = ''
    newProducer.website = ''
    newProducer.logo_url = ''
    newProducer.cover_image_url = ''
    newProducer.description = ''
    toast.success('Cantina creata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante la creazione della cantina.')
  }
}

const handleUpdateProducer = async () => {
  try {
    await fetchWithAuth(`/producers/${editProducer.id}`, {
      method: 'PUT',
      body: {
        company_name: editProducer.company_name,
        description: editProducer.description,
        logo_url: editProducer.logo_url,
        cover_image_url: editProducer.cover_image_url,
        address: {
          street: editProducer.street,
          city: editProducer.city,
          province: editProducer.province,
          zip_code: editProducer.zip_code
        },
        contacts: {
          email_contact: editProducer.email_contact,
          phone: editProducer.phone,
          whatsapp_number: editProducer.whatsapp_number,
          website: editProducer.website
        }
      }
    })
    toast.success('Cantina aggiornata con successo!')
    showEditModal.value = false
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'aggiornamento della cantina.')
  }
}

const handleDelete = async (id) => {
  if (!confirm('Eliminare questa cantina e TUTTI i suoi vini?')) return
  try {
    await fetchWithAuth(`/producers/${id}`, { method: 'DELETE' })
    toast.success('Cantina eliminata con successo!')
    await refresh()
  } catch (err) {
    toast.error('Errore durante l\'eliminazione.')
  }
}
</script>
