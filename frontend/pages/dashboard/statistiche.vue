<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[720px] flex flex-col gap-6">
    <div class="flex flex-col gap-1.5">
      <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Statistiche e Google</h1>
      <p class="text-sm text-ink-soft m-0">Google Analytics per contare le visite e la sitemap per Google Search Console.</p>
    </div>

    <!-- Google Analytics -->
    <form class="card p-6 sm:p-7 flex flex-col gap-[18px]" @submit.prevent="save">
      <div class="flex items-start justify-between gap-3">
        <div class="flex flex-col gap-1">
          <h2 class="text-lg font-bold m-0">Google Analytics</h2>
          <p class="text-[13px] text-ink-soft m-0">Incolla l'ID di misurazione (inizia con <strong>G-</strong>) oppure l'intero codice che ti dà Google: l'ID viene estratto da solo.</p>
        </div>
        <span
          :class="['shrink-0 text-[12px] font-bold px-2.5 py-1 rounded-full', savedId ? 'bg-bio-50 text-bio-900 border border-bio/30' : 'bg-sand-100 text-ink-mute']"
        >{{ savedId ? 'Attivo' : 'Spento' }}</span>
      </div>

      <div class="field-label">
        <label for="ga-id">ID di misurazione o codice di tracciamento</label>
        <textarea
          id="ga-id"
          v-model="input"
          rows="3"
          class="input h-auto py-3 font-mono text-[13px]"
          placeholder="G-AB12CD34EF"
          spellcheck="false"
          autocomplete="off"
        ></textarea>
        <span v-if="detected && detected !== savedId" class="text-[13px] font-normal text-ink-mute">ID trovato: <strong class="text-ink">{{ detected }}</strong></span>
        <span v-else-if="input.trim() && !detected" class="text-[13px] font-normal text-wine-800">Non trovo un ID che inizia con G-: controlla di aver copiato il codice di Google Analytics 4.</span>
      </div>

      <div class="flex flex-wrap gap-2">
        <button type="submit" class="btn-primary" :disabled="saving || (!!input.trim() && !detected)">
          {{ saving ? 'Salvataggio…' : 'Salva' }}
        </button>
        <button v-if="savedId" type="button" class="btn-ghost" :disabled="saving" @click="disable">Disattiva Google Analytics</button>
      </div>

      <ul class="m-0 pl-5 text-[13px] text-ink-soft leading-relaxed flex flex-col gap-1">
        <li>Google Analytics parte <strong>solo per chi accetta</strong> i cookie di statistica nel banner. Chi rifiuta non viene contato e i cookie <code>_ga</code> vengono cancellati.</li>
        <li>Le tue visite mentre sei collegato all'area riservata non vengono contate (vale anche per le cantine).</li>
        <li>Sono disattivati Google Signals e gli annunci personalizzati; i cookie durano al massimo 13 mesi.</li>
        <li>Dove trovare l'ID: Google Analytics → Amministrazione → Stream di dati → il tuo sito → "ID misurazione".</li>
      </ul>
    </form>

    <!-- Sitemap -->
    <section class="card p-6 sm:p-7 flex flex-col gap-[18px]" aria-labelledby="sez-sitemap">
      <div class="flex flex-col gap-1">
        <h2 id="sez-sitemap" class="text-lg font-bold m-0">Sitemap per Google Search Console</h2>
        <p class="text-[13px] text-ink-soft m-0">Elenco delle pagine da far trovare a Google: vini pubblicati, cantine, eventi in programma e pagine principali. Si aggiorna da sola.</p>
      </div>
      <div class="flex flex-col sm:flex-row gap-2">
        <input :value="sitemapUrl" readonly class="input font-mono text-[13px] flex-1" aria-label="Indirizzo della sitemap" @focus="$event.target.select()" />
        <button type="button" class="btn-outline shrink-0" @click="copy">{{ copied ? 'Copiato' : 'Copia' }}</button>
        <a :href="sitemapUrl" target="_blank" rel="noopener" class="btn-ghost shrink-0">Apri</a>
      </div>
      <p v-if="sitemapCount !== null" class="text-[13px] text-ink-mute m-0">Pagine nella sitemap in questo momento: <strong class="text-ink">{{ sitemapCount }}</strong></p>
      <ol class="m-0 pl-5 text-[13px] text-ink-soft leading-relaxed flex flex-col gap-1">
        <li>Su Google Search Console aggiungi la proprietà di tipo <strong>Dominio</strong> con <code>enotecamolise.it</code> e verificala con il record TXT su Aruba (DNS).</li>
        <li>Poi apri <strong>Sitemap</strong>, incolla <code>sitemap.xml</code> nel campo e premi Invia.</li>
        <li>Privacy, cookie policy, chi siamo e area riservata non sono nella sitemap e restano fuori dai risultati di ricerca.</li>
      </ol>
    </section>
  </div>
</template>

<script setup>
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Statistiche e Google - EnotecaMolise', robots: 'noindex' })

const { fetchWithAuth } = useApi()
const config = useRuntimeConfig()
const toast = useToast()
const gaId = useAnalyticsId()

const input = ref('')
const savedId = ref('')
const saving = ref(false)
const copied = ref(false)
const sitemapCount = ref(null)

const siteUrl = String(config.public.siteUrl || 'https://www.enotecamolise.it').replace(/\/+$/, '')
// in sviluppo la sitemap e' servita dal sito locale
const sitemapUrl = computed(() => (import.meta.client && location.hostname === 'localhost' ? location.origin : siteUrl) + '/sitemap.xml')

const detected = computed(() => (input.value.toUpperCase().match(/\bG-[A-Z0-9]{4,20}\b/) || [])[0] || '')

const load = async () => {
  try {
    const res = await fetchWithAuth('/site/analytics/admin')
    savedId.value = res.ga_measurement_id || ''
    input.value = savedId.value
  } catch (err) {
    toast.error(apiErrorMessage(err))
  }
}

const store = async (value) => {
  saving.value = true
  try {
    const res = await fetchWithAuth('/site/analytics', { method: 'PUT', body: { ga_measurement_id: value } })
    savedId.value = res.ga_measurement_id || ''
    input.value = savedId.value
    gaId.value = savedId.value
    toast.success(savedId.value ? `Google Analytics attivo con ${savedId.value}.` : 'Google Analytics disattivato.')
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    saving.value = false
  }
}

const save = () => store(input.value.trim())
const disable = () => store('')

const copy = async () => {
  try {
    await navigator.clipboard.writeText(sitemapUrl.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    toast.error('Copia non riuscita: seleziona l\'indirizzo e copialo a mano.')
  }
}

const countSitemap = async () => {
  try {
    const xml = await $fetch('/sitemap.xml', { responseType: 'text' })
    sitemapCount.value = (String(xml).match(/<loc>/g) || []).length
  } catch {
    sitemapCount.value = null
  }
}

onMounted(() => { load(); countSitemap() })
</script>
