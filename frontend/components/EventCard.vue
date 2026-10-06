<template>
  <article :class="['card overflow-hidden flex group', compact ? 'flex-row items-stretch' : 'flex-col']">
    <NuxtLink
      :to="url"
      tabindex="-1"
      aria-hidden="true"
      :class="['relative block overflow-hidden shrink-0', compact ? 'w-[120px] sm:w-[160px]' : 'h-[170px]']"
      :style="{ background: tone(event.title) }"
    >
      <SafeImg :src="mediaUrl(event.cover_image)" alt="" loading="lazy" class="w-full h-full object-cover group-hover:scale-[1.03] transition-transform duration-700">
        <CoverArt :seed="event.title" :place="placeLabel(event)" class="group-hover:scale-[1.03] transition-transform duration-700" />
      </SafeImg>
      <span v-if="!compact" class="absolute top-3 left-3 flex flex-col items-center justify-center w-14 h-16 rounded-xl bg-white text-ink shadow-[0_2px_8px_rgba(42,8,18,0.12)] leading-none">
        <span class="text-[11px] font-bold uppercase text-wine-800">{{ badge.weekday }}</span>
        <span class="font-serif text-[26px] font-bold">{{ badge.day }}</span>
        <span class="text-[11px] font-semibold uppercase text-ink-mute">{{ badge.month }}</span>
      </span>
      <span v-if="event.status === 'CANCELLED'" class="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-wine-800 text-white text-xs font-bold">Annullato</span>
    </NuxtLink>

    <div :class="['flex flex-col gap-1.5 flex-1 min-w-0', compact ? 'p-4' : 'px-5 pt-4 pb-5']">
      <span class="eyebrow-sm">{{ event.type_label }}</span>
      <h3 :class="['title-card', compact ? 'text-[22px]' : 'text-[24px]']">
        <NuxtLink :to="url" class="text-ink hover:text-wine-800">{{ event.title }}</NuxtLink>
      </h3>
      <span class="flex items-start gap-1.5 text-sm text-ink-soft">
        <CalendarDays class="w-[15px] h-[15px] mt-0.5 shrink-0" aria-hidden="true" />
        <span>
          {{ when?.label }}
          <span v-if="moreDates" class="text-ink-mute"> · e altre {{ moreDates }} date</span>
        </span>
      </span>
      <span class="flex items-center gap-1.5 text-sm text-ink-soft">
        <MapPin class="w-[15px] h-[15px] shrink-0" aria-hidden="true" />
        <span class="truncate">{{ placeLabel(event) }}</span>
      </span>
      <div class="mt-auto pt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span :class="['font-semibold', event.price_type === 'PAID' ? 'text-ink' : 'text-bio-900']">{{ priceLabel(event) }}</span>
        <span v-if="organizerName" class="text-ink-mute truncate">· {{ organizerName }}</span>
      </div>
    </div>
  </article>
</template>

<script setup>
import { CalendarDays, MapPin } from 'lucide-vue-next'
import CoverArt from '~/components/CoverArt.vue'
import { dateBadge, eventWhen, placeLabel, priceLabel } from '~/utils/events'

const props = defineProps({
  event: { type: Object, required: true },
  compact: { type: Boolean, default: false }
})

const { mediaUrl, tone } = useProducer()

const url = computed(() => `/eventi/${props.event.slug}`)
const when = computed(() => eventWhen(props.event))
const badge = computed(() => dateBadge(when.value?.start))
const moreDates = computed(() => {
  const upcoming = (props.event.dates || []).filter(d => !d.is_past).length
  return upcoming > 1 ? upcoming - 1 : 0
})
const organizerName = computed(() => props.event.organizer?.name
  || (props.event.participants?.length ? `${props.event.participants.length} cantine` : ''))
</script>
