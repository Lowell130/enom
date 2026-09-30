<template>
  <div class="py-20 max-w-md mx-auto px-4">
    
    <div class="bg-white rounded-3xl p-8 border border-stone-200/60 shadow-lg">
      
      <div class="text-center mb-6 space-y-2 flex flex-col items-center">
        <AppLogo variant="light" />
        <p class="text-xs text-stone-500 font-light pt-2">Accedi per gestire la tua cantina o registra la tua azienda vinicola</p>
      </div>

      <!-- Tab Switcher -->
      <div class="flex rounded-2xl bg-stone-100 p-1 mb-6 border border-stone-200/60">
        <button 
          type="button"
          @click="mode = 'login'"
          :class="['flex-1 py-2 text-xs font-bold rounded-xl transition-all', mode === 'login' ? 'bg-white text-stone-900 shadow-2xs' : 'text-stone-500 hover:text-stone-800']"
        >
          Accedi
        </button>
        <button 
          type="button"
          @click="mode = 'register'"
          :class="['flex-1 py-2 text-xs font-bold rounded-xl transition-all', mode === 'register' ? 'bg-white text-wine-900 shadow-2xs' : 'text-stone-500 hover:text-stone-800']"
        >
          Registra Cantina
        </button>
      </div>

      <!-- Login Form -->
      <form v-if="mode === 'login'" @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Email</label>
          <div class="relative">
            <Mail class="w-4 h-4 text-stone-400 absolute left-3.5 top-3.5" />
            <input 
              v-model="email" 
              type="email" 
              required 
              placeholder="cantina@valbiferno.it" 
              class="w-full border border-stone-200/80 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Password</label>
          <div class="relative">
            <Lock class="w-4 h-4 text-stone-400 absolute left-3.5 top-3.5" />
            <input 
              v-model="password" 
              type="password" 
              required 
              placeholder="••••••••" 
              class="w-full border border-stone-200/80 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            />
          </div>
        </div>

        <div v-if="error" class="p-3 bg-rose-50 text-rose-800 rounded-xl text-xs font-semibold border border-rose-200">
          {{ error }}
        </div>

        <button 
          type="submit" 
          :disabled="loading" 
          class="w-full py-3.5 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-sm font-semibold shadow-md transition-all disabled:opacity-50"
        >
          {{ loading ? 'Accesso in corso...' : 'Accedi' }}
        </button>
      </form>

      <!-- Register Form for New Winery -->
      <form v-else @submit.prevent="handleRegister" class="space-y-4">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Nome Cantina / Azienda *</label>
          <div class="relative">
            <Building2 class="w-4 h-4 text-stone-400 absolute left-3.5 top-3.5" />
            <input 
              v-model="companyName" 
              type="text" 
              required 
              placeholder="es. Tenuta San Giovanni" 
              class="w-full border border-stone-200/80 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Email Cantina *</label>
          <div class="relative">
            <Mail class="w-4 h-4 text-stone-400 absolute left-3.5 top-3.5" />
            <input 
              v-model="email" 
              type="email" 
              required 
              placeholder="info@tenutasangiovanni.it" 
              class="w-full border border-stone-200/80 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            />
          </div>
        </div>

        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Password *</label>
          <div class="relative">
            <Lock class="w-4 h-4 text-stone-400 absolute left-3.5 top-3.5" />
            <input 
              v-model="password" 
              type="password" 
              required 
              placeholder="••••••••" 
              class="w-full border border-stone-200/80 rounded-xl pl-10 pr-4 py-3 text-sm focus:ring-2 focus:ring-wine-800 focus:outline-none"
            />
          </div>
        </div>

        <div v-if="error" class="p-3 bg-rose-50 text-rose-800 rounded-xl text-xs font-semibold border border-rose-200">
          {{ error }}
        </div>

        <button 
          type="submit" 
          :disabled="loading" 
          class="w-full py-3.5 bg-wine-800 hover:bg-wine-900 text-white rounded-xl text-sm font-bold shadow-md transition-all disabled:opacity-50"
        >
          {{ loading ? 'Creazione in corso...' : 'Crea Profilo Cantina' }}
        </button>
      </form>


    </div>

  </div>
</template>

<script setup>
import { Wine, Mail, Lock, Building2 } from 'lucide-vue-next'

const mode = ref('login')
const email = ref('')
const password = ref('')
const companyName = ref('')
const error = ref('')
const loading = ref(false)

const { login, registerProducer } = useAuth()
const route = useRoute()
const toast = useToast()

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
