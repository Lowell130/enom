<template>
  <!-- "E' la tua cantina?": solo per le pagine senza un accesso attivo. Caricato nel browser,
       cosi' la pagina pubblica resta in cache e non fa richieste in piu' al server. -->
  <div v-if="info?.claimable" id="rivendica" class="card p-5 sm:p-6 flex flex-col gap-4 border-dashed">
    <div class="flex flex-col sm:flex-row sm:items-center gap-3 sm:justify-between">
      <div class="flex items-start gap-3">
        <span class="w-10 h-10 rounded-full bg-sand-100 text-wine-800 flex items-center justify-center shrink-0" aria-hidden="true">
          <KeyRound class="w-5 h-5" />
        </span>
        <div class="flex flex-col gap-0.5">
          <h2 class="font-serif text-[22px] font-bold leading-tight m-0">È la tua cantina?</h2>
          <p class="m-0 text-sm text-ink-soft">Gestisci gratuitamente questa pagina: storia, foto, vini ed eventi.
            <NuxtLink to="/guida" target="_blank" class="font-semibold text-wine-800 underline underline-offset-2 whitespace-nowrap">Come funziona</NuxtLink></p>
        </div>
      </div>
      <button v-if="!open" type="button" class="btn-outline btn-sm shrink-0" :aria-expanded="open" aria-controls="rivendica-pannello" @click="open = true">
        Richiedi l'accesso
      </button>
    </div>

    <div v-if="open" id="rivendica-pannello" class="flex flex-col gap-4 border-t border-line pt-4">
      <!-- 1. link all'email della cantina gia' presente nel sito -->
      <div v-if="info.has_email && !manual" class="flex flex-col gap-3">
        <p v-if="sent" role="status" class="m-0 p-3 rounded-[10px] bg-bio-50 border border-bio/30 text-bio-900 text-sm font-semibold">{{ sent }}</p>
        <template v-else>
          <p class="m-0 text-sm text-ink-soft">
            Per verificare che tu sia il titolare, mandiamo il link per scegliere la password all'email della cantina
            che trovi su questa pagina: <strong class="text-ink">{{ info.masked_email }}</strong>.
          </p>
          <div class="flex flex-wrap items-center gap-2">
            <button type="button" class="btn-primary btn-sm" :disabled="sending" @click="sendLink">
              {{ sending ? 'Invio…' : `Invia il link a ${info.masked_email}` }}
            </button>
          </div>
        </template>
        <p v-if="error" role="alert" class="m-0 p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>
        <button type="button" class="self-start text-sm font-semibold text-wine-800 underline underline-offset-2" @click="manual = true; error = ''">
          Non hai accesso a questa email o non è corretta?
        </button>
      </div>

      <!-- 2. richiesta verificata a mano dall'amministratore -->
      <div v-else-if="claimSent" role="status" class="p-3 rounded-[10px] bg-bio-50 border border-bio/30 text-bio-900 text-sm font-semibold">{{ claimSent }}</div>
      <form v-else class="flex flex-col gap-4 relative" novalidate @submit.prevent="sendClaim">
        <p class="m-0 text-sm text-ink-soft">
          Lasciaci i tuoi dati: verifichiamo che tu sia il titolare (di solito con una telefonata) e ti mandiamo il link di accesso
          all'indirizzo che indichi.
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="field-label">Nome e cognome *<input v-model="form.name" type="text" autocomplete="name" maxlength="120" class="input" /></label>
          <label class="field-label">Ruolo in cantina<input v-model="form.role" type="text" maxlength="80" placeholder="es. titolare" class="input" /></label>
          <label class="field-label">Email *<input v-model="form.email" type="email" autocomplete="email" class="input" /></label>
          <label class="field-label">Telefono *<input v-model="form.phone" type="tel" autocomplete="tel" maxlength="40" class="input" /></label>
        </div>
        <label class="field-label">Note (facoltative)
          <textarea v-model="form.message" rows="3" maxlength="2000" class="input h-auto py-3" placeholder="Es. l'email sul sito non è più attiva"></textarea>
        </label>
        <div class="absolute -left-[9999px] w-px h-px overflow-hidden" aria-hidden="true">
          <label>Sito web <input v-model="form.website" type="text" tabindex="-1" autocomplete="off" /></label>
        </div>
        <label class="flex items-start gap-2.5 text-[13px] text-ink-soft cursor-pointer">
          <input v-model="form.privacy_accepted" type="checkbox" class="mt-0.5 w-4 h-4 accent-wine-800 shrink-0" />
          <span>Ho letto l'<NuxtLink to="/privacy" target="_blank" class="font-semibold text-wine-800 underline underline-offset-2">informativa sulla privacy</NuxtLink> e acconsento all'uso dei miei dati per verificare la richiesta.</span>
        </label>
        <p v-if="error" role="alert" class="m-0 p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>
        <div class="flex flex-wrap gap-2">
          <button type="submit" class="btn-primary btn-sm" :disabled="sending">{{ sending ? 'Invio…' : 'Invia la richiesta' }}</button>
          <button v-if="info.has_email" type="button" class="btn-ghost btn-sm" @click="manual = false; error = ''">Torna all'invio del link</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { KeyRound } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

const props = defineProps({
  producerId: { type: String, required: true },
  slug: { type: String, required: true }
})

const { fetchWithAuth } = useApi()
const route = useRoute()

const info = ref(null)
const open = ref(false)
const manual = ref(false)
const sending = ref(false)
const sent = ref('')
const claimSent = ref('')
const error = ref('')
const form = reactive({ name: '', role: '', email: '', phone: '', message: '', privacy_accepted: false, website: '' })

onMounted(async () => {
  try {
    info.value = await fetchWithAuth(`/producers/${props.slug}/claim`)
    // dal link "rivendicala" della registrazione: pannello gia' aperto
    if (info.value?.claimable && route.query.rivendica) {
      open.value = true
      if (!info.value.has_email) manual.value = true
      await nextTick()
      document.getElementById('rivendica')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
    if (info.value && !info.value.has_email) manual.value = true
  } catch {
    info.value = null
  }
})

const sendLink = async () => {
  error.value = ''
  sending.value = true
  try {
    const res = await fetchWithAuth(`/producers/${props.slug}/claim/email`, { method: 'POST' })
    sent.value = res.message
  } catch (err) {
    error.value = apiErrorMessage(err, 'Invio non riuscito: riprova o usa il modulo qui sotto.')
  } finally {
    sending.value = false
  }
}

const sendClaim = async () => {
  error.value = ''
  const missing = []
  if (!form.name.trim()) missing.push('il nome')
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) missing.push('un\'email valida')
  if (form.phone.trim().length < 5) missing.push('il telefono')
  if (missing.length) { error.value = `Manca ${missing.join(', ').replace(/, ([^,]*)$/, ' e $1')}.`; return }
  if (!form.privacy_accepted) { error.value = 'Per inviare la richiesta devi accettare l\'informativa sulla privacy.'; return }
  sending.value = true
  try {
    const res = await fetchWithAuth('/contact/claim', { method: 'POST', body: { ...form, producer_id: props.producerId } })
    claimSent.value = res.message
  } catch (err) {
    error.value = apiErrorMessage(err, 'Invio non riuscito: riprova o scrivici a info@enotecamolise.it.')
  } finally {
    sending.value = false
  }
}
</script>
