<template>
  <!-- Sagoma di bottiglia usata finche' il vino non ha una foto -->
  <svg :width="size * 0.36" :height="size" viewBox="0 0 54 150" fill="none" aria-hidden="true">
    <path d="M21 4h12v34c0 6 13 12 13 30v72a6 6 0 0 1-6 6H14a6 6 0 0 1-6-6V68c0-18 13-24 13-30V4Z" stroke="#B9A894" stroke-width="2" />
    <rect x="12" y="84" width="30" height="34" rx="2" stroke="#B9A894" stroke-width="2" />
  </svg>
</template>

<script setup>
defineProps({ size: { type: Number, default: 150 } })
</script>
