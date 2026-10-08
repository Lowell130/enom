<template>
  <section class="page-container pt-12 md:pt-16 pb-20 flex justify-center">
    <div class="w-full max-w-[480px] flex flex-col gap-6">
      <div class="flex flex-col gap-2">
        <span class="eyebrow">Area produttori</span>
        <h1 class="font-serif text-[40px] font-semibold leading-[1.05]">Attiva il tuo accesso</h1>
        <p v-if="invite" class="text-[16px] text-ink-soft m-0">
          Benvenuti su EnotecaMolise! Scegliete la password per gestire la pagina di
          <strong class="text-ink">{{ invite.company_name }}</strong>: vini, eventi e richieste dei visitatori.
        </p>
      </div>

      <div v-if="checking" class="card p-6 text-sm text-ink-mute">Verifica dell'invito…</div>

      <div v-else-if="!invite" role="alert" class="card p-6 flex flex-col gap-3">
        <p class="font-semibold text-ink m-0">Invito non valido o scaduto</p>
        <p class="text-sm text-ink-soft m-0">
          Il link si usa una sola volta e vale {{ days }} giorni. Se l'avete già usato, accedete con la password scelta;
          altrimenti scriveteci e vi mandiamo un nuovo invito.
        </p>
        <div class="flex flex-wrap gap-2">
          <NuxtLink to="/login" class="btn-primary btn-sm">Vai all'accesso</NuxtLink>
          <NuxtLink to="/password-dimenticata" class="btn-ghost btn-sm">Password dimenticata?</NuxtLink>
        </div>
      </div>

      <form v-else class="flex flex-col gap-[18px]" @submit.prevent="submit">
        <div class="field-label">
          <span>Email di accesso</span>
          <input :value="invite.email" type="email" readonly class="input bg-sand-100 text-ink-soft" />
        </div>
        <div class="field-label">
          <label for="invite-password">Password</label>
          <PasswordInput id="invite-password" v-model="password" autocomplete="new-password" :minlength="8" />
          <span class="text-[13px] font-normal text-ink-mute">Almeno 8 caratteri.</span>
        </div>
        <div class="field-label">
          <label for="invite-password-2">Ripeti la password</label>
          <PasswordInput id="invite-password-2" v-model="confirm" autocomplete="new-password" :minlength="8" />
        </div>
        <label class="flex items-start gap-2.5 text-sm text-ink-soft cursor-pointer">
          <input v-model="consent" type="checkbox" class="mt-0.5 w-4 h-4 accent-wine-800 shrink-0" />
          <span>Autorizzo EnotecaMolise a pubblicare i testi, le foto e le schede dei vini di <strong class="text-ink">{{ invite.company_name }}</strong> già presenti sulla pagina. Potrò modificarli o toglierli in qualsiasi momento dall'area riservata.</span>
        </label>
        <label class="flex items-start gap-2.5 text-sm text-ink-soft cursor-pointer">
          <input v-model="privacy" type="checkbox" class="mt-0.5 w-4 h-4 accent-wine-800 shrink-0" />
          <span>Ho letto l'<NuxtLink to="/privacy" target="_blank" class="font-semibold text-wine-800 underline underline-offset-2">informativa sulla privacy</NuxtLink> e accetto il trattamento dei dati della cantina per l'uso del portale.</span>
        </label>
        <p v-if="error" role="alert" class="m-0 p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>
        <button type="submit" :disabled="loading" class="btn-primary h-[52px] text-base">
          {{ loading ? 'Attivazione…' : 'Attiva l\'accesso ed entra' }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup>
import PasswordInput from '~/components/PasswordInput.vue'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Attiva il tuo accesso - EnotecaMolise', robots: 'noindex' })

const route = useRoute()
const { fetchWithAuth } = useApi()
const { tokenCookie, fetchUser } = useAuth()
const token = String(route.query.token || '')
const days = 14

const checking = ref(true)
const invite = ref(null)
const password = ref('')
const confirm = ref('')
const privacy = ref(false)
const consent = ref(false)
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  if (token) {
    try { invite.value = await fetchWithAuth(`/auth/invite/${encodeURIComponent(token)}`) } catch (e) { invite.value = null }
  }
  checking.value = false
})

const submit = async () => {
  error.value = ''
  if (password.value.length < 8) { error.value = 'La password deve contenere almeno 8 caratteri.'; return }
  if (password.value !== confirm.value) { error.value = 'Le due password non coincidono.'; return }
  if (!consent.value) { error.value = 'Per attivare l\'accesso serve l\'autorizzazione a pubblicare testi e foto della cantina. Se preferite di no, scriveteci: toglieremo i vostri contenuti.'; return }
  if (!privacy.value) { error.value = 'Per attivare l\'accesso serve accettare l\'informativa sulla privacy.'; return }
  loading.value = true
  try {
    const res = await fetchWithAuth('/auth/invite/accept', {
      method: 'POST',
      body: { token, password: password.value, privacy_accepted: true, content_consent: true }
    })
    tokenCookie.value = res.access_token
    await fetchUser(res.access_token)
    await navigateTo('/dashboard')
  } catch (err) {
    error.value = apiErrorMessage(err, 'Attivazione non riuscita: riprova.')
  } finally {
    loading.value = false
  }
}
</script>
