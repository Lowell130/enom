<template>
  <div :class="bare ? 'overflow-hidden' : 'card overflow-hidden'">
    <div v-if="!bare" class="px-5 py-4 border-b border-line flex items-center justify-between gap-4">
      <div class="flex flex-col">
        <h3 class="font-serif font-bold text-ink text-xl leading-tight">{{ title || 'Mappa delle cantine' }}</h3>
        <p class="text-[13px] text-ink-mute">{{ subtitle || 'Dove si trovano i produttori molisani' }}</p>
      </div>
      <span class="shrink-0 px-2.5 py-1 rounded-full bg-sand-100 text-wine-900 text-xs font-bold">
        {{ validProducers.length }} {{ validProducers.length === 1 ? 'cantina' : 'cantine' }}
      </span>
    </div>

    <div ref="mapContainer" :class="['w-full relative z-0 bg-[#E9E4D8]', tall ? 'h-[480px] md:h-[640px]' : bare ? 'h-[300px]' : 'h-80 sm:h-[420px]']">
      <div v-if="loadingMap" class="absolute inset-0 flex items-center justify-center text-ink-mute text-sm">
        <span>Caricamento della mappa…</span>
      </div>
    </div>
  </div>
</template>

<script setup>

const props = defineProps({
  producers: {
    type: Array,
    default: () => []
  },
  title: String,
  subtitle: String,
  tall: { type: Boolean, default: false },
  // senza intestazione e bordo, per inserirla dentro un altro riquadro
  bare: { type: Boolean, default: false },
  zoom: {
    type: Number,
    default: 9.5
  }
})

const { mediaBase } = useApi()
const { getWhatsAppUrl } = useWhatsApp()

const mapContainer = ref(null)
const loadingMap = ref(true)
let mapInstance = null
let resizeObserver = null

// Complete database of fallback coordinates for Molise municipalities & key wine areas

const validProducers = computed(() => {
  return (props.producers || []).filter(p => p && p.company_name)
})


const loadLeafletAssets = () => {
  return new Promise((resolve) => {
    if (window.L) {
      resolve(window.L)
      return
    }

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
      const interval = setInterval(() => {
        if (window.L) {
          clearInterval(interval)
          resolve(window.L)
        }
      }, 50)
    }
  })
}

const initMap = async () => {
  if (!mapContainer.value) return
  const L = await loadLeafletAssets()
  loadingMap.value = false

  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }

  const producersList = validProducers.value
  const coordsList = producersList.map((p, idx) => getProducerCoordinatesSync(p, idx))

  let center = [41.62, 14.60]
  if (coordsList.length === 1) {
    center = coordsList[0]
  }

  mapInstance = L.map(mapContainer.value, {
    center: center,
    zoom: coordsList.length === 1 ? 13 : props.zoom,
    zoomControl: true,
    scrollWheelZoom: false
  })

  // Standard OpenStreetMap Tile Layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | EnotecaMolise',
    maxZoom: 18
  }).addTo(mapInstance)

  // Sleek Monochromatic Burgundy Pin SVG
  const createCustomIcon = () => {
    return L.divIcon({
      className: 'custom-wine-pin',
      html: `
        <div style="
          background-color: #6B1D2F;
          color: #FFFFFF;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: 2px solid #FFFFFF;
          box-shadow: 0 4px 12px rgba(0,0,0,0.25);
          display: flex;
          align-items: center;
          justify-content: center;
        ">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M8 22h8"></path>
            <path d="M12 15v7"></path>
            <path d="M12 15a7 7 0 0 0 7-7H5a7 7 0 0 0 7 7z"></path>
            <path d="M5 8V3h14v5"></path>
          </svg>
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 32],
      popupAnchor: [0, -32]
    })
  }

  const bounds = []

  producersList.forEach((producer, idx) => {
    const coords = coordsList[idx]
    bounds.push(coords)

    const marker = L.marker(coords, { icon: createCustomIcon() }).addTo(mapInstance)

    const logo = producer.logo_url 
      ? (producer.logo_url.startsWith('http') ? producer.logo_url : `${mediaBase}${producer.logo_url}`)
      : 'https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=150&q=80'

    const waUrl = getWhatsAppUrl({
      number: producer.contacts?.whatsapp_number,
      companyName: producer.company_name
    })

    const streetStr = producer.address?.street ? `${producer.address.street}, ` : ''
    const zipStr = producer.address?.zip_code ? `${producer.address.zip_code} ` : ''
    const cityStr = producer.address?.city || 'Molise'
    const provStr = producer.address?.province || 'CB'

    const popupHtml = `
      <div style="font-family: 'Plus Jakarta Sans', sans-serif; padding: 4px; max-width: 240px;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
          <img src="${logo}" style="width: 40px; height: 40px; border-radius: 6px; object-fit: cover; border: 1px solid #E7E5E4;" />
          <div>
            <strong style="font-size: 13px; color: #1C1917; display: block; leading-height: 1.2;">${producer.company_name}</strong>
            <span style="font-size: 11px; color: #78716C; display: block; margin-top: 2px;">
              ${streetStr}${zipStr}${cityStr} (${provStr})
            </span>
          </div>
        </div>
        <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 6px;">
          <a href="/produttori/${producer.slug}" style="display: block; text-align: center; background-color: #6B1D2F; color: #FFF; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; text-decoration: none;">
            Vedi Scheda Cantina
          </a>
          ${waUrl !== '#' ? `
            <a href="${waUrl}" target="_blank" style="display: block; text-align: center; background-color: #047857; color: #FFF; padding: 6px 12px; border-radius: 6px; font-size: 11px; font-weight: 600; text-decoration: none;">
              Contatta su WhatsApp
            </a>
          ` : ''}
        </div>
      </div>
    `

    marker.bindPopup(popupHtml)

    // Open popup automatically if single producer view
    if (producersList.length === 1) {
      marker.openPopup()
    }
  })

  if (producersList.length > 1 && bounds.length > 0) {
    mapInstance.fitBounds(bounds, { padding: [40, 40] })
  }

  // Ensure Leaflet resizes correctly after rendering or view mode switches
  nextTick(() => {
    setTimeout(() => {
      if (mapInstance) {
        mapInstance.invalidateSize()
      }
    }, 200)
  })
}

// Handle container resizing (e.g. view mode toggles)
const handleResize = () => {
  if (mapInstance) {
    mapInstance.invalidateSize()
  }
}

onMounted(() => {
  initMap()

  window.addEventListener('resize', handleResize)

  if (window.ResizeObserver && mapContainer.value) {
    resizeObserver = new ResizeObserver(() => {
      if (mapInstance) {
        mapInstance.invalidateSize()
      }
    })
    resizeObserver.observe(mapContainer.value)
  }
})

watch(() => props.producers, () => {
  initMap()
}, { deep: true })

// Come componente .client il contenuto viene disegnato dopo il primo mount:
// se in onMounted il contenitore non esiste ancora, la mappa parte appena compare.
watch(mapContainer, (el) => {
  if (el && !mapInstance) initMap()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>

<style>
/* Leaflet Popup & Pin Overrides */
.custom-wine-pin {
  background: transparent !important;
  border: none !important;
}
.leaflet-popup-content-wrapper {
  border-radius: 8px !important;
  padding: 6px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
  border: 1px solid #E7E5E4 !important;
}
.leaflet-container {
  font-family: inherit !important;
}
</style>
