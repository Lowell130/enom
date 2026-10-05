<template>
  <section class="page-container pt-12 md:pt-16 pb-20 flex justify-center">
    <div class="w-full max-w-[460px] flex flex-col gap-6">
      <div class="flex flex-col gap-2">
        <span class="eyebrow">Area produttori</span>
        <h1 class="font-serif text-[40px] font-semibold leading-[1.05]">Scegli una nuova password</h1>
      </div>

      <div v-if="!token" role="alert" class="card p-6 flex flex-col gap-3">
        <p class="font-semibold text-ink">Link incompleto</p>
        <p class="text-sm text-ink-soft">Apri il link esattamente come arriva nell'email, oppure richiedine uno nuovo.</p>
        <NuxtLink to="/password-dimenticata" class="btn-outline btn-sm w-fit">Richiedi un nuovo link</NuxtLink>
      </div>

      <div v-else-if="done" role="status" class="card p-6 flex flex-col gap-3">
        <span class="w-11 h-11 rounded-xl bg-bio-50 text-bio flex items-center justify-center"><Check class="w-5 h-5" aria-hidden="true" /></span>
        <p class="font-semibold text-ink">Password aggiornata</p>
        <p class="text-sm text-ink-soft">Ora puoi accedere con la nuova password. Per sicurezza le sessioni aperte su altri dispositivi sono state chiuse.</p>
        <NuxtLink to="/login" class="btn-primary btn-sm w-fit">Vai all'accesso</NuxtLink>
      </div>

      <form v-else class="flex flex-col gap-[18px]" @submit.prevent="submit">
        <div class="field-label">
          <label for="new-password">Nuova password</label>
          <PasswordInput id="new-password" v-model="password" autocomplete="new-password" :minlength="8" />
          <span class="text-[13px] font-normal text-ink-mute">Almeno 8 caratteri.</span>
        </div>
        <div class="field-label">
          <label for="new-password-2">Ripeti la nuova password</label>
          <PasswordInput id="new-password-2" v-model="confirm" autocomplete="new-password" :minlength="8" />
        </div>
        <p v-if="error" role="alert" class="p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">
          {{ error }}
          <NuxtLink v-if="expired" to="/password-dimenticata" class="block mt-1 underline">Richiedi un nuovo link</NuxtLink>
        </p>
        <button type="submit" :disabled="loading" class="btn-primary h-[52px] text-base">
          {{ loading ? 'Salvataggio…' : 'Salva la nuova password' }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { Check } from 'lucide-vue-next'
import PasswordInput from '~/components/PasswordInput.vue'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Nuova password - EnotecaMolise', robots: 'noindex' })

const route = useRoute()
const { fetchWithAuth } = useApi()
const token = computed(() => String(route.query.token || ''))
const password = ref('')
const confirm = ref('')
const loading = ref(false)
const done = ref(false)
const error = ref('')
const expired = ref(false)

const submit = async () => {
  error.value = ''
  expired.value = false
  if (password.value.length < 8) {
    error.value = 'La password deve contenere almeno 8 caratteri'
    return
  }
  if (password.value !== confirm.value) {
    error.value = 'Le due password non coincidono'
    return
  }
  loading.value = true
  try {
    await fetchWithAuth('/auth/password/reset', { method: 'POST', body: { token: token.value, password: password.value } })
    done.value = true
  } catch (err) {
    error.value = apiErrorMessage(err)
    expired.value = err?.status === 400
  } finally {
    loading.value = false
  }
}
</script>
