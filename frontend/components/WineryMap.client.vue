<template>
  <div class="bg-white rounded-3xl border border-stone-200/70 shadow-xs overflow-hidden">
    <div class="p-4 bg-stone-50 border-b border-stone-200/60 flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <div class="w-8 h-8 rounded-xl bg-wine-800 text-amber-200 flex items-center justify-center font-bold text-xs shadow-xs">
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
      <span class="px-2.5 py-1 text-xs font-semibold bg-wine-50 text-wine-900 rounded-full border border-wine-100">
        {{ validProducers.length }} {{ validProducers.length === 1 ? 'Cantina' : 'Cantine' }}
      </span>
    </div>

    <!-- Map Container -->
    <div ref="mapContainer" class="w-full h-80 sm:h-96 relative z-0 bg-stone-100">
      <div v-if="loadingMap" class="absolute inset-0 flex items-center justify-center bg-stone-100 text-stone-400 text-xs font-medium">
        Caricamento mappa interattiva...
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

// Database of fallback coordinates for Molise towns
const cityCoordinates = {
  'castropignano': [41.6748, 14.5768],
  'campobasso': [41.5603, 14.6626],
  'isernia': [41.5960, 14.2345],
  'termoli': [41.9961, 14.9922],
  'larino': [41.8014, 14.9108],
  'agnone': [41.8105, 14.3779],
  'venafro': [41.4839, 14.0440],
  'bojano': [41.4828, 14.4750],
  'ferrazzano': [41.5301, 14.6739],
  'gildone': [41.5122, 14.7397],
  'san martino in pensilis': [41.8708, 15.0125],
  'guglionesi': [41.9161, 14.9167],
  'ururi': [41.8211, 15.0175],
  'monteroduni': [41.5211, 14.1756],
  'roccamandolfi': [41.4988, 14.3541],
  'capracotta': [41.8344, 14.2678],
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
  'campomarino': [41.9564, 15.0342],
  'petacciato': [42.0125, 14.8603],
  'montenero di bisaccia': [41.9567, 14.7806],
  'portocannone': [41.9167, 15.0083],
  'montecilfone': [41.9028, 14.8378],
  'mafalda': [41.9444, 14.7167],
  'san giacomo degli schiavoni': [41.9617, 14.9472],
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
  'duronia': [41.6625, 14.4639]
}

const geocodeCache = reactive({})

const validProducers = computed(() => {
  return (props.producers || []).filter(p => p && p.company_name)
})

const getProducerCoordinates = async (producer, index = 0) => {
  const company = (producer.company_name || '').toLowerCase()
  const street = (producer.address?.street || '').trim()
  const city = (producer.address?.city || '').trim()
  const zip = (producer.address?.zip_code || producer.zip_code || '').trim()

  // 1. Specific Winery & Contrada Exact Override (Cantina Il Colle Tinto, Contrada Iannaricciola 27, Castropignano)
  if (company.includes('colle tinto') || street.toLowerCase().includes('iannaricciola')) {
    return [41.6748, 14.5768]
  }

  // 2. Explicit geo_coordinates lat/lng in DB
  const geo = producer.address?.geo_coordinates || producer.geo_coordinates
  if (geo && typeof geo.lat === 'number' && typeof geo.lng === 'number' && geo.lat !== 0 && geo.lng !== 0) {
    return [geo.lat, geo.lng]
  }
  if (producer.latitude && producer.longitude) {
    const lat = parseFloat(producer.latitude)
    const lng = parseFloat(producer.longitude)
    if (!isNaN(lat) && !isNaN(lng) && lat !== 0) {
      return [lat, lng]
    }
  }

  const cacheKey = `${company}_${street}_${zip}_${city}`
  if (geocodeCache[cacheKey]) {
    return geocodeCache[cacheKey]
  }

  // 3. Try Nominatim Live Search by Company Name + City
  if (company && city) {
    try {
      const q = `${producer.company_name}, ${city}, Italy`
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`)
      const data = await res.json()
      if (data && data.length > 0) {
        const coords = [parseFloat(data[0].lat), parseFloat(data[0].lon)]
        geocodeCache[cacheKey] = coords
        return coords
      }
    } catch (e) {}
  }

  // 4. Try Nominatim Live Search with full address (Street + ZIP + City)
  if (street || zip) {
    try {
      const q = [street, zip, city, 'Molise', 'Italy'].filter(Boolean).join(', ')
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`)
      const data = await res.json()
      if (data && data.length > 0) {
        const coords = [parseFloat(data[0].lat), parseFloat(data[0].lon)]
        geocodeCache[cacheKey] = coords
        return coords
      }
    } catch (e) {}
  }

  // 5. Try Nominatim Search without street number (e.g., "Contrada Iannaricciola, Castropignano")
  if (street && city) {
    try {
      const cleanStreet = street.replace(/,\s*\d+/g, '').trim()
      const q = `${cleanStreet}, ${city}, Italy`
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(q)}`)
      const data = await res.json()
      if (data && data.length > 0) {
        const coords = [parseFloat(data[0].lat), parseFloat(data[0].lon)]
        geocodeCache[cacheKey] = coords
        return coords
      }
    } catch (e) {}
  }

  // 6. Local static city table lookup
  const cityKey = city.toLowerCase()
  if (cityKey && cityCoordinates[cityKey]) {
    const base = cityCoordinates[cityKey]
    const offsetLat = (index % 3 - 1) * 0.003
    const offsetLng = (Math.floor(index / 3) % 3 - 1) * 0.003
    const coords = [base[0] + offsetLat, base[1] + offsetLng]
    geocodeCache[cacheKey] = coords
    return coords
  }

  // 7. Default Molise center fallback
  const offsetLat = (index * 0.012) % 0.15 - 0.075
  const offsetLng = (index * 0.018) % 0.20 - 0.10
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
  const coordsList = await Promise.all(producersList.map((p, idx) => getProducerCoordinates(p, idx)))

  let center = [41.62, 14.60]
  if (coordsList.length === 1) {
    center = coordsList[0]
  }

  mapInstance = L.map(mapContainer.value, {
    center: center,
    zoom: coordsList.length === 1 ? 13 : props.zoom,
    zoomControl: true
  })

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> | EnotecaMolise.it',
    maxZoom: 18
  }).addTo(mapInstance)

  const createCustomIcon = () => {
    return L.divIcon({
      className: 'custom-wine-pin',
      html: `
        <div style="
          background-color: #6B1D2F;
          color: #FFF;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          border: 2px solid #FFF;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          font-size: 14px;
        ">
          🍷
        </div>
      `,
      iconSize: [32, 32],
      iconAnchor: [16, 16],
      popupAnchor: [0, -16]
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

    const popupHtml = `
      <div style="font-family: 'Plus Jakarta Sans', sans-serif; padding: 4px; max-width: 230px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
          <img src="${logo}" style="width: 38px; height: 38px; border-radius: 8px; object-fit: cover; border: 1px solid #E7E5E4;" />
          <div>
            <strong style="font-size: 14px; color: #1C1917; display: block; line-height: 1.2;">${producer.company_name}</strong>
            <span style="font-size: 11px; color: #78716C; display: block; margin-top: 2px;">📍 ${streetStr}${zipStr}${producer.address?.city || 'Molise'} (${producer.address?.province || 'CB'})</span>
          </div>
        </div>
        <div style="margin-top: 8px; display: flex; flex-direction: column; gap: 4px;">
          <a href="/produttori/${producer.slug}" style="display: block; text-align: center; background-color: #6B1D2F; color: #FFF; padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: bold; text-decoration: none;">
            Vedi Scheda Cantina
          </a>
          ${waUrl !== '#' ? `
            <a href="${waUrl}" target="_blank" style="display: block; text-align: center; background-color: #047857; color: #FFF; padding: 6px 12px; border-radius: 8px; font-size: 11px; font-weight: bold; text-decoration: none;">
              💬 WhatsApp Diretto
            </a>
          ` : ''}
        </div>
      </div>
    `

    marker.bindPopup(popupHtml)
  })

  if (producersList.length > 1 && bounds.length > 0) {
    mapInstance.fitBounds(bounds, { padding: [40, 40] })
  }
}

onMounted(() => {
  initMap()
})

watch(() => props.producers, () => {
  initMap()
}, { deep: true })

onUnmounted(() => {
  if (mapInstance) {
    mapInstance.remove()
    mapInstance = null
  }
})
</script>
