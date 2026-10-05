<template>
  <section class="page-container pt-10 md:pt-12 pb-16 md:pb-20 grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-12 items-stretch">
    <!-- Pannello per i produttori -->
    <div class="hidden lg:flex flex-col justify-between gap-8 rounded-[22px] bg-sand p-10 min-h-[560px]">
      <div class="flex flex-col gap-3.5">
        <span class="eyebrow">Area produttori</span>
        <h1 class="font-serif text-[48px] font-semibold leading-[1.02]">Porta i tuoi vini davanti a chi cerca il Molise</h1>
      </div>
      <ul class="m-0 p-0 list-none flex flex-col gap-4 text-base text-ink-soft">
        <li v-for="point in benefits" :key="point" class="flex gap-3">
          <Check class="w-[22px] h-[22px] text-wine-800 shrink-0" aria-hidden="true" /><span>{{ point }}</span>
        </li>
      </ul>
      <img
        src="https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=900&q=80"
        alt=""
        class="h-[200px] w-full object-cover rounded-2xl bg-sand-300"
      />
    </div>

    <!-- Modulo -->
    <div class="flex flex-col justify-center gap-6 w-full max-w-[460px] justify-self-center">
      <div role="tablist" aria-label="Accesso o registrazione" class="segmented">
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'login'"
          :class="['segmented-item flex-1 h-11 text-[15px]', mode === 'login' && 'segmented-item-active']"
          @click="switchMode('login')"
        >
          Accedi
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'register'"
          :class="['segmented-item flex-1 h-11 text-[15px]', mode === 'register' && 'segmented-item-active']"
          @click="switchMode('register')"
        >
          Registra cantina
        </button>
      </div>

      <form v-if="mode === 'login'" class="flex flex-col gap-[18px]" @submit.prevent="handleLogin">
        <div class="flex flex-col gap-1">
          <h2 class="font-serif text-4xl font-bold leading-tight">Bentornato</h2>
          <p class="text-[15px] text-ink-soft">Accedi per gestire la tua cantina e i tuoi vini.</p>
        </div>
        <label class="field-label">Email
          <input v-model="email" type="email" required autocomplete="username" placeholder="nome@cantina.it" class="input" />
        </label>
        <div class="field-label">
          <span class="flex items-center justify-between gap-3">
            <label for="login-password">Password</label>
            <NuxtLink to="/password-dimenticata" class="text-[13px] font-semibold text-wine-800 hover:text-wine-900">Password dimenticata?</NuxtLink>
          </span>
          <PasswordInput id="login-password" v-model="password" autocomplete="current-password" />
        </div>
        <p v-if="error" role="alert" class="p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>
        <button type="submit" :disabled="loading" class="btn-primary h-[52px] text-base">
          {{ loading ? 'Accesso in corso…' : 'Accedi' }}
        </button>
        <p class="text-sm text-ink-soft text-center">
          Non hai un account?
          <button type="button" class="font-bold text-wine-800 hover:text-wine-900" @click="switchMode('register')">Registra la tua cantina</button>
        </p>
      </form>

      <form v-else class="flex flex-col gap-[18px]" @submit.prevent="handleRegister">
        <div class="flex flex-col gap-1">
          <h2 class="font-serif text-4xl font-bold leading-tight">Registra la tua cantina</h2>
          <p class="text-[15px] text-ink-soft">Gratuito. Verifichiamo i dati e attiviamo il profilo pubblico dopo l'approvazione.</p>
        </div>
        <label class="field-label">Nome della cantina
          <input v-model="companyName" type="text" required autocomplete="organization" placeholder="es. Tenuta San Giovanni" class="input" />
        </label>
        <label class="field-label">Email della cantina
          <input v-model="regEmail" type="email" required autocomplete="email" placeholder="info@cantina.it" class="input" />
          <span class="text-[13px] font-normal text-ink-mute">Sarà la tua email di accesso: qui riceverai le conferme e le richieste dei clienti.</span>
        </label>
        <div class="field-label">
          <label for="reg-password">Password</label>
          <PasswordInput id="reg-password" v-model="regPassword" autocomplete="new-password" :minlength="8" />
          <span class="text-[13px] font-normal text-ink-mute">Almeno 8 caratteri.</span>
        </div>
        <label class="flex items-start gap-3 text-sm text-ink-soft cursor-pointer">
          <input v-model="privacyAccepted" type="checkbox" required class="mt-0.5 w-[18px] h-[18px] accent-wine-800 shrink-0" />
          <span>
            Ho letto l'<NuxtLink to="/privacy" target="_blank" class="font-semibold text-wine-800 underline underline-offset-2">informativa sulla privacy</NuxtLink>
            e acconsento al trattamento dei dati per la creazione e la gestione del profilo della cantina.
          </span>
        </label>
        <p v-if="error" role="alert" class="p-3 rounded-[10px] bg-wine-50 border border-wine-200 text-wine-900 text-sm font-semibold">{{ error }}</p>
        <button type="submit" :disabled="loading" class="btn-primary h-[52px] text-base">
          {{ loading ? 'Invio in corso…' : 'Invia la registrazione' }}
        </button>
      </form>
    </div>
  </section>
</template>

<script setup>
import { Check } from 'lucide-vue-next'
import PasswordInput from '~/components/PasswordInput.vue'
import { apiErrorMessage } from '~/utils/apiError'

useSeoMeta({ title: 'Accedi - EnotecaMolise' })

const route = useRoute()
const mode = ref(route.query.mode === 'register' ? 'register' : 'login')
const email = ref('')
const password = ref('')
// la registrazione ha i suoi campi: email e password del login non vengono riportate
const regEmail = ref('')
const regPassword = ref('')
const companyName = ref('')
const privacyAccepted = ref(false)
const error = ref('')
const loading = ref(false)

const benefits = [
  'Una pagina per la cantina, con storia, foto e contatti.',
  'Le schede dei vini, anche lette in automatico dai tuoi PDF.',
  'Le richieste dei clienti arrivano direttamente a te.'
]

const { login, registerProducer } = useAuth()
const toast = useToast()

const switchMode = (value) => {
  mode.value = value
  error.value = ''
  password.value = ''
  regPassword.value = ''
}

watch(() => route.query.mode, (v) => { mode.value = v === 'register' ? 'register' : 'login' })
watch([email, password, regEmail, regPassword, companyName, privacyAccepted], () => { error.value = '' })

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    await login({ email: email.value, password: password.value })
    const redirect = route.query.redirect
    navigateTo(typeof redirect === 'string' && redirect.startsWith('/dashboard') ? redirect : '/dashboard')
  } catch (err) {
    if (!err?.status) {
      // nessuna risposta: il server non e' raggiungibile, le credenziali non c'entrano
      error.value = 'Il server non risponde. Controlla la connessione e riprova tra poco.'
    } else if (err.status === 429) {
      error.value = err.data?.detail || 'Troppi tentativi di accesso. Riprova tra qualche minuto.'
    } else {
      error.value = 'Credenziali errate o account non trovato'
    }
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!companyName.value.trim()) {
    error.value = 'Inserisci il nome della tua cantina'
    return
  }
  if (regPassword.value.length < 8) {
    error.value = 'La password deve contenere almeno 8 caratteri'
    return
  }
  if (!privacyAccepted.value) {
    error.value = "Per registrarti devi accettare l'informativa sulla privacy"
    return
  }
  loading.value = true
  error.value = ''
  try {
    await registerProducer({
      email: regEmail.value.trim(),
      password: regPassword.value,
      company_name: companyName.value.trim(),
      privacy_accepted: true
    })
    toast.success('Registrazione completata! Ti abbiamo inviato un\'email di conferma: la cantina sarà pubblica dopo l\'approvazione.')
    navigateTo('/dashboard')
  } catch (err) {
    error.value = apiErrorMessage(err, 'Non è stato possibile completare la registrazione. Riprova.')
  } finally {
    loading.value = false
  }
}
</script>
