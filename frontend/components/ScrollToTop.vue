<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="opacity-0 translate-y-4 scale-95"
    enter-to-class="opacity-100 translate-y-0 scale-100"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="opacity-100 translate-y-0 scale-100"
    leave-to-class="opacity-0 translate-y-4 scale-95"
  >
    <button
      v-if="show"
      @click="scrollToTop"
      type="button"
      aria-label="Torna in alto"
      title="Torna in alto"
      class="fixed bottom-6 right-6 z-50 p-3 bg-wine-800 hover:bg-wine-900 text-white rounded-2xl shadow-xl border border-wine-700/50 hover:scale-110 active:scale-95 transition-all duration-300 flex items-center justify-center group"
    >
      <ArrowUp class="w-5 h-5 group-hover:-translate-y-0.5 transition-transform" />
    </button>
  </Transition>
</template>

<script setup>
import { ArrowUp } from 'lucide-vue-next'

const show = ref(false)

const handleScroll = () => {
  if (typeof window !== 'undefined') {
    show.value = window.scrollY > 300
  }
}

const scrollToTop = () => {
  if (typeof window !== 'undefined') {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })
  }
}

onMounted(() => {
  window.addEventListener('scroll', handleScroll, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll)
})
</script>
