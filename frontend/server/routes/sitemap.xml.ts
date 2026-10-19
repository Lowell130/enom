// Sitemap per Google Search Console: pagine principali, vini pubblicati, cantine approvate
// ed eventi in programma. Si rigenera da sola (cache di un'ora), non va aggiornata a mano.
// Privacy, cookie, chi siamo e area riservata restano fuori: non devono essere indicizzate.

const STATIC_PAGES = [
  { path: '/', priority: '1.0', changefreq: 'daily' },
  { path: '/vini', priority: '0.9', changefreq: 'daily' },
  { path: '/produttori', priority: '0.9', changefreq: 'weekly' },
  { path: '/eventi', priority: '0.8', changefreq: 'daily' },
  { path: '/report', priority: '0.6', changefreq: 'weekly' },
  { path: '/contatti', priority: '0.4', changefreq: 'yearly' }
]

const xmlEscape = (s: string) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&apos;')

const isoDate = (v: unknown) => {
  if (!v) return ''
  const d = new Date(String(v).endsWith('Z') || String(v).includes('+') ? String(v) : String(v) + 'Z')
  return isNaN(d.getTime()) ? '' : d.toISOString().slice(0, 10)
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const site = String(config.public.siteUrl || 'https://www.enotecamolise.it').replace(/\/+$/, '')
  const api = String(config.public.apiBase).replace(/\/+$/, '')

  const get = (path: string) => $fetch<any[]>(`${api}${path}`, { timeout: 15000 }).catch(() => [])
  const [products, producers, events] = await Promise.all([
    get('/products?limit=1000'),
    get('/producers'),
    get('/events?limit=500')
  ])

  type Entry = { loc: string, lastmod?: string, changefreq?: string, priority?: string }
  const entries: Entry[] = STATIC_PAGES.map(p => ({ loc: site + p.path, changefreq: p.changefreq, priority: p.priority }))

  for (const p of Array.isArray(producers) ? producers : []) {
    if (p?.slug && (p.status ?? 'APPROVED') === 'APPROVED') {
      entries.push({ loc: `${site}/produttori/${encodeURIComponent(p.slug)}`, lastmod: isoDate(p.updated_at), changefreq: 'weekly', priority: '0.8' })
    }
  }
  for (const w of Array.isArray(products) ? products : []) {
    if (w?.slug && (w.status ?? 'PUBLISHED') === 'PUBLISHED') {
      entries.push({ loc: `${site}/vini/${encodeURIComponent(w.slug)}`, lastmod: isoDate(w.updated_at), changefreq: 'monthly', priority: '0.7' })
    }
  }
  for (const e of Array.isArray(events) ? events : []) {
    if (e?.slug) {
      entries.push({ loc: `${site}/eventi/${encodeURIComponent(e.slug)}`, lastmod: isoDate(e.updated_at), changefreq: 'weekly', priority: '0.6' })
    }
  }

  const seen = new Set<string>()
  const body = entries
    .filter(e => (seen.has(e.loc) ? false : (seen.add(e.loc), true)))
    .map(e => [
      '  <url>',
      `    <loc>${xmlEscape(e.loc)}</loc>`,
      e.lastmod ? `    <lastmod>${e.lastmod}</lastmod>` : '',
      e.changefreq ? `    <changefreq>${e.changefreq}</changefreq>` : '',
      e.priority ? `    <priority>${e.priority}</priority>` : '',
      '  </url>'
    ].filter(Boolean).join('\n'))
    .join('\n')

  setHeader(event, 'Content-Type', 'application/xml; charset=utf-8')
  setHeader(event, 'Cache-Control', 'public, max-age=0, s-maxage=3600, stale-while-revalidate=86400')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`
})
