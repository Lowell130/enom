<template>
  <div
    v-if="visible"
    class="no-print fixed inset-0 z-[70] bg-wine-950/80 backdrop-blur-sm flex items-center justify-center p-4"
  >
    <section
      role="dialog"
      aria-modal="true"
      aria-labelledby="age-title"
      aria-describedby="age-text"
      class="w-full max-w-[440px] bg-cream rounded-[22px] shadow-2xl p-7 sm:p-9 flex flex-col items-center gap-5 text-center"
    >
      <AppLogo />
      <template v-if="!refused">
        <h2 id="age-title" class="font-serif text-[30px] font-bold leading-tight m-0">Hai almeno 18 anni?</h2>
        <p id="age-text" class="m-0 text-[15px] leading-relaxed text-ink-soft">
          EnotecaMolise parla di vino: per entrare devi avere l'età legale per il consumo di bevande alcoliche.
        </p>
        <div class="grid grid-cols-2 gap-2.5 w-full">
          <button type="button" class="btn-outline" @click="refused = true">No</button>
          <button ref="yesBtn" type="button" class="btn-primary" @click="accept">Sì, ho 18 anni</button>
        </div>
        <p class="m-0 text-[12px] text-ink-mute">
          Entrando confermi di essere maggiorenne. Ricordiamo la risposta su questo dispositivo con un
          <NuxtLink to="/cookie" class="underline underline-offset-2">cookie tecnico</NuxtLink>.
        </p>
      </template>
      <template v-else>
        <h2 id="age-title" class="font-serif text-[30px] font-bold leading-tight m-0">Ci vediamo più avanti</h2>
        <p id="age-text" class="m-0 text-[15px] leading-relaxed text-ink-soft">
          Il sito è riservato ai maggiorenni. Il consumo di alcol è vietato ai minori di 18 anni.
        </p>
        <button type="button" class="text-sm font-semibold text-wine-800 underline underline-offset-2" @click="refused = false">
          Ho sbagliato risposta
        </button>
      </template>
    </section>
  </div>
</template>

<script setup>
const route = useRoute()
const { confirmed, confirm } = useAgeGate()

// pagine di servizio senza conferma: area riservata, attivazione e recupero password, testi legali
const EXEMPT = ['/dashboard', '/attiva-account', '/reimposta-password', '/password-dimenticata', '/privacy', '/cookie']

const refused = ref(false)
const yesBtn = ref(null)
// solo nel browser: i motori di ricerca leggono comunque i contenuti della pagina
const mounted = ref(false)
onMounted(() => { mounted.value = true })

const visible = computed(() => mounted.value && !confirmed.value && !EXEMPT.some(p => route.path.startsWith(p)))

// pagina ferma sotto la finestra; focus sul pulsante principale
const gateOpen = useState('age_gate_open', () => false)
watch(visible, async (v) => {
  gateOpen.value = v
  if (typeof document === 'undefined') return
  document.documentElement.style.overflow = v ? 'hidden' : ''
  if (v) { await nextTick(); yesBtn.value?.focus() }
}, { immediate: true })
onBeforeUnmount(() => { if (typeof document !== 'undefined') document.documentElement.style.overflow = '' })

const accept = () => confirm()
</script>
