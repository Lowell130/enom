// Dati di presentazione comuni a card e pagina della cantina
const ARTICLES = new Set(['il', 'lo', 'la', 'le', 'i', 'gli'])
const PREPOSITIONS = new Set(['di', 'd', 'del', 'della', 'dei', 'delle', 'e', 'ed'])
// foto generiche inserite dal seed: vengono sostituite dalla copertina illustrata (CoverArt)
const SEED_COVERS = ['photo-1506377247377', 'photo-1560493676-04071c5f467b']
const TONES = ['#C9B79E', '#B7AE92', '#A9B19D', '#C4AF97', '#B2B3A0', '#BFA992', '#BDB096', '#AEB29A']

export const useProducer = () => {
  const { mediaBase } = useApi()

  const mediaUrl = (url?: string) => {
    if (!url) return ''
    return url.startsWith('http') ? url : `${mediaBase}${url}`
  }

  // senza copertina propria (o con una foto generica del seed) restituisce '': la pagina mostra CoverArt
  const coverUrl = (producer: any) => {
    const url = producer?.cover_image_url || ''
    if (!url || SEED_COVERS.some(id => url.includes(id))) return ''
    return mediaUrl(url)
  }

  const logoUrl = (producer: any) => mediaUrl(producer?.logo_url || '')

  const initials = (name?: string) => {
    const words = (text: string) => text
      .split(/[\s'’-]+/)
      .filter((w, i) => w && !ARTICLES.has(w.toLowerCase()) && !(i > 0 && PREPOSITIONS.has(w.toLowerCase())))
    const full = String(name || '').trim()
    let list = words(full.replace(/^(cantina|cantine|azienda agricola)\s+/i, ''))
    if (list.length < 2) {
      const all = words(full)
      list = all.length >= 2 ? [all[0], list[0] || all[1]] : all
    }
    return ((list[0]?.[0] || '') + (list[1]?.[0] || '')).toUpperCase() || 'EM'
  }

  const tone = (key?: string) => {
    let h = 0
    for (const ch of String(key || '')) h = (h * 31 + ch.charCodeAt(0)) >>> 0
    return TONES[h % TONES.length]
  }

  const place = (producer: any) => {
    const city = producer?.address?.city
    const prov = producer?.address?.province
    if (!city) return 'Molise'
    return prov ? `${city} (${prov})` : city
  }

  const countLabel = (n?: number) => {
    if (!n) return 'Vini in arrivo'
    return `${n} ${n === 1 ? 'vino' : 'vini'}`
  }

  const websiteUrl = (site?: string) => {
    if (!site) return ''
    return /^https?:\/\//i.test(site) ? site : `https://${site}`
  }

  const socialUrl = (handleOrUrl: string, platform: 'instagram' | 'facebook') => {
    if (!handleOrUrl) return ''
    if (handleOrUrl.startsWith('http')) return handleOrUrl
    const clean = handleOrUrl.replace('@', '')
    return platform === 'instagram' ? `https://instagram.com/${clean}` : `https://facebook.com/${clean}`
  }

  return { mediaUrl, coverUrl, logoUrl, initials, tone, place, countLabel, websiteUrl, socialUrl }
}
