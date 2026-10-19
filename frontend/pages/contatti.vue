<template>
  <section class="page-container pt-10 md:pt-14 pb-20">
    <div class="max-w-[760px] flex flex-col gap-6">
      <nav aria-label="Percorso" class="text-[13px] text-ink-mute">
        <NuxtLink to="/" class="hover:text-wine-800">Home</NuxtLink> / <span class="text-ink font-semibold">Contatti</span>
      </nav>
      <div class="flex flex-col gap-2">
        <h1 class="title-display">Contatti</h1>
        <p class="text-ink-soft m-0 max-w-[620px]">
          Scrivi a EnotecaMolise per segnalare un errore, chiedere la rimozione di un contenuto o far conoscere la tua cantina.
          Per prezzi, ordini e visite scrivi invece direttamente alla cantina, dal pulsante "Scrivi alla cantina" nella sua pagina.
        </p>
      </div>

      <div v-if="sent" role="status" class="card p-6 sm:p-8 flex flex-col items-start gap-3">
        <span class="w-11 h-11 rounded-full bg-bio-50 text-bio-900 flex items-center justify-center"><CheckCircle class="w-6 h-6" aria-hidden="true" /></span>
        <h2 class="font-serif text-2xl font-bold text-ink m-0">Messaggio inviato</h2>
        <p class="text-ink-soft m-0">{{ sent }} Ti abbiamo mandato una ricevuta a <strong class="text-ink">{{ sentTo }}</strong>: se non la vedi, controlla nello spam.</p>
        <div class="flex flex-wrap gap-2 pt-1">
          <NuxtLink to="/vini" class="btn-primary">Torna ai vini</NuxtLink>
          <button type="button" class="btn-ghost" @click="reset">Scrivi un altro messaggio</button>
        </div>
      </div>

      <form v-else class="card p-6 sm:p-8 flex flex-col gap-[18px] relative" novalidate @submit.prevent="submit">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label class="field-label">Nome e cognome *
            <input v-model="form.name" type="text" required maxlength="120" autocomplete="name" class="input" />
          </label>
          <label class="field-label">Email *
            <input v-model="form.email" type="email" required autocomplete="email" class="input" />
            <span class="text-[13px] font-normal text-ink-mute">Ti rispondiamo qui.</span>
          </label>
        </div>
        <label class="field-label">Motivo
          <select v-model="form.reason" class="select">
            <option v-for="r in reasons" :key="r.value" :value="r.value">{{ r.label }}</option>
          </select>
        </label>
        <p v-if="form.reason === 'CANTINA'" class="m-0 -mt-2 text-[13px] text-ink-soft">
          Puoi anche <NuxtLink to="/login?mode=register" class="font-semibold text-wine-800 underline underline-offset-2">registrare subito la tua cantina</NuxtLink>: la pagina è gratuita e la gestisci tu.
        </p>
        <label class="field-label">Messaggio *
          <textarea v-model="form.message" rows="6" required maxlength="5000" class="input h-auto py-3 leading-relaxed"
                    :placeholder="placeholder"></textarea>
        </label>

        <!-- campo trappola per i programmi di spam: nascosto alle persone e ai lettori di schermo -->
        <div class="absolute -left-[9999px] w-px h-px overflow-hidden" aria-hidden="true">
          <label>Sito web <input v-model="form.website" type="text" tabindex="-1" autocomplete="off" /></label>
        </div>

        <label class="flex items-start gap-2.5 text-[13px] text-ink-soft cursor-pointer">
          <input v-model="form.privacy_accepted" type="checkbox" required class="mt-0.5 w-4 h-4 accent-wine-800 shrink-0" />
          <span>
            Ho letto l'<NuxtLink to="/privacy" target="_blank" class="font-semibold text-wine-800 underline underline-offset-2">informativa sulla privacy</NuxtLink>
            e acconsento all'uso dei miei dati per ricevere una risposta.
          </span>
        </label>

        <p v-if="error" role="alert" class="m-0 p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>

        <button type="submit" class="btn-primary self-start" :disabled="sending">
          <Send class="w-4 h-4" aria-hidden="true" /> {{ sending ? 'Invio in corso…' : 'Invia il messaggio' }}
        </button>
      </form>

      <p class="text-[13px] text-ink-mute m-0">Puoi anche scriverci direttamente a <a href="mailto:info@enotecamolise.it" class="font-semibold text-wine-800">info@enotecamolise.it</a>.</p>
    </div>
  </section>
</template>

<script setup>
import { CheckCircle, Send } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({
  title: 'Contatti - EnotecaMolise',
  description: 'Scrivi a EnotecaMolise: segnalazioni, richieste di rimozione e cantine che vogliono comparire sul portale dei vini del Molise.'
})

const { fetchWithAuth } = useApi()
const route = useRoute()

const reasons = [
  { value: 'CANTINA', label: 'Sono una cantina e voglio essere sul sito' },
  { value: 'SEGNALAZIONE', label: 'Segnalare un errore o un contenuto' },
  { value: 'RIMOZIONE', label: 'Richiesta di rimozione' },
  { value: 'ALTRO', label: 'Altro' }
]

const blank = () => ({ name: '', email: '', reason: 'ALTRO', message: '', privacy_accepted: false, website: '' })
const form = reactive(blank())
// /contatti?motivo=RIMOZIONE preseleziona il motivo (es. dal link della pagina Chi siamo)
const preset = String(route.query.motivo || '').toUpperCase()
if (reasons.some(r => r.value === preset)) form.reason = preset

const placeholder = computed(() => ({
  CANTINA: 'Nome della cantina, comune e come possiamo contattarvi…',
  SEGNALAZIONE: 'Quale pagina o vino, e cosa c\'è da correggere…',
  RIMOZIONE: 'Quale contenuto (link alla pagina) e perché va rimosso…',
  ALTRO: 'Scrivi qui il tuo messaggio…'
}[form.reason]))

const sending = ref(false)
const error = ref('')
const sent = ref('')
const sentTo = ref('')

const submit = async () => {
  error.value = ''
  if (!form.name.trim() || !form.email.trim() || form.message.trim().length < 5) {
    error.value = 'Compila nome, email e messaggio.'
    return
  }
  if (!form.privacy_accepted) {
    error.value = 'Per inviare il messaggio devi accettare l\'informativa sulla privacy.'
    return
  }
  sending.value = true
  try {
    const res = await fetchWithAuth('/contact', { method: 'POST', body: { ...form } })
    sentTo.value = form.email.trim()
    sent.value = res?.message || 'Messaggio inviato.'
  } catch (err) {
    error.value = apiErrorMessage(err, 'Non è stato possibile inviare il messaggio. Riprova o scrivici a info@enotecamolise.it.')
  } finally {
    sending.value = false
  }
}

const reset = () => {
  Object.assign(form, blank())
  sent.value = ''
}
</script>
