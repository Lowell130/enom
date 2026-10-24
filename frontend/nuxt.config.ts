// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2026-09-09',
  devtools: { enabled: false },
  modules: [
    '@nuxtjs/tailwindcss',
    '@pinia/nuxt',
  ],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000/api/v1',
      mediaBase: process.env.NUXT_PUBLIC_MEDIA_BASE || 'http://127.0.0.1:8000',
      // indirizzo pubblico del sito, usato da sitemap.xml e robots.txt
      siteUrl: process.env.NUXT_PUBLIC_SITE_URL || 'https://www.enotecamolise.it'
    }
  },
  // pagine con i dati del gestore o riservate: fuori dai motori di ricerca anche
  // tramite intestazione HTTP (oltre al meta robots nella pagina)
  routeRules: {
    '/privacy': { headers: { 'X-Robots-Tag': 'noindex, nofollow, noarchive' } },
    '/cookie': { headers: { 'X-Robots-Tag': 'noindex, nofollow, noarchive' } },
    '/chi-siamo': { headers: { 'X-Robots-Tag': 'noindex, nofollow, noarchive' } },
    '/dashboard/**': { headers: { 'X-Robots-Tag': 'noindex, nofollow' } },
    '/attiva-account': { headers: { 'X-Robots-Tag': 'noindex, nofollow' } },
    '/guida': { headers: { 'X-Robots-Tag': 'noindex, nofollow' } }
  },
  app: {
    head: {
      title: 'EnotecaMolise - I Grandi Vini del Molise',
      meta: [
        { name: 'theme-color', content: '#6B1D2F' },
        { name: 'description', content: 'Il portale gratuito dei vini e delle cantine del Molise: Tintilia, Biferno, Pentro, la mappa delle cantine e gli eventi. Contatta direttamente i produttori.' }
      ],
      link: [
        // icona del sito: "EM" in Cormorant Garamond su bordeaux (SVG per i browser moderni, ICO per gli altri)
        { rel: 'icon', href: '/favicon.ico', sizes: '48x48' },
        { rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' },
        { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' },
        { rel: 'manifest', href: '/site.webmanifest' },
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400;1,600&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap' },
        { rel: 'stylesheet', href: 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css' }
      ]
    }
  }
})
