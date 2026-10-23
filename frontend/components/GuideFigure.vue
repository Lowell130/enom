<template>
  <!-- Schermata della guida: si apre a tutta grandezza in una nuova scheda -->
  <figure class="m-0 flex flex-col gap-2">
    <a :href="src" target="_blank" rel="noopener" class="block rounded-xl border border-line bg-white overflow-hidden shadow-[0_1px_2px_rgba(0,0,0,0.04)] hover:border-line-strong"
       :class="narrow && 'max-w-[420px]'" :aria-label="`${alt} (apri l'immagine grande)`">
      <img :src="src" :alt="alt" :width="width" :height="height" loading="lazy" decoding="async" class="block w-full h-auto" />
    </a>
    <figcaption v-if="$slots.default" class="text-[13px] text-ink-mute leading-snug"><slot /></figcaption>
  </figure>
</template>

<script setup>
defineProps({
  src: { type: String, required: true },
  alt: { type: String, required: true },
  width: { type: Number, required: true },
  height: { type: Number, required: true },
  narrow: { type: Boolean, default: false }
})
</script>
