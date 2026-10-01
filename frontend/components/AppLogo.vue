<template>
  <span class="inline-flex flex-col">
    <span :class="['font-serif text-[26px] sm:text-[28px] font-bold leading-none', variant === 'dark' ? 'text-white' : 'text-ink']">
      EnotecaMolise
    </span>
    <span :class="['text-[10px] tracking-[0.22em] uppercase mt-1', variant === 'dark' ? 'text-[#E2C98F]' : 'text-gold-600']">
      {{ subtitle }}
    </span>
  </span>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'light' // 'light' | 'dark'
  },
  subtitle: {
    type: String,
    default: 'I vini del Molise'
  }
})
</script>
