<template>
  <Transition
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="opacity-0 translate-y-4"
    enter-to-class="opacity-100 translate-y-0"
    leave-active-class="transition duration-200 ease-in"
    leave-from-class="opacity-100 translate-y-0"
    leave-to-class="opacity-0 translate-y-4"
  >
    <section
      v-if="visible"
      role="dialog"
      aria-labelledby="cookie-title"
      aria-describedby="cookie-text"
      class="no-print fixed z-[60] bottom-3 inset-x-3 sm:inset-x-auto sm:bottom-6 sm:right-6 sm:w-[400px] max-h-[calc(100vh-24px)] overflow-y-auto bg-white border border-line rounded-2xl shadow-2xl"
    >
      <div class="p-5 flex flex-col gap-4">
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-center gap-2.5">
            <span class="w-9 h-9 rounded-xl bg-sand-100 text-wine-800 flex items-center justify-center shrink-0">
              <Cookie class="w-5 h-5" aria-hidden="true" />
            </span>
            <h2 id="cookie-title" class="font-serif text-[22px] font-bold leading-tight m-0">
              {{ prefs ? 'Preferenze cookie' : 'Cookie su EnotecaMolise' }}
            </h2>
          </div>
          <button
            type="button"
            class="p-1.5 -mr-1.5 -mt-1 rounded-lg text-ink-mute hover:text-ink hover:bg-sand-100"
            :aria-label="closeLabel"
            :title="closeLabel"
            @click="close"
          >
            <X class="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        <p id="cookie-text" class="text-sm text-ink-soft leading-relaxed m-0">
          Usiamo cookie tecnici, necessari al funzionamento del sito. Con il tuo consenso potremmo usare anche
          cookie di statistica, per capire in forma aggregata quali pagine sono più utili. Puoi cambiare idea
          quando vuoi da "Preferenze cookie" in fondo alla pagina.
          <NuxtLink to="/cookie" class="font-semibold text-wine-800 underline underline-offset-2">Cookie policy</NuxtLink>
        </p>

        <ul v-if="prefs" class="list-none m-0 p-0 flex flex-col divide-y divide-line border border-line rounded-xl">
          <li v-for="cat in categories" :key="cat.key" class="p-3.5 flex items-start justify-between gap-4">
            <div class="flex flex-col gap-0.5">
              <span :id="`cookie-cat-${cat.key}`" class="text-sm font-bold text-ink">{{ cat.label }}</span>
              <span class="text-[13px] text-ink-soft leading-snug">{{ cat.description }}</span>
            </div>
            <span v-if="cat.locked" class="shrink-0 mt-0.5 text-[12px] font-bold text-ink-mute">Sempre attivi</span>
            <button
              v-else
              type="button"
              role="switch"
              :aria-checked="choices[cat.key]"
              :aria-labelledby="`cookie-cat-${cat.key}`"
              :class="['shrink-0 mt-0.5 relative w-11 h-6 rounded-full transition-colors', choices[cat.key] ? 'bg-wine-800' : 'bg-sand-300']"
              @click="choices[cat.key] = !choices[cat.key]"
            >
              <span :class="['absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform', choices[cat.key] && 'translate-x-5']"></span>
            </button>
          </li>
        </ul>

        <!-- Accetta e Rifiuta hanno lo stesso peso, come chiede il Garante -->
        <div class="grid grid-cols-2 gap-2">
          <button type="button" class="btn-primary btn-sm" @click="rejectAll">Rifiuta</button>
          <button type="button" class="btn-primary btn-sm" @click="acceptAll">Accetta tutti</button>
        </div>
        <button v-if="prefs" type="button" class="btn-ghost btn-sm w-full" @click="saveChoices">Salva le mie scelte</button>
        <button v-else type="button" class="self-center text-sm font-semibold text-wine-800 underline underline-offset-2" @click="openPrefs">
          Personalizza
        </button>
      </div>
    </section>
  </Transition>
</template>

<script setup>
import { Cookie, X } from 'lucide-vue-next'

const { consent, decided, panelOpen, acceptAll, rejectAll, save } = useCookieConsent()

const categories = [
  { key: 'necessari', label: 'Necessari', locked: true, description: 'Tengono attivo l\'accesso all\'area riservata e ricordano queste scelte. Senza, il sito non funziona.' },
  { key: 'statistiche', label: 'Statistiche', description: 'Misurano in forma anonima e aggregata le visite alle pagine. Al momento il sito non ne usa: se verranno attivati, partiranno solo con il tuo consenso.' }
]

const choices = reactive({ statistiche: false })
const prefsMode = ref(false)
const prefs = computed(() => prefsMode.value || panelOpen.value)

// solo nel browser: niente banner nell'HTML generato dal server (e niente sfarfallio per chi ha gia' scelto)
const mounted = ref(false)
onMounted(() => { mounted.value = true })
const visible = computed(() => mounted.value && (!decided.value || panelOpen.value))

watch(panelOpen, (open) => {
  if (open) choices.statistiche = !!consent.value?.statistiche
}, { immediate: true })

// alla prima visita la X vale come rifiuto; riaperto dal footer chiude senza cambiare nulla
const closeLabel = computed(() => decided.value ? 'Chiudi' : 'Chiudi e rifiuta i cookie non necessari')
const close = () => {
  if (decided.value) { panelOpen.value = false; prefsMode.value = false } else rejectAll()
}

const openPrefs = () => {
  choices.statistiche = !!consent.value?.statistiche
  prefsMode.value = true
}
const saveChoices = () => {
  save({ statistiche: choices.statistiche })
  prefsMode.value = false
}
watch(decided, (d) => { if (d) prefsMode.value = false })
</script>
