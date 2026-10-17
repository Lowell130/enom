// robots.txt del sito pubblico: tutto visibile tranne l'area riservata, con il link alla sitemap.
// Privacy, cookie e chi siamo NON sono bloccate qui apposta: Google deve poterle aprire
// per leggere il "noindex" che le tiene fuori dai risultati.
export default defineEventHandler((event) => {
  const config = useRuntimeConfig()
  const site = String(config.public.siteUrl || 'https://www.enotecamolise.it').replace(/\/+$/, '')
  setHeader(event, 'Content-Type', 'text/plain; charset=utf-8')
  return [
    'User-agent: *',
    'Disallow: /dashboard',
    'Disallow: /login',
    'Disallow: /attiva-account',
    'Disallow: /password-dimenticata',
    'Disallow: /reimposta-password',
    '',
    `Sitemap: ${site}/sitemap.xml`,
    ''
  ].join('\n')
})
