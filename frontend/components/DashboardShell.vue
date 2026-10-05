<template>
  <div class="min-h-screen bg-[#F8F5F1] md:grid md:grid-cols-[252px_minmax(0,1fr)]">
    <!-- Barra superiore mobile -->
    <div class="md:hidden sticky top-0 z-40 flex items-center justify-between gap-4 px-4 h-16 bg-cream border-b border-line">
      <NuxtLink to="/dashboard" aria-label="Area riservata"><AppLogo subtitle="Area riservata" /></NuxtLink>
      <button
        type="button"
        class="flex items-center justify-center w-11 h-11 rounded-[10px] border border-line-strong bg-white"
        :aria-expanded="open"
        aria-controls="menu-area-riservata"
        :aria-label="open ? 'Chiudi menu' : 'Apri menu'"
        @click="open = !open"
      >
        <X v-if="open" class="w-5 h-5" aria-hidden="true" />
        <Menu v-else class="w-5 h-5" aria-hidden="true" />
      </button>
    </div>

    <aside
      id="menu-area-riservata"
      :class="['bg-cream border-r border-line px-3.5 py-5 flex-col gap-6 md:flex md:sticky md:top-0 md:h-screen', open ? 'flex' : 'hidden']"
    >
      <NuxtLink to="/dashboard" class="hidden md:block px-2.5" aria-label="Area riservata"><AppLogo subtitle="Area riservata" /></NuxtLink>

      <nav aria-label="Area riservata" class="flex flex-col gap-0.5 overflow-y-auto">
        <NuxtLink v-for="item in mainNav" :key="item.to" :to="item.to" :class="itemClass(item)" :aria-current="isActive(item) ? 'page' : undefined">
          <component :is="item.icon" class="w-[18px] h-[18px] shrink-0" aria-hidden="true" />
          <span class="flex-1">{{ item.label }}</span>
        </NuxtLink>

        <template v-if="isAdmin">
          <span class="mt-5 mb-1.5 px-3 text-[11px] font-bold uppercase tracking-[0.14em] text-gold-600">Amministrazione</span>
          <NuxtLink v-for="item in adminNav" :key="item.to" :to="item.to" :class="itemClass(item)" :aria-current="isActive(item) ? 'page' : undefined">
            <component :is="item.icon" class="w-[18px] h-[18px] shrink-0" aria-hidden="true" />
            <span class="flex-1">{{ item.label }}</span>
          </NuxtLink>
        </template>
      </nav>

      <div class="mt-auto flex flex-col gap-0.5 border-t border-line pt-3.5">
        <span v-if="user?.email" class="px-3 pb-2 text-xs text-ink-mute truncate">{{ user.email }}</span>
        <NuxtLink to="/" class="flex items-center gap-3 min-h-[40px] px-3 rounded-[10px] text-ink-soft font-semibold hover:bg-sand-100">
          <ArrowLeft class="w-[18px] h-[18px]" aria-hidden="true" /> Torna al sito
        </NuxtLink>
        <button type="button" class="flex items-center gap-3 min-h-[40px] px-3 rounded-[10px] text-ink-soft font-semibold hover:bg-sand-100 text-left" @click="logout">
          <LogOut class="w-[18px] h-[18px]" aria-hidden="true" /> Esci
        </button>
      </div>
    </aside>

    <main class="min-w-0">
      <slot />
    </main>
  </div>
</template>

<script setup>
import {
  LayoutDashboard, Wine, MessageSquare, Building2, Store, Grape, Utensils, ListChecks,
  ArrowLeft, LogOut, Menu, X, Mail
} from 'lucide-vue-next'

const route = useRoute()
const { user, isAdmin, logout } = useAuth()
const open = ref(false)

const mainNav = computed(() => [
  { label: 'Panoramica', to: '/dashboard', icon: LayoutDashboard, exact: true },
  { label: 'Vini', to: '/dashboard/prodotti', icon: Wine },
  { label: 'Richieste', to: '/dashboard/messaggi', icon: MessageSquare },
  ...(isAdmin.value ? [] : [{ label: 'Profilo cantina', to: '/dashboard/profilo', icon: Store }])
])

const adminNav = [
  { label: 'Cantine', to: '/dashboard/cantine', icon: Building2 },
  { label: 'Vitigni', to: '/dashboard/vitigni', icon: Grape },
  { label: 'Abbinamenti', to: '/dashboard/abbinamenti', icon: Utensils },
  { label: 'Campi scheda tecnica', to: '/dashboard/attributi', icon: ListChecks },
  { label: 'Email e testi', to: '/dashboard/email', icon: Mail }
]

const isActive = (item) => (item.exact ? route.path === item.to : route.path.startsWith(item.to))

const itemClass = (item) => [
  'flex items-center gap-3 min-h-[40px] px-3 rounded-[10px] font-semibold transition-colors',
  isActive(item) ? 'bg-sand-100 text-wine-900' : 'text-ink-soft hover:bg-sand-100/60 hover:text-ink'
]

watch(() => route.fullPath, () => { open.value = false })
</script>
