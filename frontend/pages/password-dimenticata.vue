<template>
  <section class="page-container pt-12 md:pt-16 pb-20 flex justify-center">
    <div class="w-full max-w-[460px] flex flex-col gap-6">
      <NuxtLink to="/login" class="text-sm font-semibold text-wine-800 hover:text-wine-900 w-fit">← Torna all'accesso</NuxtLink>
      <div class="flex flex-col gap-2">
        <span class="eyebrow">Area produttori</span>
        <h1 class="font-serif text-[40px] font-semibold leading-[1.05]">Password dimenticata?</h1>
        <p class="text-[15px] text-ink-soft">Scrivi l'email con cui accedi: ti mandiamo un link per sceglierne una nuova.</p>
      </div>

      <div v-if="sent" role="status" class="card p-6 flex flex-col gap-3">
        <span class="w-11 h-11 rounded-xl bg-bio-50 text-bio flex items-center justify-center"><MailCheck class="w-5 h-5" aria-hidden="true" /></span>
        <p class="font-semibold text-ink">Controlla la posta</p>
        <p class="text-sm text-ink-soft">{{ message }} Il link vale {{ ttl }} minuti. Se non la trovi, guarda anche nella cartella spam.</p>
        <button type="button" class="text-sm font-semibold text-wine-800 hover:text-wine-900 w-fit" @click="sent = false">Non è arrivata? Riprova</button>
      </div>

      <form v-else class="flex flex-col gap-[18px]" @submit.prevent="submit">
        <label class="field-label">Email
          <input v-model="email" type="email" required autocomplete="username" placeholder="nome@cantina.it" class="input" />
        </label>
        <p v-if="error" role="alert" class="p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>
        <button type="submit" :disabled="loading" class="btn-primary h-[52px] text-base">
          {{ loading ? 'Invio in corso…' : 'Inviami il link' }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { MailCheck } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Password dimenticata - EnotecaMolise', robots: 'noindex' })

const { fetchWithAuth } = useApi()
const email = ref('')
const loading = ref(false)
const sent = ref(false)
const error = ref('')
const message = ref('')
const ttl = 60

const submit = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await fetchWithAuth('/auth/password/forgot', { method: 'POST', body: { email: email.value.trim() } })
    message.value = res?.message || ''
    sent.value = true
  } catch (err) {
    error.value = apiErrorMessage(err)
  } finally {
    loading.value = false
  }
}
</script>
