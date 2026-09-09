<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 overflow-y-auto bg-stone-900/40 backdrop-blur-xs flex items-center justify-center p-4">
    <div class="bg-white rounded-3xl max-w-lg w-full p-6 sm:p-8 shadow-2xl relative animate-in fade-in zoom-in-95 duration-200 border border-stone-100">
      
      <!-- Close Button -->
      <button @click="close" class="absolute top-5 right-5 text-stone-400 hover:text-stone-700 p-1.5 rounded-full hover:bg-stone-100 transition-colors">
        <X class="w-5 h-5" />
      </button>

      <div class="mb-6">
        <span class="text-xs font-bold text-wine-800 uppercase tracking-widest block mb-1">Contatta il Produttore</span>
        <h3 class="font-serif text-2xl font-bold text-stone-900">
          {{ producerName }}
        </h3>
        <p v-if="productName" class="text-sm text-stone-500 mt-1">
          Richiesta per il vino: <strong class="text-wine-800 font-semibold">{{ productName }}</strong>
        </p>
      </div>

      <!-- Quick WhatsApp Button -->
      <div v-if="whatsappNumber" class="mb-6">
        <a 
          :href="whatsappUrl" 
          target="_blank" 
          class="w-full inline-flex items-center justify-center space-x-2 bg-emerald-700 hover:bg-emerald-800 text-white py-3 px-4 rounded-xl font-semibold text-sm transition-all shadow-xs"
        >
          <MessageSquare class="w-4 h-4 text-emerald-200" />
          <span>Contatta Subito via WhatsApp</span>
        </a>
        <div class="relative my-5">
          <div class="absolute inset-0 flex items-center"><div class="w-full border-t border-stone-200/60"></div></div>
          <div class="relative flex justify-center text-xs uppercase tracking-wider"><span class="bg-white px-3 text-stone-400 font-medium">oppure invia un messaggio</span></div>
        </div>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-xs font-semibold text-stone-700 mb-1">Il tuo Nome e Cognome *</label>
          <div class="relative">
            <User class="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
            <input 
              v-model="form.user_name" 
              type="text" 
              required 
              placeholder="es. Mario Rossi" 
              class="w-full border border-stone-200 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">La tua Email *</label>
            <div class="relative">
              <Mail class="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
              <input 
                v-model="form.user_email" 
                type="email" 
                required 
                placeholder="mario@email.com" 
                class="w-full border border-stone-200 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-stone-700 mb-1">Telefono (Opzionale)</label>
            <div class="relative">
              <Phone class="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
              <input 
                v-model="form.user_phone" 
                type="tel" 
                placeholder="+39 333 1234567" 
                class="w-full border border-stone-200 rounded-xl pl-10 pr-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
              />
            </div>
          </div>
        </div>

        <div>
          <label class="block text-xs font-semibold text-stone-700 mb-1">Tipo di Richiesta</label>
          <select v-model="form.message_type" class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none">
            <option value="INFO_PREZZI">Informazioni su Prezzi e Listino</option>
            <option value="DISPONIBILITA">Verifica Disponibilità e Spedizione</option>
            <option value="VISITA_CANTINA">Prenotazione Visita / Degustazione in Cantina</option>
            <option value="ALTRO">Altra richiesta</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-stone-700 mb-1">Messaggio *</label>
          <textarea 
            v-model="form.message" 
            rows="3" 
            required 
            placeholder="Scrivi qui il tuo messaggio per la cantina..." 
            class="w-full border border-stone-200 rounded-xl px-4 py-2.5 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
          ></textarea>
        </div>

        <div v-if="successMessage" class="p-3.5 bg-emerald-50 text-emerald-800 rounded-xl text-xs font-semibold flex items-center space-x-2 border border-emerald-200">
          <CheckCircle class="w-4 h-4 text-emerald-600 flex-shrink-0" />
          <span>{{ successMessage }}</span>
        </div>

        <div v-if="errorMessage" class="p-3.5 bg-rose-50 text-rose-800 rounded-xl text-xs font-semibold flex items-center space-x-2 border border-rose-200">
          <AlertCircle class="w-4 h-4 text-rose-600 flex-shrink-0" />
          <span>{{ errorMessage }}</span>
        </div>

        <div class="pt-2 flex justify-end space-x-3">
          <button type="button" @click="close" class="px-4 py-2.5 text-sm text-stone-600 hover:text-stone-800 font-medium">
            Annulla
          </button>
          <button 
            type="submit" 
            :disabled="submitting" 
            class="inline-flex items-center space-x-2 px-6 py-2.5 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-sm font-semibold transition-all shadow-xs disabled:opacity-50"
          >
            <Send class="w-4 h-4" />
            <span>{{ submitting ? 'Invio in corso...' : 'Invia Messaggio' }}</span>
          </button>
        </div>
      </form>

    </div>
  </div>
</template>

<script setup>
import { X, MessageSquare, User, Mail, Phone, Send, CheckCircle, AlertCircle } from 'lucide-vue-next'

const props = defineProps({
  isOpen: Boolean,
  producerId: String,
  producerName: String,
  productId: String,
  productName: String,
  whatsappNumber: String
})

const emit = defineEmits(['close'])
const { fetchWithAuth } = useApi()

const form = reactive({
  user_name: '',
  user_email: '',
  user_phone: '',
  message_type: 'INFO_PREZZI',
  message: ''
})

const submitting = ref(false)
const successMessage = ref('')
const errorMessage = ref('')

const { getWhatsAppUrl } = useWhatsApp()

const whatsappUrl = computed(() => {
  return getWhatsAppUrl({
    number: props.whatsappNumber,
    companyName: props.producerName,
    productName: props.productName
  })
})

const close = () => {
  successMessage.value = ''
  errorMessage.value = ''
  emit('close')
}

const handleSubmit = async () => {
  submitting.value = true
  successMessage.value = ''
  errorMessage.value = ''

  try {
    await fetchWithAuth('/inquiries', {
      method: 'POST',
      body: {
        producer_id: props.producerId,
        product_id: props.productId || null,
        user_name: form.user_name,
        user_email: form.user_email,
        user_phone: form.user_phone,
        message_type: form.message_type,
        message: form.message
      }
    })
    successMessage.value = 'Messaggio inviato con successo! La cantina ti risponderà al più presto.'
    setTimeout(() => {
      close()
    }, 2000)
  } catch (err) {
    errorMessage.value = 'Errore durante l\'invio. Riprova più tardi.'
  } finally {
    submitting.value = false
  }
}
</script>
