<template>
  <footer class="bg-wine-950 text-stone-300 border-t border-wine-900/40 pt-16 pb-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-10">
        
        <div class="md:col-span-2">
          <div class="mb-4">
            <NuxtLink to="/">
              <AppLogo variant="dark" />
            </NuxtLink>
          </div>
          <p class="text-sm text-stone-400 leading-relaxed max-w-md font-light">
            Il portale centrale dei viticoltori e delle cantine del Molise. Un viaggio tra Tintilia DOC, Biferno, Pentro e spumanti autoctoni. Valorizziamo l'eccellenza enologica molisana.
          </p>
        </div>

        <div>
          <h4 class="font-serif text-base font-semibold text-amber-200 mb-4 tracking-wide">Navigazione</h4>
          <ul class="space-y-2.5 text-sm text-stone-400 font-light">
            <li><NuxtLink to="/" class="hover:text-white transition-colors">Home</NuxtLink></li>
            <li><NuxtLink to="/vini" class="hover:text-white transition-colors">Tutti i Vini</NuxtLink></li>
            <li><NuxtLink to="/produttori" class="hover:text-white transition-colors">Elenco Cantine</NuxtLink></li>
            <li><NuxtLink to="/login" class="hover:text-white transition-colors">Area Riservata Produttori</NuxtLink></li>
          </ul>
        </div>

        <div>
          <h4 class="font-serif text-base font-semibold text-amber-200 mb-4 tracking-wide">Menzioni Enologiche</h4>
          <ul class="space-y-2.5 text-sm text-stone-400 font-light">
            <li>Tintilia del Molise DOC</li>
            <li>Biferno DOC (Rosso, Bianco, Rosato)</li>
            <li>Pentro d'Isernia DOC</li>
            <li>Molise IGT / IGP</li>
          </ul>
        </div>

      </div>

      <div class="mt-12 pt-8 border-t border-wine-900/60 flex flex-col md:flex-row justify-between items-center text-xs text-stone-500 font-light">
        <p>© 2026 EnotecaMolise - Tutti i diritti riservati.</p>
        <p class="mt-2 md:mt-0">Prodotto Enologico Molisano</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { Wine } from 'lucide-vue-next'
</script>
