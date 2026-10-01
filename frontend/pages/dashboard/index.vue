<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 flex flex-col gap-6 max-w-[1240px]">
    <div class="flex flex-wrap items-end justify-between gap-4">
      <div class="flex flex-col gap-1">
        <span class="text-[13px] text-ink-mute">
          {{ isAdmin ? 'Amministratore' : (user?.producer?.company_name || 'La tua cantina') }} · {{ user?.email }}
        </span>
        <h1 class="font-serif text-[40px] md:text-[44px] font-semibold leading-none">Panoramica</h1>
      </div>
      <div class="flex flex-wrap gap-2.5">
        <NuxtLink v-if="!isAdmin && user?.producer?.slug" :to="`/produttori/${user.producer.slug}`" class="btn-ghost btn-sm h-11">Vedi la pagina pubblica</NuxtLink>
        <NuxtLink to="/dashboard/prodotti/nuovo" class="btn-primary btn-sm h-11">
          <Plus class="w-4 h-4" aria-hidden="true" /> Nuovo vino
        </NuxtLink>
      </div>
    </div>

    <p
      v-if="!isAdmin && user?.producer?.status && user.producer.status !== 'APPROVED'"
      role="status"
      class="p-4 rounded-xl border border-[#E8D9B8] bg-[#FBF5E8] text-[#5A4524] text-sm font-medium"
    >
      <template v-if="user.producer.status === 'SUSPENDED'">La tua cantina è stata sospesa dall'amministratore: il profilo e i vini non sono visibili al pubblico.</template>
      <template v-else>La tua cantina è in attesa di approvazione: puoi già inserire i vini, che diventeranno pubblici dopo la verifica dell'amministratore.</template>
    </p>

    <dl v-if="kpis.length" class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div v-for="kpi in kpis" :key="kpi.label" class="px-[18px] py-4 rounded-[14px] border border-line bg-white">
        <dt class="text-[13px] text-ink-soft">{{ kpi.label }}</dt>
        <dd class="mt-0.5 font-serif text-[34px] font-bold leading-tight">{{ kpi.value }}</dd>
      </div>
    </dl>

    <template v-if="privateInsights">
      <DashboardInquiries :data="privateInsights.inquiries" :show-producers="isAdmin" />
      <DashboardCompleteness v-if="privateInsights.completeness?.wines" :data="privateInsights.completeness" :show-producer="isAdmin" />
    </template>

    <section aria-labelledby="scorciatoie" class="flex flex-col gap-3">
      <h2 id="scorciatoie" class="eyebrow-sm tracking-[0.14em]">Cosa vuoi fare</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
        <NuxtLink
          v-for="item in shortcuts"
          :key="item.to"
          :to="item.to"
          class="group flex items-start gap-4 p-5 rounded-2xl border border-line bg-white text-ink hover:border-line-strong"
        >
          <span class="shrink-0 w-11 h-11 rounded-xl bg-sand-100 text-wine-800 flex items-center justify-center">
            <component :is="item.icon" class="w-5 h-5" aria-hidden="true" />
          </span>
          <span class="flex flex-col gap-1">
            <span class="font-bold text-[15px] group-hover:text-wine-800">{{ item.title }}</span>
            <span class="text-sm text-ink-soft">{{ item.text }}</span>
          </span>
        </NuxtLink>
      </div>
    </section>
  </div>
</template>

<script setup>
import { Wine, Building2, MessageSquare, ListChecks, Grape, Plus, Store, Utensils } from 'lucide-vue-next'

useSeoMeta({ title: 'Area riservata - EnotecaMolise' })

const { user, isAdmin } = useAuth()
const { fetchWithAuth } = useApi()

const { data: stats } = await useAsyncData('admin_stats', async () => {
  if (!isAdmin.value) return {}
  return (await fetchWithAuth('/admin/stats')) || {}
}, { default: () => ({}) })

// Richieste ricevute e completezza delle schede (l'admin vede tutto, la cantina solo i propri vini)
const { data: privateInsights } = await useAsyncData('private_insights', async () => {
  try {
    return (await fetchWithAuth('/reports/private')) || null
  } catch (err) {
    return null
  }
}, { default: () => null })

const kpis = computed(() => {
  const s = stats.value || {}
  if (!isAdmin.value || s.total_products === undefined) return []
  return [
    { label: 'Vini inseriti', value: s.total_products },
    { label: 'Vini pubblicati', value: s.published_products },
    { label: 'Cantine in attesa', value: Math.max(0, (s.total_producers || 0) - (s.approved_producers || 0)) },
    { label: 'Richieste da leggere', value: s.unread_inquiries ?? s.total_inquiries }
  ]
})

const shortcuts = computed(() => {
  const list = [
    { to: '/dashboard/prodotti', icon: Wine, title: 'Gestisci i vini', text: isAdmin.value ? 'Catalogo completo, importazione schede e pubblicazione.' : 'Aggiungi, modifica e pubblica le schede dei tuoi vini.' },
    { to: '/dashboard/messaggi', icon: MessageSquare, title: 'Richieste dei clienti', text: 'Messaggi arrivati dalle schede dei vini e delle cantine.' }
  ]
  if (!isAdmin.value) {
    list.push({ to: '/dashboard/profilo', icon: Store, title: 'Profilo della cantina', text: 'Storia, logo, copertina, indirizzo e contatti.' })
  } else {
    list.push(
      { to: '/dashboard/cantine', icon: Building2, title: 'Cantine', text: 'Approva le nuove registrazioni e gestisci i profili.' },
      { to: '/dashboard/vitigni', icon: Grape, title: 'Vitigni', text: 'Elenco ufficiale dei vitigni usati nelle schede.' },
      { to: '/dashboard/abbinamenti', icon: Utensils, title: 'Abbinamenti', text: 'Le categorie di abbinamento gastronomico.' },
      { to: '/dashboard/attributi', icon: ListChecks, title: 'Campi scheda tecnica', text: 'I campi disponibili nella scheda tecnica dei vini.' }
    )
  }
  return list
})
</script>
