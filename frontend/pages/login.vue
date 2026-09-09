<template>
  <div class="py-20 max-w-md mx-auto px-4">
    
    <div class="bg-white rounded-3xl p-8 border border-stone-200/60 shadow-lg">
      
      <div class="text-center mb-8 space-y-2">
        <div class="w-12 h-12 rounded-full bg-wine-800 flex items-center justify-center text-white mx-auto shadow-xs">
          <Wine class="w-6 h-6 text-amber-200" />
        </div>
        <h1 class="font-serif text-3xl font-light text-stone-900">Area Riservata</h1>
        <p class="text-xs text-stone-500 font-light">Accedi per gestire il tuo catalogo o amministrare il portale</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label class="block text-xs font-bold uppercase tracking-wider text-stone-600 mb-1.5">Email</label>
          <div class="relative">
            <Mail class="w-4 h-4 text-stone-400 absolute left-3.5 top-3.5" />
            <input 
              v-model="email" 
              type="email" 
              required 
              placeholder="admin@enotecamolise.it" 
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

        <div v-if="error" class="p-3.5 bg-rose-50 text-rose-800 rounded-xl text-xs font-semibold border border-rose-200">
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

      <!-- Quick Demo Login Helpers -->
      <div class="mt-8 pt-6 border-t border-stone-100 text-center">
        <span class="text-[11px] text-stone-400 font-medium block mb-3 uppercase tracking-widest">Credenziali Demo</span>
        
        <div class="space-y-2">
          <button 
            @click="fillAdmin" 
            class="w-full py-2.5 px-3 bg-stone-100/80 hover:bg-stone-100 text-stone-800 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between border border-stone-200/50"
          >
            <span class="inline-flex items-center space-x-1.5">
              <ShieldCheck class="w-4 h-4 text-wine-800" />
              <span>Accedi come Admin</span>
            </span>
            <span class="text-[10px] text-stone-500 font-normal">(Super Utente)</span>
          </button>
          
          <button 
            @click="fillProducer" 
            class="w-full py-2.5 px-3 bg-amber-500/10 hover:bg-amber-500/20 text-amber-900 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between border border-amber-500/20"
          >
            <span class="inline-flex items-center space-x-1.5">
              <Building2 class="w-4 h-4 text-amber-800" />
              <span>Accedi come Cantina</span>
            </span>
            <span class="text-[10px] text-amber-700 font-normal">(Valbiferno)</span>
          </button>
        </div>
      </div>

    </div>

  </div>
</template>

<script setup>
import { Wine, Mail, Lock, ShieldCheck, Building2 } from 'lucide-vue-next'

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const { login } = useAuth()

const fillAdmin = () => {
  email.value = 'admin@enotecamolise.it'
  password.value = 'AdminPass2026!'
}

const fillProducer = () => {
  email.value = 'cantina@valbiferno.it'
  password.value = 'CantinaPass2026!'
}

const handleLogin = async () => {
  loading.value = true
  error.value = ''
  try {
    await login({ email: email.value, password: password.value })
    navigateTo('/dashboard')
  } catch (err) {
    error.value = 'Credenziali errate o account non trovato'
  } finally {
    loading.value = false
  }
}
</script>
