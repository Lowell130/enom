<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[900px]">
    
    <div class="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div>
        <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Profilo della cantina</h1>
        <p class="text-sm text-ink-soft mt-1.5">Storia, logo, copertina, indirizzo e contatti: è ciò che vedono i visitatori.</p>
      </div>

      <!-- Admin Producer Selector Dropdown -->
      <div v-if="isAdmin && producersList.length" class="w-full md:w-64">
        <label for="scelta-cantina" class="block text-[13px] font-semibold text-ink-soft mb-1">Cantina da modificare</label>
        <select
          id="scelta-cantina"
          v-model="selectedAdminProducerId"
          @change="loadProfile"
          class="select h-10 text-sm"
        >
          <option v-for="p in producersList" :key="p.id" :value="p.id">
            {{ p.company_name }}
          </option>
        </select>
      </div>
    </div>

    <!-- Stato della cantina (solo per la cantina stessa) -->
    <p v-if="!isAdmin && producerStatus === 'PENDING_APPROVAL'" role="status" class="mb-5 p-4 rounded-xl border border-[#E8D9B8] bg-[#FBF5E8] text-[#5A4524] text-sm">
      <strong>In attesa di approvazione.</strong> Completa il profilo: lo verifichiamo e ti avvisiamo via email quando la cantina sarà pubblica.
    </p>

    <!-- Loading State -->
    <div v-if="pending" class="card p-12 text-center text-sm text-ink-mute flex flex-col items-center justify-center gap-3">
      <RefreshCw class="w-6 h-6 text-wine-800 animate-spin" />
      <span>Caricamento del profilo…</span>
    </div>

    <!-- Form State -->
    <form v-else-if="form" @submit.prevent="handleSubmit" class="flex flex-col gap-8 card p-6 sm:p-8">

      <!-- Dati e indirizzo -->
      <section class="flex flex-col gap-4" aria-labelledby="sez-dati">
        <h2 id="sez-dati" class="font-serif text-2xl font-bold text-ink">Dati della cantina e posizione</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="field-label sm:col-span-2">Nome della cantina *
            <input v-model="form.company_name" type="text" required class="input" />
          </label>
          <label class="field-label">Comune *
            <input v-model="form.city" type="text" required list="comuni-molise" placeholder="es. Larino" class="input" />
            <span v-if="!form.city" class="text-[13px] font-normal text-wine-800">Indica il comune: serve per la pagina pubblica e per la mappa.</span>
          </label>
          <datalist id="comuni-molise">
            <option v-for="t in towns" :key="t" :value="t" />
          </datalist>
          <label class="field-label">Provincia
            <select v-model="form.province" class="select">
              <option value="">—</option>
              <option value="CB">Campobasso (CB)</option>
              <option value="IS">Isernia (IS)</option>
            </select>
          </label>
          <div class="sm:col-span-2 grid grid-cols-1 sm:grid-cols-[1fr_160px] gap-4">
            <label class="field-label">Indirizzo (via o contrada)
              <input v-model="form.street" type="text" placeholder="es. Contrada Colle 14" class="input" />
            </label>
            <label class="field-label">CAP
              <input v-model="form.zip_code" type="text" inputmode="numeric" maxlength="5" placeholder="86035" class="input" />
            </label>
          </div>
          <div class="sm:col-span-2 flex flex-col gap-2">
            <span class="text-sm font-semibold text-ink">Posizione sulla mappa</span>
            <ClientOnly>
              <LocationPicker :lat="form.lat" :lng="form.lng" :town="form.city" @update="onPickLocation" />
            </ClientOnly>
            <details class="text-[13px] text-ink-mute">
              <summary class="cursor-pointer w-fit">Inserisci le coordinate a mano</summary>
              <div class="grid grid-cols-2 gap-3 mt-2">
                <label class="field-label">Latitudine<input v-model="form.lat" type="text" inputmode="decimal" placeholder="41,80140" class="input font-mono text-sm" /></label>
                <label class="field-label">Longitudine<input v-model="form.lng" type="text" inputmode="decimal" placeholder="14,91080" class="input font-mono text-sm" /></label>
              </div>
            </details>
          </div>
        </div>
      </section>

      <!-- Contatti -->
      <section class="flex flex-col gap-4" aria-labelledby="sez-contatti">
        <h2 id="sez-contatti" class="font-serif text-2xl font-bold text-ink">Contatti</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="field-label">Email per le richieste dei clienti
            <input v-model="form.email_contact" type="email" class="input" />
            <span class="text-[13px] font-normal text-ink-mute">Qui ti avvisiamo quando un cliente ti scrive.</span>
          </label>
          <label class="field-label">Telefono
            <input v-model="form.phone" type="tel" class="input" />
          </label>
          <label class="field-label">WhatsApp
            <input v-model="form.whatsapp_number" type="tel" placeholder="es. 393331234567" class="input" />
            <span class="text-[13px] font-normal text-ink-mute">Con il prefisso 39, senza spazi: comparirà il pulsante WhatsApp.</span>
          </label>
          <label class="field-label">Sito web
            <input v-model="form.website" type="text" placeholder="www.lamiacantina.it" class="input" />
          </label>
        </div>
      </section>

      <!-- Immagini e storia -->
      <section class="flex flex-col gap-4" aria-labelledby="sez-immagini">
        <h2 id="sez-immagini" class="font-serif text-2xl font-bold text-ink">Immagini e storia</h2>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <FileUploadField v-model="form.logo_url" label="Logo" kind="logo" hint="PNG o JPG, meglio quadrato. Appare sempre su fondo bianco." />
          <FileUploadField v-model="form.cover_image_url" label="Foto di copertina" kind="cover" hint="Una foto orizzontale dei vigneti o della cantina. Senza foto usiamo un'illustrazione." />
        </div>
        <label class="field-label">La storia della cantina
          <textarea v-model="form.description" rows="6" class="input h-auto py-3 leading-relaxed" placeholder="Chi siete, dove sono le vigne, cosa rende speciali i vostri vini…"></textarea>
          <span class="text-[13px] font-normal" :class="(form.description || '').length < 150 ? 'text-ink-mute' : 'text-bio'">
            {{ (form.description || '').length }} caratteri · consigliati almeno 150
          </span>
        </label>
      </section>

      <div class="pt-5 flex flex-wrap items-center justify-between gap-3 border-t border-line">
        <button
          v-if="isAdmin"
          type="button"
          @click="handleDeleteProducer"
          class="btn-ghost btn-sm text-wine-800"
        >
          <Trash2 class="w-4 h-4" aria-hidden="true" /> Elimina la cantina
        </button>
        <div class="flex items-center gap-3 ml-auto">
          <NuxtLink to="/dashboard" class="btn-ghost">Annulla</NuxtLink>
          <button type="submit" :disabled="submitting" class="btn-primary">
            {{ submitting ? 'Salvataggio…' : 'Salva il profilo' }}
          </button>
        </div>
      </div>
    </form>

    <!-- Cancellazione dell'account (cantina) -->
    <section v-if="form && !isAdmin" class="mt-6 card p-6 flex flex-col gap-3" aria-labelledby="sez-cancella">
      <h2 id="sez-cancella" class="font-serif text-xl font-bold text-ink">Cancellazione dell'account</h2>
      <template v-if="deletionRequestedAt">
        <p class="text-sm text-ink-soft m-0">
          Hai chiesto la cancellazione il {{ formatDate(deletionRequestedAt) }}. L'amministratore ti contatterà per confermarla;
          fino ad allora il profilo resta com'è.
        </p>
        <button type="button" class="btn-ghost btn-sm w-fit" :disabled="deleting" @click="cancelDeletion">Annulla la richiesta</button>
      </template>
      <template v-else-if="showDeletionForm">
        <label class="field-label">Vuoi dirci il motivo? (facoltativo)
          <textarea v-model="deletionReason" rows="3" maxlength="1000" class="input h-auto py-3"></textarea>
        </label>
        <p class="text-[13px] text-ink-mute m-0">La cancellazione elimina la pagina della cantina, tutti i vini e l'account, e non si può annullare.</p>
        <div class="flex gap-2">
          <button type="button" class="btn-primary btn-sm" :disabled="deleting" @click="requestDeletion">Invia la richiesta</button>
          <button type="button" class="btn-ghost btn-sm" @click="showDeletionForm = false">Annulla</button>
        </div>
      </template>
      <template v-else>
        <p class="text-sm text-ink-soft m-0">Puoi chiedere di cancellare la cantina, i vini e l'account: la richiesta arriva all'amministratore.</p>
        <button type="button" class="btn-ghost btn-sm w-fit text-wine-800" @click="showDeletionForm = true">Chiedi la cancellazione</button>
      </template>
    </section>

    <!-- Error / Missing Profile State -->
    <div v-else class="bg-white rounded-2xl p-8 border border-line shadow-xs text-center py-12 space-y-4">
      <Building2 class="w-12 h-12 text-stone-300 mx-auto" />
      <h3 class="font-serif text-xl font-bold text-stone-800">Profilo Cantina non Disponibile</h3>
      <p class="text-sm text-ink-mute max-w-md mx-auto font-light">
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
import { Building2, RefreshCw, Trash2 } from 'lucide-vue-next'
import FileUploadField from '~/components/FileUploadField.vue'
import LocationPicker from '~/components/LocationPicker.client.vue'
import { apiErrorMessage } from '~/utils/apiError'

const route = useRoute()
const { fetchWithAuth } = useApi()
const { user, fetchUser, isAdmin } = useAuth()
const toast = useToast()

const submitting = ref(false)
const pending = ref(true)
const form = ref(null)
const loadError = ref(null)

const producersList = ref([])
const producerStatus = ref('')
const deletionRequestedAt = ref(null)
const showDeletionForm = ref(false)
const deletionReason = ref('')
const deleting = ref(false)

// comuni del Molise suggeriti nel campo (si puo' comunque scrivere qualsiasi nome)
const towns = ['Acquaviva Collecroce', 'Agnone', 'Bojano', 'Campobasso', 'Campomarino', 'Casacalenda', 'Castropignano', 'Colletorto',
  'Guardialfiera', 'Guglionesi', 'Isernia', 'Larino', 'Macchia d\'Isernia', 'Mafalda', 'Montecilfone', 'Montenero di Bisaccia',
  'Monteroduni', 'Montorio nei Frentani', 'Palata', 'Petacciato', 'Petrella Tifernina', 'Portocannone', 'Pozzilli', 'Ripalimosani',
  'Rotello', 'San Felice del Molise', 'San Giacomo degli Schiavoni', 'San Martino in Pensilis', 'Santa Croce di Magliano',
  'Sesto Campano', 'Termoli', 'Ururi', 'Venafro']

// provincia proposta in automatico per i comuni noti (resta modificabile)
const ISERNIA_TOWNS = ['Agnone', 'Isernia', 'Macchia d\'Isernia', 'Monteroduni', 'Pozzilli', 'Sesto Campano', 'Venafro']
watch(() => form.value?.city, (city) => {
  if (!form.value || form.value.province || !city) return
  const name = city.trim().toLowerCase()
  if (!towns.some(t => t.toLowerCase() === name)) return
  form.value.province = ISERNIA_TOWNS.some(t => t.toLowerCase() === name) ? 'IS' : 'CB'
})

const onPickLocation = ({ lat, lng }) => {
  form.value.lat = lat ?? ''
  form.value.lng = lng ?? ''
}

const formatDate = (d) => new Date(d).toLocaleDateString('it-IT', { day: 'numeric', month: 'long', year: 'numeric' })
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
        const list = await fetchWithAuth('/producers?include_all=true')
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
      producerStatus.value = p.status || ''
      deletionRequestedAt.value = p.deletion_requested_at || null
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
    toast.success('Profilo salvato.')
    await fetchUser()
    navigateTo('/dashboard')
  } catch (err) {
    toast.error(apiErrorMessage(err, 'Errore durante il salvataggio del profilo.'))
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

const requestDeletion = async () => {
  deleting.value = true
  try {
    const res = await fetchWithAuth('/producers/me/deletion-request', { method: 'POST', body: { reason: deletionReason.value } })
    deletionRequestedAt.value = res.deletion_requested_at
    showDeletionForm.value = false
    toast.success('Richiesta inviata all\'amministratore.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    deleting.value = false
  }
}

const cancelDeletion = async () => {
  deleting.value = true
  try {
    await fetchWithAuth('/producers/me/deletion-request', { method: 'DELETE' })
    deletionRequestedAt.value = null
    toast.success('Richiesta di cancellazione annullata.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    deleting.value = false
  }
}
</script>
