<template>
  <img v-if="src && !failed" ref="el" :src="src" :alt="alt" v-bind="$attrs" @error="failed = true" />
  <slot v-else />
</template>

<script setup>
// Immagine con ripiego: se manca o non si carica mostra lo slot (iniziali, sagoma della bottiglia...).
// Il controllo in onMounted copre gli errori avvenuti prima dell'idratazione (immagini renderizzate lato server).
defineOptions({ inheritAttrs: false })

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' }
})

const failed = ref(false)
const el = ref(null)

onMounted(() => {
  const img = el.value
  if (img && img.complete && img.naturalWidth === 0) failed.value = true
})

watch(() => props.src, () => { failed.value = false })
</script>
