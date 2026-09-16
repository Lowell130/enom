<template>
  <div class="py-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
    
    <div class="mb-8">
      <NuxtLink to="/dashboard" class="inline-flex items-center space-x-1 text-xs text-wine-800 font-semibold hover:underline mb-1">
        <ArrowLeft class="w-3.5 h-3.5" />
        <span>Torna alla Dashboard</span>
      </NuxtLink>
      <h1 class="font-sans text-3xl font-extrabold text-stone-900 tracking-tight">
        Richieste di Contatto Utenti
      </h1>
      <p class="text-xs text-stone-500 mt-1">
        Messaggi inviati dagli utenti del portale per informazioni su prezzi, disponibilità e degustazioni.
      </p>
    </div>

    <div class="bg-white rounded-3xl border border-stone-200/60 shadow-xs overflow-hidden">
      
      <div v-if="pending" class="p-8 text-center text-sm text-stone-500">
        Caricamento messaggi...
      </div>

      <div v-else-if="inquiries && inquiries.length" class="divide-y divide-stone-100">
        <div 
          v-for="msg in inquiries" 
          :key="msg.id" 
          class="p-6 transition-colors hover:bg-stone-50/50 flex flex-col md:flex-row md:items-center justify-between gap-4"
          :class="{ 'bg-wine-50/20': !msg.is_read }"
        >
          <div class="space-y-2">
            <div class="flex flex-wrap items-center gap-2">
              <span class="font-bold text-stone-900 text-sm">{{ msg.user_name }}</span>
              <span class="text-xs text-stone-400 font-light">&lt;{{ msg.user_email }}&gt;</span>
              <span v-if="msg.user_phone" class="inline-flex items-center space-x-1 text-xs text-stone-500 font-medium">
                <Phone class="w-3 h-3 text-stone-400" />
                <span>{{ msg.user_phone }}</span>
              </span>
              <span v-if="!msg.is_read" class="px-2.5 py-0.5 bg-wine-800 text-white rounded-full text-[10px] font-bold tracking-wider uppercase">NUOVO</span>
            </div>

            <div class="text-xs font-semibold text-wine-900 flex items-center space-x-1.5">
              <Building2 class="w-3.5 h-3.5 text-wine-800" />
              <span>Cantina: {{ msg.producer_name }}</span>
              <span v-if="msg.product_name" class="ml-2 text-stone-600 font-normal">| Vino: <strong>{{ msg.product_name }}</strong></span>
            </div>

            <p class="text-sm text-stone-700 bg-stone-50/80 p-4 rounded-2xl border border-stone-200/50 leading-relaxed max-w-3xl font-light">
              "{{ msg.message }}"
            </p>
          </div>

          <div class="flex items-center space-x-3 flex-shrink-0">
            <a 
              :href="`mailto:${msg.user_email}?subject=Risposta da ${msg.producer_name}`" 
              class="inline-flex items-center space-x-1.5 px-4 py-2.5 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-xs font-semibold transition-all shadow-xs"
            >
              <Mail class="w-3.5 h-3.5" />
              <span>Rispondi via Email</span>
            </a>
            
            <button 
              v-if="!msg.is_read" 
              @click="markRead(msg.id)" 
              class="inline-flex items-center space-x-1 px-3 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl text-xs font-semibold"
            >
              <CheckCircle class="w-3.5 h-3.5 text-stone-500" />
              <span>Segna letto</span>
            </button>
          </div>
        </div>
      </div>

      <div v-else class="p-16 text-center text-stone-500">
        <MessageSquare class="w-8 h-8 text-stone-400 mx-auto mb-2" />
        <p class="text-sm font-light">Nessuna richiesta di contatto ricevuta.</p>
      </div>

    </div>

  </div>
</template>

<script setup>
import { ArrowLeft, Phone, Building2, Mail, CheckCircle, MessageSquare } from 'lucide-vue-next'

const { fetchWithAuth } = useApi()

const { data: inquiries, pending, refresh } = await useAsyncData('user_inquiries', async () => {
  const res = await fetchWithAuth('/inquiries')
  return res || []
}, { default: () => [] })

const toast = useToast()

const markRead = async (id) => {
  try {
    await fetchWithAuth(`/inquiries/${id}/read`, { method: 'PUT' })
    toast.success('Messaggio segnato come letto.')
    await refresh()
  } catch (err) {
    toast.error('Errore aggiornamento stato.')
  }
}
</script>
