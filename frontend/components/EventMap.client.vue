<template>
  <div ref="mapContainer" :class="['w-full rounded-2xl overflow-hidden bg-[#E9E4D8] relative z-0', tall ? 'h-[460px] md:h-[600px]' : 'h-[260px]']" role="img" :aria-label="ariaLabel">
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center text-sm text-ink-mute">Caricamento della mappa…</div>
  </div>
</template>

<script setup>
// Mappa degli eventi: un segnaposto per evento (punto esatto se indicato, altrimenti il centro del comune).
import { getTownCoordinates } from '~/utils/producerCoords'
import { eventWhen, placeLabel } from '~/utils/events'

const props = defineProps({
  events: { type: Array, default: () => [] },
  tall: { type: Boolean, default: false },
  zoom: { type: Number, default: 13 }
})

const mapContainer = ref(null)
const loading = ref(true)
let map = null
let layer = null

const ariaLabel = computed(() => props.events.length === 1
  ? `Mappa: ${placeLabel(props.events[0])}`
  : `Mappa di ${props.events.length} eventi`)

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
    document.head.appendChild(script)
  }
  const wait = setInterval(() => {
    if (window.L) { clearInterval(wait); resolve(window.L) }
  }, 50)
})

const pointOf = (event) => {
  const loc = event.location || {}
  const lat = Number(loc.lat)
  const lng = Number(loc.lng)
  if (loc.lat != null && loc.lng != null && !Number.isNaN(lat) && !Number.isNaN(lng)) return [lat, lng]
  return getTownCoordinates(loc.city || '')
}

const escapeHtml = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))

const draw = async () => {
  if (!mapContainer.value) return
  const L = await loadLeaflet()
  loading.value = false
  if (!map) {
    map = L.map(mapContainer.value, { center: [41.7, 14.6], zoom: 9, scrollWheelZoom: false })
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 18
    }).addTo(map)
  }
  if (layer) layer.remove()
  layer = L.layerGroup().addTo(map)
  const icon = L.divIcon({
    className: '',
    html: '<div style="width:30px;height:30px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);background:#6B1D2F;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>',
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30]
  })
  const points = []
  for (const event of props.events) {
    const pt = pointOf(event)
    if (!pt) continue
    points.push(pt)
    const marker = L.marker(pt, { icon }).addTo(layer)
    if (props.events.length > 1) {
      marker.bindPopup(`
        <div style="font-family:'Plus Jakarta Sans',sans-serif;max-width:220px">
          <strong style="display:block;font-size:13px;color:#1C1917">${escapeHtml(event.title)}</strong>
          <span style="display:block;font-size:11px;color:#78716C;margin-top:2px">${escapeHtml(eventWhen(event)?.label || '')}</span>
          <span style="display:block;font-size:11px;color:#78716C">${escapeHtml(placeLabel(event))}</span>
          <a href="/eventi/${encodeURIComponent(event.slug)}" style="display:inline-block;margin-top:6px;font-size:12px;font-weight:700;color:#6B1D2F">Apri l'evento →</a>
        </div>`)
    }
  }
  map.invalidateSize()
  if (points.length > 1) map.fitBounds(points, { padding: [40, 40], maxZoom: 12 })
  else if (points.length === 1) map.setView(points[0], props.zoom)
}

onMounted(draw)
watch(() => props.events, draw, { deep: true })
onBeforeUnmount(() => { if (map) { map.remove(); map = null } })
</script>
