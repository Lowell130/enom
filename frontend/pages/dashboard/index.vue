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

    <!-- Cantina: cosa manca per un profilo completo -->
    <section v-if="!isAdmin && onboarding.total && onboarding.done < onboarding.total" aria-labelledby="onboarding" class="card p-5 sm:p-6 flex flex-col gap-4">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div class="flex flex-col gap-1">
          <h2 id="onboarding" class="font-serif text-2xl font-bold">Completa la tua cantina</h2>
          <p class="text-sm text-ink-soft m-0">{{ user?.producer?.status === 'APPROVED' ? 'Un profilo completo si trova meglio nel catalogo e ispira più fiducia ai visitatori.' : 'Un profilo completo viene approvato prima e si trova meglio nel catalogo.' }}</p>
        </div>
        <span class="text-sm font-semibold text-wine-800">{{ onboarding.done }} di {{ onboarding.total }}</span>
      </div>
      <div class="h-2 rounded-full bg-sand-200 overflow-hidden" aria-hidden="true">
        <div class="h-full bg-wine-800 rounded-full transition-all" :style="{ width: `${Math.round(onboarding.done / onboarding.total * 100)}%` }" />
      </div>
      <ul class="m-0 p-0 list-none grid grid-cols-1 sm:grid-cols-2 gap-2">
        <li v-for="step in onboarding.steps" :key="step.label">
          <NuxtLink :to="step.to" :class="['flex items-center gap-3 p-3 rounded-xl border text-sm', step.ok ? 'border-line text-ink-mute' : 'border-line-strong bg-white text-ink hover:border-wine-800']">
            <span :class="['w-6 h-6 rounded-full flex items-center justify-center shrink-0', step.ok ? 'bg-bio-50 text-bio' : 'bg-sand-100 text-ink-mute']">
              <Check v-if="step.ok" class="w-3.5 h-3.5" aria-hidden="true" />
            </span>
            <span :class="step.ok && 'line-through'">{{ step.label }}</span>
            <span class="sr-only">{{ step.ok ? '(fatto)' : '(da fare)' }}</span>
          </NuxtLink>
        </li>
      </ul>
    </section>

    <!-- Admin: cose da fare -->
    <NuxtLink v-if="isAdmin && stats?.pending_producers" to="/dashboard/cantine?stato=PENDING_APPROVAL"
      class="flex items-center justify-between gap-3 p-4 rounded-xl border border-[#E8D9B8] bg-[#FBF5E8] text-[#5A4524] text-sm font-semibold hover:border-[#CBB27F]">
      <span>{{ stats.pending_producers === 1 ? '1 cantina è in attesa di approvazione' : `${stats.pending_producers} cantine sono in attesa di approvazione` }}</span>
      <span>Rivedi →</span>
    </NuxtLink>
    <NuxtLink v-if="isAdmin && stats?.deletion_requests" to="/dashboard/cantine?stato=DELETION"
      class="flex items-center justify-between gap-3 p-4 rounded-xl border border-wine-200 bg-wine-50 text-wine-900 text-sm font-semibold hover:border-wine-800">
      <span>{{ stats.deletion_requests === 1 ? '1 cantina ha chiesto la cancellazione' : `${stats.deletion_requests} cantine hanno chiesto la cancellazione` }}</span>
      <span>Gestisci →</span>
    </NuxtLink>

    <p v-if="isAdmin && stats?.orphan_products" role="alert" class="p-4 rounded-xl border border-wine-200 bg-wine-50 text-wine-900 text-sm font-medium">
      {{ stats.orphan_products === 1 ? 'C\'è 1 vino collegato' : `Ci sono ${stats.orphan_products} vini collegati` }} a una cantina che non esiste più: non compaiono nel sito. Ricollegali a una cantina o eliminali.
    </p>

    <dl v-if="kpis.length" class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <div v-for="kpi in kpis" :key="kpi.label" class="relative px-[18px] py-4 rounded-[14px] border border-line bg-white hover:border-line-strong">
        <dt class="text-[13px] text-ink-soft">
          <NuxtLink :to="kpi.to" class="after:absolute after:inset-0 hover:text-wine-800">{{ kpi.label }}</NuxtLink>
        </dt>
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
import { Wine, Building2, MessageSquare, ListChecks, Grape, Plus, Store, Utensils, Check, Mail } from 'lucide-vue-next'

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
    { label: 'Vini inseriti', value: s.total_products, to: '/dashboard/prodotti' },
    { label: 'Vini pubblicati', value: s.published_products, to: '/vini' },
    { label: 'Cantine in attesa', value: s.pending_producers ?? Math.max(0, (s.total_producers || 0) - (s.approved_producers || 0)), to: '/dashboard/cantine?stato=PENDING_APPROVAL' },
    { label: 'Richieste da leggere', value: s.unread_inquiries ?? s.total_inquiries, to: '/dashboard/messaggi' }
  ]
})

// Passi per completare il profilo della cantina (con il link alla pagina dove si fa)
const { data: myWines } = await useAsyncData('my_wines_count', async () => {
  const pid = user.value?.producer_id || user.value?.producer?.id
  if (isAdmin.value || !pid) return []
  return (await fetchWithAuth(`/products?status=ALL&producer_id=${pid}`).catch(() => [])) || []
}, { default: () => [] })

const onboarding = computed(() => {
  const p = user.value?.producer
  if (isAdmin.value || !p) return { steps: [], done: 0, total: 0 }
  const geo = p.address?.geo_coordinates
  const steps = [
    { label: 'Indica il comune della cantina', ok: !!p.address?.city, to: '/dashboard/profilo' },
    { label: 'Segna la cantina sulla mappa', ok: !!(geo && geo.lat && geo.lng), to: '/dashboard/profilo' },
    { label: 'Carica il logo', ok: !!p.logo_url, to: '/dashboard/profilo' },
    { label: 'Aggiungi una foto di copertina', ok: !!p.cover_image_url, to: '/dashboard/profilo' },
    { label: 'Racconta la storia della cantina', ok: (p.description || '').length >= 150, to: '/dashboard/profilo' },
    { label: 'Aggiungi telefono o sito web', ok: !!(p.contacts?.phone || p.contacts?.website), to: '/dashboard/profilo' },
    { label: 'Inserisci il primo vino', ok: (myWines.value || []).length > 0, to: '/dashboard/prodotti/nuovo' }
  ]
  return { steps, done: steps.filter(s => s.ok).length, total: steps.length }
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
      { to: '/dashboard/attributi', icon: ListChecks, title: 'Campi scheda tecnica', text: 'I campi disponibili nella scheda tecnica dei vini.' },
      { to: '/dashboard/email', icon: Mail, title: 'Email e testi', text: 'Modelli delle email, posta in uscita e informativa privacy.' }
    )
  }
  return list
})
</script>
