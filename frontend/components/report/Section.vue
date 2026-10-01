<template>
  <section :aria-labelledby="id" class="flex flex-col gap-5">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div class="flex flex-col gap-2 max-w-[720px]">
        <span class="eyebrow">{{ eyebrow }}</span>
        <h2 :id="id" class="title-section text-[32px] md:text-[40px] scroll-mt-28">{{ title }}</h2>
        <p v-if="intro" class="text-base text-ink-soft">{{ intro }}</p>
      </div>
      <p v-if="note" class="text-[13px] text-ink-mute max-w-[320px]">{{ note }}</p>
    </header>
    <slot />
  </section>
</template>

<script setup>
// Intestazione comune alle sezioni di approfondimento dell'Osservatorio
defineProps({
  id: { type: String, required: true },
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  intro: { type: String, default: '' },
  note: { type: String, default: '' }
})
</script>
