<template>
  <div class="flex flex-col gap-6">
    <!-- Mese -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h2 class="font-serif text-[30px] font-bold m-0 capitalize" aria-live="polite">{{ monthLabel }}</h2>
      <div class="flex items-center gap-2">
        <button type="button" class="btn-ghost btn-sm h-10" :disabled="isCurrentMonth" @click="goToday">Oggi</button>
        <button type="button" class="btn-ghost btn-sm h-10 w-10 px-0" aria-label="Mese precedente" @click="shift(-1)">
          <ChevronLeft class="w-5 h-5" aria-hidden="true" />
        </button>
        <button type="button" class="btn-ghost btn-sm h-10 w-10 px-0" aria-label="Mese successivo" @click="shift(1)">
          <ChevronRight class="w-5 h-5" aria-hidden="true" />
        </button>
      </div>
    </div>

    <!-- Griglia -->
    <div class="card overflow-hidden">
      <div class="grid grid-cols-7 border-b border-line bg-sand-100/60">
        <span v-for="d in WEEKDAYS" :key="d" class="py-2 text-center text-[12px] font-bold uppercase tracking-[0.08em] text-ink-mute">{{ d }}</span>
      </div>
      <div class="grid grid-cols-7" role="grid" :aria-label="`Eventi di ${monthLabel}`">
        <button
          v-for="cell in cells"
          :key="cell.key"
          type="button"
          role="gridcell"
          :aria-selected="selected === cell.key"
          :aria-label="cellLabel(cell)"
          :class="[
            'relative min-h-[64px] sm:min-h-[112px] p-1.5 sm:p-2 border-b border-r border-line text-left flex flex-col gap-1 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-wine-800',
            cell.inMonth ? 'bg-white' : 'bg-cream/70',
            selected === cell.key ? 'ring-2 ring-inset ring-wine-800' : 'hover:bg-sand-100/50'
          ]"
          @click="selected = cell.key"
        >
          <span :class="[
            'inline-flex items-center justify-center w-7 h-7 rounded-full text-[13px] font-semibold self-center sm:self-start',
            cell.isToday ? 'bg-wine-800 text-white' : (cell.inMonth ? 'text-ink' : 'text-ink-mute/60')
          ]">{{ cell.day }}</span>

          <!-- schermi larghi: titoli -->
          <span class="hidden sm:flex flex-col gap-1 min-w-0">
            <span
              v-for="occ in cell.items.slice(0, 3)"
              :key="occ.key"
              :class="['block truncate rounded-r-[4px] border-l-[3px] px-1.5 py-0.5 text-[12px] leading-tight', typeStyle(occ.event.type).chip, occ.continued && 'opacity-70']"
              :title="`${occ.event.title}${occ.time ? ` · ${occ.time}` : ''}`"
            >
              <span v-if="occ.time" class="font-semibold mr-1">{{ occ.time }}</span><span v-if="occ.continued" class="mr-0.5">↳</span>{{ occ.event.title }}
            </span>
            <span v-if="cell.items.length > 3" class="text-[12px] font-semibold text-ink-mute px-1">+{{ cell.items.length - 3 }} altri</span>
          </span>

          <!-- telefono: pallini -->
          <span v-if="cell.items.length" class="sm:hidden flex justify-center gap-0.5" aria-hidden="true">
            <span v-for="occ in cell.items.slice(0, 3)" :key="occ.key" :class="['w-1.5 h-1.5 rounded-full', typeStyle(occ.event.type).dot]"></span>
          </span>
        </button>
      </div>
    </div>

    <!-- Legenda -->
    <ul class="list-none m-0 p-0 flex flex-wrap gap-x-4 gap-y-1.5 text-[13px] text-ink-soft" aria-label="Legenda dei tipi di evento">
      <li v-for="t in legend" :key="t.key" class="inline-flex items-center gap-1.5">
        <span :class="['w-2.5 h-2.5 rounded-full', typeStyle(t.key).dot]" aria-hidden="true"></span>{{ t.label }}
      </li>
    </ul>

    <!-- Giorno scelto -->
    <section class="flex flex-col gap-3" aria-live="polite">
      <template v-if="selected">
        <h3 class="font-serif text-[26px] font-bold m-0 first-letter:uppercase">{{ selectedLabel }}</h3>
        <ul v-if="selectedItems.length" class="list-none m-0 p-0 flex flex-col gap-2">
          <li v-for="occ in selectedItems" :key="occ.key">
            <NuxtLink :to="`/eventi/${occ.event.slug}`" class="card flex items-stretch gap-0 overflow-hidden text-ink hover:border-line-strong">
              <span :class="['w-1.5 shrink-0', typeStyle(occ.event.type).dot]" aria-hidden="true"></span>
              <span class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-4 p-4 flex-1 min-w-0">
                <span class="w-[120px] shrink-0 text-sm font-semibold text-ink-soft">{{ occ.timeRange }}</span>
                <span class="flex flex-col min-w-0 flex-1">
                  <span class="font-bold text-[16px] truncate">{{ occ.event.title }}</span>
                  <span class="text-[13px] text-ink-mute truncate">
                    {{ occ.event.type_label }} · {{ placeLabel(occ.event) }}{{ occ.event.organizer ? ` · ${occ.event.organizer.name}` : '' }}
                  </span>
                </span>
                <span :class="['text-sm font-semibold shrink-0', occ.event.price_type === 'PAID' ? 'text-ink' : 'text-bio-900']">{{ priceLabel(occ.event) }}</span>
              </span>
            </NuxtLink>
          </li>
        </ul>
        <p v-else class="m-0 text-ink-soft">Nessun evento in questo giorno.</p>
      </template>
      <div v-else-if="!monthHasEvents" class="card p-8 text-center flex flex-col items-center gap-3">
        <p class="m-0 text-ink-soft">Nessun evento a {{ monthLabel }}.</p>
        <button v-if="nextMonthWithEvents" type="button" class="btn-outline" @click="setMonth(nextMonthWithEvents)">
          Vai a {{ monthName(nextMonthWithEvents) }}
        </button>
      </div>
      <p v-else class="m-0 text-ink-soft">Scegli un giorno per vedere gli eventi.</p>
    </section>
  </div>
</template>

<script setup>
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'
import { EVENT_TYPES, parseLocal, placeLabel, priceLabel } from '~/utils/events'

const props = defineProps({
  events: { type: Array, default: () => [] },
  month: { type: String, default: '' }   // "2026-11"; vuoto = mese corrente
})
const emit = defineEmits(['update:month'])

const WEEKDAYS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom']
const MONTHS = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
const DAYS = ['domenica', 'lunedì', 'martedì', 'mercoledì', 'giovedì', 'venerdì', 'sabato']
const STYLES = {
  DEGUSTAZIONE: { chip: 'bg-wine-50 text-wine-900 border-wine-800', dot: 'bg-wine-800' },
  VISITA: { chip: 'bg-bio-50 text-bio-900 border-bio', dot: 'bg-bio' },
  CENA: { chip: 'bg-[#FBF1E3] text-gold-600 border-gold-500', dot: 'bg-gold-500' },
  FIERA: { chip: 'bg-[#EEF0F6] text-[#2F3B57] border-[#4F5F86]', dot: 'bg-[#4F5F86]' },
  CORSO: { chip: 'bg-[#F3EEF6] text-[#4B2F5C] border-[#7A5A8E]', dot: 'bg-[#7A5A8E]' },
  VENDEMMIA: { chip: 'bg-[#F5EFE0] text-[#5E4A1C] border-[#A3853C]', dot: 'bg-[#A3853C]' },
  ALTRO: { chip: 'bg-sand-100 text-ink-soft border-ink-mute', dot: 'bg-ink-mute' }
}
const typeStyle = (t) => STYLES[t] || STYLES.ALTRO

const pad = (n) => String(n).padStart(2, '0')
const keyOf = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
const todayKey = keyOf(new Date())
const currentMonth = todayKey.slice(0, 7)

const month = computed(() => (/^\d{4}-\d{2}$/.test(props.month) ? props.month : currentMonth))
const isCurrentMonth = computed(() => month.value === currentMonth)
const monthName = (m) => `${MONTHS[+m.slice(5, 7) - 1]} ${m.slice(0, 4)}`
const monthLabel = computed(() => monthName(month.value))

const setMonth = (m) => emit('update:month', m === currentMonth ? '' : m)
const shift = (delta) => {
  const [y, m] = month.value.split('-').map(Number)
  const d = new Date(y, m - 1 + delta, 1)
  setMonth(`${d.getFullYear()}-${pad(d.getMonth() + 1)}`)
}
const goToday = () => { setMonth(currentMonth); selected.value = todayKey }

// ogni data di ogni evento, ripetuta su tutti i giorni che copre (fiere di piu' giorni)
const hm = (p) => (p && (p.h || p.min) ? `${pad(p.h)}:${pad(p.min)}` : '')
const occurrencesByDay = computed(() => {
  const map = new Map()
  for (const ev of props.events) {
    (ev.dates || []).forEach((d, i) => {
      const s = parseLocal(d.start)
      if (!s) return
      const e = parseLocal(d.end) || s
      const first = new Date(s.y, s.m - 1, s.d)
      const last = new Date(e.y, e.m - 1, e.d)
      let day = new Date(first)
      for (let n = 0; day <= last && n < 62; n++) {
        const k = keyOf(day)
        const multi = last > first
        const startTime = n === 0 ? hm(s) : ''
        const endTime = day.getTime() === last.getTime() ? hm(e) : ''
        const occ = {
          key: `${ev.id}-${i}-${n}`,
          event: ev,
          continued: n > 0,
          time: startTime,
          timeRange: multi
            ? (n === 0 ? `dalle ${startTime || 'mattina'}` : (endTime ? `fino alle ${endTime}` : 'tutto il giorno'))
            : (startTime ? `${startTime}${endTime && endTime !== startTime ? `–${endTime}` : ''}` : 'tutto il giorno'),
          sort: n === 0 ? s.h * 60 + s.min : -1
        }
        if (!map.has(k)) map.set(k, [])
        map.get(k).push(occ)
        day = new Date(day.getFullYear(), day.getMonth(), day.getDate() + 1)
      }
    })
  }
  for (const list of map.values()) list.sort((a, b) => a.sort - b.sort)
  return map
})

const cells = computed(() => {
  const [y, m] = month.value.split('-').map(Number)
  const first = new Date(y, m - 1, 1)
  const offset = (first.getDay() + 6) % 7   // lunedi' = 0
  const start = new Date(y, m - 1, 1 - offset)
  const days = Math.ceil((offset + new Date(y, m, 0).getDate()) / 7) * 7
  return Array.from({ length: days }, (_, i) => {
    const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i)
    const key = keyOf(d)
    return { key, day: d.getDate(), inMonth: d.getMonth() === m - 1, isToday: key === todayKey, items: occurrencesByDay.value.get(key) || [] }
  })
})

const monthHasEvents = computed(() => cells.value.some(c => c.inMonth && c.items.length))
const nextMonthWithEvents = computed(() => {
  const later = [...occurrencesByDay.value.keys()].filter(k => k.slice(0, 7) > month.value).sort()
  return later[0]?.slice(0, 7) || ''
})

// giorno scelto: oggi se ha eventi, altrimenti il primo giorno del mese con eventi
const selected = ref('')
const pickDefault = () => {
  const inMonth = cells.value.filter(c => c.inMonth && c.items.length)
  const today = inMonth.find(c => c.key === todayKey)
  const upcoming = inMonth.find(c => c.key >= todayKey)
  selected.value = (today || upcoming || inMonth[0])?.key || ''
}
watch(month, pickDefault)
watch(() => props.events, () => { if (!selected.value || selected.value.slice(0, 7) !== month.value) pickDefault() })
pickDefault()

const selectedItems = computed(() => occurrencesByDay.value.get(selected.value) || [])
const selectedLabel = computed(() => {
  if (!selected.value) return ''
  const [y, m, d] = selected.value.split('-').map(Number)
  const date = new Date(y, m - 1, d)
  return `${DAYS[date.getDay()]} ${d} ${MONTHS[m - 1]}${y !== new Date().getFullYear() ? ` ${y}` : ''}`
})
const cellLabel = (cell) => {
  const n = cell.items.length
  return `${cell.day} ${MONTHS[+cell.key.slice(5, 7) - 1]}: ${n ? (n === 1 ? '1 evento' : `${n} eventi`) : 'nessun evento'}`
}

const legend = computed(() => {
  const present = new Set(props.events.map(e => e.type))
  return Object.entries(EVENT_TYPES).filter(([k]) => present.has(k)).map(([key, label]) => ({ key, label }))
})
</script>
