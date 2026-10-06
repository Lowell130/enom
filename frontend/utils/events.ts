// Eventi: etichette e date in italiano. Le date arrivano dal server come ora italiana senza fuso
// ("2026-10-17T18:00:00"): si leggono a mano per non subire spostamenti di fuso orario.

export const EVENT_TYPES: Record<string, string> = {
  DEGUSTAZIONE: 'Degustazione',
  VISITA: 'Visita in cantina',
  CENA: 'Cena e abbinamenti',
  FIERA: 'Fiera e festival',
  CORSO: 'Corso',
  VENDEMMIA: 'Vendemmia',
  ALTRO: 'Altro'
}

const MONTHS = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']
const MONTHS_SHORT = ['gen', 'feb', 'mar', 'apr', 'mag', 'giu', 'lug', 'ago', 'set', 'ott', 'nov', 'dic']
const DAYS_SHORT = ['dom', 'lun', 'mar', 'mer', 'gio', 'ven', 'sab']

export interface LocalParts { y: number; m: number; d: number; h: number; min: number }

export const parseLocal = (value?: string | null): LocalParts | null => {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}))?/)
  if (!match) return null
  return { y: +match[1], m: +match[2], d: +match[3], h: +(match[4] || 0), min: +(match[5] || 0) }
}

export const toDate = (p: LocalParts) => new Date(p.y, p.m - 1, p.d, p.h, p.min)

/** Riquadro data delle schede: { day: '17', month: 'ott', weekday: 'sab' } */
export const dateBadge = (value?: string | null) => {
  const p = parseLocal(value)
  if (!p) return { day: '', month: '', weekday: '' }
  return { day: String(p.d), month: MONTHS_SHORT[p.m - 1], weekday: DAYS_SHORT[toDate(p).getDay()] }
}

export const monthTitle = (value?: string | null) => {
  const p = parseLocal(value)
  if (!p) return ''
  const name = MONTHS[p.m - 1]
  return `${name.charAt(0).toUpperCase()}${name.slice(1)} ${p.y}`
}

export const priceLabel = (event: any) =>
  event?.price_type === 'PAID' ? (event.price_text || 'A pagamento') : 'Gratuito'

export const placeLabel = (event: any) => {
  const loc = event?.location || {}
  const city = loc.city ? `${loc.city}${loc.province ? ` (${loc.province})` : ''}` : ''
  if (loc.name && city && !event?.use_producer_address) return `${loc.name}, ${city}`
  return city || loc.name || 'Molise'
}

/** Prossima data utile (o la prima, per gli eventi passati). */
export const eventWhen = (event: any) => event?.next_date || event?.dates?.[0] || null

/** "2026-10-17" e "18:00" -> "2026-10-17T18:00" per il server. */
export const joinLocal = (date: string, time: string) => (date ? `${date}T${time || '00:00'}` : '')

export const splitLocal = (value?: string | null) => {
  const p = parseLocal(value)
  if (!p) return { date: '', time: '' }
  const pad = (n: number) => String(n).padStart(2, '0')
  return { date: `${p.y}-${pad(p.m)}-${pad(p.d)}`, time: `${pad(p.h)}:${pad(p.min)}` }
}
