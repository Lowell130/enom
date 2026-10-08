<template>
  <footer class="bg-wine-950 text-[#F3E7DF] no-print">
    <div class="page-container pt-14 pb-8 grid gap-8 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
      <div class="flex flex-col gap-2.5">
        <NuxtLink to="/" aria-label="EnotecaMolise, vai alla home">
          <AppLogo variant="dark" />
        </NuxtLink>
        <p class="text-sm text-[#D9C8BE] max-w-xs">Il portale dei vini e delle cantine del Molise.</p>
      </div>
      <nav aria-label="Esplora" class="flex flex-col gap-2 text-sm">
        <span class="font-bold text-[#E2C98F]">Esplora</span>
        <NuxtLink to="/vini" class="text-[#F3E7DF] hover:text-white">Vini</NuxtLink>
        <NuxtLink to="/produttori" class="text-[#F3E7DF] hover:text-white">Cantine</NuxtLink>
        <NuxtLink to="/eventi" class="text-[#F3E7DF] hover:text-white">Eventi</NuxtLink>
        <NuxtLink to="/produttori?view=map" class="text-[#F3E7DF] hover:text-white">Mappa</NuxtLink>
        <NuxtLink to="/report" class="text-[#F3E7DF] hover:text-white">Osservatorio</NuxtLink>
        <NuxtLink to="/chi-siamo" class="text-[#F3E7DF] hover:text-white">Chi siamo</NuxtLink>
      </nav>
      <nav aria-label="Denominazioni" class="flex flex-col gap-2 text-sm">
        <span class="font-bold text-[#E2C98F]">Denominazioni</span>
        <NuxtLink to="/vini?search=Tintilia" class="text-[#F3E7DF] hover:text-white">Tintilia del Molise</NuxtLink>
        <NuxtLink to="/vini?search=Biferno" class="text-[#F3E7DF] hover:text-white">Biferno</NuxtLink>
        <NuxtLink to="/vini?search=Pentro" class="text-[#F3E7DF] hover:text-white">Pentro d'Isernia</NuxtLink>
        <NuxtLink to="/vini?search=Osci" class="text-[#F3E7DF] hover:text-white">Molise / Terre degli Osci</NuxtLink>
      </nav>
      <nav aria-label="Produttori" class="flex flex-col gap-2 text-sm">
        <span class="font-bold text-[#E2C98F]">Sei un produttore?</span>
        <NuxtLink to="/login?mode=register" class="text-[#F3E7DF] hover:text-white">Registra la tua cantina</NuxtLink>
        <NuxtLink to="/login" class="text-[#F3E7DF] hover:text-white">Area riservata</NuxtLink>
      </nav>
    </div>
    <div class="page-container py-5 border-t border-[#4A1A26] text-[13px] text-[#CDB8AE] flex flex-wrap gap-x-5 gap-y-1 justify-between">
      <span>© {{ year }} EnotecaMolise</span>
      <div class="flex flex-wrap gap-x-5 gap-y-1">
        <NuxtLink to="/privacy" class="text-[#CDB8AE] hover:text-white">Informativa privacy</NuxtLink>
        <NuxtLink to="/cookie" class="text-[#CDB8AE] hover:text-white">Cookie policy</NuxtLink>
        <button type="button" class="text-[#CDB8AE] hover:text-white" @click="openPreferences">Preferenze cookie</button>
      </div>
    </div>
  </footer>
</template>

<script setup>
const year = new Date().getFullYear()
const { openPreferences } = useCookieConsent()
</script>
