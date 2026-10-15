<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[640px] flex flex-col gap-6">
    <div class="flex flex-col gap-1.5">
      <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Account e password</h1>
      <p class="text-sm text-ink-soft m-0">
        Accedi con <strong class="text-ink">{{ user?.email }}</strong>.
      </p>
    </div>

    <form class="card p-6 sm:p-7 flex flex-col gap-[18px]" @submit.prevent="submit">
      <h2 class="text-lg font-bold m-0">Cambia password</h2>
      <div class="field-label">
        <label for="pw-current">Password attuale</label>
        <PasswordInput id="pw-current" v-model="current" autocomplete="current-password" />
      </div>
      <div class="field-label">
        <label for="pw-new">Nuova password</label>
        <PasswordInput id="pw-new" v-model="next" autocomplete="new-password" :minlength="8" />
        <span class="text-[13px] font-normal text-ink-mute">Almeno 8 caratteri; meglio una frase lunga che non usi altrove.</span>
      </div>
      <div class="field-label">
        <label for="pw-confirm">Ripeti la nuova password</label>
        <PasswordInput id="pw-confirm" v-model="confirm" autocomplete="new-password" :minlength="8" />
      </div>
      <p v-if="error" role="alert" class="m-0 p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>
      <p v-if="done" role="status" class="m-0 p-3 rounded-[10px] bg-bio-50 border border-bio/30 text-bio-900 text-sm font-semibold">{{ done }}</p>
      <button type="submit" class="btn-primary self-start" :disabled="loading">
        {{ loading ? 'Salvataggio…' : 'Cambia password' }}
      </button>
    </form>

    <p class="text-[13px] text-ink-mute m-0">
      Non ricordi la password attuale? Esci e usa
      <NuxtLink to="/password-dimenticata" class="font-semibold text-wine-800 underline underline-offset-2">Password dimenticata</NuxtLink>.
    </p>
  </div>
</template>

<script setup>
import PasswordInput from '~/components/PasswordInput.vue'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Account e password - EnotecaMolise', robots: 'noindex' })

const { fetchWithAuth } = useApi()
const { user, tokenCookie } = useAuth()

const current = ref('')
const next = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')
const done = ref('')

const submit = async () => {
  error.value = ''
  done.value = ''
  if (next.value.length < 8) { error.value = 'La nuova password deve avere almeno 8 caratteri.'; return }
  if (next.value !== confirm.value) { error.value = 'Le due nuove password non coincidono.'; return }
  loading.value = true
  try {
    const res = await fetchWithAuth('/auth/password/change', {
      method: 'POST',
      body: { current_password: current.value, new_password: next.value }
    })
    // la vecchia sessione non vale piu': si passa subito al nuovo accesso
    tokenCookie.value = res.access_token
    refreshCookie('auth_token')
    current.value = ''; next.value = ''; confirm.value = ''
    done.value = res.message || 'Password cambiata.'
  } catch (err) {
    error.value = apiErrorMessage(err, 'Non è stato possibile cambiare la password.')
  } finally {
    loading.value = false
  }
}
</script>
