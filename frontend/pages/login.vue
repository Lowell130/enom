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
          <input v-model="email" type="email" required autocomplete="email" placeholder="nome@cantina.it" class="input" />
        </label>
        <label class="field-label">Password
          <input v-model="password" type="password" required autocomplete="current-password" class="input" />
        </label>
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
          <input v-model="email" type="email" required autocomplete="email" placeholder="info@cantina.it" class="input" />
        </label>
        <label class="field-label">Password
          <input v-model="password" type="password" required minlength="8" autocomplete="new-password" class="input" />
          <span class="text-[13px] font-normal text-ink-mute">Almeno 8 caratteri.</span>
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

useSeoMeta({ title: 'Accedi - EnotecaMolise' })

const route = useRoute()
const mode = ref(route.query.mode === 'register' ? 'register' : 'login')
const email = ref('')
const password = ref('')
const companyName = ref('')
const error = ref('')
const loading = ref(false)

const benefits = [
  'Una pagina per la cantina, con storia, foto e contatti.',
  'Le schede dei vini, anche caricate da PDF.',
  'Le richieste dei clienti arrivano direttamente a te.'
]

const { login, registerProducer } = useAuth()
const toast = useToast()

const switchMode = (value) => {
  mode.value = value
  error.value = ''
}

watch(() => route.query.mode, (v) => { mode.value = v === 'register' ? 'register' : 'login' })

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    await login({ email: email.value, password: password.value })
    const redirect = route.query.redirect
    navigateTo(typeof redirect === 'string' && redirect.startsWith('/dashboard') ? redirect : '/dashboard')
  } catch (err) {
    error.value = err?.status === 429
      ? (err.data?.detail || 'Troppi tentativi di accesso. Riprova tra qualche minuto.')
      : 'Credenziali errate o account non trovato'
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  if (!companyName.value.trim()) {
    error.value = 'Inserisci il nome della tua cantina'
    return
  }
  if (password.value.length < 8) {
    error.value = 'La password deve contenere almeno 8 caratteri'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await registerProducer({
      email: email.value,
      password: password.value,
      company_name: companyName.value
    })
    toast.success('Profilo cantina creato! Sarà visibile al pubblico dopo l\'approvazione dell\'amministratore.')
    navigateTo('/dashboard')
  } catch (err) {
    const detail = err.data?.detail
    error.value = (typeof detail === 'string' && detail) || 'Errore durante la creazione della cantina'
  } finally {
    loading.value = false
  }
}
</script>
