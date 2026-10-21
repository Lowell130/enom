<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[900px] flex flex-col gap-6">
    <div class="flex flex-col gap-1.5">
      <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Messaggi dal sito</h1>
      <p class="text-sm text-ink-soft m-0">
        Arrivano dalla pagina <NuxtLink to="/contatti" target="_blank" class="font-semibold text-wine-800 underline underline-offset-2">Contatti</NuxtLink>
        e anche per email: per rispondere usa "Rispondi" nella tua posta. Vengono cancellati da soli dopo 24 mesi.
      </p>
    </div>

    <div class="flex flex-wrap gap-2" role="tablist" aria-label="Filtra i messaggi">
      <button v-for="f in filters" :key="f.value" type="button" role="tab" :aria-selected="filter === f.value"
              :class="['pill', filter === f.value && 'pill-active']" @click="filter = f.value">
        {{ f.label }} <span class="ml-1 opacity-70">{{ f.count }}</span>
      </button>
    </div>

    <div v-if="pending" class="card p-10 text-center text-sm text-ink-mute">Caricamento…</div>
    <div v-else-if="!visible.length" class="card p-10 text-center text-sm text-ink-mute">
      {{ messages.length ? 'Nessun messaggio con questo filtro.' : 'Ancora nessun messaggio dal modulo Contatti.' }}
    </div>

    <ul v-else class="list-none m-0 p-0 flex flex-col gap-3">
      <li v-for="m in visible" :key="m.id" :class="['card p-5 flex flex-col gap-3', !m.is_read && 'border-wine-800/40']">
        <div class="flex flex-wrap items-start justify-between gap-2">
          <div class="flex flex-col gap-0.5 min-w-0">
            <span class="font-bold text-ink flex items-center gap-2">
              <span v-if="!m.is_read" class="w-2 h-2 rounded-full bg-wine-800 shrink-0" aria-label="Da leggere"></span>
              {{ m.name }}
            </span>
            <a :href="mailtoLink(m)" class="text-sm text-wine-800 font-semibold break-all">{{ m.email }}</a>
          </div>
          <div class="flex flex-col items-end gap-1 text-right">
            <span class="text-[12px] font-bold px-2.5 py-1 rounded-full bg-sand-100 text-ink-soft">{{ m.reason_label }}</span>
            <span class="text-[12px] text-ink-mute">{{ fmt(m.created_at) }}</span>
          </div>
        </div>
        <!-- richiesta di accesso a una cantina gia' presente -->
        <div v-if="m.reason === 'RIVENDICAZIONE'" class="p-3.5 rounded-xl bg-sand-100/70 border border-line flex flex-col gap-2 text-sm">
          <span>
            Chiede di gestire
            <NuxtLink v-if="m.producer_slug" :to="`/produttori/${m.producer_slug}`" target="_blank" class="font-bold text-wine-800">{{ m.producer_name }}</NuxtLink>
            <strong v-else>{{ m.producer_name }}</strong>
            <template v-if="m.role"> come <strong>{{ m.role }}</strong></template>.
          </span>
          <span v-if="m.phone">Telefono: <a :href="`tel:${m.phone}`" class="font-semibold text-wine-800">{{ m.phone }}</a></span>
          <span class="text-ink-soft">Prima di invitare verifica che sia davvero il titolare, per esempio chiamando il numero della cantina.</span>
          <span v-if="m.producer_account === 'active'" class="font-semibold text-bio-900">La cantina ha già un accesso attivo.</span>
          <button v-else-if="m.producer_id" type="button" class="btn-outline btn-sm self-start" :disabled="inviting === m.id" @click="invite(m)">
            {{ inviting === m.id ? 'Invio…' : `Verificato: invia l'invito a ${m.email}` }}
          </button>
        </div>
        <p v-if="m.message" class="m-0 text-sm text-ink whitespace-pre-line leading-relaxed">{{ m.message }}</p>
        <div class="flex flex-wrap gap-2 pt-1">
          <a :href="mailtoLink(m)" class="btn-primary btn-sm" @click="markRead(m, true)">
            <Reply class="w-4 h-4" aria-hidden="true" /> Rispondi
          </a>
          <button type="button" class="btn-ghost btn-sm" @click="markRead(m, !m.is_read)">
            {{ m.is_read ? 'Segna da leggere' : 'Segna come letto' }}
          </button>
          <button type="button" class="btn-ghost btn-sm text-wine-800 ml-auto" @click="remove(m)">
            <Trash2 class="w-4 h-4" aria-hidden="true" /> Elimina
          </button>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { Reply, Trash2 } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Messaggi dal sito - EnotecaMolise', robots: 'noindex' })

const { fetchWithAuth } = useApi()
const toast = useToast()

const messages = ref([])
const pending = ref(true)
const filter = ref('UNREAD')

const load = async () => {
  pending.value = true
  try {
    messages.value = (await fetchWithAuth('/contact')) || []
    if (!messages.value.some(m => !m.is_read)) filter.value = 'ALL'
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    pending.value = false
  }
}
onMounted(load)

const filters = computed(() => [
  { value: 'UNREAD', label: 'Da leggere', count: messages.value.filter(m => !m.is_read).length },
  { value: 'ALL', label: 'Tutti', count: messages.value.length }
])
const visible = computed(() => filter.value === 'UNREAD' ? messages.value.filter(m => !m.is_read) : messages.value)

const fmt = (v) => new Date(String(v).endsWith('Z') || String(v).includes('+') ? v : `${v}Z`)
  .toLocaleString('it-IT', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' })

const mailtoLink = (m) => {
  const subject = `Re: il tuo messaggio a EnotecaMolise (${m.reason_label})`
  const quoted = m.message.split('\n').map(l => `> ${l}`).join('\n')
  const body = `Ciao ${m.name},\n\n\n\n---\nIl ${fmt(m.created_at)} hai scritto:\n${quoted}`
  return `mailto:${m.email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`
}

const markRead = async (m, read) => {
  if (m.is_read === read) return
  try {
    await fetchWithAuth(`/contact/${m.id}/read?read=${read}`, { method: 'PUT' })
    m.is_read = read
  } catch (err) {
    toast.error(apiErrorMessage(err))
  }
}

const inviting = ref('')
const invite = async (m) => {
  if (!confirm(`Mandare il link di accesso a ${m.email}? Diventerà l'email di accesso di ${m.producer_name}.`)) return
  inviting.value = m.id
  try {
    const res = await fetchWithAuth(`/producers/${m.producer_id}/invite`, { method: 'POST', body: { email: m.email } })
    m.producer_account = 'invited'
    await markRead(m, true)
    toast.success(res?.message || 'Invito mandato.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    inviting.value = ''
  }
}

const remove = async (m) => {
  if (!confirm(`Eliminare il messaggio di ${m.name}? Non si può annullare.`)) return
  try {
    await fetchWithAuth(`/contact/${m.id}`, { method: 'DELETE' })
    messages.value = messages.value.filter(x => x.id !== m.id)
    toast.success('Messaggio eliminato.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  }
}
</script>
