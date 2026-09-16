<template>
  <div class="inline-flex flex-col group cursor-pointer">
    <span :class="[
      'font-serif text-2xl sm:text-3xl font-bold tracking-tight leading-none transition-colors',
      variant === 'dark' ? 'text-white group-hover:text-amber-200' : 'text-stone-900 group-hover:text-wine-800'
    ]">
      EnotecaMolise
    </span>
    <span :class="[
      'text-[10px] sm:text-[11px] tracking-[0.22em] uppercase font-semibold mt-1',
      variant === 'dark' ? 'text-amber-200/80' : 'text-stone-500'
    ]">
      I Vini del Molise
    </span>
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'light' // 'light' | 'dark'
  }
})
</script>
