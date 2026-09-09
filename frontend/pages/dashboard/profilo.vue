<template>
  <div class="py-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="mb-8">
      <NuxtLink to="/dashboard" class="text-xs font-semibold text-wine-800 hover:text-wine-900 mb-2 inline-flex items-center gap-1">
        <ArrowLeft class="w-3.5 h-3.5" />
        <span>Torna alla Dashboard</span>
      </NuxtLink>
      <h1 class="font-sans text-3xl font-extrabold text-stone-900 tracking-tight">
        Profilo Cantina
      </h1>
      <p class="text-xs text-gray-500 mt-1">
        Gestisci la storia, la foto copertina, il logo e i contatti della tua azienda vinicola.
      </p>
    </div>

    <div v-if="pending" class="p-12 text-center text-sm text-gray-500">
      Caricamento profilo cantina...
    </div>

    <form v-else-if="form" @submit.prevent="handleSubmit" class="space-y-8 bg-white rounded-3xl p-8 border border-gray-100 shadow-sm">
      
      <!-- General Info -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-gray-100 pb-2">
          Dati Aziendali
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-gray-700 mb-1">Nome Cantina / Ragione Sociale *</label>
            <input v-model="form.company_name" type="text" required class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Città *</label>
            <input v-model="form.city" type="text" required class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">CAP (Codice Avviamento Postale)</label>
            <input v-model="form.zip_code" type="text" placeholder="es. 86010" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Provincia</label>
            <input v-model="form.province" type="text" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>

          <div class="sm:col-span-2">
            <label class="block text-xs font-semibold text-gray-700 mb-1">Indirizzo (Via/Contrada)</label>
            <input v-model="form.street" type="text" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>
        </div>
      </div>

      <!-- Contacts -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-gray-100 pb-2">
          Contatti & Social
        </h3>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Email Pubblica Contatto</label>
            <input v-model="form.email_contact" type="email" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Telefono Fisso / Sede</label>
            <input v-model="form.phone" type="text" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">WhatsApp Diretto (es. 393331234567)</label>
            <input v-model="form.whatsapp_number" type="text" placeholder="393331234567" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Sito Web Ufficiale</label>
            <input v-model="form.website" type="text" placeholder="https://..." class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm" />
          </div>
        </div>
      </div>

      <!-- Immagini & Storia -->
      <div>
        <h3 class="font-sans text-lg font-bold text-wine-900 mb-4 border-b border-gray-100 pb-2">
          Immagini & Storia della Cantina
        </h3>

        <div class="space-y-4">
          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Logo Cantina (URL o carica file)</label>
            <input v-model="form.logo_url" type="text" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUpload(e, 'logo')" class="text-xs text-gray-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">Foto Copertina Cantina (URL o carica file)</label>
            <input v-model="form.cover_image_url" type="text" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm mb-1" />
            <input type="file" accept="image/*" @change="e => handleUpload(e, 'cover')" class="text-xs text-gray-500" />
          </div>

          <div>
            <label class="block text-xs font-semibold text-gray-700 mb-1">La Storia & Filosofia della Cantina</label>
            <textarea v-model="form.description" rows="5" class="w-full border border-gray-200 rounded-xl px-4 py-2.5 text-sm"></textarea>
          </div>
        </div>
      </div>

      <div class="pt-4 flex justify-end space-x-4">
        <NuxtLink to="/dashboard" class="px-6 py-3 border border-gray-200 text-gray-700 font-semibold rounded-xl text-sm hover:bg-gray-50">
          Annulla
        </NuxtLink>
        <button type="submit" :disabled="submitting" class="px-8 py-3 bg-wine-800 hover:bg-wine-900 text-white font-bold rounded-xl text-sm shadow-md transition-all">
          {{ submitting ? 'Salvataggio...' : 'Salva Profilo Cantina' }}
        </button>
      </div>

    </form>

  </div>
</template>

<script setup>
import { ArrowLeft, MapPin } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()
const { user, fetchUser } = useAuth()

const submitting = ref(false)
const form = ref(null)

const producerId = computed(() => user.value?.producer_id || user.value?.producer?.id)

const { data: producer, pending } = await useAsyncData('my_producer_profile', async () => {
  const me = await fetchUser()
  const pId = me?.producer_id || me?.producer?.id
  if (!pId) return null
  const p = await fetchWithAuth(`/producers/${pId}`)
  const pGeo = p.address?.geo_coordinates || {}
  form.value = {
    company_name: p.company_name,
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
  return p
})

const toast = useToast()

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

const handleSubmit = async () => {
  if (!producerId.value) return
  submitting.value = true
  try {
    await fetchWithAuth(`/producers/${producerId.value}`, {
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
          geo_coordinates: (form.value.lat && form.value.lng) ? { lat: Number(form.value.lat), lng: Number(form.value.lng) } : null
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
  } catch (err) {
    toast.error('Errore durante l\'aggiornamento.')
  } finally {
    submitting.value = false
  }
}
</script>
