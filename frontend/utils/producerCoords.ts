// Coordinate delle cantine: usate dalla mappa e dal calcolo delle cantine vicine.
const cityCoordinates: Record<string, [number, number]> = {
  // Campobasso Province
  'campobasso': [41.5603, 14.6626],
  'san felice del molise': [41.8892, 14.7025],
  'acquaviva collecroce': [41.8667, 14.7478],
  'san biase': [41.7139, 14.5917],
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

const parseCoord = (val: any): number | null => {
  if (typeof val === 'number' && !isNaN(val)) return val
  if (typeof val === 'string' && val.trim()) {
    const num = parseFloat(val.replace(',', '.').trim())
    if (!isNaN(num) && num !== 0) return num
  }
  return null
}

// Instant, synchronous coordinate resolution (0 network latency)
export const getProducerCoordinatesSync = (producer: any, index = 0): [number, number] => {
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

// Coordinate di un comune (nome come "San Martino In Pensilis"), se presente nell'elenco
export const getTownCoordinates = (name: string): [number, number] | null => {
  const key = String(name || '').toLowerCase().replace(/\s+/g, ' ').trim()
  if (!key) return null
  if (cityCoordinates[key]) return cityCoordinates[key]
  for (const [k, v] of Object.entries(cityCoordinates)) {
    if (key.includes(k) || k.includes(key)) return v
  }
  return null
}
