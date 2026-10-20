<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[900px] flex flex-col gap-6">
    <div class="flex flex-col gap-1.5">
      <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Attività delle cantine</h1>
      <p class="text-sm text-ink-soft m-0">
        Cosa fanno le cantine nella loro area riservata: accessi, profilo, vini ed eventi. Le tue modifiche da amministratore
        non compaiono qui. Il registro si svuota da solo dopo 12 mesi.
      </p>
    </div>
    <DashboardActivityFeed />
  </div>
</template>

<script setup>
useSeoMeta({ title: 'Attività delle cantine - EnotecaMolise', robots: 'noindex' })
</script>
