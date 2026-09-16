<template>
  <div class="py-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <NuxtLink to="/dashboard" class="text-xs font-semibold text-wine-800 hover:text-wine-900 mb-2 inline-flex items-center gap-1">
          <ArrowLeft class="w-3.5 h-3.5" />
          <span>Torna alla Dashboard</span>
        </NuxtLink>
        <h1 class="font-sans text-3xl font-extrabold text-stone-900 tracking-tight">
          Profilo Cantina
        </h1>
        <p class="text-xs text-stone-500 mt-1">
          Gestisci la storia, la foto copertina, il logo e i contatti della tua azienda vinicola.
        </p>
      </div>

      <!-- Admin Producer Selector Dropdown -->
      <div v-if="isAdmin && producersList.length" class="w-full md:w-64">
        <label class="block text-xs font-bold uppercase text-stone-500 mb-1">Seleziona Cantina (Admin)</label>
        <select 
          v-model="selectedAdminProducerId" 
          @change="loadProfile"
          class="w-full border border-stone-200 rounded-xl px-3 py-2 text-xs font-semibold bg-white text-stone-800 focus:ring-2 focus:ring-wine-800"
        >
          <option v-for="p in producersList" :key="p.id" :value="p.id">
            {{ p.company_name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="pending" class="bg-white rounded-3xl p-12 text-center text-sm text-stone-500 flex flex-col items-center justify-center space-y-3 border border-stone-100 shadow-xs">
      <RefreshCw class="w-6 h-6 text-wine-800 animate-spin" />
      <span>Caricamento profilo cantina in corso...</span>
    </div>

    <!-- Form State -->
    <form v-else-if="form" @submit.prevent="handleSubmit" class="space-y-8 bg-white rounded-3xl p-8 border border-stone-200/70 shadow-xs">
      
      <!-- General Info -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-stone-100 pb-2">
          Dati Aziendali & Posizione Mappa
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-stone-700 mb-1">Nome Cantina / Ragione Sociale *</label>
            <input v-model="form.company_name" type="text" required class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Città *</label>
            <input v-model="form.city" type="text" required class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">CAP (Codice Avviamento Postale)</label>
            <input v-model="form.zip_code" type="text" placeholder="es. 86010" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Provincia</label>
            <input v-model="form.province" type="text" placeholder="es. CB" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-stone-700 mb-1">Indirizzo (Via/Contrada)</label>
            <input v-model="form.street" type="text" placeholder="es. Contrada Colle 14" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <!-- Coordinate GPS Mappa -->
          <div class="sm:col-span-2 bg-stone-50 p-4 rounded-xl border border-stone-200/80 space-y-3">
            <div class="flex items-center space-x-2 text-wine-900 font-bold text-xs">
              <MapPin class="w-4 h-4 text-wine-800" />
              <span>Coordinate GPS Mappa Interattiva</span>
            </div>
            <p class="text-xs text-stone-500 font-light leading-relaxed">
              Inserisci la latitudine e longitudine della tua cantina per posizionare con precisione la tua azienda sulla Mappa delle Cantine Molisane.
            </p>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label class="block text-xs font-semibold text-stone-700 mb-1">Latitudine (es. 41,6147818 o 41.6147818)</label>
                <input v-model="form.lat" type="text" placeholder="41,6147818" class="w-full bg-white border border-stone-200 rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-wine-800 focus:outline-none font-mono" />
              </div>
              <div>
                <label class="block text-xs font-semibold text-stone-700 mb-1">Longitudine (es. 14,5462307 o 14.5462307)</label>
                <input v-model="form.lng" type="text" placeholder="14,5462307" class="w-full bg-white border border-stone-200 rounded-lg px-3 py-2 text-xs focus:ring-2 focus:ring-wine-800 focus:outline-none font-mono" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Contacts -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-stone-100 pb-2">
          Contatti & Social
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Email Pubblica Contatto</label>
            <input v-model="form.email_contact" type="email" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Telefono Fisso / Sede</label>
            <input v-model="form.phone" type="text" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">WhatsApp Diretto (es. 393331234567)</label>
            <input v-model="form.whatsapp_number" type="text" placeholder="393331234567" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Sito Web Ufficiale</label>
            <input v-model="form.website" type="text" placeholder="https://..." class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
          </div>
        </div>
      </div>

      <!-- Immagini & Storia -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-stone-100 pb-2">
          Immagini & Storia della Cantina
        </h3>

        <div class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Logo Cantina (URL o carica file)</label>
            <div class="flex items-center space-x-2">
              <input v-model="form.logo_url" type="text" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
              <label class="px-4 py-2.5 bg-stone-100 hover:bg-wine-50 text-stone-700 hover:text-wine-900 border border-stone-200 text-xs font-semibold rounded-xl cursor-pointer shrink-0 transition-colors">
                <span>Carica File</span>
                <input type="file" accept="image/*" @change="e => handleUpload(e, 'logo')" class="hidden" />
              </label>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Foto Copertina Cantina (URL o carica file)</label>
            <div class="flex items-center space-x-2">
              <input v-model="form.cover_image_url" type="text" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none" />
              <label class="px-4 py-2.5 bg-stone-100 hover:bg-wine-50 text-stone-700 hover:text-wine-900 border border-stone-200 text-xs font-semibold rounded-xl cursor-pointer shrink-0 transition-colors">
                <span>Carica File</span>
                <input type="file" accept="image/*" @change="e => handleUpload(e, 'cover')" class="hidden" />
              </label>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">La Storia & Filosofia della Cantina</label>
            <textarea v-model="form.description" rows="5" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"></textarea>
          </div>
        </div>
      </div>

      <div class="pt-4 flex items-center justify-between space-x-4 border-t border-stone-100">
        <button 
          v-if="isAdmin || form.id"
          type="button"
          @click="handleDeleteProducer"
          class="px-4 py-2.5 bg-rose-50 hover:bg-rose-100 text-rose-700 font-semibold rounded-xl text-xs transition-colors flex items-center space-x-1.5"
        >
          <Trash2 class="w-3.5 h-3.5" />
          <span>Elimina Scheda Cantina</span>
        </button>

        <div class="flex items-center space-x-3 ml-auto">
          <NuxtLink to="/dashboard" class="px-6 py-3 border border-stone-200 text-stone-700 font-semibold rounded-xl text-sm hover:bg-stone-50 transition-colors">
            Annulla
          </NuxtLink>
          <button type="submit" :disabled="submitting" class="px-8 py-3 bg-wine-800 hover:bg-wine-900 text-white font-bold rounded-xl text-sm shadow-md transition-all">
            {{ submitting ? 'Salvataggio...' : 'Salva Profilo Cantina' }}
          </button>
        </div>
      </div>

    </form>

    <!-- Error / Missing Profile State -->
    <div v-else class="bg-white rounded-3xl p-8 border border-stone-200/60 shadow-xs text-center py-12 space-y-4">
      <Building2 class="w-12 h-12 text-stone-300 mx-auto" />
      <h3 class="font-serif text-xl font-bold text-stone-800">Profilo Cantina non Disponibile</h3>
      <p class="text-sm text-stone-500 max-w-md mx-auto font-light">
        {{ loadError || 'Impossibile caricare i dati della cantina. Assicurati che l\'account sia collegato a una cantina.' }}
      </p>
      <button @click="loadProfile" class="inline-flex items-center space-x-2 px-6 py-2.5 bg-wine-800 text-white text-xs font-bold rounded-xl shadow-xs hover:bg-wine-900 transition-all">
        <RefreshCw class="w-4 h-4" />
        <span>Riprova a Caricare</span>
      </button>
    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Building2, RefreshCw, Trash2, MapPin } from 'lucide-vue-next'

const route = useRoute()
const { fetchWithAuth } = useApi()
const { user, fetchUser, isAdmin } = useAuth()
const toast = useToast()

const submitting = ref(false)
const pending = ref(true)
const form = ref(null)
const loadError = ref(null)

const producersList = ref([])
const selectedAdminProducerId = ref('')

const currentProducerId = computed(() => {
  if (isAdmin.value && selectedAdminProducerId.value) {
    return selectedAdminProducerId.value
  }
  return user.value?.producer_id || user.value?.producer?.id
})

const loadProfile = async () => {
  pending.value = true
  loadError.value = null
  try {
    const me = await fetchUser()
    
    // If Admin, load producers list so they can switch
    if (me?.role === 'ADMIN') {
      if (!producersList.value.length) {
        const list = await fetchWithAuth('/producers')
        producersList.value = list || []
      }
      if (route.query.producer_id) {
        selectedAdminProducerId.value = String(route.query.producer_id)
      } else if (producersList.value.length && !selectedAdminProducerId.value) {
        selectedAdminProducerId.value = producersList.value[0].id
      }
    }

    const pId = isAdmin.value ? selectedAdminProducerId.value : (me?.producer_id || me?.producer?.id || user.value?.producer_id || user.value?.producer?.id)
    
    if (!pId) {
      loadError.value = "Nessuna cantina associata a questo account utente."
      pending.value = false
      return
    }

    const p = await fetchWithAuth(`/producers/${pId}`)
    if (p) {
      const pGeo = p.address?.geo_coordinates || {}
      form.value = {
        id: p.id,
        company_name: p.company_name || '',
        city: p.address?.city || '',
        province: p.address?.province || '',
        zip_code: p.address?.zip_code || '',
        street: p.address?.street || '',
        lat: pGeo.lat || '',
        lng: pGeo.lng || '',
        email_contact: p.contacts?.email_contact || '',
        phone: p.contacts?.phone || '',
        whatsapp_number: p.contacts?.whatsapp_number || '',
        website: p.contacts?.website || '',
        logo_url: p.logo_url || '',
        cover_image_url: p.cover_image_url || '',
        description: p.description || ''
      }
    }
  } catch (err) {
    console.error('Errore caricamento profilo cantina:', err)
    loadError.value = 'Impossibile recuperare le informazioni della cantina.'
  } finally {
    pending.value = false
  }
}

onMounted(() => {
  loadProfile()
})

watch(() => route.query.producer_id, (newPId) => {
  if (newPId && isAdmin.value) {
    selectedAdminProducerId.value = String(newPId)
    loadProfile()
  }
})

watch(() => user.value, (newVal) => {
  if (newVal && !form.value) {
    loadProfile()
  }
})

const handleUpload = async (event, type) => {
  const file = event.target.files[0]
  if (!file) return
  const formData = new FormData()
  formData.append('file', file)
  try {
    const res = await fetchWithAuth('/uploads/image', {
      method: 'POST',
      body: formData
    })
    if (type === 'logo') form.value.logo_url = res.url
    if (type === 'cover') form.value.cover_image_url = res.url
    toast.success('Immagine caricata con successo!')
  } catch (err) {
    toast.error('Errore durante l\'upload dell\'immagine.')
  }
}

const parseCoordInput = (val) => {
  if (val === null || val === undefined || val === '') return null
  const num = Number(String(val).replace(',', '.').trim())
  return isNaN(num) ? null : num
}

const handleSubmit = async () => {
  const targetId = form.value?.id || currentProducerId.value
  if (!targetId) return
  submitting.value = true
  try {
    const latNum = parseCoordInput(form.value.lat)
    const lngNum = parseCoordInput(form.value.lng)
    await fetchWithAuth(`/producers/${targetId}`, {
      method: 'PUT',
      body: {
        company_name: form.value.company_name,
        description: form.value.description,
        logo_url: form.value.logo_url,
        cover_image_url: form.value.cover_image_url,
        address: {
          street: form.value.street,
          city: form.value.city,
          province: form.value.province,
          zip_code: form.value.zip_code,
          geo_coordinates: (latNum !== null && lngNum !== null) ? { lat: latNum, lng: lngNum } : null
        },
        contacts: {
          email_contact: form.value.email_contact,
          phone: form.value.phone,
          whatsapp_number: form.value.whatsapp_number,
          website: form.value.website
        }
      }
    })
    toast.success('Profilo cantina aggiornato con successo!')
    await fetchUser()
    navigateTo('/dashboard')
  } catch (err) {
    toast.error('Errore durante l\'aggiornamento.')
  } finally {
    submitting.value = false
  }
}

const handleDeleteProducer = async () => {
  const targetId = form.value?.id || currentProducerId.value
  if (!targetId) return
  if (!confirm(`Sei sicuro di voler eliminare la scheda della cantina "${form.value?.company_name || ''}" e tutti i suoi vini?`)) return
  
  try {
    await fetchWithAuth(`/producers/${targetId}`, { method: 'DELETE' })
    toast.success('Scheda cantina eliminata con successo!')
    await fetchUser()
    form.value = null
    loadProfile()
  } catch (err) {
    toast.error('Errore durante l\'eliminazione della cantina.')
  }
}
</script>
