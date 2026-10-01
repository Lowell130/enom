<template>
  <div ref="mapContainer" class="w-full h-[420px] md:h-[520px] rounded-2xl overflow-hidden bg-[#E9E4D8] relative z-0" role="img" :aria-label="ariaLabel">
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center text-sm text-ink-mute">Caricamento della mappa…</div>
  </div>
</template>

<script setup>
// Mappa dei comuni di produzione: un cerchio per comune, grande quanto il numero di vini.
const props = defineProps({
  towns: { type: Array, default: () => [] }
})
const emit = defineEmits(['select'])

const mapContainer = ref(null)
const loading = ref(true)
let map = null
let layer = null
let points = []
let resizeObserver = null

// inquadra tutti i comuni; va ripetuto quando il riquadro cambia dimensione
const fit = () => {
  if (!map) return
  map.invalidateSize()
  if (points.length > 1) map.fitBounds(points, { padding: [40, 40], maxZoom: 10 })
  else if (points.length === 1) map.setView(points[0], 11)
}

const ariaLabel = computed(() => `Mappa dei comuni di produzione: ${props.towns.slice(0, 5).map(t => `${t.city} ${t.count} vini`).join(', ')}`)

const loadLeaflet = () => new Promise((resolve) => {
  if (window.L) return resolve(window.L)
  if (!document.getElementById('leaflet-css')) {
    const link = document.createElement('link')
    link.id = 'leaflet-css'
    link.rel = 'stylesheet'
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
    document.head.appendChild(link)
  }
  let script = document.getElementById('leaflet-js')
  if (!script) {
    script = document.createElement('script')
    script.id = 'leaflet-js'
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
    document.head.appendChild(script)
  }
  const wait = setInterval(() => {
    if (window.L) { clearInterval(wait); resolve(window.L) }
  }, 50)
})

const townPoint = (town) => {
  const own = getTownCoordinates(town.city)
  if (own) return own
  const producer = (town.producers || [])[0]
  return producer ? getProducerCoordinatesSync(producer, 0) : null
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

  const max = Math.max(1, ...props.towns.map(t => t.count))
  points = []
  for (const town of props.towns) {
    const pt = townPoint(town)
    if (!pt) continue
    points.push(pt)
    // area del cerchio proporzionale ai vini
    const radius = 6 + Math.sqrt(town.count / max) * 20
    const marker = L.circleMarker(pt, {
      radius,
      color: '#FFFFFF',
      weight: 2,
      fillColor: '#9B2F4A',
      fillOpacity: 0.72
    }).addTo(layer)
    const producers = (town.producers || []).map(p => escapeHtml(p.company_name)).join(', ')
    marker.bindTooltip(
      `<strong>${escapeHtml(town.city)}</strong><br>${town.count} ${town.count === 1 ? 'vino' : 'vini'}${producers ? `<br><span style="color:#6E625A">${producers}</span>` : ''}`,
      { direction: 'top', offset: [0, -radius], className: 'town-tooltip' }
    )
    marker.on('click', () => emit('select', town))
  }
  fit()
  if (!resizeObserver && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => fit())
    resizeObserver.observe(mapContainer.value)
  }
}

onMounted(() => { draw() })
watch(mapContainer, (el) => { if (el && !map) draw() })
watch(() => props.towns, () => { draw() })

onUnmounted(() => {
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null }
  if (map) { map.remove(); map = null }
})
</script>

<style>
.town-tooltip {
  font-family: 'Plus Jakarta Sans', sans-serif;
  font-size: 13px;
  border-radius: 8px;
  border: 1px solid #ECE4DA;
  box-shadow: 0 4px 16px rgba(42, 8, 18, 0.12);
}
</style>
