<template>
  <div class="px-4 sm:px-6 lg:px-9 py-7 lg:py-8 max-w-[1240px]">
    <div class="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="font-serif text-[40px] font-semibold leading-none text-ink">Eventi</h1>
        <p class="text-sm text-ink-soft mt-1.5 mb-0">
          {{ isAdmin ? 'Gli eventi delle cantine e quelli del territorio. Puoi nascondere quelli non adatti.' : 'Degustazioni, visite e feste della tua cantina: le richieste di partecipazione arrivano in «Richieste».' }}
        </p>
      </div>
      <NuxtLink to="/dashboard/eventi/nuovo" class="btn-primary btn-sm h-11">
        <Plus class="w-4 h-4" aria-hidden="true" /> Nuovo evento
      </NuxtLink>
    </div>

    <div role="tablist" aria-label="Stato degli eventi" class="flex flex-wrap gap-1.5 mb-5">
      <button
        v-for="t in tabs"
        :key="t.value"
        type="button"
        role="tab"
        :aria-selected="tab === t.value"
        :class="['pill h-10', tab === t.value && 'pill-active']"
        @click="tab = t.value"
      >
        {{ t.label }} <span class="opacity-70 ml-1">{{ counts[t.value] }}</span>
      </button>
    </div>

    <div class="card overflow-hidden">
      <div v-if="pending" class="p-8 text-center text-sm text-ink-mute">Caricamento degli eventi…</div>

      <div v-else-if="!visible.length" class="p-12 text-center flex flex-col items-center gap-3">
        <CalendarDays class="w-8 h-8 text-ink-mute" aria-hidden="true" />
        <p class="text-base font-semibold text-ink m-0">{{ emptyText }}</p>
        <NuxtLink v-if="tab === 'UPCOMING'" to="/dashboard/eventi/nuovo" class="btn-primary btn-sm h-11 mt-1">Crea il primo evento</NuxtLink>
      </div>

      <ul v-else class="list-none m-0 p-0 divide-y divide-stone-100">
        <li v-for="ev in visible" :key="ev.id" class="p-5 flex flex-col lg:flex-row lg:items-center gap-4">
          <div class="flex items-start gap-4 flex-1 min-w-0">
            <span class="shrink-0 flex flex-col items-center justify-center w-14 h-16 rounded-xl bg-sand-100 leading-none">
              <span class="text-[11px] font-bold uppercase text-wine-800">{{ badge(ev).weekday }}</span>
              <span class="font-serif text-[24px] font-bold text-ink">{{ badge(ev).day }}</span>
              <span class="text-[11px] font-semibold uppercase text-ink-mute">{{ badge(ev).month }}</span>
            </span>
            <div class="flex flex-col gap-1 min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <NuxtLink :to="`/eventi/${ev.slug}`" class="font-bold text-ink hover:text-wine-800 truncate">{{ ev.title }}</NuxtLink>
                <span v-if="ev.status === 'DRAFT'" class="px-2.5 py-0.5 rounded-full bg-sand-100 text-[#5A4524] text-xs font-bold">Bozza</span>
                <span v-else-if="ev.status === 'CANCELLED'" class="px-2.5 py-0.5 rounded-full bg-wine-50 text-wine-800 border border-wine-200 text-xs font-bold">Annullato</span>
                <span v-else-if="ev.is_past" class="px-2.5 py-0.5 rounded-full bg-stone-100 text-ink-mute text-xs font-bold">Concluso</span>
                <span v-else class="px-2.5 py-0.5 rounded-full bg-bio-50 text-bio-900 border border-bio/20 text-xs font-bold">Pubblicato</span>
                <span v-if="ev.hidden" class="px-2.5 py-0.5 rounded-full bg-wine-800 text-white text-xs font-bold">Nascosto</span>
              </div>
              <span class="text-sm text-ink-soft">
                {{ eventWhen(ev)?.label }}<template v-if="futureDates(ev) > 1"> · {{ futureDates(ev) }} date</template> · {{ placeLabel(ev) }}
              </span>
              <span class="text-[13px] text-ink-mute">
                {{ ev.type_label }}
                <template v-if="isAdmin"> · {{ ev.organizer ? ev.organizer.name : `Evento del territorio${ev.participants.length ? `, ${ev.participants.length} cantine` : ''}` }}</template>
                <template v-else-if="!ev.can_edit"> · organizzato da {{ ev.organizer?.name || 'EnotecaMolise' }}: partecipi come cantina</template>
                <template v-if="ev.requests_count">
                  · <NuxtLink :to="`/dashboard/messaggi?evento=${ev.id}`" class="font-semibold">{{ ev.requests_count === 1 ? '1 richiesta' : `${ev.requests_count} richieste` }}</NuxtLink>
                </template>
              </span>
            </div>
          </div>

          <div class="flex flex-wrap items-center gap-2 shrink-0">
            <NuxtLink :to="`/eventi/${ev.slug}`" class="btn-ghost btn-sm h-9"><Eye class="w-4 h-4" aria-hidden="true" /> Vedi</NuxtLink>
            <template v-if="ev.can_edit">
              <NuxtLink :to="`/dashboard/eventi/${ev.id}`" class="btn-ghost btn-sm h-9"><Pencil class="w-4 h-4" aria-hidden="true" /> Modifica</NuxtLink>
              <button type="button" class="btn-ghost btn-sm h-9" :disabled="busy === ev.id" @click="duplicate(ev)"><Copy class="w-4 h-4" aria-hidden="true" /> Duplica</button>
              <button v-if="ev.status === 'PUBLISHED' && !ev.is_past" type="button" class="btn-ghost btn-sm h-9 text-wine-800" @click="openCancel(ev)"><Ban class="w-4 h-4" aria-hidden="true" /> Annulla</button>
              <button v-if="isAdmin" type="button" class="btn-ghost btn-sm h-9" :disabled="busy === ev.id" @click="toggleHidden(ev)">
                <EyeOff class="w-4 h-4" aria-hidden="true" /> {{ ev.hidden ? 'Mostra' : 'Nascondi' }}
              </button>
              <button type="button" class="btn-ghost btn-sm h-9 text-wine-800" :aria-label="`Elimina ${ev.title}`" :disabled="busy === ev.id" @click="remove(ev)"><Trash2 class="w-4 h-4" aria-hidden="true" /></button>
            </template>
          </div>
        </li>
      </ul>
    </div>

    <!-- Annullamento -->
    <div v-if="cancelling" class="fixed inset-0 z-50 bg-stone-900/40 flex items-center justify-center p-4" role="dialog" aria-modal="true" aria-labelledby="annulla-titolo" @click.self="cancelling = null">
      <div class="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-line flex flex-col gap-4">
        <h3 id="annulla-titolo" class="font-sans text-lg font-bold text-ink m-0">Annullare «{{ cancelling.title }}»?</h3>
        <p class="text-sm text-ink-soft m-0">
          L'evento resterà visibile con la scritta «Annullato» e sparirà dal calendario.
          <template v-if="cancelling.requests_count"> Avviseremo via email {{ cancelling.requests_count === 1 ? 'la persona che aveva' : `le ${cancelling.requests_count} richieste che avevano` }} chiesto di partecipare.</template>
        </p>
        <label class="field-label">Motivo (compare nella pagina e nell'email)
          <textarea v-model="cancelMessage" rows="3" maxlength="2000" class="input h-auto py-2.5 text-sm" placeholder="es. Per il maltempo previsto rimandiamo a una data che comunicheremo presto."></textarea>
        </label>
        <div class="flex justify-end gap-3">
          <button type="button" class="btn-ghost btn-sm h-10" @click="cancelling = null">Indietro</button>
          <button type="button" class="btn-primary btn-sm h-10" :disabled="busy" @click="confirmCancel">Annulla l'evento</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Plus, CalendarDays, Eye, EyeOff, Pencil, Copy, Ban, Trash2 } from 'lucide-vue-next'
import { dateBadge, eventWhen, placeLabel } from '~/utils/events'
import { apiErrorMessage } from '~/utils/apiError'

const { fetchWithAuth } = useApi()
const { isAdmin } = useAuth()
const toast = useToast()

const { data: events, pending, refresh } = await useAsyncData('dashboard_events', () => fetchWithAuth('/events/manage'), { default: () => [] })

const tab = ref('UPCOMING')
const tabs = computed(() => [
  { value: 'UPCOMING', label: 'In programma' },
  { value: 'DRAFT', label: 'Bozze' },
  { value: 'PAST', label: 'Conclusi' },
  { value: 'CANCELLED', label: 'Annullati' },
  ...(isAdmin.value ? [{ value: 'HIDDEN', label: 'Nascosti' }] : [])
])
const inTab = (ev, t) => ({
  UPCOMING: ev.status === 'PUBLISHED' && !ev.is_past,
  DRAFT: ev.status === 'DRAFT',
  PAST: ev.status === 'PUBLISHED' && ev.is_past,
  CANCELLED: ev.status === 'CANCELLED',
  HIDDEN: !!ev.hidden
}[t])
const counts = computed(() => Object.fromEntries(tabs.value.map(t => [t.value, (events.value || []).filter(ev => inTab(ev, t.value)).length])))
const visible = computed(() => (events.value || []).filter(ev => inTab(ev, tab.value)))
const emptyText = computed(() => ({
  UPCOMING: 'Nessun evento in programma',
  DRAFT: 'Nessuna bozza',
  PAST: 'Nessun evento concluso',
  CANCELLED: 'Nessun evento annullato',
  HIDDEN: 'Nessun evento nascosto'
}[tab.value]))

const badge = (ev) => dateBadge(eventWhen(ev)?.start)
const futureDates = (ev) => (ev.dates || []).filter(d => !d.is_past).length

const busy = ref(null)
const cancelling = ref(null)
const cancelMessage = ref('')

const run = async (ev, fn, ok) => {
  busy.value = ev.id
  try {
    const res = await fn()
    toast.success(typeof ok === 'function' ? ok(res) : ok)
    await refresh()
  } catch (err) {
    toast.error(apiErrorMessage(err, 'Operazione non riuscita: riprova.'))
  } finally {
    busy.value = null
  }
}

const duplicate = (ev) => run(ev, () => fetchWithAuth(`/events/${ev.id}/duplicate`, { method: 'POST' }),
  'Copia creata tra le bozze: cambia le date e pubblicala.').then(() => { tab.value = 'DRAFT' })
const toggleHidden = (ev) => run(ev, () => fetchWithAuth(`/events/${ev.id}/visibility`, { method: 'PUT', body: { hidden: !ev.hidden } }),
  ev.hidden ? 'Evento di nuovo visibile sul sito.' : 'Evento nascosto dal sito.')
const remove = (ev) => {
  if (!window.confirm(`Eliminare definitivamente «${ev.title}»? Se vuoi solo avvisare chi si era iscritto, usa «Annulla».`)) return
  run(ev, () => fetchWithAuth(`/events/${ev.id}`, { method: 'DELETE' }), 'Evento eliminato.')
}
const openCancel = (ev) => { cancelling.value = ev; cancelMessage.value = '' }
const confirmCancel = async () => {
  const ev = cancelling.value
  await run(ev, () => fetchWithAuth(`/events/${ev.id}/cancel`, { method: 'POST', body: { message: cancelMessage.value } }),
    (res) => res?.message || 'Evento annullato.')
  cancelling.value = null
}
</script>
