<template>
  <header class="sticky top-0 z-50 bg-white/85 backdrop-blur-md border-b border-stone-200/60 transition-all duration-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-20">
        
        <!-- Logo -->
        <NuxtLink to="/" class="flex items-center space-x-3 group">
          <div class="w-10 h-10 rounded-full bg-wine-800 flex items-center justify-center text-white shadow-xs group-hover:scale-105 transition-transform">
            <Wine class="w-5 h-5 text-amber-200" />
          </div>
          <div class="flex flex-col">
            <span class="font-serif text-2xl font-semibold tracking-tight text-stone-900 leading-none group-hover:text-wine-800 transition-colors">EnotecaMolise</span>
            <span class="text-[11px] tracking-widest uppercase font-medium text-stone-500 mt-1">I Vini del Molise</span>
          </div>
        </NuxtLink>

        <!-- Navigation Links -->
        <nav class="hidden md:flex items-center space-x-6 lg:space-x-8 text-sm font-medium tracking-wide">
          <NuxtLink to="/" class="text-stone-600 hover:text-wine-800 transition-colors py-1 border-b-2 border-transparent" active-class="text-wine-800 font-semibold border-wine-800">
            Home
          </NuxtLink>
          <NuxtLink to="/vini" class="text-stone-600 hover:text-wine-800 transition-colors py-1 border-b-2 border-transparent" active-class="text-wine-800 font-semibold border-wine-800">
            Catalogo Vini
          </NuxtLink>
          <NuxtLink to="/produttori" class="text-stone-600 hover:text-wine-800 transition-colors py-1 border-b-2 border-transparent" active-class="text-wine-800 font-semibold border-wine-800">
            Cantine & Produttori
          </NuxtLink>
          <NuxtLink to="/report" class="text-stone-600 hover:text-wine-800 transition-colors py-1 border-b-2 border-transparent" active-class="text-wine-800 font-semibold border-wine-800">
            Osservatorio Vino
          </NuxtLink>
        </nav>

        <!-- User Actions & Search -->
        <div class="flex items-center space-x-3">
          <!-- Search Trigger Button -->
          <button 
            @click="isSearchOpen = true"
            class="hidden sm:flex items-center space-x-2.5 px-3.5 py-2 bg-stone-100/80 hover:bg-stone-100 text-stone-500 rounded-xl text-xs font-medium border border-stone-200/60 transition-all hover:text-stone-900 group shadow-2xs"
            title="Cerca vino o cantina (Ctrl+K)"
          >
            <Search class="w-3.5 h-3.5 text-stone-400 group-hover:text-wine-800 transition-colors" />
            <span>Cerca vino o cantina...</span>
            <kbd class="px-1.5 py-0.5 text-[10px] font-mono text-stone-400 bg-white border border-stone-200 rounded shadow-2xs">⌘K</kbd>
          </button>

          <button 
            @click="isSearchOpen = true"
            class="sm:hidden p-2.5 text-stone-600 hover:text-wine-800 transition-colors rounded-xl bg-stone-100/60 border border-stone-200/50"
            title="Cerca"
          >
            <Search class="w-4 h-4" />
          </button>

          <template v-if="isAuthenticated">
            <NuxtLink to="/dashboard" class="inline-flex items-center space-x-2 px-4 py-2.5 text-sm font-semibold rounded-xl text-white bg-wine-800 hover:bg-wine-900 transition-all shadow-xs">
              <LayoutDashboard class="w-4 h-4 text-amber-200" />
              <span class="hidden md:inline">{{ isAdmin ? 'Dashboard Admin' : 'Area Produttore' }}</span>
            </NuxtLink>
            <button @click="logout" class="p-2 text-stone-500 hover:text-wine-800 transition-colors" title="Esci">
              <LogOut class="w-4 h-4" />
            </button>
          </template>
          <template v-else>
            <NuxtLink to="/login" class="inline-flex items-center space-x-2 px-4 py-2 border border-wine-800 text-wine-800 hover:bg-wine-800 hover:text-white transition-all text-sm font-semibold rounded-xl">
              <LogIn class="w-4 h-4" />
              <span>Accedi</span>
            </NuxtLink>
          </template>
        </div>

      </div>
    </div>

    <!-- Global Search Modal -->
    <GlobalSearchModal :is-open="isSearchOpen" @close="isSearchOpen = false" />
  </header>
</template>

<script setup>
import { Wine, LayoutDashboard, LogOut, LogIn, Search } from 'lucide-vue-next'

const { isAuthenticated, isAdmin, logout } = useAuth()
const isSearchOpen = ref(false)

onMounted(() => {
  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      isSearchOpen.value = true
    }
  }
  window.addEventListener('keydown', handleKeyDown)
  onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
})
</script>
