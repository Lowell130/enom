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
        <nav class="hidden md:flex items-center space-x-8 text-sm font-medium tracking-wide">
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

        <!-- User Actions / Login -->
        <div class="flex items-center space-x-4">
          <template v-if="isAuthenticated">
            <NuxtLink to="/dashboard" class="inline-flex items-center space-x-2 px-4 py-2.5 text-sm font-semibold rounded-xl text-white bg-wine-800 hover:bg-wine-900 transition-all shadow-xs">
              <LayoutDashboard class="w-4 h-4 text-amber-200" />
              <span>{{ isAdmin ? 'Dashboard Admin' : 'Area Produttore' }}</span>
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
  </header>
</template>

<script setup>
import { Wine, LayoutDashboard, LogOut, LogIn } from 'lucide-vue-next'
const { isAuthenticated, isAdmin, logout } = useAuth()
</script>
