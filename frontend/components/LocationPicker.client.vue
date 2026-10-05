<template>
  <!-- Scelta della posizione della cantina sulla mappa: clic sulla mappa o trascinamento del segnaposto -->
  <div class="flex flex-col gap-2.5">
    <div class="relative rounded-xl overflow-hidden border border-line bg-sand">
      <div ref="mapEl" class="h-[300px] w-full" />
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center text-sm text-ink-mute">Caricamento mappa…</div>
    </div>
    <div class="flex flex-wrap items-center justify-between gap-2">
      <p class="text-[13px] text-ink-soft m-0" aria-live="polite">
        <template v-if="hasPoint">
          <MapPin class="inline w-3.5 h-3.5 text-wine-800 -mt-0.5" aria-hidden="true" />
          Punto scelto ({{ format(current[0]) }}, {{ format(current[1]) }}). Trascina il segnaposto per correggerla.
        </template>
        <template v-else-if="townCoords">Clicca sulla mappa nel punto della cantina. Senza un punto, sulla mappa del sito verrà usato il centro di {{ town }}.</template>
        <template v-else>Indica prima il comune, poi clicca sulla mappa nel punto esatto della cantina.</template>
      </p>
      <div class="flex gap-2">
        <button v-if="townCoords" type="button" class="btn-ghost btn-sm h-9" @click="centerOnTown">Centra su {{ town }}</button>
        <button v-if="hasPoint" type="button" class="btn-ghost btn-sm h-9 text-wine-800" @click="clearPoint">Rimuovi il punto</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { MapPin } from 'lucide-vue-next'
import { getTownCoordinates } from '~/utils/producerCoords'

const props = defineProps({
  lat: { type: [Number, String], default: null },
  lng: { type: [Number, String], default: null },
  town: { type: String, default: '' }
})
const emit = defineEmits(['update'])

const MOLISE_CENTER = [41.62, 14.6]
const mapEl = ref(null)
const loading = ref(true)
let map = null
let marker = null
let L = null

const toNumber = (v) => {
  if (v === null || v === undefined || v === '') return null
  const n = Number(String(v).replace(',', '.'))
  return Number.isFinite(n) && n !== 0 ? n : null
}
const current = computed(() => [toNumber(props.lat), toNumber(props.lng)])
const hasPoint = computed(() => current.value[0] !== null && current.value[1] !== null)
const townCoords = computed(() => getTownCoordinates(props.town))
const format = (n) => Number(n).toFixed(5).replace('.', ',')

const loadLeaflet = () => new Promise((resolve) => {
  if (window.L) return resolve(window.L)
  if (!document.getElementById('leaflet-css')) {
    const link = document.createElement('link')
    link.id = 'leaflet-css'
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
  }
  if (!document.getElementById('leaflet-js')) {
    const script = document.createElement('script')
    script.id = 'leaflet-js'
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    script.onload = () => resolve(window.L)
    document.head.appendChild(script)
  } else {
    const t = setInterval(() => { if (window.L) { clearInterval(t); resolve(window.L) } }, 50)
  }
})

const pinIcon = () => L.divIcon({
  className: '',
  html: '<div style="width:28px;height:28px;border-radius:50% 50% 50% 0;background:#6B1F2E;transform:rotate(-45deg);border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>',
  iconSize: [28, 28],
  iconAnchor: [14, 28]
})

const placeMarker = (latlng) => {
  if (!marker) {
    marker = L.marker(latlng, { draggable: true, icon: pinIcon(), keyboard: true, title: 'Posizione della cantina' }).addTo(map)
    marker.on('dragend', () => {
      const p = marker.getLatLng()
      emit('update', { lat: round(p.lat), lng: round(p.lng) })
    })
  } else {
    marker.setLatLng(latlng)
  }
}

const round = (n) => Math.round(n * 1e6) / 1e6

const centerOnTown = () => {
  if (map && townCoords.value) map.setView(townCoords.value, 14)
}

const clearPoint = () => {
  if (marker) {
    map.removeLayer(marker)
    marker = null
  }
  emit('update', { lat: null, lng: null })
}

onMounted(async () => {
  L = await loadLeaflet()
  loading.value = false
  const start = hasPoint.value ? current.value : (townCoords.value || MOLISE_CENTER)
  map = L.map(mapEl.value, { scrollWheelZoom: false }).setView(start, hasPoint.value ? 15 : (townCoords.value ? 13 : 9))
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(map)
  if (hasPoint.value) placeMarker(current.value)
  map.on('click', (e) => {
    placeMarker(e.latlng)
    emit('update', { lat: round(e.latlng.lat), lng: round(e.latlng.lng) })
  })
  // la mappa dentro un modulo puo' cambiare dimensione dopo il caricamento
  setTimeout(() => map && map.invalidateSize(), 300)
})

// se cambia il comune e non c'e' ancora un punto, la mappa si sposta sul nuovo comune
watch(() => props.town, () => {
  if (map && !hasPoint.value && townCoords.value) map.setView(townCoords.value, 13)
})

onBeforeUnmount(() => {
  if (map) map.remove()
  map = null
  marker = null
})
</script>
