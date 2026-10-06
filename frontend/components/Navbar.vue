<template>
  <header class="sticky top-0 z-50 border-b border-line bg-cream/95 backdrop-blur">
    <div class="page-container flex items-center justify-between gap-6 h-[76px]">
      <NuxtLink to="/" aria-label="EnotecaMolise, vai alla home">
        <AppLogo />
      </NuxtLink>

      <nav class="hidden md:flex items-center gap-8 text-sm font-semibold" aria-label="Navigazione principale">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          :class="['py-1 border-b-2 transition-colors', isActive(link) ? 'text-wine-800 border-wine-800' : 'text-ink border-transparent hover:text-wine-800']"
          :aria-current="isActive(link) ? 'page' : undefined"
        >
          {{ link.label }}
        </NuxtLink>
      </nav>

      <div class="flex items-center gap-2.5">
        <button
          type="button"
          class="hidden lg:flex items-center gap-2.5 h-11 px-3.5 rounded-[10px] border border-line-strong bg-white text-sm text-ink-mute hover:border-ink-mute transition-colors"
          @click="isSearchOpen = true"
        >
          <Search class="w-4 h-4" aria-hidden="true" />
          <span>Cerca vino o cantina</span>
          <kbd class="text-[11px] font-sans border border-line-strong rounded-md px-1.5">Ctrl K</kbd>
        </button>
        <button
          type="button"
          class="lg:hidden flex items-center justify-center w-11 h-11 rounded-[10px] border border-line-strong bg-white text-ink"
          aria-label="Cerca vino o cantina"
          @click="isSearchOpen = true"
        >
          <Search class="w-[18px] h-[18px]" aria-hidden="true" />
        </button>

        <template v-if="isAuthenticated">
          <NuxtLink to="/dashboard" class="btn-primary btn-sm h-11">
            <LayoutDashboard class="w-4 h-4" aria-hidden="true" />
            <span class="hidden sm:inline">{{ isAdmin ? 'Area admin' : 'Area cantina' }}</span>
          </NuxtLink>
          <button type="button" class="hidden sm:flex items-center justify-center w-11 h-11 rounded-[10px] text-ink-soft hover:text-wine-800" aria-label="Esci" @click="logout">
            <LogOut class="w-[18px] h-[18px]" aria-hidden="true" />
          </button>
        </template>
        <NuxtLink v-else to="/login" class="hidden sm:inline-flex items-center h-11 px-[18px] rounded-[10px] border border-wine-800 text-wine-800 text-sm font-semibold hover:bg-wine-50 transition-colors">
          Accedi
        </NuxtLink>

        <button
          type="button"
          class="md:hidden flex items-center justify-center w-11 h-11 rounded-[10px] border border-line-strong bg-white text-ink"
          :aria-expanded="isMenuOpen"
          aria-controls="menu-mobile"
          :aria-label="isMenuOpen ? 'Chiudi menu' : 'Apri menu'"
          @click="isMenuOpen = !isMenuOpen"
        >
          <X v-if="isMenuOpen" class="w-5 h-5" aria-hidden="true" />
          <Menu v-else class="w-5 h-5" aria-hidden="true" />
        </button>
      </div>
    </div>

    <!-- Menu mobile -->
    <nav v-if="isMenuOpen" id="menu-mobile" class="md:hidden border-t border-line bg-cream" aria-label="Menu">
      <div class="page-container py-3 flex flex-col">
        <NuxtLink
          v-for="link in links"
          :key="link.to"
          :to="link.to"
          :class="['flex items-center min-h-[48px] text-base font-semibold border-b border-line-soft', isActive(link) ? 'text-wine-800' : 'text-ink']"
          @click="isMenuOpen = false"
        >
          {{ link.label }}
        </NuxtLink>
        <NuxtLink v-if="!isAuthenticated" to="/login" class="btn-outline mt-4" @click="isMenuOpen = false">Accedi</NuxtLink>
        <button v-else type="button" class="btn-ghost mt-4" @click="logout">Esci</button>
      </div>
    </nav>

    <GlobalSearchModal :is-open="isSearchOpen" @close="isSearchOpen = false" />
  </header>
</template>

<script setup>
import { LayoutDashboard, LogOut, Search, Menu, X } from 'lucide-vue-next'

const { isAuthenticated, isAdmin, logout } = useAuth()
const route = useRoute()
const isSearchOpen = ref(false)
const isMenuOpen = ref(false)

const links = [
  { label: 'Vini', to: '/vini', match: '/vini' },
  { label: 'Cantine', to: '/produttori', match: '/produttori' },
  { label: 'Eventi', to: '/eventi', match: '/eventi' },
  { label: 'Mappa', to: '/produttori?view=map', match: 'map' },
  { label: 'Osservatorio', to: '/report', match: '/report' }
]

const isActive = (link) => {
  if (link.match === 'map') return route.path === '/produttori' && route.query.view === 'map'
  if (link.match === '/produttori') return route.path.startsWith('/produttori') && route.query.view !== 'map'
  return route.path.startsWith(link.match)
}

watch(() => route.fullPath, () => { isMenuOpen.value = false })

onMounted(() => {
  const handleKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault()
      isSearchOpen.value = true
    }
  }
  window.addEventListener('keydown', handleKeyDown)
  onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
})
</script>
