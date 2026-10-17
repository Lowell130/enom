<template>
  <!-- Scelta della posizione della cantina sulla mappa: clic sulla mappa o trascinamento del segnaposto -->
  <div class="flex flex-col gap-2.5">
    <!-- 1. ricerca per indirizzo o nome (OpenStreetMap), 2. coordinate o link di Google Maps incollati -->
    <div class="flex flex-col sm:flex-row gap-2">
      <div class="relative flex-1">
        <input
          v-model="query"
          type="search"
          class="input h-10 text-sm w-full"
          :placeholder="`Cerca indirizzo o nome, es. Contrada Colle Tinto ${town || ''}`.trim()"
          aria-label="Cerca un indirizzo o un luogo sulla mappa"
          @keydown.enter.prevent="search"
        />
      </div>
      <button type="button" class="btn-outline btn-sm h-10 shrink-0" :disabled="searching || !query.trim()" @click="search">
        {{ searching ? 'Cerco…' : 'Cerca' }}
      </button>
    </div>
    <ul v-if="results.length" class="list-none m-0 p-0 border border-line rounded-xl divide-y divide-line bg-white max-h-56 overflow-y-auto">
      <li v-for="r in results" :key="r.place_id">
        <button type="button" class="w-full text-left px-3 py-2 text-[13px] hover:bg-sand-100" @click="choose(r)">
          <span class="font-semibold text-ink">{{ r.name || r.display_name.split(',')[0] }}</span>
          <span class="block text-ink-mute">{{ r.display_name }}</span>
        </button>
      </li>
    </ul>
    <p v-if="searchMsg" class="text-[13px] text-ink-soft m-0" role="status">{{ searchMsg }}</p>
    <details class="text-[13px] text-ink-soft">
      <summary class="cursor-pointer font-semibold text-wine-800 w-fit">Hai le coordinate o un link di Google Maps?</summary>
      <div class="mt-2 flex flex-col sm:flex-row gap-2">
        <input
          v-model="pasted"
          type="text"
          class="input h-10 text-sm flex-1"
          placeholder="41.67480, 14.57680 oppure link di Google Maps"
          aria-label="Coordinate o link di Google Maps"
          @keydown.enter.prevent="usePasted"
        />
        <button type="button" class="btn-outline btn-sm h-10 shrink-0" :disabled="!pasted.trim()" @click="usePasted">Usa</button>
      </div>
      <p class="mt-1.5 mb-0 text-ink-mute">Su Google Maps tieni premuto (o clic destro) sul punto della cantina: in alto compaiono le coordinate, cliccale per copiarle.</p>
    </details>
    <div class="relative rounded-xl overflow-hidden border border-line bg-sand">
      <div ref="mapEl" class="h-[300px] w-full" />
      <div v-if="loading" class="absolute inset-0 flex items-center justify-center text-sm text-ink-mute">Caricamento mappa…</div>
      <button
        v-if="!loading"
        type="button"
        class="absolute top-2.5 right-2.5 z-[1000] px-2.5 h-8 rounded-lg bg-white/95 border border-line shadow-sm text-[12px] font-bold text-ink hover:bg-white"
        :aria-pressed="satellite"
        @click="toggleSatellite"
      >{{ satellite ? 'Mappa' : 'Satellite' }}</button>
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
let streetLayer = null
let satelliteLayer = null

const query = ref('')
const results = ref([])
const searching = ref(false)
const searchMsg = ref('')
const pasted = ref('')
const satellite = ref(false)

// area del Molise (con un po' di margine) per non pescare omonimi in altre regioni
const MOLISE_VIEWBOX = '13.85,42.10,15.20,41.35'
let lastSearch = 0

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

const setPoint = (lat, lng, zoom = 17) => {
  const latlng = [round(lat), round(lng)]
  placeMarker(latlng)
  map.setView(latlng, Math.max(map.getZoom(), zoom))
  emit('update', { lat: latlng[0], lng: latlng[1] })
}

// Ricerca con Nominatim (OpenStreetMap): solo su richiesta, al massimo una al secondo
const search = async () => {
  const q = query.value.trim()
  if (!q || !map) return
  const wait = 1100 - (Date.now() - lastSearch)
  if (wait > 0) await new Promise(r => setTimeout(r, wait))
  lastSearch = Date.now()
  searching.value = true
  searchMsg.value = ''
  results.value = []
  try {
    const params = new URLSearchParams({
      q: props.town && !q.toLowerCase().includes(props.town.toLowerCase()) ? `${q}, ${props.town}` : q,
      format: 'jsonv2', limit: '6', countrycodes: 'it', viewbox: MOLISE_VIEWBOX, bounded: '1', 'accept-language': 'it'
    })
    let list = await $fetch(`https://nominatim.openstreetmap.org/search?${params}`)
    if (!list.length && props.town) {
      // seconda prova senza il comune aggiunto
      params.set('q', q)
      list = await $fetch(`https://nominatim.openstreetmap.org/search?${params}`)
    }
    if (list.length === 1) {
      choose(list[0])
    } else if (list.length) {
      results.value = list
    } else {
      searchMsg.value = 'Nessun risultato: le contrade di campagna spesso non sono sulle mappe. Prova la vista satellite e clicca sull\'edificio, oppure incolla le coordinate da Google Maps.'
    }
  } catch {
    searchMsg.value = 'Ricerca non disponibile in questo momento: clicca sulla mappa o incolla le coordinate.'
  } finally {
    searching.value = false
  }
}

const choose = (r) => {
  results.value = []
  setPoint(Number(r.lat), Number(r.lon))
  searchMsg.value = 'Punto spostato sul risultato: controlla con la vista satellite e trascina il segnaposto se serve.'
}

// "41.6748, 14.5768", "41,6748 14,5768" o un link di Google Maps (@lat,lng / !3dlat!4dlng / ?q=lat,lng)
const parseCoords = (text) => {
  const t = String(text || '').trim()
  const patterns = [
    /!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)/,
    /@(-?\d+\.\d+),(-?\d+\.\d+)/,
    /[?&](?:q|query|ll|destination)=(-?\d+\.\d+)(?:,|%2C)\s*(-?\d+\.\d+)/i,
    /^(-?\d{1,2}[.,]\d+)\s*[,;\s]\s*(-?\d{1,3}[.,]\d+)$/
  ]
  for (const re of patterns) {
    const m = t.match(re)
    if (m) {
      const lat = Number(m[1].replace(',', '.'))
      const lng = Number(m[2].replace(',', '.'))
      if (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) return [lat, lng]
    }
  }
  return null
}

const usePasted = () => {
  const c = parseCoords(pasted.value)
  if (!c) {
    searchMsg.value = 'Non riconosco le coordinate: scrivile come 41.67480, 14.57680 oppure incolla il link completo di Google Maps (i link brevi maps.app.goo.gl non contengono le coordinate).'
    return
  }
  if (c[0] < 41 || c[0] > 42.3 || c[1] < 13.6 || c[1] > 15.4) {
    searchMsg.value = 'Attenzione: il punto è fuori dal Molise. Controlla di non aver invertito latitudine e longitudine.'
  } else {
    searchMsg.value = ''
  }
  setPoint(c[0], c[1])
  pasted.value = ''
}

const toggleSatellite = () => {
  if (!map) return
  satellite.value = !satellite.value
  if (satellite.value) {
    map.removeLayer(streetLayer)
    satelliteLayer.addTo(map)
  } else {
    map.removeLayer(satelliteLayer)
    streetLayer.addTo(map)
  }
}

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
  streetLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(map)
  satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Immagini &copy; Esri, Maxar, Earthstar Geographics'
  })
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
  streetLayer = null
  satelliteLayer = null
})
</script>
