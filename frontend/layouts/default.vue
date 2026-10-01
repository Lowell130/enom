<template>
  <DashboardShell v-if="isDashboard">
    <slot />
  </DashboardShell>
  <div v-else class="min-h-screen flex flex-col bg-cream font-sans text-ink antialiased selection:bg-wine-800 selection:text-white">
    <Navbar />
    <main class="flex-1">
      <slot />
    </main>
    <Footer />
    <ScrollToTop />
  </div>
</template>

<script setup>
const route = useRoute()
const { fetchUser } = useAuth()
const isDashboard = computed(() => route.path.startsWith('/dashboard'))

onMounted(() => {
  fetchUser()
})
</script>
