<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 flex flex-col gap-6 max-w-[1240px]">
    <div class="flex flex-col gap-1">
      <h1 class="font-serif text-[40px] md:text-[44px] font-semibold leading-none">Email e testi</h1>
      <p class="text-sm text-ink-soft">I messaggi che il portale manda a cantine, clienti e amministratori, e i testi legali del sito.</p>
    </div>

    <!-- Come vengono gestite le email adesso -->
    <div v-if="status" :class="['p-4 rounded-xl border text-sm flex flex-col gap-1', status.mode === 'smtp' ? 'border-bio/30 bg-bio-50 text-bio-900' : 'border-[#E8D9B8] bg-[#FBF5E8] text-[#5A4524]']" role="status">
      <template v-if="status.mode === 'smtp'">
        <strong>Invio attivo</strong>
        <span>Le email partono davvero tramite {{ status.smtp_host }}. Restano comunque registrate nella Posta in uscita.</span>
      </template>
      <template v-else>
        <strong>Modalità sviluppo: le email non vengono spedite</strong>
        <span>
          Ogni email viene salvata nella <button type="button" class="underline font-semibold" @click="tab = 'outbox'">Posta in uscita</button>,
          dove puoi leggerla esattamente come la riceverebbe il destinatario. Quando avrai il dominio, basterà inserire i dati SMTP nel file
          <code class="font-mono text-[13px]">backend/.env</code> (EMAIL_MODE=smtp) e riavviare il backend.
          <span v-if="status.requested_mode === 'smtp' && !status.smtp_configured"> Attenzione: EMAIL_MODE è "smtp" ma manca SMTP_HOST.</span>
        </span>
        <span class="text-[13px]">I link nelle email puntano a <strong>{{ status.site_url }}</strong> (SITE_URL nel .env).</span>
      </template>
    </div>

    <div role="tablist" aria-label="Sezioni" class="segmented w-fit flex-wrap">
      <button v-for="t in tabs" :key="t.value" type="button" role="tab" :aria-selected="tab === t.value"
              :class="['segmented-item', tab === t.value && 'segmented-item-active']" @click="tab = t.value">
        {{ t.label }}<span v-if="t.value === 'outbox' && status?.outbox_count" class="ml-1.5 text-ink-mute font-semibold">{{ status.outbox_count }}</span>
      </button>
    </div>

    <!-- MODELLI -->
    <section v-if="tab === 'templates'" class="grid grid-cols-1 lg:grid-cols-[300px_1fr] gap-5 items-start">
      <ul class="m-0 p-0 list-none card overflow-hidden" aria-label="Modelli email">
        <li v-for="t in templates" :key="t.key" class="border-b border-line-soft last:border-b-0">
          <button type="button" :class="['w-full text-left px-4 py-3 flex flex-col gap-0.5 hover:bg-sand-100', selectedKey === t.key && 'bg-sand-100']"
                  :aria-current="selectedKey === t.key ? 'true' : undefined" @click="selectTemplate(t.key)">
            <span class="flex items-center gap-2 text-sm font-bold text-ink">
              {{ t.label }}
              <span v-if="!t.enabled" class="badge-soft">Disattivata</span>
              <span v-else-if="t.customized" class="badge-soft">Modificata</span>
            </span>
            <span class="text-[13px] text-ink-mute">{{ t.recipient }}</span>
          </button>
        </li>
      </ul>

      <div v-if="draft" class="card p-5 sm:p-6 flex flex-col gap-5">
        <div class="flex flex-wrap items-start justify-between gap-3">
          <div class="flex flex-col gap-1">
            <h2 class="font-serif text-2xl font-bold">{{ current.label }}</h2>
            <p class="text-sm text-ink-soft m-0">{{ current.description }} <span class="text-ink-mute">Destinatario: {{ current.recipient }}.</span></p>
          </div>
          <label class="flex items-center gap-2 text-sm font-semibold cursor-pointer">
            <input v-model="draft.enabled" type="checkbox" class="w-[18px] h-[18px] accent-wine-800" />
            Email attiva
          </label>
        </div>

        <label class="field-label">Oggetto
          <input ref="subjectEl" v-model="draft.subject" type="text" maxlength="300" class="input" @focus="lastField = 'subject'" />
        </label>
        <div class="field-label">
          <label for="tpl-body">Testo</label>
          <textarea id="tpl-body" ref="bodyEl" v-model="draft.body" rows="14" class="input h-auto py-3 font-mono text-[13px] leading-relaxed" @focus="lastField = 'body'"></textarea>
          <span class="text-[13px] font-normal text-ink-mute">
            Riga vuota = nuovo paragrafo. Pulsante: <code class="font-mono" v-text="buttonExample"></code> su una riga a sé.
          </span>
        </div>
        <div class="flex flex-col gap-2">
          <span class="text-[13px] font-semibold text-ink-soft">Inserisci un dato (clic per aggiungerlo dove si trova il cursore)</span>
          <div class="flex flex-wrap gap-1.5">
            <button v-for="v in current.variables" :key="v" type="button" class="chip font-mono text-[12px]" @click="insertVariable(v)" v-text="varToken(v)"></button>
          </div>
        </div>

        <div class="flex flex-wrap gap-2.5">
          <button type="button" class="btn-primary btn-sm" :disabled="saving" @click="saveTemplate">{{ saving ? 'Salvataggio…' : 'Salva' }}</button>
          <button type="button" class="btn-ghost btn-sm" :disabled="saving" @click="sendTest">Invia una prova a me</button>
          <button v-if="current.customized" type="button" class="btn-ghost btn-sm" :disabled="saving" @click="resetTemplate">Ripristina il testo originale</button>
          <span v-if="dirty" class="self-center text-[13px] text-wine-800 font-semibold">Modifiche non salvate</span>
        </div>

        <div class="flex flex-col gap-2">
          <span class="text-sm font-semibold">Anteprima con dati di esempio</span>
          <p class="text-sm m-0"><span class="text-ink-mute">Oggetto:</span> <strong>{{ preview.subject }}</strong></p>
          <iframe :srcdoc="preview.html" title="Anteprima dell'email" sandbox="" class="w-full h-[560px] rounded-xl border border-line bg-[#F6F1EA]" />
        </div>
      </div>
    </section>

    <!-- POSTA IN USCITA -->
    <section v-else-if="tab === 'outbox'" class="flex flex-col gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <select v-model="outboxFilter" class="select h-10 w-auto text-sm" aria-label="Filtra per stato">
          <option value="">Tutte</option>
          <option value="outbox">Non spedite (sviluppo)</option>
          <option value="sent">Spedite</option>
          <option value="error">Con errore</option>
        </select>
        <button type="button" class="btn-ghost btn-sm h-10" @click="loadOutbox"><RefreshCw class="w-4 h-4" aria-hidden="true" /> Aggiorna</button>
        <button v-if="outbox.length" type="button" class="btn-ghost btn-sm h-10 text-wine-800 ml-auto" @click="clearOutbox">Svuota la posta in uscita</button>
      </div>
      <div class="card overflow-x-auto">
        <table v-if="outbox.length" class="w-full text-left text-sm">
          <thead class="text-xs uppercase tracking-[0.08em] font-bold text-ink-mute border-b border-line">
            <tr><th class="py-3 px-4">Data</th><th class="py-3 px-4">Email</th><th class="py-3 px-4">Destinatari</th><th class="py-3 px-4">Oggetto</th><th class="py-3 px-4">Stato</th></tr>
          </thead>
          <tbody class="divide-y divide-line-soft">
            <tr v-for="m in outbox" :key="m.id" class="hover:bg-sand-100 cursor-pointer" tabindex="0" @click="openEmail(m.id)" @keydown.enter="openEmail(m.id)">
              <td class="py-3 px-4 whitespace-nowrap text-ink-soft">{{ formatDateTime(m.created_at) }}</td>
              <td class="py-3 px-4 whitespace-nowrap">{{ templateLabel(m.template) }}<span v-if="m.related?.test" class="badge-soft ml-1.5">Prova</span></td>
              <td class="py-3 px-4 text-ink-soft">{{ (m.to || []).join(', ') || '—' }}</td>
              <td class="py-3 px-4 font-semibold text-ink">{{ m.subject }}</td>
              <td class="py-3 px-4 whitespace-nowrap">
                <span :class="statusClass(m.status)">{{ statusLabel(m.status) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-else class="p-10 text-center text-ink-mute m-0">Nessuna email. Registrando una cantina, approvandola o inviando una richiesta le email compariranno qui.</p>
      </div>
    </section>

    <!-- IMPOSTAZIONI -->
    <section v-else-if="tab === 'settings'" class="card p-5 sm:p-6 flex flex-col gap-4 max-w-[760px]">
      <h2 class="font-serif text-2xl font-bold">Mittente e notifiche</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label class="field-label">Nome del mittente
          <input v-model="settingsForm.sender_name" type="text" maxlength="120" class="input" />
        </label>
        <label class="field-label">Email del mittente
          <input v-model="settingsForm.sender_email" type="email" placeholder="es. noreply@enotecamolise.it" class="input" />
          <span class="text-[13px] font-normal text-ink-mute">Deve appartenere al dominio del server SMTP. Vuoto = utente SMTP.</span>
        </label>
        <label class="field-label">Rispondi a
          <input v-model="settingsForm.reply_to" type="email" placeholder="es. info@enotecamolise.it" class="input" />
        </label>
        <label class="field-label">Email che ricevono le notifiche admin
          <input v-model="recipientsText" type="text" placeholder="una o più, separate da virgola" class="input" />
          <span class="text-[13px] font-normal text-ink-mute">Ora: {{ (settingsForm.effective_admin_recipients || []).join(', ') || '—' }}</span>
        </label>
        <label class="field-label sm:col-span-2">Testo a piè di pagina
          <textarea v-model="settingsForm.footer_text" rows="2" class="input h-auto py-3"></textarea>
        </label>
      </div>
      <div><button type="button" class="btn-primary btn-sm" :disabled="saving" @click="saveSettings">Salva</button></div>

      <details class="mt-2 text-sm text-ink-soft">
        <summary class="cursor-pointer font-semibold text-ink">Come attivare l'invio reale quando avrai il dominio</summary>
        <ol class="mt-3 pl-5 flex flex-col gap-1.5">
          <li>Scegli un servizio di invio (quello del tuo hosting, oppure Brevo, Mailgun, Amazon SES…) e verifica il dominio (record SPF e DKIM).</li>
          <li>Nel file <code class="font-mono">backend/.env</code> imposta <code class="font-mono">EMAIL_MODE=smtp</code>, <code class="font-mono">SMTP_HOST</code>, <code class="font-mono">SMTP_PORT</code>, <code class="font-mono">SMTP_USER</code>, <code class="font-mono">SMTP_PASSWORD</code> e <code class="font-mono">SITE_URL</code> con l'indirizzo del sito.</li>
          <li>Riavvia il backend e usa "Invia una prova a me" da un modello.</li>
        </ol>
      </details>
    </section>

    <!-- PRIVACY -->
    <section v-else-if="tab === 'privacy' && privacy" class="grid grid-cols-1 xl:grid-cols-2 gap-5 items-start">
      <div class="card p-5 sm:p-6 flex flex-col gap-4">
        <div class="flex flex-col gap-1">
          <h2 class="font-serif text-2xl font-bold">Informativa sulla privacy</h2>
          <p class="text-sm text-ink-soft m-0">
            È la pagina collegata ai consensi di registrazione e contatto. Completa i dati tra [parentesi quadre]
            e falla verificare da un consulente prima della messa online.
          </p>
        </div>
        <label class="field-label">Titolo
          <input v-model="privacy.title" type="text" class="input" />
        </label>
        <label class="field-label">Testo
          <textarea v-model="privacy.body" rows="22" class="input h-auto py-3 text-[14px] leading-relaxed"></textarea>
          <span class="text-[13px] font-normal text-ink-mute">"## " a inizio riga = titolo; "- " = elenco; riga vuota = nuovo paragrafo.</span>
        </label>
        <div class="flex flex-wrap gap-2.5">
          <button type="button" class="btn-primary btn-sm" :disabled="saving" @click="savePrivacy">Salva</button>
          <NuxtLink to="/privacy" target="_blank" class="btn-ghost btn-sm">Apri la pagina</NuxtLink>
          <button v-if="privacy.customized" type="button" class="btn-ghost btn-sm" @click="resetPrivacy">Ripristina la bozza iniziale</button>
        </div>
      </div>
      <div class="card p-5 sm:p-6 flex flex-col gap-3">
        <span class="eyebrow-sm">Anteprima</span>
        <h3 class="font-serif text-3xl font-semibold m-0">{{ privacy.title }}</h3>
        <RichText :text="privacy.body" />
      </div>
    </section>

    <!-- Email aperta -->
    <div v-if="openedEmail" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" @click.self="openedEmail = null">
      <div role="dialog" aria-modal="true" aria-labelledby="email-title" class="bg-white rounded-2xl w-full max-w-[760px] max-h-[92vh] flex flex-col overflow-hidden">
        <div class="p-5 border-b border-line flex items-start justify-between gap-4">
          <div class="flex flex-col gap-1 min-w-0">
            <h2 id="email-title" class="font-bold text-lg m-0 break-words">{{ openedEmail.subject }}</h2>
            <p class="text-[13px] text-ink-soft m-0">A: {{ (openedEmail.to || []).join(', ') }} · {{ formatDateTime(openedEmail.created_at) }} ·
              <span :class="statusClass(openedEmail.status)">{{ statusLabel(openedEmail.status) }}</span></p>
            <p v-if="openedEmail.error" class="text-[13px] text-wine-800 m-0">{{ openedEmail.error }}</p>
          </div>
          <button type="button" class="p-2 rounded-lg hover:bg-sand-100" aria-label="Chiudi" @click="openedEmail = null"><X class="w-5 h-5" aria-hidden="true" /></button>
        </div>
        <iframe :srcdoc="openedEmail.html" title="Contenuto dell'email" sandbox="allow-popups allow-popups-to-escape-sandbox" class="flex-1 min-h-[520px] w-full bg-[#F6F1EA]" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { RefreshCw, X } from 'lucide-vue-next'
import RichText from '~/components/RichText.vue'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Email e testi - EnotecaMolise' })

const { fetchWithAuth } = useApi()
const toast = useToast()
const route = useRoute()

const tabs = [
  { value: 'templates', label: 'Modelli' },
  { value: 'outbox', label: 'Posta in uscita' },
  { value: 'settings', label: 'Impostazioni' },
  { value: 'privacy', label: 'Privacy' }
]
const tab = ref(tabs.some(t => t.value === route.query.tab) ? route.query.tab : 'templates')

const status = ref(null)
const templates = ref([])
const selectedKey = ref('')
const draft = ref(null)
const preview = ref({ subject: '', html: '' })
const saving = ref(false)
const lastField = ref('body')
const subjectEl = ref(null)
const bodyEl = ref(null)
const outbox = ref([])
const outboxFilter = ref('')
const openedEmail = ref(null)
const settingsForm = ref({})
const recipientsText = ref('')
const privacy = ref(null)

const current = computed(() => templates.value.find(t => t.key === selectedKey.value) || {})
const dirty = computed(() => draft.value && current.value.key && (
  draft.value.subject !== current.value.subject || draft.value.body !== current.value.body || draft.value.enabled !== current.value.enabled))

const loadStatus = async () => { status.value = await fetchWithAuth('/emails/status').catch(() => null) }

const loadTemplates = async () => {
  templates.value = (await fetchWithAuth('/emails/templates').catch(() => [])) || []
  if (!selectedKey.value && templates.value.length) selectTemplate(templates.value[0].key)
}

const selectTemplate = (key) => {
  if (dirty.value && !confirm('Ci sono modifiche non salvate a questo modello. Vuoi lasciarle?')) return
  selectedKey.value = key
  const t = templates.value.find(x => x.key === key)
  draft.value = t ? { subject: t.subject, body: t.body, enabled: t.enabled } : null
}

// anteprima aggiornata mentre si scrive
let previewTimer = null
watch(() => draft.value && [selectedKey.value, draft.value.subject, draft.value.body], () => {
  clearTimeout(previewTimer)
  previewTimer = setTimeout(async () => {
    if (!draft.value || !selectedKey.value) return
    try {
      preview.value = await fetchWithAuth(`/emails/templates/${selectedKey.value}/preview`, {
        method: 'POST', body: { subject: draft.value.subject || ' ', body: draft.value.body || ' ' }
      })
    } catch (e) { /* l'anteprima non e' essenziale */ }
  }, 350)
}, { immediate: true })

const insertVariable = (name) => {
  const token = varToken(name)
  const field = lastField.value === 'subject' ? 'subject' : 'body'
  const el = field === 'subject' ? subjectEl.value : bodyEl.value
  const text = draft.value[field] || ''
  const start = el?.selectionStart ?? text.length
  const end = el?.selectionEnd ?? text.length
  draft.value[field] = text.slice(0, start) + token + text.slice(end)
  nextTick(() => {
    el?.focus()
    el?.setSelectionRange(start + token.length, start + token.length)
  })
}

const replaceTemplate = (updated) => {
  templates.value = templates.value.map(t => (t.key === updated.key ? updated : t))
  draft.value = { subject: updated.subject, body: updated.body, enabled: updated.enabled }
}

const saveTemplate = async () => {
  saving.value = true
  try {
    replaceTemplate(await fetchWithAuth(`/emails/templates/${selectedKey.value}`, { method: 'PUT', body: draft.value }))
    toast.success('Modello salvato.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

const resetTemplate = async () => {
  if (!confirm('Tornare al testo originale di questo modello? Le modifiche andranno perse.')) return
  saving.value = true
  try {
    replaceTemplate(await fetchWithAuth(`/emails/templates/${selectedKey.value}/reset`, { method: 'POST' }))
    toast.success('Testo originale ripristinato.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

const sendTest = async () => {
  if (dirty.value) await saveTemplate()
  saving.value = true
  try {
    const res = await fetchWithAuth(`/emails/templates/${selectedKey.value}/test`, { method: 'POST', body: {} })
    if (res.status === 'error') toast.error(`Invio non riuscito: ${res.error}`)
    else if (res.mode === 'outbox') toast.success(`Prova salvata nella Posta in uscita (destinatario: ${res.to.join(', ')}).`)
    else toast.success(`Email di prova inviata a ${res.to.join(', ')}.`)
    loadStatus()
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

const loadOutbox = async () => {
  const q = outboxFilter.value ? `?status=${outboxFilter.value}` : ''
  outbox.value = (await fetchWithAuth(`/emails/outbox${q}`).catch(() => [])) || []
}
watch(outboxFilter, loadOutbox)

const openEmail = async (id) => {
  try { openedEmail.value = await fetchWithAuth(`/emails/outbox/${id}`) } catch (err) { toast.error(apiErrorMessage(err)) }
}

const clearOutbox = async () => {
  if (!confirm('Eliminare tutte le email della posta in uscita?')) return
  await fetchWithAuth('/emails/outbox', { method: 'DELETE' })
  await Promise.all([loadOutbox(), loadStatus()])
  toast.success('Posta in uscita svuotata.')
}

const loadSettings = async () => {
  settingsForm.value = (await fetchWithAuth('/emails/settings').catch(() => ({}))) || {}
  recipientsText.value = (settingsForm.value.admin_recipients || []).join(', ')
}

const saveSettings = async () => {
  saving.value = true
  try {
    const recipients = recipientsText.value.split(/[,;\s]+/).map(s => s.trim()).filter(Boolean)
    settingsForm.value = await fetchWithAuth('/emails/settings', { method: 'PUT', body: {
      sender_name: settingsForm.value.sender_name || '',
      sender_email: settingsForm.value.sender_email || '',
      reply_to: settingsForm.value.reply_to || '',
      footer_text: settingsForm.value.footer_text || '',
      admin_recipients: recipients
    } })
    recipientsText.value = (settingsForm.value.admin_recipients || []).join(', ')
    toast.success('Impostazioni salvate.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

const loadPrivacy = async () => { privacy.value = await fetchWithAuth('/site/pages/privacy').catch(() => null) }

const savePrivacy = async () => {
  saving.value = true
  try {
    privacy.value = await fetchWithAuth('/site/pages/privacy', { method: 'PUT', body: { title: privacy.value.title, body: privacy.value.body } })
    toast.success('Informativa salvata.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

const resetPrivacy = async () => {
  if (!confirm('Tornare alla bozza iniziale dell\'informativa? Il testo attuale andrà perso.')) return
  privacy.value = await fetchWithAuth('/site/pages/privacy/reset', { method: 'POST' })
}

const OPEN = '{' + '{'
const CLOSE = '}' + '}'
const varToken = (name) => `${OPEN}${name}${CLOSE}`
const buttonExample = `[[Testo del pulsante|${OPEN}link_area_riservata${CLOSE}]]`

const templateLabel = (key) => templates.value.find(t => t.key === key)?.label || key
const statusLabel = (s) => ({ outbox: 'Non spedita', sent: 'Spedita', error: 'Errore' }[s] || s)
const statusClass = (s) => ({ outbox: 'badge-soft', sent: 'badge-bio', error: 'badge-denom' }[s] || 'badge-soft')
const formatDateTime = (d) => d ? new Date(d.endsWith?.('Z') ? d : `${d}Z`).toLocaleString('it-IT', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : ''

watch(tab, (t) => {
  if (t === 'outbox') loadOutbox()
  if (t === 'settings') loadSettings()
  if (t === 'privacy' && !privacy.value) loadPrivacy()
}, { immediate: true })

onMounted(() => {
  loadStatus()
  loadTemplates()
})
</script>
