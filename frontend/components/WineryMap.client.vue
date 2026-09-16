<template>
  <div class="bg-white rounded-xl border border-stone-200/80 shadow-xs overflow-hidden">
    <!-- Header -->
    <div class="p-4 bg-stone-50 border-b border-stone-200/60 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-8 h-8 rounded-lg bg-wine-800 text-stone-100 flex items-center justify-center font-bold text-xs shadow-xs">
          <MapPin class="w-4 h-4" />
        </div>
        <div>
          <h3 class="font-serif font-bold text-stone-900 text-base leading-tight">
            {{ title || 'Mappa delle Cantine' }}
          </h3>
          <p class="text-xs text-stone-500 font-light">
            {{ subtitle || 'Localizzazione geografica dei produttori molisani' }}
          </p>
        </div>
      </div>
      <span class="px-2.5 py-1 text-xs font-semibold bg-wine-50 text-wine-900 rounded-md border border-wine-100">
        {{ validProducers.length }} {{ validProducers.length === 1 ? 'Cantina' : 'Cantine' }}
      </span>
    </div>

    <!-- Map Container -->
    <div ref="mapContainer" class="w-full h-80 sm:h-[420px] relative z-0 bg-stone-100 min-h-[320px]">
      <div v-if="loadingMap" class="absolute inset-0 flex items-center justify-center bg-stone-100 text-stone-400 text-xs font-medium space-x-2">
        <span>Caricamento mappa interattiva...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { MapPin } from 'lucide-vue-next'

const props = defineProps({
  producers: {
    type: Array,
    default: () => []
  },
  title: String,
  subtitle: String,
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
const cityCoordinates = {
  // Campobasso Province
  'campobasso': [41.5603, 14.6626],
  'castropignano': [41.6748, 14.5768],
  'termoli': [41.9961, 14.9922],
  'larino': [41.8014, 14.9108],
  'campomarino': [41.9564, 15.0342],
  'san martino in pensilis': [41.8708, 15.0125],
  'guglionesi': [41.9161, 14.9167],
  'ururi': [41.8211, 15.0175],
  'petacciato': [42.0125, 14.8603],
  'montenero di bisaccia': [41.9567, 14.7806],
  'portocannone': [41.9167, 15.0083],
  'montecilfone': [41.9028, 14.8378],
  'mafalda': [41.9444, 14.7167],
  'san giacomo degli schiavoni': [41.9617, 14.9472],
  'ferrazzano': [41.5301, 14.6739],
  'gildone': [41.5122, 14.7397],
  'bojano': [41.4828, 14.4750],
  'boiano': [41.4828, 14.4750],
  'trivento': [41.7765, 14.5516],
  'ripalimosani': [41.6111, 14.6611],
  'oratino': [41.5833, 14.5833],
  'torella del sannio': [41.6375, 14.5194],
  'fossalto': [41.6706, 14.5458],
  'busso': [41.5544, 14.5603],
  'baranello': [41.5283, 14.5583],
  'colle d\'anchise': [41.5078, 14.5175],
  'spinete': [41.5458, 14.4842],
  'sepino': [41.4117, 14.6192],
  'vinchiaturo': [41.4950, 14.5883],
  'campochiaro': [41.4447, 14.5061],
  'petrella tifernina': [41.6917, 14.6958],
  'montagano': [41.6444, 14.6722],
  'matrice': [41.6167, 14.7167],
  'riccia': [41.4833, 14.8333],
  'jelsi': [41.5167, 14.8000],
  'gambatesa': [41.5086, 14.9081],
  'campodipietra': [41.5583, 14.7472],
  'toro': [41.5722, 14.7639],
  'monacilioni': [41.6139, 14.8111],
  'sant\'elia a pianisi': [41.6222, 14.8778],
  'bonefro': [41.7056, 14.9333],
  'casacalenda': [41.7389, 14.8472],
  'rotello': [41.7472, 15.0028],
  'morrone del sannio': [41.7139, 14.7778],
  'ripabottoni': [41.6917, 14.8111],
  'guardialfiera': [41.8028, 14.7972],
  'palata': [41.8889, 14.7889],

  // Isernia Province
  'isernia': [41.5960, 14.2345],
  'venafro': [41.4839, 14.0440],
  'agnone': [41.8105, 14.3779],
  'monteroduni': [41.5211, 14.1756],
  'roccamandolfi': [41.4988, 14.3541],
  'capracotta': [41.8344, 14.2678],
  'frosolone': [41.6044, 14.4464],
  'carovilli': [41.7139, 14.3000],
  'pesche': [41.6111, 14.2806],
  'miranda': [41.6444, 14.2444],
  'pettoranello del molise': [41.5794, 14.2803],
  'macchia d\'isernia': [41.5625, 14.1625],
  'scapoli': [41.6167, 14.0500],
  'colli a volturno': [41.6000, 14.1000],
  'cerro al volturno': [41.6500, 14.1000],
  'castel san vincenzo': [41.6542, 14.0639],
  'rocchetta a volturno': [41.6250, 14.0889],
  'fornelli': [41.6056, 14.1417],
  'belmonte del sannio': [41.8333, 14.4167],
  'poggio sannita': [41.7778, 14.4111],
  'vastogirardi': [41.7778, 14.2667],
  'bagnoli del trigno': [41.7028, 14.4569],
  'duronia': [41.6625, 14.4639],
  'cantalupo nel sannio': [41.5167, 14.3833],
  'santa maria del molise': [41.5528, 14.3667],
  'macchiagodena': [41.5611, 14.4056],
  'carpinone': [41.5917, 14.3222],
  'pescolanciano': [41.6778, 14.3361]
}

const validProducers = computed(() => {
  return (props.producers || []).filter(p => p && p.company_name)
})

const parseCoord = (val) => {
  if (typeof val === 'number' && !isNaN(val)) return val
  if (typeof val === 'string' && val.trim()) {
    const num = parseFloat(val.replace(',', '.').trim())
    if (!isNaN(num) && num !== 0) return num
  }
  return null
}

// Instant, synchronous coordinate resolution (0 network latency)
const getProducerCoordinatesSync = (producer, index = 0) => {
  const company = (producer.company_name || '').toLowerCase()
  const street = (producer.address?.street || '').toLowerCase()
  const city = (producer.address?.city || '').toLowerCase().trim()

  // 1. Explicit geo_coordinates in DB
  const geo = producer.address?.geo_coordinates || producer.geo_coordinates
  if (geo) {
    const lat = parseCoord(geo.lat)
    const lng = parseCoord(geo.lng)
    if (lat !== null && lng !== null) {
      return [lat, lng]
    }
  }
  if (producer.latitude && producer.longitude) {
    const lat = parseCoord(producer.latitude)
    const lng = parseCoord(producer.longitude)
    if (lat !== null && lng !== null) {
      return [lat, lng]
    }
  }

  // 2. Exact company overrides for official cantine
  if (company.includes('colle tinto') || street.includes('iannaricciola')) return [41.6147818, 14.5462307]
  if (company.includes('colloredo')) return [41.8874849, 15.0733404]
  if (company.includes('giulio')) return [41.8874849, 15.0733405]
  if (company.includes('herero')) return [41.5494343, 14.6481744]
  if (company.includes('valerio')) return [41.53885, 14.1560701]
  if (company.includes('zenone')) return [41.9821036, 14.7844206]
  if (company.includes('norante') || company.includes('majo')) return [41.9107052, 15.0961883]
  if (company.includes('catabbo')) return [41.8785571, 15.0263503]
  if (company.includes('cipressi')) return [41.871341, 14.6886823]
  if (company.includes('uva')) return [41.8054757, 14.9428415]
  if (company.includes('vinica') || company.includes('agricolavinica') || company.includes('agricovinica')) return [41.6114758, 14.6820045]

  // 3. Match city in local database
  if (city && cityCoordinates[city]) {
    const base = cityCoordinates[city]
    const offsetLat = ((index % 4) - 1.5) * 0.003
    const offsetLng = (Math.floor(index / 4) % 4 - 1.5) * 0.003
    return [base[0] + offsetLat, base[1] + offsetLng]
  }

  // 4. Match city partial substring
  for (const [key, coords] of Object.entries(cityCoordinates)) {
    if (city.includes(key) || key.includes(city)) {
      const offsetLat = ((index % 4) - 1.5) * 0.003
      const offsetLng = (Math.floor(index / 4) % 4 - 1.5) * 0.003
      return [coords[0] + offsetLat, coords[1] + offsetLng]
    }
  }

  // 5. Default Molise center fallback with spread offset
  const offsetLat = ((index % 5) - 2) * 0.012
  const offsetLng = (Math.floor(index / 5) % 5 - 2) * 0.015
  return [41.62 + offsetLat, 14.60 + offsetLng]
}

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
