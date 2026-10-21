<template>
  <!-- Cronologia delle attività delle cantine (solo amministratore). compact = riquadro della panoramica -->
  <div class="flex flex-col gap-4">
    <div v-if="!compact" class="flex flex-col sm:flex-row gap-2 sm:items-center">
      <label class="sr-only" for="att-cantina">Cantina</label>
      <select id="att-cantina" v-model="producerId" class="select h-10 text-sm sm:w-64">
        <option value="">Tutte le cantine</option>
        <option v-for="p in producers" :key="p.id" :value="p.id">{{ p.company_name }}</option>
      </select>
      <div class="flex flex-wrap gap-2" role="tablist" aria-label="Tipo di attività">
        <button v-for="g in groupOptions" :key="g.value" type="button" role="tab" :aria-selected="group === g.value"
                :class="['pill', group === g.value && 'pill-active']" @click="group = g.value">{{ g.label }}</button>
      </div>
    </div>

    <div v-if="loading && !items.length" class="text-sm text-ink-mute py-6 text-center">Caricamento…</div>
    <p v-else-if="!items.length" class="text-sm text-ink-mute m-0 py-6 text-center">
      {{ producerId || group ? 'Nessuna attività con questi filtri.' : 'Ancora nessuna attività delle cantine.' }}
    </p>

    <div v-for="day in days" :key="day.key" class="flex flex-col gap-2">
      <h3 v-if="!compact" class="eyebrow-sm tracking-[0.14em] m-0 pt-2">{{ day.label }}</h3>
      <ol class="list-none m-0 p-0 flex flex-col gap-2">
        <li v-for="it in day.items" :key="it.id" class="card p-3.5 sm:p-4 flex gap-3">
          <span :class="['mt-0.5 w-8 h-8 rounded-full flex items-center justify-center shrink-0', tone(it.group)]" aria-hidden="true">
            <component :is="icon(it.group)" class="w-4 h-4" />
          </span>
          <div class="flex flex-col gap-1 min-w-0 flex-1">
            <p class="m-0 text-sm text-ink leading-snug">
              <NuxtLink v-if="it.producer_slug" :to="`/produttori/${it.producer_slug}`" target="_blank" class="font-bold text-ink hover:text-wine-800">{{ it.producer_name || 'Cantina' }}</NuxtLink>
              <strong v-else>{{ it.producer_name || it.user_email }}</strong>
              {{ ' ' + it.action_label.charAt(0).toLowerCase() + it.action_label.slice(1) }}<template v-if="it.target_name && it.target_type !== 'producer'">:
                <NuxtLink v-if="targetLink(it)" :to="targetLink(it)" target="_blank" class="font-semibold text-wine-800 hover:underline">{{ it.target_name }}</NuxtLink>
                <span v-else class="font-semibold">{{ it.target_name }}</span>
              </template>
            </p>
            <ul v-if="it.changes.length" class="list-none m-0 p-0 flex flex-col gap-0.5 text-[13px] text-ink-soft">
              <li v-for="c in it.changes.slice(0, compact ? 3 : 20)" :key="c.field">
                <span class="font-semibold text-ink-soft">{{ c.label }}</span>:
                <template v-if="c.note">{{ c.note }}</template>
                <template v-else><span class="line-through decoration-ink-mute/60">{{ c.before }}</span> → <span class="text-ink">{{ c.after }}</span></template>
              </li>
              <li v-if="compact && it.changes.length > 3" class="text-ink-mute">e altri {{ it.changes.length - 3 }} campi</li>
            </ul>
            <p v-if="it.details" class="m-0 text-[13px] text-ink-soft">{{ it.details }}</p>
            <span class="text-[12px] text-ink-mute">{{ time(it.created_at) }}<template v-if="it.user_email"> · {{ it.user_email }}</template></span>
          </div>
        </li>
      </ol>
    </div>

    <button v-if="hasMore && !compact" type="button" class="btn-ghost self-center" :disabled="loading" @click="load(true)">
      {{ loading ? 'Caricamento…' : 'Carica le attività precedenti' }}
    </button>
    <NuxtLink v-if="compact && items.length" to="/dashboard/attivita" class="text-sm font-semibold text-wine-800 self-start">Vedi tutte le attività →</NuxtLink>
  </div>
</template>

<script setup>
import { CalendarDays, KeyRound, Store, Wine } from 'lucide-vue-next'
import { apiErrorMessage } from '~/utils/apiError'

const props = defineProps({
  compact: { type: Boolean, default: false },
  limit: { type: Number, default: 40 }
})

const { fetchWithAuth } = useApi()
const toast = useToast()

const items = ref([])
const hasMore = ref(false)
const loading = ref(false)
const producerId = ref('')
const group = ref('')
const producers = ref([])
const groupOptions = [
  { value: '', label: 'Tutto' },
  { value: 'product', label: 'Vini' },
  { value: 'producer', label: 'Profilo' },
  { value: 'event', label: 'Eventi' },
  { value: 'account', label: 'Accessi' }
]

const toDate = (v) => new Date(String(v).endsWith('Z') || String(v).includes('+') ? v : `${v}Z`)

const load = async (more = false) => {
  loading.value = true
  try {
    const params = new URLSearchParams({ limit: String(props.limit) })
    if (producerId.value) params.set('producer_id', producerId.value)
    if (group.value) params.set('group', group.value)
    if (more && items.value.length) params.set('before', items.value[items.value.length - 1].created_at)
    const res = await fetchWithAuth(`/activity?${params}`)
    items.value = more ? [...items.value, ...res.items] : res.items
    hasMore.value = res.has_more
  } catch (err) {
    toast.error(apiErrorMessage(err))
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  load()
  if (!props.compact) {
    try {
      const list = await fetchWithAuth('/producers?include_all=true')
      producers.value = (list || []).slice().sort((a, b) => (a.company_name || '').localeCompare(b.company_name || '', 'it'))
    } catch { /* il filtro per cantina resta vuoto */ }
  }
})
watch([producerId, group], () => load())

const days = computed(() => {
  const out = []
  const today = new Date().toDateString()
  const yesterday = new Date(Date.now() - 86400000).toDateString()
  for (const it of items.value) {
    const d = toDate(it.created_at)
    const key = d.toDateString()
    let day = out[out.length - 1]
    if (!day || day.key !== key) {
      const label = key === today ? 'Oggi' : key === yesterday ? 'Ieri'
        : d.toLocaleDateString('it-IT', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
      day = { key, label: label.charAt(0).toUpperCase() + label.slice(1), items: [] }
      out.push(day)
    }
    day.items.push(it)
  }
  return out
})

const time = (v) => {
  const d = toDate(v)
  const t = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
  return props.compact ? `${d.toLocaleDateString('it-IT', { day: 'numeric', month: 'short' })}, ${t}` : t
}

const icon = (g) => ({ product: Wine, event: CalendarDays, producer: Store }[g] || KeyRound)
const tone = (g) => ({
  product: 'bg-wine-50 text-wine-800',
  event: 'bg-[#FBF5E8] text-[#5A4524]',
  producer: 'bg-sand-100 text-ink-soft'
}[g] || 'bg-stone-100 text-ink-mute')

const targetLink = (it) => {
  if (!it.target_slug || it.action.endsWith('.deleted')) return ''
  if (it.target_type === 'product') return `/vini/${it.target_slug}`
  if (it.target_type === 'event') return `/eventi/${it.target_slug}`
  return ''
}
</script>
