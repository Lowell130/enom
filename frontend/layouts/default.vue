<template>
  <div class="min-h-screen flex flex-col bg-cream font-sans text-gray-800 antialiased selection:bg-wine-800 selection:text-white">
    <Navbar />
    <main class="flex-1">
      <slot />
    </main>
    <Footer />
  </div>
</template>

<script setup>
const { fetchUser } = useAuth()
onMounted(() => {
  fetchUser()
})
</script>
